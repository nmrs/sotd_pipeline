#!/usr/bin/env python3
"""Extract remaining bracket/parenthesis patterns from normalized blade fields.

This script analyzes the normalized blade strings to find patterns that are still
present and could potentially be normalized out. It looks for any remaining
brackets, parentheses, or braces that weren't stripped during normalization.
"""

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


def extract_remaining_bracket_patterns(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Extract remaining bracket/parenthesis patterns from normalized blade fields."""
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
                normalized_clean = normalized.strip()

                if normalized_clean:
                    # Find all remaining bracket/parenthesis patterns
                    # This includes unbalanced patterns like (something] or [something)
                    bracket_patterns = re.findall(r"[\(\[\{][^\)\]\}]*[\)\]\}]", normalized_clean)

                    # Find unmatched opening brackets/parentheses
                    unmatched_open = []
                    for match in re.finditer(r"[\(\[\{]", normalized_clean):
                        pos = match.start()
                        # Check if there's a closing bracket after this opening one
                        remaining_text = normalized_clean[pos:]
                        if not re.search(r"[\)\]\}]", remaining_text):
                            unmatched_open.append(match.group())

                    # Find unmatched closing brackets/parentheses
                    unmatched_close = []
                    for match in re.finditer(r"[\)\]\}]", normalized_clean):
                        pos = match.start()
                        # Check if there's an opening bracket before this closing one
                        preceding_text = normalized_clean[:pos]
                        if not re.search(r"[\(\[\{]", preceding_text):
                            unmatched_close.append(match.group())

                    all_patterns = bracket_patterns + unmatched_open + unmatched_close

                    if all_patterns:
                        patterns.append(
                            {
                                "original": original.strip(),
                                "normalized": normalized_clean,
                                "remaining_patterns": all_patterns,
                                "pattern_text": " ".join(all_patterns),
                                "pattern_type": "remaining_brackets",
                            }
                        )

    return patterns


def analyze_remaining_patterns(all_patterns: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Analyze the remaining bracket patterns by type and frequency."""
    pattern_counts = {}
    pattern_examples = {}

    for pattern_data in all_patterns:
        for pattern in pattern_data["remaining_patterns"]:
            if pattern not in pattern_counts:
                pattern_counts[pattern] = 0
                pattern_examples[pattern] = {}

            pattern_counts[pattern] += 1

            # Store example with context
            example = {
                "original": pattern_data["original"],
                "normalized": pattern_data["normalized"],
            }
            # Convert dict to tuple for hashing
            example_tuple = (example["original"], example["normalized"])
            if example_tuple not in pattern_examples[pattern]:
                pattern_examples[pattern][example_tuple] = 0
            pattern_examples[pattern][example_tuple] += 1

    # Sort by frequency
    sorted_patterns = sorted(pattern_counts.items(), key=lambda x: x[1], reverse=True)

    return {
        "total_records_with_patterns": len(all_patterns),
        "total_pattern_occurrences": sum(pattern_counts.values()),
        "unique_patterns": len(pattern_counts),
        "pattern_frequency": sorted_patterns,
        "pattern_examples": pattern_examples,
    }


def create_bucketed_yaml(analysis: Dict[str, Any]) -> Dict[str, Any]:
    """Create structured YAML output with bucketed patterns."""
    bucketed = {
        "analysis_metadata": {
            "analysis_date": datetime.now().isoformat(),
            "total_records_with_patterns": analysis["total_records_with_patterns"],
            "total_pattern_occurrences": analysis["total_pattern_occurrences"],
            "unique_patterns": analysis["unique_patterns"],
        },
        "pattern_categories": {
            "high_frequency": [],  # 10+ occurrences
            "medium_frequency": [],  # 3-9 occurrences
            "low_frequency": [],  # 1-2 occurrences
        },
        "detailed_patterns": {},
    }

    # Categorize patterns by frequency
    for pattern, count in analysis["pattern_frequency"]:
        pattern_info = {"pattern": pattern, "count": count, "examples": []}

        # Add examples (limit to 5 per pattern)
        examples = analysis["pattern_examples"][pattern]
        for example_tuple, freq in sorted(examples.items(), key=lambda x: x[1], reverse=True)[:5]:
            original, normalized = example_tuple
            pattern_info["examples"].append(
                {"original": original, "normalized": normalized, "frequency": freq}
            )

        bucketed["detailed_patterns"][pattern] = pattern_info

        # Categorize by frequency
        if count >= 10:
            bucketed["pattern_categories"]["high_frequency"].append(pattern)
        elif count >= 3:
            bucketed["pattern_categories"]["medium_frequency"].append(pattern)
        else:
            bucketed["pattern_categories"]["low_frequency"].append(pattern)

    return bucketed


def process_month_file(file_path: Path) -> Optional[List[Dict[str, Any]]]:
    """Process a single month file and extract remaining bracket patterns."""
    try:
        with open(file_path, encoding="utf-8") as f:
            data = json.load(f)

        records = data.get("data", [])
        if not records:
            return None

        return extract_remaining_bracket_patterns(records)

    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return None


def main():
    """Main function to extract remaining bracket patterns from extracted data."""
    parser = argparse.ArgumentParser(
        description="Extract remaining bracket/parenthesis patterns from normalized blade fields"
    )
    parser.add_argument(
        "--data-dir",
        default="data/extracted",
        help="Directory containing extracted data files (default: data/extracted)",
    )
    parser.add_argument(
        "--output-dir",
        default="analysis",
        help="Output directory for analysis files (default: analysis)",
    )
    parser.add_argument(
        "--parallel", action="store_true", help="Use parallel processing for large datasets"
    )

    args = parser.parse_args()

    data_dir = Path(args.data_dir)
    output_dir = Path(args.output_dir)

    if not data_dir.exists():
        print(f"Error: Data directory {data_dir} does not exist")
        sys.exit(1)

    # Find all extracted data files
    json_files = list(data_dir.glob("*.json"))
    if not json_files:
        print(f"No JSON files found in {data_dir}")
        sys.exit(1)

    print(f"Found {len(json_files)} extracted data files")

    # Process files sequentially
    print("Processing files sequentially...")
    all_patterns = []
    for file_path in json_files:
        print(f"Processing {file_path.name}...")
        patterns = process_month_file(file_path)
        if patterns:
            all_patterns.extend(patterns)

    if not all_patterns:
        print("No remaining bracket patterns found")
        return

    print(f"Found {len(all_patterns)} records with remaining bracket patterns")

    # Analyze patterns
    analysis = analyze_remaining_patterns(all_patterns)
    bucketed = create_bucketed_yaml(analysis)

    # Create output directory
    output_dir.mkdir(exist_ok=True)

    # Generate date for filenames
    date_str = datetime.now().strftime("%Y%m%d")

    # Save raw patterns
    raw_file = output_dir / f"{date_str}_remaining_bracket_patterns_raw.txt"
    with open(raw_file, "w", encoding="utf-8") as f:
        for pattern_data in all_patterns:
            f.write(f"Original: {pattern_data['original']}\n")
            f.write(f"Normalized: {pattern_data['normalized']}\n")
            f.write(f"Remaining Patterns: {pattern_data['remaining_patterns']}\n")
            f.write("-" * 80 + "\n")

    # Save unique patterns
    unique_patterns = set()
    for pattern_data in all_patterns:
        unique_patterns.update(pattern_data["remaining_patterns"])

    unique_file = output_dir / f"{date_str}_remaining_bracket_patterns_unique.txt"
    with open(unique_file, "w", encoding="utf-8") as f:
        for pattern in sorted(unique_patterns):
            f.write(f"{pattern}\n")

    # Save bucketed analysis
    yaml_file = output_dir / f"{date_str}_remaining_bracket_patterns_bucketed.yaml"
    with open(yaml_file, "w", encoding="utf-8") as f:
        yaml.dump(bucketed, f, default_flow_style=False, indent=2, allow_unicode=True)

    # Print summary
    print("\nAnalysis complete!")
    print(f"Raw patterns: {raw_file}")
    print(f"Unique patterns: {unique_file}")
    print(f"Bucketed analysis: {yaml_file}")

    print("\nSummary:")
    print(f"- Total records with patterns: {analysis['total_records_with_patterns']:,}")
    print(f"- Total pattern occurrences: {analysis['total_pattern_occurrences']:,}")
    print(f"- Unique patterns: {analysis['unique_patterns']:,}")

    print("\nPattern categories:")
    print(f"- High frequency (10+): {len(bucketed['pattern_categories']['high_frequency'])}")
    print(f"- Medium frequency (3-9): {len(bucketed['pattern_categories']['medium_frequency'])}")
    print(f"- Low frequency (1-2): {len(bucketed['pattern_categories']['low_frequency'])}")

    if bucketed["pattern_categories"]["high_frequency"]:
        print("\nTop high-frequency patterns:")
        for pattern in bucketed["pattern_categories"]["high_frequency"][:5]:
            count = bucketed["detailed_patterns"][pattern]["count"]
            print(f"  {pattern}: {count:,} occurrences")


if __name__ == "__main__":
    main()
