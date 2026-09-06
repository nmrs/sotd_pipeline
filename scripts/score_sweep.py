#!/usr/bin/env python3
"""Sweep brush scoring weights to find optimal configuration.

Strategy execution (expensive) runs once; scoring (cheap) re-runs per config.
A 20-step sweep takes ~90s for strategy collection + <1s per config.

Usage:
    # Show current baseline
    python scripts/score_sweep.py

    # Sweep one parameter
    python scripts/score_sweep.py --sweep base_strategies.known_brush=100:300:25

    # Sweep a modifier
    python scripts/score_sweep.py --sweep strategy_modifiers.automated_split.pattern_specificity=0:100:25

    # Grid search over multiple parameters
    python scripts/score_sweep.py \\
        --sweep base_strategies.known_brush=150:250:50 \\
        --sweep strategy_modifiers.automated_split.pattern_specificity=0:100:25

    # Test a single override (no range)
    python scripts/score_sweep.py --override base_strategies.known_brush=250

    # Restrict to specific categories
    python scripts/score_sweep.py --category brush --sweep base_strategies.known_brush=100:300:25

    # Show mismatches for the best configuration found
    python scripts/score_sweep.py --sweep base_strategies.known_brush=100:300:25 --verbose
"""

import argparse
import copy
import itertools
import sys
import time
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sotd.match.brush.matcher import BrushMatcher

# ---------------------------------------------------------------------------
# Evaluation helpers
# ---------------------------------------------------------------------------


def _load_yaml(path: Path) -> dict:
    with open(path) as f:
        return yaml.safe_load(f) or {}


def _extract_test_cases(data: dict, category: str) -> list[dict]:
    cases = []
    for level1_key, level2 in data.items():
        if not isinstance(level2, dict):
            continue
        for level2_key, inputs in level2.items():
            if not isinstance(inputs, list):
                continue
            for inp in inputs:
                if not isinstance(inp, str):
                    continue
                expected = {"input": inp, "_category": category}
                if category == "handle":
                    expected["handle_brand"] = level1_key
                    expected["handle_model"] = level2_key
                elif category == "knot":
                    expected["knot_brand"] = level1_key
                    expected["knot_model"] = level2_key
                elif category == "brush":
                    expected["brush_brand"] = level1_key
                    expected["brush_model"] = level2_key
                cases.append(expected)
    return cases


def _norm(val):
    if val is None:
        return None
    return str(val).strip().lower()


def _extract_fields(result) -> dict:
    if result is None or result.matched is None:
        return {}
    matched = result.matched
    handle = matched.get("handle", {}) if isinstance(matched.get("handle"), dict) else {}
    knot = matched.get("knot", {}) if isinstance(matched.get("knot"), dict) else {}
    return {
        "strategy": matched.get("strategy") or result.strategy,
        "handle_brand": handle.get("brand") or matched.get("handle_maker"),
        "handle_model": handle.get("model") or matched.get("handle_model"),
        "knot_brand": knot.get("brand") or matched.get("brand"),
        "knot_model": knot.get("model") or matched.get("model"),
        "brush_brand": matched.get("brand"),
        "brush_model": matched.get("model"),
    }


def _is_correct(expected: dict, actual: dict, category: str) -> bool:
    if category == "handle":
        fields = [("handle_brand", "handle_brand"), ("handle_model", "handle_model")]
    elif category == "knot":
        fields = [("knot_brand", "knot_brand"), ("knot_model", "knot_model")]
    elif category == "brush":
        fields = [("brush_brand", "brush_brand"), ("brush_model", "brush_model")]
    else:
        return True

    for exp_key, act_key in fields:
        exp_val = _norm(expected.get(exp_key))
        act_val = _norm(actual.get(act_key))
        if exp_val in ("_no_brand", "_no_model"):
            exp_val = None
        if exp_key.endswith("_model") and exp_val == "unspecified":
            continue
        if exp_val != act_val:
            return False
    return True


# ---------------------------------------------------------------------------
# Two-phase evaluation: collect once, rescore many times
# ---------------------------------------------------------------------------


