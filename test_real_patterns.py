#!/usr/bin/env python3
"""Test script to verify pattern fix works with real YAML files."""

import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from sotd.match.brush_matcher import BrushMatcher
from sotd.match.config import BrushMatcherConfig


def test_real_patterns():
    """Test pattern fields with real YAML files."""
    print("Testing pattern fields with real YAML files...")
    print("=" * 60)

    # Create brush matcher with real YAML files
    config = BrushMatcherConfig.create_default()
    matcher = BrushMatcher(config=config)

    # Test the specific case
    result = matcher.match("Jayaruh #441 w/ AP Shave Co G5C")

    if result:
        print(f"Match Type: {result.match_type}")
        print(f"Pattern: {result.pattern}")

        if "handle" in result.matched:
            handle = result.matched["handle"]
            print(f"Handle Pattern: {handle.get('_pattern', 'NOT FOUND')}")
            print(f"Handle Brand: {handle.get('brand', 'NOT FOUND')}")
            print(f"Handle Matched By: {handle.get('_matched_by', 'NOT FOUND')}")

        if "knot" in result.matched:
            knot = result.matched["knot"]
            print(f"Knot Pattern: {knot.get('_pattern', 'NOT FOUND')}")
            print(f"Knot Brand: {knot.get('brand', 'NOT FOUND')}")
            print(f"Knot Matched By: {knot.get('_matched_by', 'NOT FOUND')}")

        print("\nExpected patterns:")
        print("- Handle pattern should be: jayaruh")
        print("- Knot pattern should be: \\ba[\\s.]*p\\b.*g5c")
        print("- Both should NOT be 'split'")
    else:
        print("No match found!")


if __name__ == "__main__":
    test_real_patterns()
