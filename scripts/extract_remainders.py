#!/usr/bin/env python3
"""Extract and analyze blade count extraction remainders from enriched data."""

import argparse
import json
import re
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime

from sotd.utils.extract_normalization import normalize_remainder_text
from sotd.utils.parallel_processor import create_parallel_processor


def extract_remainders_from_records(records: List[Dict[str, Any]]) -> List[str]:
    """Extract extraction_remainder values from enriched blade data."""
    remainders = []

    for record in records:
        if "blade" in record and isinstance(record["blade"], dict):
            enriched = record["blade"].get("enriched", {})
            if isinstance(enriched, dict) and "extraction_remainder" in enriched:
                remainder = enriched["extraction_remainder"]
                if remainder and isinstance(remainder, str):
                    # Normalize the remainder text to clean up asterisk patterns
                    normalized_remainder = normalize_remainder_text(remainder)
                    if normalized_remainder:  # Only add non-empty remainders
                        remainders.append(normalized_remainder)

    return remainders


def process_month_file(file_path: Path) -> Dict[str, Any]:
    """Process a single month file to extract remainders."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        records = data.get("data", [])
        remainders = extract_remainders_from_records(records)

        return {
            "month": file_path.stem,
            "remainders": remainders,
            "count": len(remainders),
            "status": "success",
        }

    except Exception as e:
        return {
            "month": file_path.stem,
            "remainders": [],
            "count": 0,
            "status": "error",
            "error": str(e),
        }


def _process_month_parallel(year: int, month: int, base_path: Path) -> Optional[Dict[str, Any]]:
    """Process a single month for parallel execution."""
    ym = f"{year:04d}-{month:02d}"
    file_path = base_path / "enriched" / f"{ym}.json"

    if not file_path.exists():
        return None

    return process_month_file(file_path)


def analyze_remainders(all_remainders: List[str]) -> Dict[str, Any]:
    """Analyze remainder patterns and categorize them."""
    if not all_remainders:
        return {
            "total_remainders": 0,
            "unique_remainders": 0,
            "unique_remainder_list": [],
            "pattern_categories": {},
        }

    # Get unique remainders (case-insensitive deduplication)
    unique_remainders = list(set(remainder.lower() for remainder in all_remainders))
    unique_remainders.sort()  # Sort for consistent output

    # Count pattern categories
    pattern_categories = {
        "parentheses_count": 0,
        "brackets_count": 0,
        "braces_count": 0,
        "ordinal_text": 0,
        "multiplier_text": 0,
        "new_text": 0,
        "other_patterns": 0,
    }

    # Categorize each unique remainder
    for remainder in unique_remainders:
        if re.match(r"^\(\d+\)$", remainder) or re.match(r"^\(\d+x\)$", remainder):
            pattern_categories["parentheses_count"] += 1
        elif re.match(r"^\[\d+\]$", remainder) or re.match(r"^\[\d+\\\]$", remainder):
            pattern_categories["brackets_count"] += 1
        elif re.match(r"^\{\d+\}$", remainder):
            pattern_categories["braces_count"] += 1
        elif re.match(r"\d+(?:st|nd|rd|th)\s+use$", remainder) or re.match(
            r"^2\^\\(nd\\)$", remainder
        ):
            pattern_categories["ordinal_text"] += 1
        elif re.match(r"^x\d+$", remainder) or re.match(r"\d+x$", remainder):
            pattern_categories["multiplier_text"] += 1
        elif re.match(r"^\(new\)$", remainder) or remainder.lower() == "new":
            pattern_categories["new_text"] += 1
        else:
            pattern_categories["other_patterns"] += 1

    return {
        "total_remainders": len(all_remainders),
        "unique_remainders": len(unique_remainders),
        "unique_remainder_list": unique_remainders,
        "pattern_categories": pattern_categories,
    }


def create_bucketed_yaml(
    analysis: Dict[str, Any], all_remainders: List[str], output_file: str
) -> str:
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
        if re.match(r"^\(x\d+\)$", remainder):  # (x1), (x2), (x3), (x4)
            pattern_buckets["multiplier"].append(remainder)
        elif re.match(r"^\(\d+x\)$", remainder):  # (2x), (3x), (4x)
            pattern_buckets["multiplier"].append(remainder)
        elif re.match(r"^\(\d+\)$", remainder):  # (39), (256) - only pure numbers
            pattern_buckets["simple-paren"].append(remainder)
        elif re.match(r"^\[\d+\]$", remainder):  # [5], [12]
            pattern_buckets["simple-bracket"].append(remainder)
        elif re.match(r"^\[\d+\\\]$", remainder):  # [2\]
            pattern_buckets["simple-bracket"].append(remainder)
        elif re.match(r"^\{\d+\}$", remainder):  # {1}, {2}, {3}, etc.
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
        f.write(f"# Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

        f.write("metadata:\n")
        f.write(f"  total_remainders: {analysis['total_remainders']}\n")
        f.write(f"  unique_remainders: {analysis['unique_remainders']}\n")
        duplication_rate = (
            (analysis["total_remainders"] - analysis["unique_remainders"])
            / analysis["total_remainders"]
            * 100
        )
        f.write(f"  duplication_rate: {duplication_rate:.1f}%\n")
        f.write("  pattern_categories:\n")
        f.write("    # Percentages of unique patterns (pattern variety)\n")
        for category, count in analysis["pattern_categories"].items():
            if analysis["unique_remainders"] > 0:
                percentage = (count / analysis["unique_remainders"]) * 100
            else:
                percentage = 0
            f.write(f"    {category}: {count} ({percentage:.1f}% of unique)\n")

        f.write("    # Percentages of total occurrences (usage frequency)\n")
        # Count actual occurrences of each pattern type in the raw data
        pattern_usage_counts = {
            "parentheses_count": 0,
            "brackets_count": 0,
            "braces_count": 0,
            "ordinal_text": 0,
            "multiplier_text": 0,
            "new_text": 0,
            "other_patterns": 0,
        }

        # Count actual usage by categorizing each remainder in the raw data
        for remainder in all_remainders:
            if re.match(r"^\(x\d+\)$", remainder):  # (x1), (x2), (x3), (x4)
                pattern_usage_counts["multiplier_text"] += 1
            elif re.match(r"^\(\d+x\)$", remainder):  # (2x), (3x), (4x)
                pattern_usage_counts["multiplier_text"] += 1
            elif re.match(r"^\(\d+\)$", remainder):  # (39), (256) - only pure numbers
                pattern_usage_counts["parentheses_count"] += 1
            elif re.match(r"^\[\d+\]$", remainder) or re.match(r"^\[\d+\\\]$", remainder):
                pattern_usage_counts["brackets_count"] += 1
            elif re.match(r"^\{\d+\}$", remainder):
                pattern_usage_counts["braces_count"] += 1
            elif re.match(r"\d+(?:st|nd|rd|th)\s+use$", remainder) or re.match(
                r"^2\^\\(nd\\)$", remainder
            ):
                pattern_usage_counts["ordinal_text"] += 1
            elif re.match(r"^\(new\)$", remainder) or remainder.lower() == "new":
                pattern_usage_counts["new_text"] += 1
            elif re.match(r"^x\d+$", remainder) or re.match(r"\d+x$", remainder):  # x4, x1, 3x, 2x
                pattern_usage_counts["multiplier_text"] += 1
            else:
                pattern_usage_counts["other_patterns"] += 1

        # Write actual usage counts
        for category, count in pattern_usage_counts.items():
            if analysis["total_remainders"] > 0:
                percentage = (count / analysis["total_remainders"]) * 100
            else:
                percentage = 0
            f.write(f"    {category}_usage: {count} ({percentage:.1f}% of total)\n")
        f.write("\n")

        f.write("  # Key Insights:\n")
        f.write("  # - Pattern variety shows how many different types of patterns exist\n")
        f.write("  # - Usage frequency shows how often each pattern type is actually used\n")
        f.write("  # - High variety + low usage = many edge cases, ")
        f.write("low variety + high usage = common patterns\n")
        f.write("\n")

        f.write("data:\n")
        for bucket_name, patterns in pattern_buckets.items():
            if patterns:  # Only write buckets that have patterns
                f.write(f"  {bucket_name}:\n")
                # Sort patterns for consistent output
                for pattern in sorted(patterns):
                    f.write(f"    - {pattern}\n")
                f.write("\n")

    return yaml_file


def get_parser() -> argparse.ArgumentParser:
    """Get the argument parser for the script."""
    parser = argparse.ArgumentParser(
        description="Extract and analyze blade count extraction remainders"
    )

    # Add standardized parallel processing arguments
    parser.add_argument(
        "--sequential",
        action="store_true",
        help="Force sequential processing (disable parallel)",
    )
    parser.add_argument(
        "--parallel",
        action="store_true",
        help="Force parallel processing",
    )
    parser.add_argument(
        "--max-workers",
        type=int,
        default=4,
        help="Maximum parallel workers for month processing (default: 4)",
    )
    parser.add_argument(
        "--base-path",
        type=str,
        default="data",
        help="Base path for data files (default: data)",
    )

    return parser


def main():
    """Main function with parallel processing support."""
    parser = get_parser()
    args = parser.parse_args()

    base_path = Path(args.base_path)
    enriched_dir = base_path / "enriched"

    if not enriched_dir.exists():
        print(f"❌ Enriched directory not found: {enriched_dir}")
        return

    # Find all enriched data files
    enriched_files = list(enriched_dir.glob("*.json"))
    if not enriched_files:
        print(f"❌ No enriched data files found in {enriched_dir}")
        return

    print("🔍 EXTRACTING BLADE COUNT EXTRACTION REMAINDERS")
    print("=" * 60)
    print(f"📁 Found {len(enriched_files)} enriched data files")

    # Create parallel processor
    processor = create_parallel_processor("extract_remainders")

    # Convert file paths to month tuples for parallel processing
    months = []
    for file_path in enriched_files:
        month_str = file_path.stem
        if "-" in month_str:
            try:
                year, month = month_str.split("-")
                months.append((int(year), int(month)))
            except ValueError:
                continue

    # Determine if we should use parallel processing
    use_parallel = processor.should_use_parallel(months, args, debug=False)

    if use_parallel:
        # Get max workers for parallel processing
        max_workers = processor.get_max_workers(months, args, default=4)

        print(f"🚀 Processing {len(months)} months in parallel with {max_workers} workers...")

        # Process months in parallel
        results = processor.process_months_parallel(
            months, _process_month_parallel, (base_path,), max_workers, "Processing"
        )

        # Print parallel processing summary
        processor.print_parallel_summary(results, "extract_remainders")

    else:
        print(f"🐌 Processing {len(months)} months sequentially...")

        # Process months sequentially
        results = processor.process_months_sequential(
            months, _process_month_parallel, (base_path,), "Months"
        )

    # Collect all remainders from results
    all_remainders = []
    successful_months = 0

    for result in results:
        if result and result.get("status") == "success":
            all_remainders.extend(result["remainders"])
            successful_months += 1
            print(f"📊 Processing {result['month']}...")
            print(f"  ✅ Extracted {result['count']} remainders")
        elif result and result.get("status") == "error":
            print(f"❌ Error processing {result['month']}: {result.get('error', 'Unknown error')}")

    print(f"\n📈 TOTAL: {len(all_remainders):,} remainders extracted")

    if not all_remainders:
        print("❌ No remainders found to analyze")
        return

    # Analyze remainder patterns
    print("\n🔍 Analyzing remainder patterns...")
    analysis = analyze_remainders(all_remainders)

    # Write results to files
    timestamp = datetime.now().strftime("%Y-%m-%d")
    raw_output_file = f"analysis/{timestamp}_extraction_remainder_raw.txt"
    unique_output_file = f"analysis/{timestamp}_extraction_remainder_unique.txt"

    print(f"\n💾 Writing raw remainder strings to {raw_output_file}...")

    # Ensure analysis directory exists
    Path("analysis").mkdir(exist_ok=True)

    # Write raw remainders (not deduped) - shows actual usage frequency
    with open(raw_output_file, "w", encoding="utf-8") as f:
        for remainder in all_remainders:
            f.write(f"{remainder}\n")

    print(f"✅ Raw remainder strings saved to {raw_output_file}")

    # Write unique remainders (deduped) - shows pattern variety
    print(f"\n💾 Writing unique remainder strings to {unique_output_file}...")
    with open(unique_output_file, "w", encoding="utf-8") as f:
        for remainder in analysis["unique_remainder_list"]:
            f.write(f"{remainder}\n")

    print(f"✅ Unique remainder strings saved to {unique_output_file}")

    # Create bucketed YAML file
    print("\n🗂️  Creating bucketed YAML file...")
    yaml_file = create_bucketed_yaml(analysis, all_remainders, raw_output_file)
    print(f"✅ Bucketed YAML created: {yaml_file}")

    # Print summary
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
