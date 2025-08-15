#!/usr/bin/env python3
"""Test the unified regex pattern for both normal and escaped parentheses."""

import re


def test_unified_regex():
    """Test the unified regex pattern."""

    # Our unified pattern
    simple_pattern = (
        r"(?:[\(\[]|\\[\(\[])\s*\d+\s*(?:[\)\]]|\\[\)\]])\s*" r"(?:[#$]\w+(?:\s+[#$]\w+)*|\.|\s*$)"
    )

    # Test cases
    test_cases = [
        "Astra SP (1)",  # Normal parentheses
        "Astra SP (2) $tag",  # With tag
        "Astra SP (3) #tag",  # With hash tag
        "Astra SP (4).",  # With period
        "Astra SP \\(5\\)",  # Escaped parentheses
        "Astra SP \\(6\\) $tag",  # Escaped with tag
        "Astra SP \\(7\\) #tag",  # Escaped with hash tag
        "Astra SP \\(8\\).",  # Escaped with period
        "Astra SP [9]",  # Square brackets
        "Astra SP \\[10\\]",  # Escaped square brackets
    ]

    print("Testing unified regex pattern:")
    print(f"Pattern: {simple_pattern}")
    print()

    for test_case in test_cases:
        match = re.search(simple_pattern, test_case, re.IGNORECASE)
        result = "✅ MATCH" if match else "❌ NO MATCH"
        print(f"{result}: {repr(test_case)}")
        if match:
            print(f"  Matched: {match.group()}")


if __name__ == "__main__":
    test_unified_regex()
