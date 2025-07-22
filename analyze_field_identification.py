#!/usr/bin/env python3
"""
Analyze whether product types are obvious in the promising patterns.
"""

import json
import re
from collections import Counter


def analyze_field_identification():
    """Analyze whether product types are obvious in promising patterns."""

    with open("skipped_patterns_analysis.json", "r") as f:
        data = json.load(f)

    # Focus on patterns that could be parsed
    promising_patterns = [
        "checkmark_format",
        "dash_prefix_format",
        "asterisk_format",
        "emoji_bold_format",
    ]

    print("=" * 80)
    print("FIELD IDENTIFICATION ANALYSIS")
    print("=" * 80)

    for pattern in promising_patterns:
        if pattern in data["examples"]:
            examples = data["examples"][pattern]
            count = data["pattern_counts"][pattern]

            print(f"\n{pattern.upper()} ({count} occurrences):")
            print("-" * 60)

            field_counts = Counter()
            clear_examples = []
            unclear_examples = []

            for example in examples:
                line = example["line"]

                # Try to identify the field
                field = identify_field(line)
                field_counts[field] += 1

                if field and field != "unclear":
                    clear_examples.append((field, line))
                else:
                    unclear_examples.append(line)

            print("Field identification results:")
            for field, count in field_counts.most_common():
                print(f"  {field}: {count}")

            print("\nClear examples (first 5):")
            for field, line in clear_examples[:5]:
                print(f"  {field}: {line}")

            if unclear_examples:
                print("\nUnclear examples (first 5):")
                for line in unclear_examples[:5]:
                    print(f"  {line}")

            print()


def identify_field(line: str) -> str:
    """Try to identify which field this line represents."""
    line_lower = line.lower()

    # Check for obvious field indicators
    if any(word in line_lower for word in ["razor", "blade", "brush", "soap", "lather"]):
        # Extract the field name
        field_match = re.search(r"(\w+)\s*[-:]\s*", line)
        if field_match:
            field = field_match.group(1).lower()

            # Map common variations
            field_mapping = {
                "razor": "razor",
                "blade": "blade",
                "brush": "brush",
                "soap": "soap",
                "lather": "soap",
                "prep": "prep",
                "pre": "prep",
                "post": "post",
                "aftershave": "post",
                "after-shave": "post",
                "software": "soap",
                "hardware": "razor",
            }

            return field_mapping.get(field, field)

    # Check for product-specific keywords
    if any(word in line_lower for word in ["straight razor", "safety razor", "de razor"]):
        return "razor"
    elif any(word in line_lower for word in ["feather", "astra", "gillette", "blade"]):
        return "blade"
    elif any(word in line_lower for word in ["brush", "badger", "synthetic"]):
        return "brush"
    elif any(word in line_lower for word in ["soap", "cream", "lather", "shaving soap"]):
        return "soap"

    return "unclear"


def analyze_specific_patterns():
    """Analyze specific patterns in detail."""

    print("\n" + "=" * 80)
    print("DETAILED PATTERN ANALYSIS")
    print("=" * 80)

    # Sample lines from each pattern
    sample_lines = {
        "checkmark_format": [
            "✓Brush: Kent Infinity",
            "✓Razor: Kopparkant +",
            "✓Blade: feather (1)",
            "✓Lather: Cremo Citrus",
            "✓Prep: Shower/homemade pre-shave oil",
        ],
        "dash_prefix_format": [
            "- 1946-47 Aristocrat 24K replate",
            "- Préparation: Bufflehead pré-rasage savon",
            "- Software: MLS Ruby's Green",
            "- Hardware: Maggard 24mm synthetic brush",
        ],
        "asterisk_format": [
            "* Prep: Hot shower + coffee",
            "* Pre: MLS Lime Preshave Butter",
            "* Software: MLS Ruby's Green",
            "* Hardware: Maggard 24mm synthetic brush",
            "* Post: MLS Ruby's Green Aftershave splash",
        ],
        "emoji_bold_format": [
            "* **Straight Razor** - Fontani Scarperia - Lapis Lazuli",
            "* **Shaving Brush** - Leonidam - Horus - 26mm Fan",
            "* **Shaving Soap** - Saponificio Varesino - Dolomiti",
            "* **After-Shave** - Saponificio Varesino - Dolomiti - Splash",
        ],
    }

    for pattern, lines in sample_lines.items():
        print(f"\n{pattern.upper()}:")
        print("-" * 40)

        for line in lines:
            field = identify_field(line)
            print(f"  {field}: {line}")

        print()


if __name__ == "__main__":
    analyze_field_identification()
    analyze_specific_patterns()
