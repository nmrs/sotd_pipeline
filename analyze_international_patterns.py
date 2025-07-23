#!/usr/bin/env python3
"""
Analyze field prefixes in skipped comments to discover what patterns actually exist.
Focus only on patterns that could contain razor, blade, brush, soap.
"""

import json
import re
from collections import Counter


def extract_core_product_prefixes():
    """Extract field prefixes that could contain razor, blade, brush, soap."""

    with open("skipped_patterns_analysis.json", "r") as f:
        data = json.load(f)

    print("=" * 80)
    print("CORE PRODUCT PREFIX ANALYSIS - RAZOR, BLADE, BRUSH, SOAP ONLY")
    print("=" * 80)

    # Focus on patterns that might have field prefixes
    patterns_to_analyze = ["dash_prefix_format", "plain_colon_format", "asterisk_format"]

    core_product_prefixes = Counter()
    prefix_examples = {}

    # Keywords that indicate core products
    core_product_keywords = [
        "razor",
        "blade",
        "brush",
        "soap",
        "lather",
        "cream",
        "hardware",
        "software",
        "shaving",
        "straight",
        "safety",
    ]

    for pattern in patterns_to_analyze:
        if pattern in data["examples"]:
            examples = data["examples"][pattern]
            count = data["pattern_counts"][pattern]

            print(f"\n{pattern.upper()} ({count} occurrences):")
            print("-" * 60)

            for example in examples:
                line = example["line"]

                # Extract field prefix (text before colon)
                prefix_match = re.search(r"^[^\w]*(\w+(?:\s+\w+)*)\s*[-:]\s*", line)
                if prefix_match:
                    prefix = prefix_match.group(1).strip().lower()

                    # Only count if it could be a core product field
                    is_core_product = any(keyword in prefix for keyword in core_product_keywords)

                    if is_core_product:
                        core_product_prefixes[prefix] += 1

                        # Store example
                        if prefix not in prefix_examples:
                            prefix_examples[prefix] = []
                        if len(prefix_examples[prefix]) < 3:  # Keep first 3 examples
                            prefix_examples[prefix].append(
                                {"line": line, "month": example["month"]}
                            )

    print(f"\nCORE PRODUCT PREFIXES FOUND ({len(core_product_prefixes)} unique prefixes):")
    print("=" * 60)

    if core_product_prefixes:
        for prefix, count in core_product_prefixes.most_common():
            print(f"\n{prefix} ({count} occurrences):")
            for example in prefix_examples.get(prefix, []):
                print(f"  {example['line']}")
                print(f"    Month: {example['month']}")
    else:
        print("\nNo core product prefixes found in these patterns.")

    # Look for non-English core product patterns
    print(f"\n{'=' * 80}")
    print("NON-ENGLISH CORE PRODUCT PATTERNS")
    print("=" * 80)

    non_english_core_indicators = [
        "rasage",
        "lame",
        "pinceau",
        "savon",  # French
        "afeitado",
        "cuchilla",
        "brocha",
        "jabón",  # Spanish
        "rasur",
        "klinge",
        "pinsel",
        "seife",  # German
        "barba",
        "lama",
        "pennello",
        "sapone",  # Italian
    ]

    international_core_prefixes = []
    for prefix, count in core_product_prefixes.items():
        if any(indicator in prefix for indicator in non_english_core_indicators):
            international_core_prefixes.append((prefix, count))

    if international_core_prefixes:
        print(f"\nINTERNATIONAL CORE PRODUCT PREFIXES FOUND ({len(international_core_prefixes)}):")
        for prefix, count in international_core_prefixes:
            print(f"\n{prefix} ({count} occurrences):")
            for example in prefix_examples.get(prefix, []):
                print(f"  {example['line']}")
                print(f"    Month: {example['month']}")
    else:
        print("\nNo international core product patterns found.")

    # Analyze what these prefixes might map to
    print(f"\n{'=' * 80}")
    print("CORE PRODUCT FIELD MAPPING")
    print("=" * 80)

    field_mapping_suggestions = {}
    for prefix, count in core_product_prefixes.most_common():
        # Map to core fields
        if any(word in prefix for word in ["razor", "straight", "safety"]):
            field = "razor"
        elif any(word in prefix for word in ["blade", "lame", "klinge", "lama"]):
            field = "blade"
        elif any(word in prefix for word in ["brush", "pinceau", "brocha", "pinsel", "pennello"]):
            field = "brush"
        elif any(
            word in prefix
            for word in ["soap", "lather", "cream", "savon", "jabón", "seife", "sapone"]
        ):
            field = "soap"
        elif "hardware" in prefix:
            field = "hardware_ambiguous"  # Could be razor or brush
        elif "software" in prefix:
            field = "software_ambiguous"  # Could be soap
        else:
            field = "unknown"

        field_mapping_suggestions[prefix] = field
        print(f"{prefix} → {field} ({count} occurrences)")


def analyze_checkmark_and_emoji_patterns():
    """Analyze checkmark and emoji patterns for core products."""

    print(f"\n{'=' * 80}")
    print("CHECKMARK AND EMOJI PATTERN ANALYSIS")
    print("=" * 80)

    with open("skipped_patterns_analysis.json", "r") as f:
        data = json.load(f)

    # Focus on checkmark and emoji patterns
    patterns_to_analyze = ["checkmark_format", "emoji_bold_format"]

    core_product_examples = []

    for pattern in patterns_to_analyze:
        if pattern in data["examples"]:
            examples = data["examples"][pattern]
            count = data["pattern_counts"][pattern]

            print(f"\n{pattern.upper()} ({count} occurrences):")
            print("-" * 60)

            for example in examples:
                line = example["line"]

                # Check if this could contain core products
                line_lower = line.lower()
                has_core_product = any(
                    keyword in line_lower
                    for keyword in ["razor", "blade", "brush", "soap", "lather", "cream"]
                )

                if has_core_product:
                    core_product_examples.append(
                        {"pattern": pattern, "line": line, "month": example["month"]}
                    )
                    print(f"  {line}")
                    print(f"    Month: {example['month']}")

    print(f"\nCORE PRODUCT EXAMPLES IN CHECKMARK/EMOJI PATTERNS: {len(core_product_examples)}")
    if core_product_examples:
        for example in core_product_examples:
            print(f"\nPattern: {example['pattern']}")
            print(f"Line: {example['line']}")
            print(f"Month: {example['month']}")


if __name__ == "__main__":
    extract_core_product_prefixes()
    analyze_checkmark_and_emoji_patterns()
