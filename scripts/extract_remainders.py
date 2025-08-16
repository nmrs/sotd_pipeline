#!/usr/bin/env python3
"""
Extract all extraction remainders from enriched data across the full corpus.

This script analyzes all enriched data files to extract the extraction_remainder
field from blade enricher output, providing insights into what text patterns
are being extracted by the normalization-difference approach.
"""

import json
import re
from pathlib import Path
from typing import Tuple, Dict, List, Any
from collections import Counter, defaultdict
from datetime import datetime


def load_enriched_data(month: str) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
    """Load enriched data for a specific month."""
    file_path = Path(f"data/enriched/{month}.json")
    if not file_path.exists():
        return {}, []

    with open(file_path, "r") as f:
        data = json.load(f)

    # Handle different file structures
    if "records" in data:
        return data.get("metadata", {}), data.get("records", [])
    elif "data" in data:
        return data.get("metadata", {}), data.get("data", [])
    else:
        return data.get("metadata", {}), []


def extract_remainders_from_records(records: List[Dict[str, Any]]) -> List[str]:
    """Extract extraction remainders from enriched records."""
    remainders = []

    for record in records:
        if "blade" not in record:
            continue

        blade_data = record["blade"]
        if not isinstance(blade_data, dict):
            continue

        enriched = blade_data.get("enriched", {})
        if not isinstance(enriched, dict):
            continue

        # Look for extraction_remainder field
        remainder = enriched.get("extraction_remainder")
        if remainder:
            remainders.append(remainder)

    return remainders


def analyze_remainders(remainders: List[str]) -> Dict[str, Any]:
    """Analyze the extraction remainders to identify patterns and categories."""
    if not remainders:
        return {
            "total_remainders": 0,
            "unique_remainders": 0,
            "pattern_categories": {},
            "remainder_counter": Counter(),
            "examples_by_category": defaultdict(list),
        }

    # Deduplicate case-insensitively while preserving original casing for display
    # Use a dict to keep the first occurrence of each case-insensitive pattern
    unique_remainders = {}
    for remainder in remainders:
        if remainder:
            # Use lowercase as key for case-insensitive deduplication
            key = remainder.lower()
            if key not in unique_remainders:
                unique_remainders[key] = remainder

    # Convert back to list of unique remainders (preserving original casing)
    unique_remainder_list = list(unique_remainders.values())

    # Categorize patterns
    pattern_categories = {
        "parentheses_count": 0,  # (39), (2x), (256)
        "brackets_count": 0,  # [5], [2\]
        "braces_count": 0,  # {2}
        "ordinal_text": 0,  # 1st use, 2nd use, 2^(nd)
        "multiplier_text": 0,  # x4, x1, 3x
        "new_text": 0,  # (new), new
        "other_patterns": 0,  # Everything else
    }

    examples_by_category = defaultdict(list)

    for remainder in unique_remainder_list:
        # Count by pattern type
        if re.match(r"^\(\d+\)$", remainder):  # (39), (256)
            pattern_categories["parentheses_count"] += 1
            examples_by_category["parentheses_count"].append(remainder)
        elif re.match(r"^\(\d+x\)$", remainder):  # (2x), (3x)
            pattern_categories["parentheses_count"] += 1
            examples_by_category["parentheses_count"].append(remainder)
        elif re.match(r"^\[\d+\]$", remainder):  # [5], [12]
            pattern_categories["brackets_count"] += 1
            examples_by_category["brackets_count"].append(remainder)
        elif re.match(r"^\[\d+\\\]$", remainder):  # [2\]
            pattern_categories["brackets_count"] += 1
            examples_by_category["brackets_count"].append(remainder)
        elif re.match(r"^\{2\}$", remainder):  # {2}
            pattern_categories["braces_count"] += 1
            examples_by_category["braces_count"].append(remainder)
        elif re.match(r"\d+(?:st|nd|rd|th)\s+use$", remainder):  # 1st use, 2nd use
            pattern_categories["ordinal_text"] += 1
            examples_by_category["ordinal_text"].append(remainder)
        elif re.match(r"^2\^\\(nd\\)$", remainder):  # 2^(nd)
            pattern_categories["ordinal_text"] += 1
            examples_by_category["ordinal_text"].append(remainder)
        elif re.match(r"^x\d+$", remainder):  # x4, x1
            pattern_categories["multiplier_text"] += 1
            examples_by_category["multiplier_text"].append(remainder)
        elif re.match(r"\d+x$", remainder):  # 3x, 2x
            pattern_categories["multiplier_text"] += 1
            examples_by_category["multiplier_text"].append(remainder)
        elif re.match(r"^\(new\)$", remainder) or remainder.lower() == "new":
            pattern_categories["new_text"] += 1
            examples_by_category["new_text"].append(remainder)
        else:
            pattern_categories["other_patterns"] += 1
            examples_by_category["other_patterns"].append(remainder)

    return {
        "total_remainders": len(remainders),
        "unique_remainders": len(unique_remainder_list),
        "pattern_categories": pattern_categories,
        "remainder_counter": Counter(unique_remainder_list),
        "examples_by_category": examples_by_category,
        "unique_remainder_list": unique_remainder_list,  # Add this for writing
    }


