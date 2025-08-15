#!/usr/bin/env python3
"""Test our updated regex for question mark patterns."""

import re


def test_question_mark_patterns():
    """Test the updated regex for question mark patterns."""

    # Our updated pattern
    simple_pattern = (
        r"(?:[\(\[]|\\[\(\[])\s*\d+\s*\??\s*(?:[\)\]]|\\[\)\]])\s*"
        r"(?:[#$]\w+(?:\s+[#$]\w+)*|\.|\s*$)"
    )

    # Test cases including question marks
    test_cases = [
        "Astra SP (1)",  # Normal parentheses
        "Astra SP (2) $tag",  # With tag
        "Astra SP (3) #tag",  # With hash tag
        "Astra SP (4).",  # With period
        "Astra SP (5?)",  # With question mark
        "Astra SP (6?) $tag",  # Question mark with tag
        "Astra SP (7?) #tag",  # Question mark with hash tag
        "Astra SP (8?).",  # Question mark with period
        "Astra SP \\(9\\)",  # Escaped parentheses
        "Astra SP \\(10?\\)",  # Escaped with question mark
    ]

    print("Testing updated regex for question mark patterns:")
    print(f"Pattern: {simple_pattern}")
    print()

    for test_case in test_cases:
        match = re.search(simple_pattern, test_case, re.IGNORECASE)
        result = "✅ MATCH" if match else "❌ NO MATCH"
        print(f"{result}: {repr(test_case)}")
        if match:
            print(f"  Matched: {match.group()}")


if __name__ == "__main__":
    test_question_mark_patterns()
