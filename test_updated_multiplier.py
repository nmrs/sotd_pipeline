#!/usr/bin/env python3
"""Test our updated multiplier regex for both patterns."""

import re


def test_updated_multiplier_regex():
    """Test the updated multiplier regex pattern."""

    # Our updated pattern
    multiplier_pattern = (
        r"[\(\[]\s*(?:\d+\s*[xX]|[xX]\s*\d+)\s*[\)\]]\s*" r"(?:[#$]\w+(?:\s+[#$]\w+)*|\.|\s*$)"
    )

    # Test cases
    test_cases = [
        "my blade (2X)",  # Uppercase X
        "my blade (2x)",  # Lowercase x
        "my blade (3X) $tag",  # With tag
        "my blade (4x) #tag",  # With hash tag
        "my blade (5X).",  # With period
        "my blade (6x)",  # Just lowercase x
        "GWS Chinese (x2)",  # Real example from unanalyzed
        "GWS Chinese (x3)",  # Real example from unanalyzed
        "my blade (x5)",  # x first, then digit
        "my blade (X6)",  # X first, then digit
    ]

    print("Testing updated multiplier regex pattern:")
    print(f"Pattern: {multiplier_pattern}")
    print()

    for test_case in test_cases:
        match = re.search(multiplier_pattern, test_case, re.IGNORECASE)
        result = "✅ MATCH" if match else "❌ NO MATCH"
        print(f"{result}: {repr(test_case)}")
        if match:
            print(f"  Matched: {match.group()}")


if __name__ == "__main__":
    test_updated_multiplier_regex()
