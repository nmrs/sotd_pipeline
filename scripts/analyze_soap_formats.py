#!/usr/bin/env python3
"""
Analyze extracted soap data to identify format indicators.

This script analyzes all extracted soap entries and identifies format indicators
(e.g., "croap", "cream", "soap", "puck", etc.) that appear with " - " prefixes,
providing data-driven insights for deciding which formats should be stripped.
"""

import argparse
import json
import re
from collections import defaultdict
from pathlib import Path
from typing import Dict, Tuple


def is_valid_month_file(path: Path) -> bool:
    """Check if file is a valid YYYY-MM.json file (not test/backup files)."""
    name = path.name
    # Match YYYY-MM.json pattern, exclude test/backup files
    if not re.match(r"^\d{4}-\d{2}\.json$", name):
        return False
    return True


def extract_format_with_dash(text: str) -> Tuple[str | None, str]:
    """
    Extract format indicator from text ending with " - [format]".

    Args:
        text: Input text to analyze

    Returns:
        Tuple of (format, remaining_text) or (None, original_text) if no match
    """
    # Match " - [format]" at end, with optional punctuation
    pattern = r"\s*-\s*(\w+(?:\s+\w+)*)\s*[.!?]*\s*$"
    match = re.search(pattern, text, re.IGNORECASE)
    if match:
        format_indicator = match.group(1).strip().lower()
        remaining = text[: match.start()].strip()
        return format_indicator, remaining
    return None, text


def extract_final_word_token(text: str) -> str:
    """
    Extract the final word token from text, treating "shave"/"shaving" + word as full token.

    Only combines "shave"/"shaving" with format indicators like "soap", not with other words.

    Args:
        text: Input text to analyze

    Returns:
        Final word token (e.g., "soap", "shaving soap", "cream", "puck")
    """
    if not text or not text.strip():
        return ""

    # Strip trailing punctuation and whitespace
    cleaned = text.strip()
    cleaned = re.sub(r"[.!?]*\s*$", "", cleaned)

    # Split into words
    words = cleaned.split()
    if not words:
        return ""

    # Get last word
    last_word = words[-1].lower()

    # Format indicators that can be combined with "shave"/"shaving"
    # Only "soap" makes sense as "shaving soap" or "shave soap"
    shave_combinable = {"soap"}

    # Check if second-to-last word is "shave" or "shaving"
    # Only combine if the last word is a format indicator that makes sense
    if len(words) >= 2:
        second_to_last = words[-2].lower()
        if second_to_last in ("shave", "shaving") and last_word in shave_combinable:
            # Combine as full token
            return f"{second_to_last} {last_word}"

    return last_word


def extract_format_without_dash(text: str) -> Tuple[str | None, str]:
    """
    Extract format indicator from text ending with standalone format (no dash).

    Args:
        text: Input text to analyze

    Returns:
        Tuple of (format, remaining_text) or (None, original_text) if no match
    """
    # Known format indicators that can appear without dash
    # This is a conservative list to avoid false positives (scent names, etc.)
    known_formats = {
        "soap",
        "cream",
        "croap",
        "puck",
        "stick",
        "tube",
        "hard",
        "soft",
        "gel",
        "foam",
        "splash",
        "balm",
        "aftershave",
        "shaving soap",
        "shave soap",
        "crema da barba",
    }

    # Match standalone format at end (more conservative - only known formats)
    # Only match single-word formats to avoid false positives
    pattern = r"\s+(\w+)\s*[.!?]*\s*$"
    match = re.search(pattern, text, re.IGNORECASE)
    if match:
        format_indicator = match.group(1).strip().lower()
        # Only return if it's a known format indicator
        if format_indicator in known_formats:
            remaining = text[: match.start()].strip()
            return format_indicator, remaining
    return None, text


