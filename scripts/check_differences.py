#!/usr/bin/env python3
"""Check specific field differences between legacy and scoring systems."""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sotd.match.brush_parallel_data_manager import BrushParallelDataManager
from sotd.match.brush_system_comparator import BrushSystemComparator


def main():
    """Check specific field differences."""
    print("🔍 Checking field differences between systems...")

    # Load data
    manager = BrushParallelDataManager(base_path=Path("data"))
    old_data = manager.load_data("2025-05", "current")
    new_data = manager.load_data("2025-05", "new")

    # Create comparator
    comparator = BrushSystemComparator(old_data, new_data)
    results = comparator.compare_matches()

    print("\n📊 Comparison Results:")
    print(f"Total Records: {results['total_records']}")
    print(f"Matching Results: {results['matching_results']}")
    print(f"Different Results: {results['different_results']}")
    print(f"Old Only: {results['old_only_matches']}")
    print(f"New Only: {results['new_only_matches']}")
    print(f"Both Unmatched: {results['both_unmatched']}")

    # Check first few differences
    print("\n🔍 Sample Differences (first 3):")
    for i, diff in enumerate(results["detailed_differences"][:3]):
        print(f"\nDifference {i + 1}:")
        print(f"  Difference keys: {list(diff.keys())}")

        # Check what's in the difference
        if "old_match" in diff and "new_match" in diff:
            old_matched = diff["old_match"]
            new_matched = diff["new_match"]

            print(f"  Legacy brand/model: {old_matched.get('brand')} {old_matched.get('model')}")
            print(f"  Scoring brand/model: {new_matched.get('brand')} {new_matched.get('model')}")

            # Check specific field differences
            print("  Field differences:")
            for field in ["brand", "model", "fiber", "knot_size_mm", "handle_maker"]:
                old_val = old_matched.get(field)
                new_val = new_matched.get(field)
                if old_val != new_val:
                    print(f"    {field}: legacy='{old_val}' vs scoring='{new_val}'")

            # Check handle/knot structure differences
            if "handle" in old_matched and "handle" in new_matched:
                old_handle = old_matched["handle"]
                new_handle = new_matched["handle"]
                if old_handle != new_handle:
                    print("    handle section differs:")
                    for field in ["brand", "model", "_matched_by", "_pattern"]:
                        old_val = old_handle.get(field)
                        new_val = new_handle.get(field)
                        if old_val != new_val:
                            print(
                                f"      handle.{field}: legacy='{old_val}' vs scoring='{new_val}'"
                            )

            if "knot" in old_matched and "knot" in new_matched:
                old_knot = old_matched["knot"]
                new_knot = new_matched["knot"]
                if old_knot != new_knot:
                    print("    knot section differs:")
                    for field in [
                        "brand",
                        "model",
                        "fiber",
                        "knot_size_mm",
                        "_matched_by",
                        "_pattern",
                    ]:
                        old_val = old_knot.get(field)
                        new_val = new_knot.get(field)
                        if old_val != new_val:
                            print(f"      knot.{field}: legacy='{old_val}' vs scoring='{new_val}'")


if __name__ == "__main__":
    main()
