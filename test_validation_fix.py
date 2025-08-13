#!/usr/bin/env python3
"""Test script to verify the validation fix is working."""

import sys
from pathlib import Path


def test_validation_filtering():
    """Test that validated entries are properly filtered out."""

    # Add the project root to Python path
    project_root = Path(__file__).parent
    sys.path.insert(0, str(project_root))

    from sotd.match.brush_validation_counting_service import BrushValidationCountingService

    # Initialize the service
    service = BrushValidationCountingService(project_root / "data")

    # Test with 2025-06 data
    month = "2025-06"

    print(f"Testing validation filtering for {month}...")

    print("\nTesting UNVALIDATED entries method ONLY...")
    # Get strategy distribution statistics (should filter out validated entries)
    stats = service.get_strategy_distribution_statistics(month)

    print(f"Unvalidated - Total brush records: {stats['total_brush_records']}")
    print(f"Unvalidated - Correct matches count: {stats['correct_matches_count']}")
    print(f"Unvalidated - Remaining entries: {stats['remaining_entries']}")
    print(f"Unvalidated - Strategy counts: {stats['strategy_counts']}")
    print(f"Unvalidated - All strategies lengths: {stats['all_strategies_lengths']}")

    # Check if the counts make sense
    # We expect that validated entries (strategy: "correct_complete_brush") are excluded
    # So the counts should be much lower than before

    print("\nValidation check:")
    print("- If filtering is working, we should see fewer entries than before")
    print("- Previous counts showed 1: 14, 2: 20, 3: 389, 4: 438, 5: 122, 6: 18")
    print(f"- Current counts: {stats['all_strategies_lengths']}")

    # The key insight: validated entries have strategy "correct_complete_brush"
    # and should be excluded when only_unvalidated=True

    return stats


if __name__ == "__main__":
    test_validation_filtering()
