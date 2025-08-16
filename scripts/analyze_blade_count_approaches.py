#!/usr/bin/env python3
"""
Comprehensive analysis of blade count extraction approaches.

Compares the current regex-based approach (A) with the new normalization-difference
approach (B) across the full corpus of matched data to identify gaps and differences.
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Tuple, Any

from sotd.utils.match_filter_utils import (
    extract_blade_and_use_count,
    extract_blade_use_count_via_normalization,
)


def load_matched_data(month: str) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
    """Load matched data for a specific month."""
    file_path = Path(f"data/matched/{month}.json")
    if not file_path.exists():
        return {}, []

    with open(file_path, "r") as f:
        data = json.load(f)

    metadata = data.get("metadata", {})
    records = data.get("data", [])
    return metadata, records


def analyze_blade_records(records: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Analyze all blade records in the matched data."""
    analysis = {
        "total_blades": 0,
        "approaches_match": 0,
        "approaches_differ": 0,
        "approach_a_only": 0,
        "approach_b_only": 0,
        "differences": [],
        "approach_a_only_cases": [],
        "approach_b_only_cases": [],
        "performance_data": {
            "approach_a_time": 0.0,
            "approach_b_time": 0.0,
        },
    }

    for record in records:
        if "blade" not in record:
            continue

        blade_data = record["blade"]
        if not isinstance(blade_data, dict):
            continue

        original = blade_data.get("original", "")
        normalized = blade_data.get("normalized", "")
        matched = blade_data.get("matched", {})
        model = matched.get("model") if matched else None

        if not original or not normalized:
            continue

        analysis["total_blades"] += 1

        # Extract counts using both approaches
        import time

        # Time Approach A
        start_time = time.time()
        result_a = extract_blade_and_use_count(original, model)
        approach_a_time = time.time() - start_time
        analysis["performance_data"]["approach_a_time"] += approach_a_time

        # Time Approach B
        start_time = time.time()
        result_b = extract_blade_use_count_via_normalization(original, normalized, model)
        approach_b_time = time.time() - start_time
        analysis["performance_data"]["approach_b_time"] += approach_b_time

        # Compare results
        if result_a == result_b:
            analysis["approaches_match"] += 1
        else:
            analysis["approaches_differ"] += 1

            # Record the difference
            diff_record = {
                "original": original,
                "normalized": normalized,
                "model": model,
                "approach_a": result_a,
                "approach_b": result_b,
                "difference_type": "different_results",
            }
            analysis["differences"].append(diff_record)

            # Categorize the difference
            if result_a and not result_b:
                analysis["approach_a_only"] += 1
                analysis["approach_a_only_cases"].append(diff_record)
            elif result_b and not result_a:
                analysis["approach_b_only"] += 1
                analysis["approach_b_only_cases"].append(diff_record)

    return analysis


