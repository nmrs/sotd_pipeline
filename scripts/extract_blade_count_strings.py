#!/usr/bin/env python3
"""
Extract blade strings containing count/number information from all extracted data files.

This script:
1. Extracts all original blade strings from all YYYY-MM.json files in data/extracted/
2. Filters to only strings containing recognizable numbers (3, three, third, etc.)
3. Case-insensitively dedupes the strings
4. Saves unanalyzed strings to analysis/20250815-unanalyzed-blade-strings.txt
5. Saves known patterns to analysis/20250815-known-blade-patterns.yaml
"""

import json
import re
from pathlib import Path
from typing import Dict, List


def contains_number(text: str) -> bool:
    """
    Check if text contains a recognizable number.

    Looks for:
    - Arabic numerals (0-9)
    - Written numbers (one, two, three, etc.)
    - Ordinal numbers (first, second, third, etc.)
    - Roman numerals (I, II, III, etc.)
    """
    # Arabic numerals
    if re.search(r"\d", text):
        return True

    # Written numbers (one, two, three, etc.)
    written_numbers = [
        "zero",
        "one",
        "two",
        "three",
        "four",
        "five",
        "six",
        "seven",
        "eight",
        "nine",
        "ten",
        "eleven",
        "twelve",
        "thirteen",
        "fourteen",
        "fifteen",
        "sixteen",
        "seventeen",
        "eighteen",
        "nineteen",
        "twenty",
    ]

    # Ordinal numbers (first, second, third, etc.)
    ordinal_numbers = [
        "first",
        "second",
        "third",
        "fourth",
        "fifth",
        "sixth",
        "seventh",
        "eighth",
        "ninth",
        "tenth",
        "eleventh",
        "twelfth",
        "thirteenth",
        "fourteenth",
        "fifteenth",
        "sixteenth",
        "seventeenth",
        "eighteenth",
        "nineteenth",
        "twentieth",
    ]

    # Roman numerals (basic patterns)
    roman_patterns = [
        r"\b[IVX]+\.?\b",  # I, II, III, IV, V, VI, VII, VIII, IX, X, etc.
        r"\b[ivx]+\.?\b",  # lowercase versions
    ]

    text_lower = text.lower()

    # Check written numbers
    for num in written_numbers + ordinal_numbers:
        if num in text_lower:
            return True

    # Check Roman numerals
    for pattern in roman_patterns:
        if re.search(pattern, text):
            return True

    return False


def extract_original_strings(file_path: Path) -> List[str]:
    """Extract all original strings from the blade data only."""
    original_strings = []

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Extract original strings from blade data only
        for record in data.get("data", []):
            if "blade" in record and isinstance(record["blade"], dict):
                original = record["blade"].get("original")
                if original and isinstance(original, str):
                    original_strings.append(original)

                    # Debug: Check for backslash strings during extraction
                    if "\\\\" in original:
                        print(f"DEBUG: Found backslash string during extraction: {repr(original)}")
                        print(f"  File: {file_path}")
                        print(f"  Contains number: {contains_number(original)}")

        return original_strings

    except Exception as e:
        print(f"Error reading file {file_path}: {e}")
        return []


def find_extracted_files(data_dir: Path) -> List[Path]:
    """Find all YYYY-MM.json files in the data/extracted directory."""
    extracted_files = []

    if not data_dir.exists():
        print(f"Error: Directory {data_dir} not found")
        return []

    # Find all YYYY-MM.json files
    for file_path in data_dir.glob("*.json"):
        if file_path.name.endswith(".json"):
            # Check if filename matches YYYY-MM pattern
            if re.match(r"^\d{4}-\d{2}\.json$", file_path.name):
                extracted_files.append(file_path)

    # Sort by filename for consistent processing order
    extracted_files.sort()
    return extracted_files


