#!/usr/bin/env python3
"""Evaluate brush matcher accuracy against correct_matches golden dataset.

Runs the brush matcher (bypassing correct_matches lookups) against every input
string in data/correct_matches/{handle,knot,brush}.yaml and reports how many
handle brands, handle models, knot brands, knot models, and fibers are correct.

Usage:
    python scripts/eval_brush_matching.py              # summary only
    python scripts/eval_brush_matching.py --verbose    # show every mismatch
    python scripts/eval_brush_matching.py --category handle  # handle only
    python scripts/eval_brush_matching.py --strategy   # break down by winning strategy
"""

import argparse
import sys
from collections import defaultdict
from pathlib import Path

import yaml

# Ensure project root is importable
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sotd.match.brush.matcher import BrushMatcher


def load_yaml(path: Path) -> dict:
    with open(path) as f:
        return yaml.safe_load(f) or {}


def extract_test_cases(data: dict, category: str) -> list[dict]:
    """Extract (input_string, expected) pairs from correct_matches YAML.

    handle.yaml: brand -> model -> [inputs]
    knot.yaml:   brand -> fiber -> [inputs]
    brush.yaml:  brand -> fiber -> [inputs]  (whole-brush, no handle/knot split)
    """
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
                expected = {"input": inp}
                if category == "handle":
                    expected["handle_brand"] = level1_key
                    expected["handle_model"] = level2_key
                elif category == "knot":
                    expected["knot_brand"] = level1_key
                    expected["knot_model"] = level2_key  # this is fiber/model
                elif category == "brush":
                    expected["brush_brand"] = level1_key
                    expected["brush_model"] = level2_key
                cases.append(expected)
    return cases


def normalize_for_comparison(val):
    """Normalize a value for comparison (lowercase, strip, handle None)."""
    if val is None:
        return None
    return str(val).strip().lower()


def extract_result_fields(result, category: str) -> dict:
    """Pull the relevant fields from a MatchResult for comparison."""
    if result is None or result.matched is None:
        return {
            "strategy": None,
            "score": None,
            "handle_brand": None,
            "handle_model": None,
            "knot_brand": None,
            "knot_model": None,
            "brush_brand": None,
            "brush_model": None,
        }

    matched = result.matched
    strategy = matched.get("strategy") or result.strategy
    score = matched.get("score")

    # Split brush results have handle/knot sub-dicts
    handle = matched.get("handle", {}) if isinstance(matched.get("handle"), dict) else {}
    knot = matched.get("knot", {}) if isinstance(matched.get("knot"), dict) else {}

    # For whole-brush matches (no split), brand/model are top-level
    brush_brand = matched.get("brand")
    brush_model = matched.get("model")

    return {
        "strategy": strategy,
        "score": score,
        "handle_brand": handle.get("brand") or matched.get("handle_maker"),
        "handle_model": handle.get("model") or matched.get("handle_model"),
        "knot_brand": knot.get("brand") or matched.get("brand"),
        "knot_model": knot.get("model") or matched.get("model"),
        "knot_fiber": knot.get("fiber") or matched.get("fiber"),
        "brush_brand": brush_brand,
        "brush_model": brush_model,
    }


def compare(expected: dict, actual: dict, category: str) -> dict:
    """Compare expected vs actual, return field-level results."""
    results = {}

    if category == "handle":
        fields = [("handle_brand", "handle_brand"), ("handle_model", "handle_model")]
    elif category == "knot":
        fields = [("knot_brand", "knot_brand"), ("knot_model", "knot_model")]
    elif category == "brush":
        fields = [("brush_brand", "brush_brand"), ("brush_model", "brush_model")]
    else:
        fields = []

    for exp_key, act_key in fields:
        exp_val = normalize_for_comparison(expected.get(exp_key))
        act_val = normalize_for_comparison(actual.get(act_key))

        # Treat _no_brand / _no_model as None for comparison
        if exp_val in ("_no_brand", "_no_model"):
            exp_val = None

        # "unspecified" model means we don't check model
        if exp_key.endswith("_model") and exp_val == "unspecified":
            results[exp_key] = "skip"
            continue

        if exp_val == act_val:
            results[exp_key] = "correct"
        elif act_val is None:
            results[exp_key] = "missing"
        else:
            results[exp_key] = "wrong"

    return results


