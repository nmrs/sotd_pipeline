#!/usr/bin/env python3
"""
Compare user intent results between match and enrich phases.

This script loads the output from both phases and compares the user_intent
field to ensure 100% consistency in the migration.
"""

import json
import sys
from pathlib import Path
from typing import Any, Dict, List


def load_phase_data(phase: str, month: str) -> List[Dict[str, Any]]:
    """Load data from a specific phase for a given month."""
    data_file = Path(f"data/{phase}/{month}.json")
    if not data_file.exists():
        print(f"Error: {data_file} does not exist")
        return []

    with open(data_file, "r") as f:
        data = json.load(f)

    return data.get("data", [])


def extract_brush_records(data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Extract brush records from phase data."""
    brush_records = []

    for record in data:
        if "brush" in record:
            brush_data = record["brush"]
            if isinstance(brush_data, dict):
                # Check for user_intent in different possible locations
                user_intent = None

                # Check in matched section (match phase)
                if "matched" in brush_data and isinstance(brush_data["matched"], dict):
                    user_intent = brush_data["matched"].get("user_intent")

                # Check in enriched section (enrich phase)
                if "enriched" in brush_data and isinstance(brush_data["enriched"], dict):
                    user_intent = brush_data["enriched"].get("user_intent")

                # Check at top level (fallback)
                if user_intent is None:
                    user_intent = brush_data.get("user_intent")

                if user_intent is not None:
                    brush_records.append(
                        {
                            "original_comment": record.get("original_comment", ""),
                            "brush": brush_data,
                            "user_intent": user_intent,
                        }
                    )

    return brush_records


def compare_user_intent(
    match_records: List[Dict[str, Any]], enrich_records: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """Compare user intent between match and enrich phases."""

    # Create lookup by original comment
    match_lookup = {record["original_comment"]: record["user_intent"] for record in match_records}
    enrich_lookup = {record["original_comment"]: record["user_intent"] for record in enrich_records}

    # Find common comments
    common_comments = set(match_lookup.keys()) & set(enrich_lookup.keys())

    discrepancies = []
    match_only = []
    enrich_only = []
    consistent = 0

    # Check for discrepancies in common comments
    for comment in common_comments:
        match_intent = match_lookup[comment]
        enrich_intent = enrich_lookup[comment]

        if match_intent != enrich_intent:
            discrepancies.append(
                {"comment": comment, "match_intent": match_intent, "enrich_intent": enrich_intent}
            )
        else:
            consistent += 1

    # Find records only in match phase
    for comment in set(match_lookup.keys()) - set(enrich_lookup.keys()):
        match_only.append({"comment": comment, "match_intent": match_lookup[comment]})

    # Find records only in enrich phase
    for comment in set(enrich_lookup.keys()) - set(match_lookup.keys()):
        enrich_only.append({"comment": comment, "enrich_intent": enrich_lookup[comment]})

    return {
        "total_match_records": len(match_records),
        "total_enrich_records": len(enrich_records),
        "common_records": len(common_comments),
        "consistent_records": consistent,
        "discrepancies": discrepancies,
        "match_only": match_only,
        "enrich_only": enrich_only,
        "consistency_percentage": (
            (consistent / len(common_comments) * 100) if common_comments else 0
        ),
    }


def print_comparison_results(results: Dict[str, Any]) -> bool:
    """Print formatted comparison results."""
    print("=" * 80)
    print("USER INTENT MIGRATION VALIDATION RESULTS")
    print("=" * 80)

    print("\n📊 SUMMARY:")
    print(f"  Match phase records: {results['total_match_records']}")
    print(f"  Enrich phase records: {results['total_enrich_records']}")
    print(f"  Common records: {results['common_records']}")
    print(f"  Consistent records: {results['consistent_records']}")
    print(f"  Consistency: {results['consistency_percentage']:.2f}%")

    if results["discrepancies"]:
        print(f"\n❌ DISCREPANCIES ({len(results['discrepancies'])}):")
        for i, disc in enumerate(results["discrepancies"][:10], 1):  # Show first 10
            print(f"  {i}. Comment: {disc['comment'][:100]}...")
            print(f"     Match: {disc['match_intent']} | Enrich: {disc['enrich_intent']}")
        if len(results["discrepancies"]) > 10:
            remaining = len(results["discrepancies"]) - 10
            print(f"     ... and {remaining} more")

    if results["match_only"]:
        print(f"\n⚠️  MATCH ONLY ({len(results['match_only'])}):")
        for i, record in enumerate(results["match_only"][:5], 1):  # Show first 5
            print(f"  {i}. Comment: {record['comment'][:100]}...")
            print(f"     Intent: {record['match_intent']}")
        if len(results["match_only"]) > 5:
            remaining = len(results["match_only"]) - 5
            print(f"     ... and {remaining} more")

    if results["enrich_only"]:
        print(f"\n⚠️  ENRICH ONLY ({len(results['enrich_only'])}):")
        for i, record in enumerate(results["enrich_only"][:5], 1):  # Show first 5
            print(f"  {i}. Comment: {record['comment'][:100]}...")
            print(f"     Intent: {record['enrich_intent']}")
        if len(results["enrich_only"]) > 5:
            remaining = len(results["enrich_only"]) - 5
            print(f"     ... and {remaining} more")

    print("\n" + "=" * 80)

    if (
        results["consistency_percentage"] == 100.0
        and not results["match_only"]
        and not results["enrich_only"]
    ):
        print("✅ VALIDATION PASSED: 100% consistency between phases")
        return True
    else:
        print("❌ VALIDATION FAILED: Inconsistencies found")
        return False


def main():
    """Main comparison function."""
    if len(sys.argv) != 2:
        print("Usage: python compare_user_intent_results.py <month>")
        print("Example: python compare_user_intent_results.py 2025-05")
        sys.exit(1)

    month = sys.argv[1]

    print(f"Comparing user intent results for {month}...")

    # Load data from both phases
    match_data = load_phase_data("matched", month)
    enrich_data = load_phase_data("enriched", month)

    if not match_data:
        print(f"Error: No match data found for {month}")
        sys.exit(1)

    if not enrich_data:
        print(f"Error: No enrich data found for {month}")
        sys.exit(1)

    # Extract brush records with user_intent
    match_records = extract_brush_records(match_data)
    enrich_records = extract_brush_records(enrich_data)

    print(f"Found {len(match_records)} brush records with user_intent in match phase")
    print(f"Found {len(enrich_records)} brush records with user_intent in enrich phase")

    # Compare results
    results = compare_user_intent(match_records, enrich_records)

    # Print results
    success = print_comparison_results(results)

    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