def collect_strategy_results(matcher, categories):
    """Phase 1 (expensive): Run strategy execution for all test cases.

    Returns list of (input_str, category, expected, executable_results, cached_results).
    Strategy execution is the bottleneck (~90s for 5500 cases).
    """
    files = {
        "handle": Path("data/correct_matches/handle.yaml"),
        "knot": Path("data/correct_matches/knot.yaml"),
        "brush": Path("data/correct_matches/brush.yaml"),
    }

    # Collect all test cases
    all_cases = []
    for category in categories:
        path = files[category]
        if not path.exists():
            continue
        data = _load_yaml(path)
        all_cases.extend(_extract_test_cases(data, category))

    # Deduplicate strategy execution: same input string → same strategy results
    # (handle and knot share inputs, so we avoid running strategies twice)
    input_cache = {}  # input_str → (executable_results, cached_results)

    print(
        f"  Collecting strategy results for {len(all_cases)} test cases "
        f"({len(set(c['input'] for c in all_cases))} unique inputs)...",
        file=sys.stderr,
    )
    t0 = time.time()

    for case in all_cases:
        inp = case["input"]
        if inp not in input_cache:
            cached_results = matcher._precompute_handle_knot_results(inp)
            strategy_results = matcher.strategy_orchestrator.run_all_strategies(inp, cached_results)
            if strategy_results:
                executable_results = matcher._apply_dependency_constraints(strategy_results)
            else:
                executable_results = []
            input_cache[inp] = (executable_results, cached_results)

    elapsed = time.time() - t0
    print(f"  Done in {elapsed:.1f}s ({len(input_cache)} unique inputs cached)", file=sys.stderr)

    # Build full cache with category/expected info
    cache = []
    for case in all_cases:
        inp = case["input"]
        executable_results, cached_results = input_cache[inp]
        cache.append((inp, case["_category"], case, executable_results, cached_results))

    return cache


def rescore_evaluate(matcher, cache, categories):
    """Phase 2 (cheap): Re-score cached results with current config weights.

    Returns {category: {"total": N, "correct": N, "mismatches": N, "details": [...]}}.
    """
    results = {}
    for cat in categories:
        results[cat] = {"total": 0, "correct": 0, "mismatches": 0, "details": []}

    for inp, category, expected, executable_results, cached_results in cache:
        results[category]["total"] += 1

        if not executable_results:
            actual = {}
        else:
            scored = matcher.scoring_engine.score_results(executable_results, inp, cached_results)
            best = matcher.scoring_engine.get_best_result(scored)
            actual = _extract_fields(best)

        if _is_correct(expected, actual, category):
            results[category]["correct"] += 1
        else:
            results[category]["mismatches"] += 1
            results[category]["details"].append(
                {
                    "input": inp,
                    "expected": {
                        k: v for k, v in expected.items() if k not in ("input", "_category")
                    },
                    "actual": actual,
                }
            )

    return results


# ---------------------------------------------------------------------------
# Config manipulation
# ---------------------------------------------------------------------------


def get_weight(weights: dict, path: str) -> float:
    keys = path.split(".")
    d = weights
    for key in keys:
        d = d[key]
    return d


def set_weight(weights: dict, path: str, value: float) -> None:
    keys = path.split(".")
    d = weights
    for key in keys[:-1]:
        d = d[key]
    d[keys[-1]] = value


def parse_sweep(s: str) -> tuple[str, list[float]]:
    """Parse 'path=start:stop:step' into (path, [values])."""
    path, range_str = s.split("=", 1)
    parts = range_str.split(":")
    start = float(parts[0])
    stop = float(parts[1])
    step = float(parts[2]) if len(parts) > 2 else 10.0
    values = []
    v = start
    while v <= stop + 0.001:
        values.append(round(v, 2))
        v += step
    return path, values


def parse_override(s: str) -> tuple[str, float]:
    path, val = s.split("=", 1)
    return path, float(val)


# ---------------------------------------------------------------------------
# Output formatting
# ---------------------------------------------------------------------------


def total_mismatches(results: dict) -> int:
    return sum(r["mismatches"] for r in results.values())


def summary_line(results: dict, categories: list[str]) -> str:
    parts = []
    for cat in categories:
        if cat in results:
            r = results[cat]
            parts.append(f"{cat[0].upper()}:{r['correct']}/{r['total']}")
    parts.append(f"miss={total_mismatches(results)}")
    return "  ".join(parts)