def run_evaluation(categories=None, verbose=False, by_strategy=False):
    """Run the evaluation and print results."""
    if categories is None:
        categories = ["handle", "knot", "brush"]

    files = {
        "handle": Path("data/correct_matches/handle.yaml"),
        "knot": Path("data/correct_matches/knot.yaml"),
        "brush": Path("data/correct_matches/brush.yaml"),
    }

    # Initialize matcher once (expensive)
    print("Initializing BrushMatcher...")
    matcher = BrushMatcher()
    print("Ready.\n")

    for category in categories:
        path = files[category]
        if not path.exists():
            print(f"Skipping {category}: {path} not found")
            continue

        data = load_yaml(path)
        cases = extract_test_cases(data, category)
        print(f"=== {category.upper()} ({len(cases)} test cases) ===\n")

        # Counters
        field_stats = defaultdict(lambda: {"correct": 0, "wrong": 0, "missing": 0, "skip": 0})
        strategy_stats = defaultdict(lambda: {"total": 0, "correct": 0})
        mismatches = []
        no_match_count = 0

        for case in cases:
            inp = case["input"]
            result = matcher.match(inp, inp, bypass_correct_matches=True)
            actual = extract_result_fields(result, category)
            comparison = compare(case, actual, category)

            strategy_name = actual["strategy"] or "no_match"
            if result is None:
                no_match_count += 1

            # Track per-field stats
            all_correct = True
            for field, outcome in comparison.items():
                field_stats[field][outcome] += 1
                if outcome not in ("correct", "skip"):
                    all_correct = False

            # Track per-strategy stats
            if by_strategy:
                strategy_stats[strategy_name]["total"] += 1
                if all_correct:
                    strategy_stats[strategy_name]["correct"] += 1

            # Collect mismatches for verbose output
            if not all_correct:
                mismatches.append(
                    {
                        "input": inp,
                        "expected": {k: v for k, v in case.items() if k != "input"},
                        "actual": {
                            k: v for k, v in actual.items() if k not in ("strategy", "score")
                        },
                        "strategy": strategy_name,
                        "score": actual.get("score"),
                        "comparison": comparison,
                    }
                )

        # Print summary
        total = len(cases)
        print(f"  No match: {no_match_count}/{total} ({no_match_count / total * 100:.1f}%)\n")

        for field, stats in sorted(field_stats.items()):
            evaluated = stats["correct"] + stats["wrong"] + stats["missing"]
            if evaluated == 0:
                continue
            pct = stats["correct"] / evaluated * 100
            print(
                f"  {field:20s}  correct={stats['correct']:4d}  "
                f"wrong={stats['wrong']:4d}  missing={stats['missing']:4d}  "
                f"skip={stats['skip']:4d}  accuracy={pct:.1f}%"
            )

        # Strategy breakdown
        if by_strategy and strategy_stats:
            print("\n  Strategy breakdown:")
            for strat, stats in sorted(strategy_stats.items(), key=lambda x: -x[1]["total"]):
                pct = stats["correct"] / stats["total"] * 100 if stats["total"] > 0 else 0
                print(
                    f"    {strat:40s}  total={stats['total']:4d}  correct={stats['correct']:4d}  ({pct:.1f}%)"
                )

        # Verbose mismatches
        if verbose and mismatches:
            print(f"\n  Mismatches ({len(mismatches)}):")
            for m in mismatches[:50]:  # cap at 50 to avoid overwhelming output
                print(f"\n    INPUT: {m['input']}")
                print(f"    EXPECTED: {m['expected']}")
                actual_display = {k: v for k, v in m["actual"].items() if v is not None}
                print(f"    GOT:      {actual_display}")
                print(f"    STRATEGY: {m['strategy']}  SCORE: {m['score']}")
            if len(mismatches) > 50:
                print(f"\n    ... and {len(mismatches) - 50} more")

        print()


def main():
    parser = argparse.ArgumentParser(description="Evaluate brush matcher against golden dataset")
    parser.add_argument("--verbose", "-v", action="store_true", help="Show individual mismatches")
    parser.add_argument(
        "--category",
        "-c",
        choices=["handle", "knot", "brush"],
        help="Evaluate only one category",
    )
    parser.add_argument(
        "--strategy", "-s", action="store_true", help="Break down results by strategy"
    )
    args = parser.parse_args()

    categories = [args.category] if args.category else None
    run_evaluation(categories=categories, verbose=args.verbose, by_strategy=args.strategy)


if __name__ == "__main__":
    main()
