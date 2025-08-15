#!/usr/bin/env python3
"""Test our regex against real backslash cases found in the data."""

import re


def test_real_cases():
    """Test our regex against real backslash cases."""

    # Our unified pattern
    simple_pattern = (
        r"(?:[\(\[]|\\[\(\[])\s*\d+\s*(?:[\)\]]|\\[\)\]])\s*" r"(?:[#$]\w+(?:\s+[#$]\w+)*|\.|\s*$)"
    )

    # Real cases from the unanalyzed file
    real_cases = [
        "Astra SS (7\\~8 uses - solid blade, too bad I haven't discovered it earlier)",
        "Gillette Platinum \\(3rd shave\\)",
        "Gillette Platinum \\(4rd shave\\)",
        "Treet Platinum (14)\\",
        "Vokshod (ive lost track how many shaves this is its over a week at this point \\~9 days)",
    ]

    print("Testing our regex against real backslash cases:")
    print(f"Pattern: {simple_pattern}")
    print()

    for test_case in real_cases:
        match = re.search(simple_pattern, test_case, re.IGNORECASE)
        result = "✅ MATCH" if match else "❌ NO MATCH"
        print(f"{result}: {repr(test_case)}")
        if match:
            print(f"  Matched: {match.group()}")
        else:
            print(f"  Why no match? Let's analyze...")
            # Check what parts we can match
            escaped_open_match = re.search(r"\\[\(\[]", test_case)
            if escaped_open_match:
                print(f"    Has escaped opening: {escaped_open_match.group()}")
            escaped_close_match = re.search(r"\\[\)\]]", test_case)
            if escaped_close_match:
                print(f"    Has escaped closing: {escaped_close_match.group()}")
            digits_match = re.search(r"\d+", test_case)
            if digits_match:
                print(f"    Has digits: {digits_match.group()}")


if __name__ == "__main__":
    test_real_cases()