def analyze_extracted_data(data_dir: Path) -> Dict[str, Dict]:
    """
    Analyze all extracted JSON files for soap format indicators.

    Args:
        data_dir: Directory containing extracted JSON files

    Returns:
        Dictionary with format statistics and examples
    """
    format_stats: Dict[str, Dict] = defaultdict(
        lambda: {
            "with_dash": {"count": 0, "examples_original": [], "examples_normalized": []},
            "without_dash": {"count": 0, "examples_original": [], "examples_normalized": []},
        }
    )

    total_entries = 0
    months_processed = set()

    # Get all valid month files
    json_files = sorted([f for f in data_dir.glob("*.json") if is_valid_month_file(f)])

    for json_file in json_files:
        try:
            with open(json_file, encoding="utf-8") as f:
                data = json.load(f)

            month = json_file.stem
            months_processed.add(month)

            entries = data.get("data", [])
            for entry in entries:
                if "soap" not in entry:
                    continue

                total_entries += 1
                soap_data = entry["soap"]

                # Analyze original field
                original = soap_data.get("original", "")
                if original:
                    # Check for format with dash
                    format_with_dash, remaining = extract_format_with_dash(original)
                    if format_with_dash:
                        stats = format_stats[format_with_dash]["with_dash"]
                        stats["count"] += 1
                        if len(stats["examples_original"]) < 10:
                            stats["examples_original"].append(original)

                    # Check for format without dash
                    format_without_dash, remaining = extract_format_without_dash(original)
                    if format_without_dash:
                        stats = format_stats[format_without_dash]["without_dash"]
                        stats["count"] += 1
                        if len(stats["examples_original"]) < 10:
                            stats["examples_original"].append(original)

                # Analyze normalized field
                normalized = soap_data.get("normalized", "")
                if normalized:
                    # Check for format with dash
                    format_with_dash, remaining = extract_format_with_dash(normalized)
                    if format_with_dash:
                        stats = format_stats[format_with_dash]["with_dash"]
                        if len(stats["examples_normalized"]) < 10:
                            stats["examples_normalized"].append(normalized)

                    # Check for format without dash
                    format_without_dash, remaining = extract_format_without_dash(normalized)
                    if format_without_dash:
                        stats = format_stats[format_without_dash]["without_dash"]
                        if len(stats["examples_normalized"]) < 10:
                            stats["examples_normalized"].append(normalized)

        except (json.JSONDecodeError, KeyError) as e:
            print(f"Warning: Error processing {json_file}: {e}")
            continue

    return {
        "total_entries": total_entries,
        "months_processed": len(months_processed),
        "format_stats": dict(format_stats),
    }


def analyze_final_words(data_dir: Path) -> Dict[str, Dict]:
    """
    Analyze all extracted JSON files for final word tokens in soap strings.

    Args:
        data_dir: Directory containing extracted JSON files

    Returns:
        Dictionary with final word statistics and examples
    """
    final_word_stats: Dict[str, Dict] = defaultdict(
        lambda: {
            "count": 0,
            "examples_original": [],
            "examples_normalized": [],
        }
    )

    total_entries = 0
    months_processed = set()

    # Get all valid month files
    json_files = sorted([f for f in data_dir.glob("*.json") if is_valid_month_file(f)])

    for json_file in json_files:
        try:
            with open(json_file, encoding="utf-8") as f:
                data = json.load(f)

            month = json_file.stem
            months_processed.add(month)

            entries = data.get("data", [])
            for entry in entries:
                if "soap" not in entry:
                    continue

                total_entries += 1
                soap_data = entry["soap"]

                # Analyze original field
                original = soap_data.get("original", "")
                if original:
                    final_token = extract_final_word_token(original)
                    if final_token:
                        stats = final_word_stats[final_token]
                        stats["count"] += 1
                        if len(stats["examples_original"]) < 10:
                            stats["examples_original"].append(original)

                # Analyze normalized field
                normalized = soap_data.get("normalized", "")
                if normalized:
                    final_token = extract_final_word_token(normalized)
                    if final_token:
                        stats = final_word_stats[final_token]
                        if len(stats["examples_normalized"]) < 10:
                            stats["examples_normalized"].append(normalized)

        except (json.JSONDecodeError, KeyError) as e:
            print(f"Warning: Error processing {json_file}: {e}")
            continue

    return {
        "total_entries": total_entries,
        "months_processed": len(months_processed),
        "final_word_stats": dict(final_word_stats),
    }