def categorize_known_patterns(strings: List[str]) -> Dict[str, Dict[str, List[str]]]:
    """
    Categorize strings with numbers into known patterns.

    Returns nested dictionary with blade-use-count-patterns and non-blade-count-patterns.
    """
    patterns = {
        "blade-use-count-patterns": {
            "simple_blade_count": [],
            "explicit_usage_count": [],
            "multiplier_count": [],
            "hash_number": [],
            "semantic_usage_count": [],
            "month_usage_count": [],
            "blade_inventory_count": [],
        },
        "non-blade-count-patterns": {
            "straight_razor_width": [],
            "price": [],
        },
    }

    # Emoji pattern for trailing characters
    emoji_pattern = (
        r"[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF"
        r"\U0001F1E0-\U0001F1FF\U00002600-\U000027BF]"
    )

    # Simple pattern for basic numeric usage counts
    simple_pattern = (
        r"[\(\[]\s*(?:\d+\s*[?~]?|[?~]\s*\d+|\.\d+|\d+\s*[-+,]\s*\d+\s*[?]?|"
        r"\d+\s*ish\s*[?]?)\s*[\)\]]"
        r"\s*(?:[#$]\w+(?:\s+[#$]\w+)*|\.|\*|\s*$|" + emoji_pattern + r")"
    )

    # Shave/use pattern for explicit usage descriptions
    shave_use = r"(?:shave|use)"
    written_ordinals = r"(?:first|second|third|fourth|fifth|sixth|seventh|eighth|ninth|tenth)"

    # Usage pattern for explicit shave/use counts
    usage_pattern = (
        r"(?:[\(\[]?\s*(?:\d+[stndrh]+|" + written_ordinals + r")\s+" + shave_use + r"|"
        r"shave\s*#\s*\d+|"
        r"Edge\s+\d+\s*-\s*\d+[stndrh]+\s+" + shave_use + r")"
        r"\s*(?:[\)\]]|\s*$)"
    )

    # Multiplier pattern for (Nx) or (xN) patterns
    multiplier_pattern = (
        r"[\(\[]\s*(?:\d+\s*[xX]|[xX]\s*\d+)\s*[\)\]]" r"\s*(?:[#$]\w+(?:\s+[#$]\w+)*|\.|\s*$)"
    )

    # Number + Uses pattern
    number_uses_pattern = r"\d+\s+Uses?"

    for s in strings:
        # Check for number + Uses pattern first (treat as simple blade count)
        if re.search(number_uses_pattern, s, re.IGNORECASE):
            patterns["blade-use-count-patterns"]["simple_blade_count"].append(s)
            continue

        # Check for simple numeric patterns
        simple_match = re.search(simple_pattern, s, re.IGNORECASE)

        # Check for explicit usage patterns
        usage_match = re.search(usage_pattern, s, re.IGNORECASE)

        # Check for multiplier patterns
        multiplier_match = re.search(multiplier_pattern, s, re.IGNORECASE)

        # Check for hash numbers
        hash_match = re.search(r"#[0-9]+", s)

        # Check for straight razor widths - ONLY n/8 and n/16 fractions
        # This matches: "5/8", "7/8", "13/16", "5/8 Adam Edge (2X)", etc.
        # Does NOT match: "1/2 DE", "2/31", "15/31", etc.
        straight_razor_match = re.search(r"\b\d+/(?:8|16)\b", s)

        # Check for month-based usage tracking (n/31, n/30, n/28, etc.)
        # This matches: "PolSilver SI 15/31", "GSB 20/31", etc.
        # Pattern: number/number where second number is typically 28, 29, 30, or 31
        month_usage_match = re.search(r"\b\d+/(?:28|29|30|31)\b", s)

        # Check for blade inventory tracking (X of Y)
        # This matches: "#101 of 104", "15 of 100", "1 of 14", etc.
        # Pattern: number "of" number where it's tracking blade inventory, not usage
        # Also catches: "#101 of 104" (with hash prefix)
        blade_inventory_match = re.search(r"\b#?\d+\s+of\s+\d+\b", s)

        # Check for prices
        price_match = re.search(r"\$[0-9]+\.[0-9]+", s)

        # Check for semantic usage patterns (equivalent to "(1)" - first use)
        semantic_patterns = [
            r"\(NEW\)",  # (NEW)
            r"\(new\)",  # (new)
            r"\(Fresh\)",  # (Fresh)
            r"\(fresh\)",  # (fresh)
            r"\(new blade\)",  # (new blade)
            r"\(fresh blade\)",  # (fresh blade)
            r"\(first time\)",  # (first time)
            r"\(First time\)",  # (First time)
            r"\(Brand new\)",  # (Brand new)
            r"\(brand new\)",  # (brand new)
        ]

        semantic_match = False
        for pattern in semantic_patterns:
            if re.search(pattern, s, re.IGNORECASE):
                semantic_match = True
                break

        # Priority logic for hybrid patterns
        # Check straight razor width first - these should take precedence
        if straight_razor_match:
            patterns["non-blade-count-patterns"]["straight_razor_width"].append(s)
        elif simple_match and multiplier_match:
            # If both simple and multiplier patterns exist, prioritize simple (usage count)
            patterns["blade-use-count-patterns"]["simple_blade_count"].append(s)
        elif simple_match:
            patterns["blade-use-count-patterns"]["simple_blade_count"].append(s)
        elif usage_match:
            patterns["blade-use-count-patterns"]["explicit_usage_count"].append(s)
        elif multiplier_match:
            patterns["blade-use-count-patterns"]["multiplier_count"].append(s)
        elif blade_inventory_match:
            patterns["blade-use-count-patterns"]["blade_inventory_count"].append(s)
        elif hash_match:
            patterns["blade-use-count-patterns"]["hash_number"].append(s)
        elif semantic_match:
            patterns["blade-use-count-patterns"]["semantic_usage_count"].append(s)
        elif month_usage_match:
            patterns["blade-use-count-patterns"]["month_usage_count"].append(s)
        elif price_match:
            patterns["non-blade-count-patterns"]["price"].append(s)
        else:
            # This shouldn't happen for strings with numbers, but just in case
            patterns["blade-use-count-patterns"]["simple_blade_count"].append(s)

    return patterns