def print_details(results: dict, max_per_category: int = 10):
    for category, r in sorted(results.items()):
        if not r["details"]:
            continue
        print(f"\n  {category.upper()} mismatches ({r['mismatches']}):")
        for d in r["details"][:max_per_category]:
            print(f"    INPUT: {d['input']}")
            print(f"    EXPECTED: {d['expected']}")
            actual_display = {k: v for k, v in d["actual"].items() if v is not None}
            print(f"    GOT:      {actual_display}")
        if r["mismatches"] > max_per_category:
            print(f"    ... and {r['mismatches'] - max_per_category} more")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main():
    parser = argparse.ArgumentParser(
        description="Sweep brush scoring weights to find optimal configuration",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--sweep",
        action="append",
        metavar="PARAM=START:STOP:STEP",
        help="Parameter to sweep (repeatable for grid search)",
    )
    parser.add_argument(
        "--override",
        action="append",
        metavar="PARAM=VALUE",
        help="Set a specific weight value (repeatable)",
    )
    parser.add_argument(
        "--category",
        "-c",
        action="append",
        choices=["handle", "knot", "brush"],
        help="Restrict to specific category (repeatable)",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Show mismatch details for best config (or baseline/override)",
    )
    args = parser.parse_args()

    categories = args.category or ["handle", "knot", "brush"]

    print("Initializing BrushMatcher...", file=sys.stderr)
    matcher = BrushMatcher()
    original_weights = copy.deepcopy(matcher.config.weights)

    # Phase 1: Collect strategy results (expensive, done once)
    cache = collect_strategy_results(matcher, categories)

    # Phase 2: Score with current config (baseline)
    baseline = rescore_evaluate(matcher, cache, categories)
    baseline_miss = total_mismatches(baseline)
    print(f"BASELINE ({baseline_miss} mismatches):  {summary_line(baseline, categories)}")

    # --- Single overrides (no sweep) ---
    if args.override and not args.sweep:
        for ov in args.override:
            path, value = parse_override(ov)
            set_weight(matcher.config.weights, path, value)

        results = rescore_evaluate(matcher, cache, categories)
        miss = total_mismatches(results)
        delta = miss - baseline_miss
        delta_str = f"+{delta}" if delta > 0 else str(delta)
        overrides_str = ", ".join(args.override)
        print(
            f"OVERRIDE ({miss} mismatches, {delta_str}):  "
            f"{summary_line(results, categories)}  [{overrides_str}]"
        )

        if args.verbose:
            print_details(results)

        matcher.config.weights = original_weights
        return

    # --- Baseline only ---
    if not args.sweep:
        if args.verbose:
            print_details(baseline)
        return

    # --- Sweep mode ---
    sweeps = [parse_sweep(s) for s in args.sweep]
    param_names = [s[0] for s in sweeps]
    param_values = [s[1] for s in sweeps]

    for name in param_names:
        cur = get_weight(original_weights, name)
        print(f"  current {name} = {cur}")

    combos = list(itertools.product(*param_values))
    print(f"  {len(combos)} configurations to evaluate\n")

    # Header
    col_headers = [name.split(".")[-1] for name in param_names]
    header = "  ".join(f"{h:>14s}" for h in col_headers)
    for cat in categories:
        header += f"  {cat[0].upper():>10s}"
    header += "    miss  delta"
    print(header)
    print("-" * len(header))

    all_results = []
    t0 = time.time()

    for combo in combos:
        matcher.config.weights = copy.deepcopy(original_weights)
        for name, value in zip(param_names, combo):
            set_weight(matcher.config.weights, name, value)

        results = rescore_evaluate(matcher, cache, categories)
        miss = total_mismatches(results)
        delta = miss - baseline_miss

        all_results.append((combo, results, miss))

        # Print row
        row = "  ".join(f"{v:>14.1f}" for v in combo)
        for cat in categories:
            if cat in results:
                r = results[cat]
                row += f"  {r['correct']:>5d}/{r['total']:<5d}"
        delta_str = f"+{delta}" if delta > 0 else str(delta)
        row += f"  {miss:>4d}  {delta_str:>5s}"
        print(row)

    elapsed = time.time() - t0
    matcher.config.weights = copy.deepcopy(original_weights)

    # Summary
    print(f"\n  Scored {len(combos)} configs in {elapsed:.1f}s")
    best_combo, best_results, best_miss = min(all_results, key=lambda x: x[2])
    delta = best_miss - baseline_miss
    delta_str = f"+{delta}" if delta > 0 else str(delta)
    best_params = ", ".join(f"{n}={v}" for n, v in zip(param_names, best_combo))
    print(f"BEST ({best_miss} mismatches, {delta_str} vs baseline):  {best_params}")

    tied = [c for c, _, m in all_results if m == best_miss]
    if len(tied) > 1:
        print(f"  ({len(tied)} configurations tied at {best_miss} mismatches)")

    if args.verbose:
        matcher.config.weights = copy.deepcopy(original_weights)
        for name, value in zip(param_names, best_combo):
            set_weight(matcher.config.weights, name, value)
        best_results = rescore_evaluate(matcher, cache, categories)
        print_details(best_results)
        matcher.config.weights = copy.deepcopy(original_weights)


if __name__ == "__main__":
    main()
