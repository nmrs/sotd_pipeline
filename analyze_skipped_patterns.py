#!/usr/bin/env python3
"""
Analyze skipped patterns across all extracted files to identify common formats worth supporting.
"""

import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Dict


def categorize_line(line: str) -> str:
    """Categorize a line based on its pattern."""
    line = line.strip()

    # Check for checkmark format
    if re.match(r"^✓\s*\w+\s*[-:]\s*", line):
        return "checkmark_format"

    # Check for emoji-prefixed format
    if re.match(r"^\*\s*\*\*[^\*]+\*\*\s*[-:]\s*", line):
        return "emoji_bold_format"

    # Check for plain colon format
    if re.match(r"^\w+\s*[-:]\s*", line):
        return "plain_colon_format"

    # Check for dash-prefixed format
    if re.match(r"^-\s*\w+\s*[-:]\s*", line):
        return "dash_prefix_format"

    # Check for asterisk format
    if re.match(r"^\*\s*\w+\s*[-:]\s*", line):
        return "asterisk_format"

    # Check for SOTD format
    if re.match(r"^\*\s*\*\*SOTD\s*[-:]\s*", line):
        return "sotd_header_format"

    # Check for brand-product format
    if re.match(r"^\*\s*\*\*[^-]+-\s*\w+\*\*\s*[-:]\s*", line):
        return "brand_product_format"

    # Check if line contains product keywords
    keywords = [
        "razor",
        "blade",
        "brush",
        "soap",
        "lather",
        "pre-shave",
        "post-shave",
        "aftershave",
    ]
    if any(keyword in line.lower() for keyword in keywords):
        return "contains_product_keywords"

    return "other"


def analyze_skipped_patterns(data_dir: Path = Path("data/extracted")) -> Dict:
    """Analyze all extracted files for skipped patterns."""
    results = {
        "total_files": 0,
        "total_skipped": 0,
        "pattern_counts": Counter(),
        "examples": defaultdict(list),
        "monthly_stats": [],
        "potential_patterns": [],
    }

    # Get all JSON files
    json_files = list(data_dir.glob("*.json"))
    json_files.sort()

    print(f"Analyzing {len(json_files)} extracted files...")

    for file_path in json_files:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            month = file_path.stem
            skipped = data.get("skipped", [])
            skipped_count = len(skipped)

            results["total_files"] += 1
            results["total_skipped"] += skipped_count

            month_stats = {"month": month, "skipped_count": skipped_count, "patterns": Counter()}

            # Analyze each skipped comment
            for comment in skipped:
                body = comment.get("body", "")
                if not body or body == "[deleted]":
                    continue

                # Split into lines and analyze each line
                lines = body.split("\n")
                for line in lines:
                    line = line.strip()
                    if not line:
                        continue

                    pattern = categorize_line(line)
                    results["pattern_counts"][pattern] += 1
                    month_stats["patterns"][pattern] += 1

                    # Store examples (limit to 5 per pattern)
                    if len(results["examples"][pattern]) < 5:
                        results["examples"][pattern].append(
                            {
                                "line": line,
                                "month": month,
                                "full_comment": body[:200] + "..." if len(body) > 200 else body,
                            }
                        )

            results["monthly_stats"].append(month_stats)

        except Exception as e:
            print(f"Error processing {file_path}: {e}")

    # Identify potential patterns worth supporting
    potential_patterns = []
    for pattern, count in results["pattern_counts"].most_common():
        if count >= 5:  # Only consider patterns that appear at least 5 times
            examples = results["examples"][pattern]
            potential_patterns.append(
                {
                    "pattern": pattern,
                    "count": count,
                    "percentage": (count / results["total_skipped"]) * 100,
                    "examples": examples,
                }
            )

    results["potential_patterns"] = potential_patterns

    return results


def save_analysis_results(
    results: Dict, output_file: Path = Path("skipped_patterns_analysis.json")
):
    """Save analysis results to JSON file."""
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"Analysis saved to {output_file}")


def print_summary(results: Dict):
    """Print a summary of the analysis."""
    print("\n" + "=" * 60)
    print("SKIPPED PATTERNS ANALYSIS SUMMARY")
    print("=" * 60)

    print(f"\nTotal files analyzed: {results['total_files']}")
    print(f"Total skipped comments: {results['total_skipped']}")

    print("\nTop patterns by frequency:")
    for pattern, count in results["pattern_counts"].most_common(10):
        percentage = (count / results["total_skipped"]) * 100
        print(f"  {pattern:25} — {count:4d} occurrences ({percentage:5.1f}%)")

    print("\nPotential patterns worth supporting (≥5 occurrences):")
    for pattern_info in results["potential_patterns"]:
        print(
            f"\n{pattern_info['pattern']} ({pattern_info['count']} occurrences, "
            f"{pattern_info['percentage']:.1f}%):"
        )
        for example in pattern_info["examples"][:3]:  # Show first 3 examples
            print(f"  ↳ {example['line']}")
            print(f"    (from {example['month']})")


if __name__ == "__main__":
    print("Analyzing skipped patterns across all extracted files...")
    results = analyze_skipped_patterns()
    save_analysis_results(results)
    print_summary(results)