def filter_and_dedupe_strings(strings: List[str]) -> List[str]:
    """Filter strings and perform case-insensitive deduplication."""
    # No filtering - keep all strings
    # Convert back to original case for first occurrence
    deduped = []
    seen_lower = set()
    for s in strings:
        if s.lower() not in seen_lower:
            deduped.append(s)
            seen_lower.add(s.lower())

    return sorted(deduped)


def save_to_file(strings: List[str], output_path: Path) -> None:
    """Save the filtered and deduped strings to a text file, one per line."""
    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w", encoding="utf-8") as f:
            for s in strings:
                f.write(f"{s}\n")

        print(f"Saved {len(strings)} strings to {output_path}")

    except Exception as e:
        print(f"Error saving to {output_path}: {e}")


def save_yaml_patterns(patterns: Dict[str, List[str]], output_path: Path) -> None:
    """Save the known patterns to a YAML file."""
    try:
        import yaml

        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w", encoding="utf-8") as f:
            yaml.dump(
                patterns, f, default_flow_style=False, allow_unicode=True, sort_keys=False, indent=2
            )

        print(f"Saved {len(patterns)} pattern types to {output_path}")

    except Exception as e:
        print(f"Error saving YAML file: {e}")


def main():
    """Main execution function."""
    # File paths with current date
    data_dir = Path("data/extracted")
    unanalyzed_file = Path("analysis/20250815-unanalyzed-blade-strings.txt")
    patterns_file = Path("analysis/20250815-known-blade-patterns.yaml")

    print(f"Processing extracted files from {data_dir}")

    # Find all extracted files
    extracted_files = find_extracted_files(data_dir)
    if not extracted_files:
        print("No extracted files found")
        return

    print(f"Found {len(extracted_files)} extracted files to process")

    # Process all files and collect original strings
    all_original_strings = []
    for file_path in extracted_files:
        print(f"Processing {file_path.name}...")
        file_strings = extract_original_strings(file_path)
        all_original_strings.extend(file_strings)
        print(f"  Extracted {len(file_strings)} original blade strings")

        # Debug: Check for backslash strings in this file
        backslash_strings = [s for s in file_strings if "\\\\" in s]
        if backslash_strings:
            print(
                f"    DEBUG: Found {len(backslash_strings)} backslash strings in {file_path.name}"
            )
            print(f"    Sample: {repr(backslash_strings[0])}")

    print(f"\nTotal extracted: {len(all_original_strings)} original blade strings")

    if not all_original_strings:
        print("No original strings found")
        return

    # Filter and dedupe
    filtered_strings = filter_and_dedupe_strings(all_original_strings)
    if not filtered_strings:
        print("No strings containing numbers found")
        return

    # Categorize into known patterns
    print("Categorizing known patterns...")
    known_patterns = categorize_known_patterns(filtered_strings)

    # Save unanalyzed strings (all strings minus known patterns)
    known_pattern_strings = set()
    for category, patterns in known_patterns.items():
        for pattern_name, pattern_strings in patterns.items():
            known_pattern_strings.update(pattern_strings)

    unanalyzed_strings = [s for s in filtered_strings if s not in known_pattern_strings]

    # Save files
    save_to_file(unanalyzed_strings, unanalyzed_file)
    save_yaml_patterns(known_patterns, patterns_file)

    # Show summary
    print("\nExtraction Summary:")
    print(f"Total strings with numbers: {len(filtered_strings):,}")

    # Count total known patterns
    total_known = 0
    for category, patterns in known_patterns.items():
        for pattern_name, pattern_strings in patterns.items():
            total_known += len(pattern_strings)

    print(f"Known patterns: {total_known:,}")
    print(f"Unanalyzed strings: {len(unanalyzed_strings):,}")

    print("\nKnown pattern types:")
    for category, patterns in known_patterns.items():
        for pattern_name, pattern_strings in patterns.items():
            print(f"  {pattern_name}: {len(pattern_strings):,}")

    # Show some examples of known patterns
    if known_patterns:
        print("\nExamples of known patterns:")
        for category, patterns in known_patterns.items():
            print(f"  {category}:")
            for pattern_name, pattern_strings in patterns.items():
                print(f"    {pattern_name}:")
                for i, example in enumerate(pattern_strings[:3], 1):
                    print(f"      {i}. {example}")
                if len(pattern_strings) > 3:
                    print(f"      ... and {len(pattern_strings) - 3} more")


if __name__ == "__main__":
    main()
