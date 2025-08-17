#!/usr/bin/env python3
"""Analyze normalized blade patterns to find unhandled cases that should be normalized out."""

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
    from sotd.utils.parallel_processor import create_parallel_processor
except ImportError:
    print("Error: Could not import from sotd. Make sure you're running from the project root.")
    print("Try: python scripts/analyze_normalized_patterns.py")
    sys.exit(1)


def extract_unhandled_normalized_patterns(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Extract normalized blade patterns and analyze what might still need normalization."""
    patterns = []

    for record in records:
        if "blade" in record and isinstance(record["blade"], dict):
            original = record["blade"].get("original", "")
            normalized = record["blade"].get("normalized", "")

            if (
                original
                and normalized
                and isinstance(original, str)
                and isinstance(normalized, str)
            ):
                # Focus on what's still in the normalized field that might need normalization
                normalized_clean = normalized.strip()

                if normalized_clean:
                    # Look for patterns in the normalized field that might represent:
                    # 1. Blade usage count: (1), (2), (10), etc.
                    # 2. Country of origin: (USA), (Germany), etc.
                    # 3. Blade condition: (new), (fresh), etc.
                    # 4. Blade format: (stainless), (platinum), etc.
                    # 5. Other metadata that should be normalized out

                    # Check for patterns that should probably be normalized out
                    unhandled_patterns = []

                    # Look for blade usage counts still in normalized
                    usage_matches = re.findall(r"\(\d+\)|\[\d+\]|\{\d+\}", normalized_clean)
                    if usage_matches:
                        unhandled_patterns.extend(usage_matches)

                    # Look for country indicators still in normalized
                    country_matches = re.findall(r"\([A-Za-z\s]+\)", normalized_clean)
                    countries = [
                        "usa",
                        "germany",
                        "japan",
                        "china",
                        "india",
                        "russia",
                        "uk",
                        "turkey",
                        "thailand",
                        "poland",
                        "czech",
                        "slovakia",
                    ]
                    for match in country_matches:
                        if any(country in match.lower() for country in countries):
                            unhandled_patterns.append(match)

                    # Look for condition indicators still in normalized
                    condition_matches = re.findall(
                        r"\(new\)|\(fresh\)|\(vintage\)|\(old\)|\(sample\)|\(test\)",
                        normalized_clean,
                    )
                    if condition_matches:
                        unhandled_patterns.extend(condition_matches)

                    # Look for format indicators still in normalized
                    format_matches = re.findall(
                        r"\(stainless\)|\(platinum\)|\(chrome\)|\(carbon\)", normalized_clean
                    )
                    if format_matches:
                        unhandled_patterns.extend(format_matches)

                    # Look for packaging indicators still in normalized
                    packaging_matches = re.findall(
                        r"\(blue box\)|\(tuck\)|\(pack\)|\(blister\)", normalized_clean
                    )
                    if packaging_matches:
                        unhandled_patterns.extend(packaging_matches)

                    # Look for ordinal usage indicators still in normalized
                    ordinal_matches = re.findall(
                        r"\(\d+(?:st|nd|rd|th)\s+use\)|\(\d+(?:st|nd|rd|th)\)", normalized_clean
                    )
                    if ordinal_matches:
                        unhandled_patterns.extend(ordinal_matches)

                    # Look for multiplier indicators still in normalized
                    multiplier_matches = re.findall(
                        r"\(x\d+\)|\(\d+x\)|x\d+|\d+x", normalized_clean
                    )
                    if multiplier_matches:
                        unhandled_patterns.extend(multiplier_matches)

                    # Look for other metadata patterns
                    other_matches = re.findall(r"\([A-Za-z\s]+\)", normalized_clean)
                    # Filter out already matched patterns
                    other_matches = [
                        m
                        for m in other_matches
                        if m not in unhandled_patterns
                        and not re.match(r"^\([A-Za-z\s]+\)$", m)  # Avoid generic matches
                    ]
                    if other_matches:
                        unhandled_patterns.extend(other_matches)

                    if unhandled_patterns:
                        patterns.append(
                            {
                                "original": original.strip(),
                                "normalized": normalized_clean,
                                "unhandled_patterns": unhandled_patterns,
                                "unhandled_text": " ".join(unhandled_patterns),
                                "pattern_type": "unhandled_normalization",
                            }
                        )

    return patterns


def process_month_file(file_path: Path) -> Dict[str, Any]:
    """Process a single month file to extract unhandled normalized blade patterns."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        records = data.get("data", [])
        patterns = extract_unhandled_normalized_patterns(records)

        return {
            "month": file_path.stem,
            "patterns": patterns,
            "count": len(patterns),
            "status": "success",
        }

    except Exception as e:
        return {
            "month": file_path.stem,
            "patterns": [],
            "count": 0,
            "status": "error",
            "error": str(e),
        }


def _process_month_parallel(year: int, month: int, base_path: Path) -> Optional[Dict[str, Any]]:
    """Process a single month for parallel execution."""
    ym = f"{year:04d}-{month:02d}"
    file_path = base_path / "extracted" / f"{ym}.json"

    if not file_path.exists():
        return None

    return process_month_file(file_path)


def analyze_unhandled_patterns(all_patterns: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Analyze unhandled patterns and categorize them."""
    if not all_patterns:
        return {
            "total_patterns": 0,
            "unique_patterns": 0,
            "pattern_categories": {},
            "unhandled_text_analysis": {},
        }

    # Analyze what's still unhandled
    unhandled_text_counts = {}
    pattern_categories = {
        "blade_usage_count": 0,  # (1), (2), (10), etc.
        "country_origin": 0,  # (USA), (Germany), etc.
        "blade_condition": 0,  # (new), (fresh), etc.
        "blade_format": 0,  # (stainless), (platinum), etc.
        "blade_packaging": 0,  # (blue box), (tuck), etc.
        "blade_vintage": 0,  # (vintage), (old), etc.
        "blade_sample": 0,  # (sample), (test), etc.
        "ordinal_usage": 0,  # (1st use), (2nd), etc.
        "multiplier": 0,  # (x2), (2x), etc.
        "other_metadata": 0,  # Other patterns
    }

    for pattern in all_patterns:
        unhandled_text = pattern.get("unhandled_text", "").strip()

        if unhandled_text:
            # Count frequency of unhandled text
            unhandled_text_counts[unhandled_text] = unhandled_text_counts.get(unhandled_text, 0) + 1

            # Categorize the pattern
            if re.search(r"\(\d+\)|\[\d+\]|\{\d+\}", unhandled_text):
                pattern_categories["blade_usage_count"] += 1
            elif re.search(r"\([A-Za-z\s]+\)", unhandled_text) and any(
                country in unhandled_text.lower()
                for country in [
                    "usa",
                    "germany",
                    "japan",
                    "china",
                    "india",
                    "russia",
                    "uk",
                    "turkey",
                    "thailand",
                    "poland",
                    "czech",
                    "slovakia",
                ]
            ):
                pattern_categories["country_origin"] += 1
            elif re.search(
                r"\(new\)|\(fresh\)|\(vintage\)|\(old\)|\(sample\)|\(test\)", unhandled_text
            ):
                pattern_categories["blade_condition"] += 1
            elif re.search(r"\(stainless\)|\(platinum\)|\(chrome\)|\(carbon\)", unhandled_text):
                pattern_categories["blade_format"] += 1
            elif re.search(r"\(blue box\)|\(tuck\)|\(pack\)|\(blister\)", unhandled_text):
                pattern_categories["blade_packaging"] += 1
            elif re.search(r"\(\d+(?:st|nd|rd|th)\s+use\)|\(\d+(?:st|nd|rd|th)\)", unhandled_text):
                pattern_categories["ordinal_usage"] += 1
            elif re.search(r"\(x\d+\)|\(\d+x\)|x\d+|\d+x", unhandled_text):
                pattern_categories["multiplier"] += 1
            else:
                pattern_categories["other_metadata"] += 1

    # Get unique patterns (case-insensitive deduplication)
    unique_patterns = []
    seen = set()

    for pattern in all_patterns:
        # Create a key based on the transformation
        key = (pattern["original"].lower(), pattern["normalized"].lower())
        if key not in seen:
            seen.add(key)
            unique_patterns.append(pattern)

    return {
        "total_patterns": len(all_patterns),
        "unique_patterns": len(unique_patterns),
        "unique_pattern_list": unique_patterns,
        "pattern_categories": pattern_categories,
        "unhandled_text_analysis": {
            "total_unique_unhandled": len(unhandled_text_counts),
            "unhandled_text_counts": dict(
                sorted(unhandled_text_counts.items(), key=lambda x: x[1], reverse=True)[:100]
            ),  # Top 100
        },
    }


def create_bucketed_yaml(analysis: Dict[str, Any]) -> Dict[str, Any]:
    """Create a YAML file with unhandled patterns grouped into logical buckets."""

    # Define pattern buckets for what's still unhandled in normalized
    unhandled_buckets = {
        "blade_usage_count": [],  # (1), (2), (10), etc.
        "country_origin": [],  # (USA), (Germany), etc.
        "blade_condition": [],  # (new), (fresh), etc.
        "blade_format": [],  # (stainless), (platinum), etc.
        "blade_packaging": [],  # (blue box), (tuck), etc.
        "blade_vintage": [],  # (vintage), (old), etc.
        "blade_sample": [],  # (sample), (test), etc.
        "ordinal_usage": [],  # (1st use), (2nd), etc.
        "multiplier": [],  # (x2), (2x), etc.
        "other_metadata": [],  # Other patterns
    }

    # Categorize each unique pattern
    for pattern in analysis["unique_pattern_list"]:
        unhandled_text = pattern.get("unhandled_text", "").strip()

        if not unhandled_text:
            continue

        # Categorize based on unhandled text
        if re.search(r"\(\d+\)|\[\d+\]|\{\d+\}", unhandled_text):
            unhandled_buckets["blade_usage_count"].append(
                {
                    "original": pattern["original"],
                    "normalized": pattern["normalized"],
                    "unhandled": unhandled_text,
                    "type": "blade_usage_count",
                }
            )
        elif re.search(r"\([A-Za-z\s]+\)", unhandled_text) and any(
            country in unhandled_text.lower()
            for country in [
                "usa",
                "germany",
                "japan",
                "china",
                "india",
                "russia",
                "uk",
                "turkey",
                "thailand",
                "poland",
                "czech",
                "slovakia",
            ]
        ):
            unhandled_buckets["country_origin"].append(
                {
                    "original": pattern["original"],
                    "normalized": pattern["normalized"],
                    "unhandled": unhandled_text,
                    "type": "country_origin",
                }
            )
        elif re.search(
            r"\(new\)|\(fresh\)|\(vintage\)|\(old\)|\(sample\)|\(test\)", unhandled_text
        ):
            unhandled_buckets["blade_condition"].append(
                {
                    "original": pattern["original"],
                    "normalized": pattern["normalized"],
                    "unhandled": unhandled_text,
                    "type": "blade_condition",
                }
            )
        elif re.search(r"\(stainless\)|\(platinum\)|\(chrome\)|\(carbon\)", unhandled_text):
            unhandled_buckets["blade_format"].append(
                {
                    "original": pattern["original"],
                    "normalized": pattern["normalized"],
                    "unhandled": unhandled_text,
                    "type": "blade_format",
                }
            )
        elif re.search(r"\(blue box\)|\(tuck\)|\(pack\)|\(blister\)", unhandled_text):
            unhandled_buckets["blade_packaging"].append(
                {
                    "original": pattern["original"],
                    "normalized": pattern["normalized"],
                    "unhandled": unhandled_text,
                    "type": "blade_packaging",
                }
            )
        elif re.search(r"\(\d+(?:st|nd|rd|th)\s+use\)|\(\d+(?:st|nd|rd|th)\)", unhandled_text):
            unhandled_buckets["ordinal_usage"].append(
                {
                    "original": pattern["original"],
                    "normalized": pattern["normalized"],
                    "unhandled": unhandled_text,
                    "type": "ordinal_usage",
                }
            )
        elif re.search(r"\(x\d+\)|\(\d+x\)|x\d+|\d+x", unhandled_text):
            unhandled_buckets["multiplier"].append(
                {
                    "original": pattern["original"],
                    "normalized": pattern["normalized"],
                    "unhandled": unhandled_text,
                    "type": "multiplier",
                }
            )
        else:
            unhandled_buckets["other_metadata"].append(
                {
                    "original": pattern["original"],
                    "normalized": pattern["normalized"],
                    "unhandled": unhandled_text,
                    "type": "other_metadata",
                }
            )

    # Create the structured YAML data
    yaml_data = {
        "metadata": {
            "summary": {
                "total_patterns": analysis["total_patterns"],
                "unique_patterns": analysis["unique_patterns"],
                "total_unique_unhandled_text": analysis["unhandled_text_analysis"][
                    "total_unique_unhandled"
                ],
            },
            "pattern_categories": {
                "blade_usage_count": len(unhandled_buckets["blade_usage_count"]),
                "country_origin": len(unhandled_buckets["country_origin"]),
                "blade_condition": len(unhandled_buckets["blade_condition"]),
                "blade_format": len(unhandled_buckets["blade_format"]),
                "blade_packaging": len(unhandled_buckets["blade_packaging"]),
                "blade_vintage": len(unhandled_buckets["blade_vintage"]),
                "blade_sample": len(unhandled_buckets["blade_sample"]),
                "ordinal_usage": len(unhandled_buckets["ordinal_usage"]),
                "multiplier": len(unhandled_buckets["multiplier"]),
                "other_metadata": len(unhandled_buckets["other_metadata"]),
            },
        },
        "data": {
            "unhandled_patterns": unhandled_buckets,
            "unhandled_text_frequency": analysis["unhandled_text_analysis"][
                "unhandled_text_counts"
            ],
        },
    }

    return yaml_data


def get_parser() -> argparse.ArgumentParser:
    """Get the argument parser for the script."""
    parser = argparse.ArgumentParser(
        description="Analyze normalized blade patterns to find unhandled cases that should be normalized out"
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
    extracted_dir = base_path / "extracted"

    if not extracted_dir.exists():
        print(f"❌ Extracted directory not found: {extracted_dir}")
        return

    # Find all extracted data files
    extracted_files = list(extracted_dir.glob("*.json"))
    if not extracted_files:
        print(f"❌ No extracted data files found in {extracted_dir}")
        return

    print("🔍 ANALYZING UNHANDLED NORMALIZED BLADE PATTERNS")
    print("=" * 60)
    print(f"📁 Found {len(extracted_files)} extracted data files")

    # Create parallel processor
    processor = create_parallel_processor("analyze_unhandled_patterns")

    # Convert file paths to month tuples for parallel processing
    months = []
    for file_path in extracted_files:
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
        processor.print_parallel_summary(results, "analyze_unhandled_patterns")

    else:
        print(f"🐌 Processing {len(months)} months sequentially...")

        # Process months sequentially
        results = processor.process_months_sequential(
            months, _process_month_parallel, (base_path,), "Months"
        )

    # Collect all patterns from results
    all_patterns = []
    successful_months = 0

    for result in results:
        if result and result.get("status") == "success":
            all_patterns.extend(result["patterns"])
            successful_months += 1
            print(f"📊 Processing {result['month']}...")
            print(f"  ✅ Found {result['count']} unhandled patterns")
        elif result and result.get("status") == "error":
            print(f"❌ Error processing {result['month']}: {result.get('error', 'Unknown error')}")

    print(f"\n📈 TOTAL: {len(all_patterns):,} unhandled patterns found")

    if not all_patterns:
        print("❌ No unhandled patterns found to analyze")
        return

    # Analyze unhandled patterns
    print("\n🔍 Analyzing unhandled patterns...")
    analysis = analyze_unhandled_patterns(all_patterns)

    # Write results to files
    timestamp = datetime.now().strftime("%Y-%m-%d")
    raw_output_file = f"analysis/{timestamp}_unhandled_patterns_raw.txt"
    unique_output_file = f"analysis/{timestamp}_unhandled_patterns_unique.txt"
    yaml_output_file = f"analysis/{timestamp}_unhandled_patterns_bucketed.yaml"

    print(f"\n💾 Writing raw unhandled patterns to {raw_output_file}...")

    # Ensure analysis directory exists
    Path("analysis").mkdir(exist_ok=True)

    # Write raw patterns (not deduped) - shows actual frequency
    with open(raw_output_file, "w", encoding="utf-8") as f:
        for pattern in all_patterns:
            f.write(f"Original: {pattern['original']}\n")
            f.write(f"Normalized: {pattern['normalized']}\n")
            if pattern.get("unhandled_text"):
                f.write(f"Unhandled: {pattern['unhandled_text']}\n")
            f.write("-" * 50 + "\n")

    print(f"✅ Raw unhandled patterns saved to {raw_output_file}")

    # Write unique patterns (deduped) - shows pattern variety
    print(f"\n💾 Writing unique unhandled patterns to {unique_output_file}...")
    with open(unique_output_file, "w", encoding="utf-8") as f:
        for pattern in analysis["unique_pattern_list"]:
            f.write(f"Original: {pattern['original']}\n")
            f.write(f"Normalized: {pattern['normalized']}\n")
            if pattern.get("unhandled_text"):
                f.write(f"Unhandled: {pattern['unhandled_text']}\n")
            f.write("-" * 50 + "\n")

    print(f"✅ Unique unhandled patterns saved to {unique_output_file}")

    # Create bucketed YAML file
    print("\n🗂️  Creating bucketed YAML file...")
    yaml_data = create_bucketed_yaml(analysis)

    # Write YAML file
    with open(yaml_output_file, "w", encoding="utf-8") as f:
        yaml.dump(yaml_data, f, default_flow_style=False, indent=2, sort_keys=False)

    print(f"✅ Bucketed YAML created: {yaml_output_file}")

    # Print summary
    print("\n📊 ANALYSIS SUMMARY")
    print("=" * 40)
    print(f"Total patterns: {analysis['total_patterns']:,}")
    print(f"Unique patterns: {analysis['unique_patterns']:,}")
    print(
        f"Unique unhandled text: {analysis['unhandled_text_analysis']['total_unique_unhandled']:,}"
    )

    print("\n📋 PATTERN CATEGORIES")
    print("=" * 40)
    for category, count in analysis["pattern_categories"].items():
        print(f"{category.replace('_', ' ').title()}: {count:,}")


if __name__ == "__main__":
    main()
