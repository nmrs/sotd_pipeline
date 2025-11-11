#!/usr/bin/env python3
"""Extract and analyze blade count extraction remainders from enriched data."""

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

# Add the project root to the Python path so we can import from sotd
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    from sotd.utils.extract_normalization import normalize_remainder_text
    from sotd.utils.parallel_processor import create_parallel_processor
except ImportError:
    print("Error: Could not import from sotd. Make sure you're running from the project root.")
    print("Try: python scripts/extract_remainders.py")
    sys.exit(1)


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
        elif re.match(r"^\(new\)$", remainder) or re.match(r"^\(fresh\)$", remainder):
            pattern_categories["new_text"] += 1
        elif (
            re.match(r"^\(fresh blade\)$", remainder)
            or re.match(r"^\(new blade\)$", remainder)
            or re.match(r"^\(brand new\)$", remainder)
            or re.match(r"^\(first time\)$", remainder)
        ):
            pattern_categories["new_text"] += 1
        else:
            pattern_categories["other_patterns"] += 1

    return {
        "total_remainders": len(all_remainders),
        "unique_remainders": len(unique_remainders),
        "unique_remainder_list": unique_remainders,
        "pattern_categories": pattern_categories,
    }


def create_bucketed_yaml(analysis, all_remainders):
    """Create a YAML file with patterns grouped into logical buckets."""

    # Define pattern buckets for blade count patterns
    blade_count_buckets = {
        "simple-numeric": [],  # (4), (10), (100), [4], {4}, (1], [2), etc.
        "multiplier": [],  # x4, x1, 3x, 2x, (x4), (4x)
        "ordinal-use": [],  # (1st use), (2nd), (10th use)
        "complex-paren": [],  # (2) (2), (3) (3)
        "complex-bracket": [],  # Currently empty - [2x] (1) patterns moved
        # to multiplication-plus-simple
        "multiplication-plus-simple": [],  # x2 (1), (2x) (1)
        "location-plus-simple": [],  # (china) (1), (germany) [2], (india) (3)
        "location-plus-new-indicator": [],  # (thailand, new), (india, new)
        "simple-plus-simple": [],  # (2) (2), (3) (3)
        "simple-plus-ordinal": [],  # [1] [first time], [2] [second use]
        "ordinal-plus-multiplier": [],  # 1st use x2, 2nd use x3
        "new-indicator": [],  # (fresh), (new blade), (brand new), (first time), (new), [new]
    }

    # Define pattern buckets for non blade count patterns
    non_blade_count_buckets = {
        # (china), (germany), (india), (japan), (russia), (thailand),
        # (usa), (uk), (turkey), [usa], [china], etc.
        "location-indicator": [],
        "condition-indicator": [],  # (vintage), (sample), (test), (old)
        "url-link": [],  # https://..., web links
        "hashtag": [],  # #stainlessless, #foreversafety
        "other": [],  # Everything else that doesn't fit above categories
    }

    # Categorize each unique remainder using two-phase approach
    for remainder in analysis["unique_remainder_list"]:
        # Phase 1: Pre-normalization bucketing for simple, clean patterns
        if re.match(r"^\(\d+(?:\.\d+)?\)$", remainder):  # (4), (10), (100), (1.5), (2.5)
            blade_count_buckets["simple-numeric"].append(remainder)
        elif re.match(r"^\[\d+\]$", remainder):  # [4], [10], [100)
            blade_count_buckets["simple-numeric"].append(remainder)
        elif re.match(r"^\{\d+\}$", remainder):  # {4}, {10}, {100}
            blade_count_buckets["simple-numeric"].append(remainder)
        elif re.match(r"^[\(\[\{]\d+[\)\]\}]$", remainder):  # (1], [2), {3}, (4}, [5}, etc.
            blade_count_buckets["simple-numeric"].append(remainder)
        elif re.match(r"^x\d+$", remainder) or re.match(r"\d+x$", remainder):
            # x4, x1, 3x, 2x
            blade_count_buckets["multiplier"].append(remainder)
        elif re.match(r"^\d+(?:st|nd|rd|th)\s+use$", remainder):
            # 1st use, 2nd use, 3rd use
            blade_count_buckets["ordinal-use"].append(remainder)
        elif re.match(r"^\(new\)$", remainder) or re.match(r"^\(fresh\)$", remainder):
            # (new), (fresh)
            blade_count_buckets["new-indicator"].append(remainder)
        elif re.match(r"^\(fresh blade\)$", remainder) or re.match(r"^\(new blade\)$", remainder):
            # (fresh blade), (new blade)
            blade_count_buckets["new-indicator"].append(remainder)
        elif re.match(r"^\(brand new\)$", remainder) or re.match(r"^\(first time\)$", remainder):
            # (brand new), (first time)
            blade_count_buckets["new-indicator"].append(remainder)
        elif re.match(r"^\[new\]$", remainder):
            # [new]
            blade_count_buckets["new-indicator"].append(remainder)
        elif re.match(r"^\[\d+\]\s+\[[a-z\s]+\]$", remainder):  # [1] [first time], [2] [second use]
            # [number] [ordinal] - simple numeric + ordinal indicator
            blade_count_buckets["simple-plus-ordinal"].append(remainder)
        elif re.match(r"^\([a-z]+\)$", remainder) and remainder.lower() in [
            "(china)",
            "(germany)",
            "(india)",
            "(japan)",
            "(russia)",
            "(thailand)",
            "(usa)",
            "(uk)",
            "(turkey)",
            "(czechoslovakian)",
            "(indian)",
            "(poland)",
            "(russian)",
        ]:
            # (china), (germany), (india), etc. - just location
            non_blade_count_buckets["location-indicator"].append(remainder)
        elif re.match(r"^\(made in [a-z]+\)$", remainder):  # (made in china), (made in germany)
            # Complex location patterns
            non_blade_count_buckets["location-indicator"].append(remainder)
        elif re.match(r"^\([a-z]+,\s*new\)$", remainder):  # (thailand, new), (india, new)
            # (location, new) - location plus new indicator (equivalent to (1))
            blade_count_buckets["location-plus-new-indicator"].append(remainder)
        elif re.match(r"^\([a-z]+,\s*[a-z\s]+\)$", remainder):  # (india, 3rd or 4th use)
            # (location, description) - location plus description
            non_blade_count_buckets["other"].append(remainder)
        # Note: (usa, blue box) type patterns will fall through to 'other' bucket
        elif re.match(r"^\[[a-z]+\]$", remainder) and remainder.lower() in [
            "[usa]",
            "[china]",
            "[germany]",
            "[india]",
            "[japan]",
            "[russia]",
            "[thailand]",
            "[uk]",
            "[turkey]",
        ]:
            # [usa], [china], [germany], etc.
            blade_count_buckets["location-plus-simple"].append(remainder)
        elif re.match(r"^\[[a-z]+\]\s+\(\d+\)$", remainder):  # [china] (1), [germany] (2)
            blade_count_buckets["location-plus-simple"].append(remainder)
        elif re.match(r"^https?://", remainder) or re.match(r"^www\.", remainder):
            # URLs
            non_blade_count_buckets["url-link"].append(remainder)
        elif re.match(r"^[#\$][a-zA-Z0-9_]+$", remainder):
            # Hashtags and dollar-tags
            non_blade_count_buckets["hashtag"].append(remainder)
        elif re.match(r"^\([a-z]+\)\s+\[\d+\]$", remainder):  # (china) [1]
            # Check if this is a condition indicator first
            if (
                re.match(r"^\(vintage\)", remainder)
                or re.match(r"^\(sample\)", remainder)
                or re.match(r"^\(test\)", remainder)
                or re.match(r"^\(old\)", remainder)
            ):
                # Strip condition indicator and categorize the remaining pattern
                cleaned = re.sub(r"^\(vintage\)\s*", "", remainder)
                cleaned = re.sub(r"^\(sample\)\s*", "", cleaned)
                cleaned = re.sub(r"^\(test\)\s*", "", cleaned)
                cleaned = re.sub(r"^\(old\)\s*", "", cleaned)
                if re.match(r"^\[\d+\]$", cleaned):  # Now it's just [4]
                    blade_count_buckets["simple-numeric"].append(
                        cleaned
                    )  # Store the cleaned result
                else:
                    non_blade_count_buckets["other"].append(remainder)
            else:
                # This is a location indicator, categorize normally
                blade_count_buckets["location-plus-simple"].append(remainder)
        elif re.match(r"^\(made in [a-z]+\)\s+\[\d+\]$", remainder):  # (made in china) [1]
            # Complex location + simple numeric - categorize as location-plus-simple
            blade_count_buckets["location-plus-simple"].append(remainder)

        # Phase 2: Post-normalization bucketing for complex patterns that need cleaning
        else:
            # Normalize the remainder for complex pattern matching
            normalized_remainder = normalize_remainder_text(remainder)

            # Skip if the remainder becomes empty after normalization
            if not normalized_remainder:
                continue

            # Categorize the normalized remainder into appropriate buckets
            if re.match(
                r"^\(\d+(?:\.\d+)?\)$", normalized_remainder
            ):  # (4), (10), (100), (1.5), (2.5)
                blade_count_buckets["simple-numeric"].append(normalized_remainder)
            elif re.match(r"^\[\d+\]$", normalized_remainder):  # [4], [10], [100] - simple-bracket
                blade_count_buckets["simple-numeric"].append(normalized_remainder)
            elif re.match(r"^\{\d+\}$", normalized_remainder):  # {4}, {10}, {100} - simple-brace
                blade_count_buckets["simple-numeric"].append(normalized_remainder)
            elif re.match(
                r"^[\(\[\{]\d+[\)\]\}]$", normalized_remainder
            ):  # (1], [2), {3}, (4}, [5}, etc.
                blade_count_buckets["simple-numeric"].append(normalized_remainder)
            elif re.match(
                r"^\(\d+(?:st|nd|rd|th)\s+use\)$", normalized_remainder
            ):  # (1st use), (2nd use)
                blade_count_buckets["ordinal-use"].append(normalized_remainder)
            elif re.match(r"^\(\d+(?:st|nd|rd|th)\)$", normalized_remainder):  # (1st), (2nd)
                blade_count_buckets["ordinal-use"].append(normalized_remainder)
            elif re.match(r"^\([a-z]+\s+use\)$", normalized_remainder):  # (first use), (second use)
                blade_count_buckets["ordinal-use"].append(normalized_remainder)
            elif re.match(r"^2\^\(nd\)$", normalized_remainder):  # 2^(nd)
                print("DEBUG: Matched 2^(nd) -> ordinal-use")  # Debug
                blade_count_buckets["ordinal-use"].append(normalized_remainder)
            elif re.match(r"^\(\d+x\)$", normalized_remainder) or re.match(
                r"^\(x\d+\)$", normalized_remainder
            ):  # (4x), (x4)
                blade_count_buckets["multiplier"].append(normalized_remainder)
            elif re.match(r"^\(\d+x\?\)$", normalized_remainder):  # (4x?)
                blade_count_buckets["multiplier"].append(normalized_remainder)
            elif re.match(r"^\(\d+x\)\s+\(\d+\)\.?$", normalized_remainder):  # (2x) (2).
                blade_count_buckets["multiplication-plus-simple"].append(normalized_remainder)
            elif re.match(r"^\(\d+\)\s+\(\d+\)\.?$", normalized_remainder):  # (2) (2).
                blade_count_buckets["simple-plus-simple"].append(normalized_remainder)
            elif re.match(r"^\[\d+x\]\s+\(\d+\)$", normalized_remainder):  # [2x] (3)
                blade_count_buckets["multiplication-plus-simple"].append(normalized_remainder)
            elif re.match(r"^\(\d+\)\s+\([a-z]+\)$", normalized_remainder):  # (1) (india)
                blade_count_buckets["location-plus-simple"].append(normalized_remainder)
            elif re.match(r"^\([a-z]+\)\s+\(\d+\)$", normalized_remainder):  # (china) (1)
                blade_count_buckets["location-plus-simple"].append(normalized_remainder)
            elif re.match(r"^\([a-z]+\)\s+\[\d+\]$", normalized_remainder):  # (china) [1]
                blade_count_buckets["location-plus-simple"].append(normalized_remainder)
            # Note: (made in china) [1] patterns are now handled in Phase 1
            elif re.match(r"^\[[a-z]+\]\s+\(\d+\)$", normalized_remainder):  # [china] (1)
                blade_count_buckets["location-plus-simple"].append(normalized_remainder)
            elif re.match(r"^\[\d+\]\s+\([a-z]+\)$", normalized_remainder):  # [1] (india)
                blade_count_buckets["location-plus-simple"].append(normalized_remainder)
            elif re.match(r"^x\d+\s+\(\d+\)$", normalized_remainder):  # x2 (1), x3 (2)
                blade_count_buckets["multiplication-plus-simple"].append(normalized_remainder)
            elif re.match(r"^\d+(?:st|nd|rd|th)\s+use\s+x\d+$", normalized_remainder):  # 1st use x2
                blade_count_buckets["ordinal-plus-multiplier"].append(normalized_remainder)
            elif re.match(r"^\(2\^\(nd\)\s+use\)$", normalized_remainder):  # (2^(nd) use)
                print("DEBUG: Matched (2^(nd) use) -> ordinal-use")  # Debug
                blade_count_buckets["ordinal-use"].append(normalized_remainder)
            elif re.match(r"^\(2\^\(nd\)\)$", normalized_remainder):  # (2^(nd))
                print("DEBUG: Matched (2^(nd)) -> ordinal-use")  # Debug
                blade_count_buckets["ordinal-use"].append(normalized_remainder)
            elif re.match(r"^\([a-z]+\)\(\d+\)$", normalized_remainder):  # (india)(2)
                blade_count_buckets["location-plus-simple"].append(normalized_remainder)
            elif re.match(r"^\(fresh blade\)$", normalized_remainder) or re.match(
                r"^\(new blade\)$", normalized_remainder
            ):
                blade_count_buckets["new-indicator"].append(normalized_remainder)
            elif re.match(r"^\(brand new\)$", normalized_remainder) or re.match(
                r"^\(first time\)$", normalized_remainder
            ):
                blade_count_buckets["new-indicator"].append(normalized_remainder)
            elif re.match(r"^\[new\]$", normalized_remainder):
                blade_count_buckets["new-indicator"].append(normalized_remainder)
            elif re.match(
                r"^\([a-z]+\)$", normalized_remainder
            ) and normalized_remainder.lower() in [
                "(china)",
                "(germany)",
                "(india)",
                "(japan)",
                "(russia)",
                "(thailand)",
                "(usa)",
                "(uk)",
                "(turkey)",
                "(czechoslovakian)",
                "(indian)",
                "(poland)",
                "(russian)",
            ]:
                # (china), (germany), (india), etc. - just location
                non_blade_count_buckets["location-indicator"].append(normalized_remainder)
            elif re.match(
                r"^\(made in [a-z]+\)$", normalized_remainder
            ):  # (made in china), (made in germany)
                # Complex location patterns
                non_blade_count_buckets["location-indicator"].append(normalized_remainder)
            elif re.match(
                r"^\([a-z]+,\s*new\)$", normalized_remainder
            ):  # (thailand, new), (india, new)
                # (location, new) - location plus new indicator (equivalent to (1))
                blade_count_buckets["location-plus-new-indicator"].append(normalized_remainder)
            # Note: (usa, blue box) type patterns will fall through to 'other' bucket
            elif re.match(
                r"^\([a-z]+\)$", normalized_remainder
            ) and normalized_remainder.lower() in [
                "(vintage)",
                "(sample)",
                "(test)",
                "(old)",
            ]:
                non_blade_count_buckets["condition-indicator"].append(normalized_remainder)
            else:
                non_blade_count_buckets["other"].append(normalized_remainder)

    # Create the structured YAML data
    dup_rate = (
        (analysis["total_remainders"] - analysis["unique_remainders"])
        / analysis["total_remainders"]
        * 100
    )
    duplication_rate = f"{dup_rate:.1f}%"

    # Deduplicate all bucket contents to remove duplicates like (3) appearing multiple times
    for bucket_name, bucket_contents in blade_count_buckets.items():
        blade_count_buckets[bucket_name] = list(
            dict.fromkeys(bucket_contents)
        )  # Preserve order, remove duplicates

    for bucket_name, bucket_contents in non_blade_count_buckets.items():
        non_blade_count_buckets[bucket_name] = list(
            dict.fromkeys(bucket_contents)
        )  # Preserve order, remove duplicates

    # Create the structured YAML data
    yaml_data = {
        "metadata": {
            "summary": {
                "total_remainders": analysis["total_remainders"],
                "unique_remainders": analysis["unique_remainders"],
                "duplication_rate": duplication_rate,
            },
            "blade_count_patterns": {
                "total_unique": sum(len(bucket) for bucket in blade_count_buckets.values()),
                "categories": {
                    "simple-numeric": len(blade_count_buckets["simple-numeric"]),
                    "multiplier": len(blade_count_buckets["multiplier"]),
                    "ordinal-use": len(blade_count_buckets["ordinal-use"]),
                    "complex-paren": len(blade_count_buckets["complex-paren"]),
                    "complex-bracket": len(blade_count_buckets["complex-bracket"]),
                    "multiplication-plus-simple": len(
                        blade_count_buckets["multiplication-plus-simple"]
                    ),
                    "location-plus-simple": len(blade_count_buckets["location-plus-simple"]),
                    "location-plus-new-indicator": len(
                        blade_count_buckets["location-plus-new-indicator"]
                    ),
                    "simple-plus-simple": len(blade_count_buckets["simple-plus-simple"]),
                    "simple-plus-ordinal": len(blade_count_buckets["simple-plus-ordinal"]),
                    "ordinal-plus-multiplier": len(blade_count_buckets["ordinal-plus-multiplier"]),
                    "new-indicator": len(blade_count_buckets["new-indicator"]),
                },
            },
            "non_blade_count_patterns": {
                "total_unique": sum(len(bucket) for bucket in non_blade_count_buckets.values()),
                "categories": {
                    "location-indicator": len(non_blade_count_buckets["location-indicator"]),
                    "condition-indicator": len(non_blade_count_buckets["condition-indicator"]),
                    "url-link": len(non_blade_count_buckets["url-link"]),
                    "hashtag": len(non_blade_count_buckets["hashtag"]),
                    "other": len(non_blade_count_buckets["other"]),
                },
            },
        },
        "data": {
            "blade_count_patterns": blade_count_buckets,
            "non_blade_count_patterns": non_blade_count_buckets,
        },
    }

    return yaml_data


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
    yaml_data = create_bucketed_yaml(analysis, all_remainders)

    # Write YAML file
    yaml_file = raw_output_file.replace(".txt", "_bucketed.yaml")
    with open(yaml_file, "w", encoding="utf-8") as f:
        yaml.dump(yaml_data, f, default_flow_style=False, indent=2, sort_keys=False)

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
