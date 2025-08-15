#!/usr/bin/env python3
"""Test script to verify backslash handling."""

import json
from pathlib import Path


def test_backslash_handling():
    """Test how Python handles backslashes in JSON."""

    # Test with the actual file
    file_path = Path("data/extracted/2018-05.json")

    print("Testing backslash handling in JSON...")

    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Find backslash strings
    backslash_strings = []
    for record in data.get("data", []):
        if "blade" in record and isinstance(record["blade"], dict):
            original = record["blade"].get("original")
            if original and isinstance(original, str):
                # Check for different backslash patterns
                if "\\\\" in original:
                    backslash_strings.append(("double", original))
                elif "\\\\" in original:
                    backslash_strings.append(("single", original))

    print(f"Found {len(backslash_strings)} backslash strings")

    for pattern_type, string in backslash_strings[:3]:
        print(f"  {pattern_type}: {repr(string)}")
        print(f"    Length: {len(string)}")
        print(f"    Bytes: {string.encode()}")
        double_backslash = "\\\\" in string
        single_backslash = "\\\\" in string
        print(f"    Contains double backslash: {double_backslash}")
        print(f"    Contains single backslash: {single_backslash}")


if __name__ == "__main__":
    test_backslash_handling()
