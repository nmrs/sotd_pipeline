#!/usr/bin/env python3
"""
Analyze the most promising patterns from the skipped patterns analysis.
"""

import json


def analyze_promising_patterns():
    """Analyze the most promising patterns for extraction enhancement."""

    with open("skipped_patterns_analysis.json", "r") as f:
        data = json.load(f)

    print("=" * 80)
    print("PROMISING PATTERNS FOR EXTRACTION ENHANCEMENT")
    print("=" * 80)

    # Focus on patterns that could be parsed
    promising_patterns = [
        "checkmark_format",
        "plain_colon_format",
        "dash_prefix_format",
        "asterisk_format",
        "emoji_bold_format",
        "sotd_header_format",
    ]

    total_skipped = data["total_skipped"]

    for pattern in promising_patterns:
        if pattern in data["examples"]:
            examples = data["examples"][pattern]
            count = data["pattern_counts"][pattern]
            percentage = (count / total_skipped) * 100

            print(f"\n{pattern.upper()} ({count} occurrences, {percentage:.1f}%):")
            print("-" * 60)

            for i, example in enumerate(examples[:5]):  # Show first 5 examples
                print(f"{i + 1}. {example['line']}")
                print(f"   Month: {example['month']}")
                print()

    # Calculate total potential gain
    total_potential = sum(data["pattern_counts"].get(p, 0) for p in promising_patterns)
    print(f"\n{'=' * 80}")
    print(f"TOTAL POTENTIAL GAIN: {total_potential} additional extractions")
    print(f"This represents {(total_potential / total_skipped) * 100:.1f}% of all skipped comments")
    print(f"{'=' * 80}")


def suggest_regex_patterns():
    """Suggest regex patterns for the promising formats."""

    print("\n" + "=" * 80)
    print("SUGGESTED REGEX PATTERNS FOR EXTRACTION ENHANCEMENT")
    print("=" * 80)

    patterns = {
        "checkmark_format": [
            r"^✓\s*(\w+)\s*[-:]\s*(.+)$",  # ✓Field: Value
            r"^✓\s*(\w+)\s*[-:]\s*(.+)$",  # ✓ Field: Value (with space)
        ],
        "plain_colon_format": [
            r"^(\w+)\s*[-:]\s*(.+)$",  # Field: Value
        ],
        "dash_prefix_format": [
            r"^-\s*(\w+)\s*[-:]\s*(.+)$",  # - Field: Value
        ],
        "asterisk_format": [
            r"^\*\s*(\w+)\s*[-:]\s*(.+)$",  # * Field: Value
        ],
        "emoji_bold_format": [
            r"^\*\s*\*\*([^*]+)\*\*\s*[-:]\s*(.+)$",  # * **Field** Value
        ],
        "sotd_header_format": [
            r"^\*\s*\*\*SOTD\s*[-:]\s*(.+)\*\*$",  # * **SOTD - Date**
        ],
    }

    for pattern_name, regex_list in patterns.items():
        print(f"\n{pattern_name.upper()}:")
        for regex in regex_list:
            print(f"  {regex}")

    print(f"\n{'=' * 80}")


if __name__ == "__main__":
    analyze_promising_patterns()
    suggest_regex_patterns()