def analyze_patterns_in_differences(differences: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Analyze patterns in the differences to understand what we're missing."""
    pattern_analysis = {
        "ordinal_patterns": [],
        "special_patterns": [],
        "complex_patterns": [],
        "model_confusion": [],
        "other_patterns": [],
    }

    for diff in differences:
        original = diff["original"]
        approach_a = diff["approach_a"]
        approach_b = diff["approach_b"]

        # Categorize based on patterns
        if re.search(r"\b\d+(?:st|nd|rd|th)\b", original, re.IGNORECASE):
            pattern_analysis["ordinal_patterns"].append(diff)
        elif re.search(r"\(x\d+\)", original, re.IGNORECASE):
            pattern_analysis["special_patterns"].append(diff)
        elif re.search(r"\(\d+x\)", original, re.IGNORECASE):
            pattern_analysis["complex_patterns"].append(diff)
        elif re.search(r"\(\d+\)", original) and approach_a and not approach_b:
            # This might be model confusion
            pattern_analysis["model_confusion"].append(diff)
        else:
            pattern_analysis["other_patterns"].append(diff)

    return pattern_analysis


def print_analysis_summary(analysis: Dict[str, Any], month: str):
    """Print a comprehensive analysis summary."""
    print(f"\n{'=' * 80}")
    print(f"BLADE COUNT APPROACH ANALYSIS - {month}")
    print(f"{'=' * 80}")

    print(f"\n📊 OVERALL STATISTICS:")
    print(f"  Total blade records: {analysis['total_blades']:,}")
    match_pct = analysis["approaches_match"] / analysis["total_blades"] * 100
    print(f"  Approaches match: {analysis['approaches_match']:,} ({match_pct:.1f}%)")
    diff_pct = analysis["approaches_differ"] / analysis["total_blades"] * 100
    print(f"  Approaches differ: {analysis['approaches_differ']:,} ({diff_pct:.1f}%)")

    print(f"\n🔍 DIFFERENCE BREAKDOWN:")
    print(f"  Approach A only (regex catches): {analysis['approach_a_only']:,}")
    print(f"  Approach B only (normalization catches): {analysis['approach_b_only']:,}")

    print(f"\n⚡ PERFORMANCE COMPARISON:")
    total_time_a = analysis["performance_data"]["approach_a_time"]
    total_time_b = analysis["performance_data"]["approach_b_time"]
    speedup = total_time_a / total_time_b if total_time_b > 0 else float("inf")
    print(f"  Approach A total time: {total_time_a:.4f}s")
    print(f"  Approach B total time: {total_time_b:.4f}s")
    print(f"  Speedup: {speedup:.1f}x")

    if analysis["differences"]:
        print(f"\n❌ DETAILED DIFFERENCES ({len(analysis['differences'])} cases):")
        print(f"{'=' * 80}")

        # Show first 10 differences
        for i, diff in enumerate(analysis["differences"][:10]):
            print(f"\n{i + 1}. Original: {diff['original']}")
            print(f"   Normalized: {diff['normalized']}")
            print(f"   Model: {diff['model']}")
            print(f"   Approach A: {diff['approach_a']}")
            print(f"   Approach B: {diff['approach_b']}")
            print(f"   {'-' * 60}")

        if len(analysis["differences"]) > 10:
            remaining = len(analysis["differences"]) - 10
            print(f"\n... and {remaining} more differences")


def main():
    """Main analysis function."""
    print("🔍 COMPREHENSIVE BLADE COUNT APPROACH ANALYSIS")
    print("=" * 80)

    # Find all matched data files
    matched_dir = Path("data/matched")
    if not matched_dir.exists():
        print("❌ No matched data directory found")
        return

    matched_files = sorted([f.stem for f in matched_dir.glob("*.json")])
    print(f"📁 Found {len(matched_files)} matched data files: {', '.join(matched_files)}")

    # Analyze each month
    all_analysis = {}
    total_stats = {
        "total_blades": 0,
        "approaches_match": 0,
        "approaches_differ": 0,
        "approach_a_only": 0,
        "approach_b_only": 0,
        "total_time_a": 0.0,
        "total_time_b": 0.0,
    }

    for month in matched_files:
        print(f"\n📅 Analyzing {month}...")

        metadata, records = load_matched_data(month)
        if not records:
            print(f"  ⚠️  No data found for {month}")
            continue

        analysis = analyze_blade_records(records)
        all_analysis[month] = analysis

        # Print summary for this month
        print_analysis_summary(analysis, month)

        # Accumulate totals
        total_stats["total_blades"] += analysis["total_blades"]
        total_stats["approaches_match"] += analysis["approaches_match"]
        total_stats["approaches_differ"] += analysis["approaches_differ"]
        total_stats["approach_a_only"] += analysis["approach_a_only"]
        total_stats["approach_b_only"] += analysis["approach_b_only"]
        total_stats["total_time_a"] += analysis["performance_data"]["approach_a_time"]
        total_stats["total_time_b"] += analysis["performance_data"]["approach_b_time"]

    # Print overall summary
    print(f"\n{'=' * 80}")
    print("🎯 OVERALL CORPUS ANALYSIS SUMMARY")
    print(f"{'=' * 80}")

    print(f"\n📊 TOTAL STATISTICS ACROSS ALL MONTHS:")
    print(f"  Total blade records: {total_stats['total_blades']:,}")
    total_match_pct = total_stats["approaches_match"] / total_stats["total_blades"] * 100
    print(f"  Approaches match: {total_stats['approaches_match']:,} ({total_match_pct:.1f}%)")
    total_diff_pct = total_stats["approaches_differ"] / total_stats["total_blades"] * 100
    print(f"  Approaches differ: {total_stats['approaches_differ']:,} ({total_diff_pct:.1f}%)")

    print(f"\n🔍 OVERALL DIFFERENCE BREAKDOWN:")
    print(f"  Approach A only (regex catches): {total_stats['approach_a_only']:,}")
    print(f"  Approach B only (normalization catches): {total_stats['approach_b_only']:,}")

    print(f"\n⚡ OVERALL PERFORMANCE:")
    speedup = (
        total_stats["total_time_a"] / total_stats["total_time_b"]
        if total_stats["total_time_b"] > 0
        else float("inf")
    )
    print(f"  Total time Approach A: {total_stats['total_time_a']:.4f}s")
    print(f"  Total time Approach B: {total_stats['total_time_b']:.4f}s")
    print(f"  Overall speedup: {speedup:.1f}x")

    # Pattern analysis for differences
    all_differences = []
    for month_analysis in all_analysis.values():
        all_differences.extend(month_analysis["differences"])

    if all_differences:
        pattern_analysis = analyze_patterns_in_differences(all_differences)

        print(f"\n🔍 PATTERN ANALYSIS OF DIFFERENCES:")
        print(f"  Ordinal patterns (1st, 2nd, etc.): {len(pattern_analysis['ordinal_patterns'])}")
        print(f"  Special patterns (x1, x2, etc.): {len(pattern_analysis['special_patterns'])}")
        print(f"  Complex patterns (2x, 3x, etc.): {len(pattern_analysis['complex_patterns'])}")
        print(f"  Model confusion cases: {len(pattern_analysis['model_confusion'])}")
        print(f"  Other patterns: {len(pattern_analysis['other_patterns'])}")

        # Show examples of each pattern type
        for pattern_type, cases in pattern_analysis.items():
            if cases:
                print(f"\n📝 {pattern_type.upper()} EXAMPLES:")
                for case in cases[:3]:  # Show first 3 examples
                    print(
                        f"  - {case['original']} -> A:{case['approach_a']} B:{case['approach_b']}"
                    )
                if len(cases) > 3:
                    remaining = len(cases) - 3
                    print(f"    ... and {remaining} more")


if __name__ == "__main__":
    main()
