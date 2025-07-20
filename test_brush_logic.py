#!/usr/bin/env python3
"""Test script to verify brush unmatched logic."""

import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from sotd.match.tools.analyzers.unmatched_analyzer import UnmatchedAnalyzer


def test_brush_logic():
    """Test the brush unmatched logic."""
    analyzer = UnmatchedAnalyzer()

    # Create mock args
    class MockArgs:
        def __init__(self):
            self.field = "brush"
            self.months = ["2025-01"]
            self.month = "2025-01"  # Required by date_span
            self.limit = 5
            self.out_dir = "data"  # Required by analysis_base
            self.debug = False  # Required by analysis_base

    args = MockArgs()

    # Test the analyze_unmatched method
    result = analyzer.analyze_unmatched(args)

    print("=== Brush Unmatched Analysis Result ===")
    print(f"Field: {result['field']}")
    print(f"Total unmatched: {result['total_unmatched']}")
    print(f"Items returned: {len(result['unmatched_items'])}")

    if result["unmatched_items"]:
        print("\n=== First Item Structure ===")
        first_item = result["unmatched_items"][0]
        print(f"Item: {first_item['item']}")
        print(f"Count: {first_item['count']}")
        print(f"Examples: {first_item['examples']}")
        print(f"Comment IDs: {first_item['comment_ids']}")

        if "unmatched" in first_item:
            print(f"Unmatched structure: {first_item['unmatched']}")

        if "matched" in first_item:
            print(f"Matched structure: {first_item['matched']}")


if __name__ == "__main__":
    test_brush_logic()