def create_bucketed_yaml(analysis: Dict[str, Any], output_file: str) -> str:
    """Create a bucketed YAML file grouping remainders by pattern type."""
    yaml_file = output_file.replace(".txt", "_bucketed.yaml")

    # Define pattern buckets with descriptive names
    pattern_buckets = {
        "simple-paren": [],  # (39), (256), (2x)
        "simple-bracket": [],  # [1], [18], [4]
        "simple-brace": [],  # {2}
        "ordinal-use": [],  # 4th use, 10th use, 3rd use
        "multiplier": [],  # x4, x1, 3x, 2x
        "new-indicator": [],  # (new), new
        "complex-paren": [],  # (2x) (2)., (India) (1)
        "complex-bracket": [],  # [2x] (3)
        "complex-mixed": [],  # Mixed patterns
        "other": [],  # Everything else
    }

    # Categorize each unique remainder into buckets
    for remainder in analysis["unique_remainder_list"]:
        if re.match(r"^\(\d+\)$", remainder):  # (39), (256)
            pattern_buckets["simple-paren"].append(remainder)
        elif re.match(r"^\(\d+x\)$", remainder):  # (2x), (3x)
            pattern_buckets["simple-paren"].append(remainder)
        elif re.match(r"^\[\d+\]$", remainder):  # [5], [12]
            pattern_buckets["simple-bracket"].append(remainder)
        elif re.match(r"^\[\d+\\\]$", remainder):  # [2\]
            pattern_buckets["simple-bracket"].append(remainder)
        elif re.match(r"^\{2\}$", remainder):  # {2}
            pattern_buckets["simple-brace"].append(remainder)
        elif re.match(r"\d+(?:st|nd|rd|th)\s+use$", remainder):  # 1st use, 2nd use
            pattern_buckets["ordinal-use"].append(remainder)
        elif re.match(r"^2\^\\(nd\\)$", remainder):  # 2^(nd)
            pattern_buckets["ordinal-use"].append(remainder)
        elif re.match(r"^x\d+$", remainder):  # x4, x1
            pattern_buckets["multiplier"].append(remainder)
        elif re.match(r"\d+x$", remainder):  # 3x, 2x
            pattern_buckets["multiplier"].append(remainder)
        elif re.match(r"^\(new\)$", remainder) or remainder.lower() == "new":
            pattern_buckets["new-indicator"].append(remainder)
        elif re.match(r"^\(\d+x\)\s+\(\d+\)\.?$", remainder):  # (2x) (2).
            pattern_buckets["complex-paren"].append(remainder)
        elif re.match(r"^\([^)]+\)\s+\(\d+\)$", remainder):  # (India) (1)
            pattern_buckets["complex-paren"].append(remainder)
        elif re.match(r"^\[\d+x\]\s+\(\d+\)$", remainder):  # [2x] (3)
            pattern_buckets["complex-bracket"].append(remainder)
        elif re.search(r"[\[\]\(\)]\d+[xX]?[\]\)]", remainder):  # Mixed bracket/paren patterns
            pattern_buckets["complex-mixed"].append(remainder)
        else:
            pattern_buckets["other"].append(remainder)

    # Write YAML file
    with open(yaml_file, "w", encoding="utf-8") as f:
        f.write("# BLADE COUNT EXTRACTION REMAINDER PATTERNS\n")
        f.write(f"# Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"# Total unique patterns: {analysis['unique_remainders']}\n")
        f.write(f"# Total occurrences: {analysis['total_remainders']}\n\n")

        for bucket_name, patterns in pattern_buckets.items():
            if patterns:  # Only write buckets that have patterns
                f.write(f"{bucket_name}:\n")
                # Sort patterns for consistent output
                for pattern in sorted(patterns):
                    f.write(f"  - {pattern}\n")
                f.write("\n")

    return yaml_file


def main():
    """Main function to extract and analyze all extraction remainders."""
    print("🔍 EXTRACTING BLADE COUNT EXTRACTION REMAINDERS")
    print("=" * 60)

    # Get all enriched data files
    enriched_dir = Path("data/enriched")
    if not enriched_dir.exists():
        print("❌ Error: data/enriched directory not found")
        return

    enriched_files = sorted([f.stem for f in enriched_dir.glob("*.json")])
    print(f"📁 Found {len(enriched_files)} enriched data files")

    # Extract all remainders
    all_remainders = []
    month_stats = {}

    for month in enriched_files:
        print(f"📊 Processing {month}...")
        metadata, records = load_enriched_data(month)

        if not records:
            print(f"  ⚠️  No records found in {month}")
            continue

        month_remainders = extract_remainders_from_records(records)
        month_stats[month] = len(month_remainders)
        all_remainders.extend(month_remainders)

        print(f"  ✅ Extracted {len(month_remainders):,} remainders")

    print(f"\n📈 TOTAL: {len(all_remainders):,} remainders extracted")

    # Analyze patterns
    print("\n🔍 Analyzing remainder patterns...")
    analysis = analyze_remainders(all_remainders)

    # Write results to file
    timestamp = datetime.now().strftime("%Y-%m-%d")
    output_file = f"analysis/{timestamp}_extraction_remainder.txt"

    print(f"\n💾 Writing results to {output_file}...")

    # Ensure analysis directory exists
    Path("analysis").mkdir(exist_ok=True)

    with open(output_file, "w", encoding="utf-8") as f:
        f.write("BLADE COUNT EXTRACTION REMAINDER ANALYSIS\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("=" * 80 + "\n\n")

        f.write("📊 OVERALL STATISTICS:\n")
        f.write(f"  Total remainders: {analysis['total_remainders']:,}\n")
        f.write(f"  Unique remainders: {analysis['unique_remainders']:,}\n")
        duplication_rate = (
            (analysis["total_remainders"] - analysis["unique_remainders"])
            / analysis["total_remainders"]
            * 100
        )
        f.write(f"  Duplication rate: {duplication_rate:.1f}%\n")
        f.write("\n")

        f.write("📅 MONTHLY BREAKDOWN:\n")
        for month, count in month_stats.items():
            f.write(f"  {month}: {count:,} remainders\n")
        f.write("\n")

        f.write("🔍 PATTERN CATEGORIES:\n")
        for category, count in analysis["pattern_categories"].items():
            if analysis["total_remainders"] > 0:
                percentage = (count / analysis["total_remainders"]) * 100
            else:
                percentage = 0
            f.write(f"  {category.title()}: {count:,} ({percentage:.1f}%)\n")
        f.write("\n")

        f.write("📝 TOP 20 MOST COMMON REMAINDERS:\n")
        for remainder, count in analysis["remainder_counter"].most_common(20):
            f.write(f"  {remainder}: {count:,} occurrences\n")
        f.write("\n")

        f.write("📋 EXAMPLES BY CATEGORY:\n")
        for category, examples in analysis["examples_by_category"].items():
            if examples:
                f.write(f"\n  {category.upper()}:\n")
                # Show unique examples, limited to 10 per category
                unique_examples = list(set(examples))[:10]
                for example in unique_examples:
                    f.write(f"    {example}\n")
                if len(set(examples)) > 10:
                    remaining = len(set(examples)) - 10
                    f.write(f"    ... and {remaining} more unique examples\n")

        f.write("\n" + "=" * 80 + "\n")
        f.write("DETAILED REMAINDER DATA:\n")
        f.write("=" * 80 + "\n\n")

        # Write detailed data
        for remainder in analysis["unique_remainder_list"]:
            f.write(f"{remainder}\n")

    print(f"✅ Analysis complete! Results saved to {output_file}")

    # Create bucketed YAML file
    print("\n🗂️  Creating bucketed YAML file...")
    yaml_file = create_bucketed_yaml(analysis, output_file)
    print(f"✅ Bucketed YAML created: {yaml_file}")

    print(
        f"📊 Found {analysis['unique_remainders']:,} unique remainders out of "
        f"{analysis['total_remainders']:,} total"
    )
    duplication_rate = (
        (analysis["total_remainders"] - analysis["unique_remainders"])
        / analysis["total_remainders"]
        * 100
    )
    print(f"🔄 Duplication rate: {duplication_rate:.1f}%")


if __name__ == "__main__":
    main()
