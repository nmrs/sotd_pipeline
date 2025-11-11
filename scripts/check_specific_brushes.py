#!/usr/bin/env python3
"""Check specific brushes that are failing to match in the scoring system."""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sotd.match.brush_parallel_data_manager import BrushParallelDataManager  # noqa: E402

from sotd.match.brush_matcher import BrushScoringMatcher  # noqa: E402


def main():
    """Check specific brushes."""
    print("🔍 Checking specific brushes...")

    # Load data
    manager = BrushParallelDataManager(base_path=Path("data"))
    old_data = manager.load_data("2025-05", "current")

    # Create scoring matcher
    scoring_matcher = BrushScoringMatcher()

    # Check specific brands that are failing
    target_brands = ["Summer Break", "Mountain Hare Shaving", "Maggard"]

    print("\n📋 Checking specific brushes:")
    for i, record in enumerate(old_data["data"]):
        brush = record.get("brush", {})
        matched = brush.get("matched", {})
        brand = matched.get("brand")

        if brand in target_brands:
            original_text = brush.get("original", "")
            print(f"\nRecord {i}:")
            print(f"  Original: {original_text}")
            print(f"  Legacy match: {brand} {matched.get('model')}")

            # Test with scoring system
            scoring_result = scoring_matcher.match(original_text)
            if scoring_result and scoring_result.matched:
                scoring_brand = scoring_result.matched.get("brand")
                scoring_model = scoring_result.matched.get("model")
                print(f"  Scoring match: {scoring_brand} {scoring_model}")
            else:
                print("  Scoring match: None")

            # Check legacy strategy
            handle = matched.get("handle", {})
            knot = matched.get("knot", {})
            print(f"  Legacy handle strategy: {handle.get('_matched_by')}")
            print(f"  Legacy knot strategy: {knot.get('_matched_by')}")

            # Remove this brand from target list to avoid duplicates
            target_brands.remove(brand)
            if not target_brands:
                break


if __name__ == "__main__":
    main()