def print_results(results: Dict, limit_examples: int = 5):
    """Print formatted analysis results to console."""
    print("=" * 80)
    print("SOAP FORMAT INDICATOR ANALYSIS")
    print("=" * 80)
    print()
    print(
        f"Analyzed {results['total_entries']:,} soap entries from {results['months_processed']} months"
    )
    print()

    format_stats = results["format_stats"]
    if not format_stats:
        print("No format indicators found.")
        return

    # Sort formats by total frequency (with_dash + without_dash)
    sorted_formats = sorted(
        format_stats.items(),
        key=lambda x: (
            x[1]["with_dash"]["count"] + x[1]["without_dash"]["count"],
            x[1]["with_dash"]["count"],
        ),
        reverse=True,
    )

    print("FORMAT INDICATORS SUMMARY")
    print("-" * 80)
    with_dash_label = 'With " - "'
    without_dash_label = 'Without " - "'
    print(f"{'Format':<20} {with_dash_label:<15} {without_dash_label:<15} {'Total':<10}")
    print("-" * 80)

    for format_name, stats in sorted_formats:
        with_dash_count = stats["with_dash"]["count"]
        without_dash_count = stats["without_dash"]["count"]
        total = with_dash_count + without_dash_count
        print(f"{format_name:<20} {with_dash_count:<15,} {without_dash_count:<15,} {total:<10,}")

    print()
    print("=" * 80)
    print("DETAILED EXAMPLES")
    print("=" * 80)
    print()

    for format_name, stats in sorted_formats:
        with_dash_count = stats["with_dash"]["count"]
        without_dash_count = stats["without_dash"]["count"]

        if with_dash_count == 0 and without_dash_count == 0:
            continue

        print(f"Format: {format_name.upper()}")
        print("-" * 80)

        if with_dash_count > 0:
            print(f'  With " - " prefix: {with_dash_count:,} occurrences')
            examples = stats["with_dash"]["examples_original"][:limit_examples]
            for example in examples:
                print(f"    - {example}")

        if without_dash_count > 0:
            print(f'  Without " - " prefix: {without_dash_count:,} occurrences')
            examples = stats["without_dash"]["examples_original"][:limit_examples]
            for example in examples:
                print(f"    - {example}")

        print()


def print_final_words_results(results: Dict, limit_examples: int = 5):
    """Print formatted final word analysis results to console."""
    print("=" * 80)
    print("SOAP FINAL WORD ANALYSIS")
    print("=" * 80)
    print()
    print(
        f"Analyzed {results['total_entries']:,} soap entries from {results['months_processed']} months"
    )
    print()

    final_word_stats = results["final_word_stats"]
    if not final_word_stats:
        print("No final words found.")
        return

    # Sort final words by frequency (descending)
    sorted_words = sorted(
        final_word_stats.items(),
        key=lambda x: x[1]["count"],
        reverse=True,
    )

    print("FINAL WORD TOKENS SUMMARY")
    print("-" * 80)
    print(f"{'Final Word/Token':<30} {'Count':<15}")
    print("-" * 80)

    for word_token, stats in sorted_words:
        count = stats["count"]
        print(f"{word_token:<30} {count:<15,}")

    print()
    print("=" * 80)
    print("DETAILED EXAMPLES")
    print("=" * 80)
    print()

    for word_token, stats in sorted_words:
        count = stats["count"]
        if count == 0:
            continue

        print(f"Final Word/Token: {word_token.upper()}")
        print("-" * 80)
        print(f"  Count: {count:,} occurrences")
        examples = stats["examples_original"][:limit_examples]
        if examples:
            print("  Examples:")
            for example in examples:
                print(f"    - {example}")
        print()


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Analyze extracted soap data for format indicators"
    )
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=Path("data/extracted"),
        help="Directory containing extracted JSON files (default: data/extracted)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Optional JSON file to save detailed results",
    )
    parser.add_argument(
        "--limit-examples",
        type=int,
        default=5,
        help="Maximum number of examples to show per format (default: 5)",
    )
    parser.add_argument(
        "--final-words",
        action="store_true",
        help="Analyze final words instead of format indicators",
    )

    args = parser.parse_args()

    if not args.data_dir.exists():
        print(f"Error: Data directory does not exist: {args.data_dir}")
        return 1

    if args.final_words:
        print("Analyzing final words in extracted soap data...")
        results = analyze_final_words(args.data_dir)
        print_final_words_results(results, limit_examples=args.limit_examples)

        if args.output:
            # Save detailed results to JSON
            output_data = {
                "summary": {
                    "total_entries": results["total_entries"],
                    "months_processed": results["months_processed"],
                    "unique_final_words": len(results["final_word_stats"]),
                },
                "final_word_stats": results["final_word_stats"],
            }
            with open(args.output, "w", encoding="utf-8") as f:
                json.dump(output_data, f, indent=2)
            print(f"\nDetailed results saved to: {args.output}")
    else:
        print("Analyzing extracted soap data...")
        results = analyze_extracted_data(args.data_dir)
        print_results(results, limit_examples=args.limit_examples)

        if args.output:
            # Save detailed results to JSON
            output_data = {
                "summary": {
                    "total_entries": results["total_entries"],
                    "months_processed": results["months_processed"],
                    "unique_formats": len(results["format_stats"]),
                },
                "format_stats": results["format_stats"],
            }
            with open(args.output, "w", encoding="utf-8") as f:
                json.dump(output_data, f, indent=2)
            print(f"\nDetailed results saved to: {args.output}")

    return 0


if __name__ == "__main__":
    exit(main())
