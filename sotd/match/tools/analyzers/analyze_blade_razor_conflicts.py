#!/usr/bin/env python3
"""
Analyze blade-razor format conflicts in matched data.

This tool analyzes matched data to identify potential format mismatches between
blades and razors, such as:
- DE blades used with cartridge/disposable razors
- AC blades used with DE razors
- GEM blades used with DE razors
- Any other format incompatibilities

The tool provides detailed analysis and examples of potential conflicts.
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple

# Add project root to Python path for direct execution
if __name__ == "__main__":
    # Find project root by looking for the directory containing 'sotd' module
    current_file = Path(__file__).resolve()
    project_root = current_file.parent.parent.parent.parent
    if not (project_root / "sotd").exists():
        # If that doesn't work, try to find it by looking for the project structure
        for parent in current_file.parents:
            if (parent / "sotd").exists() and (parent / "run.py").exists():
                project_root = parent
                break
    sys.path.insert(0, str(project_root))

from sotd.cli_utils.date_span import month_span

# Define compatible format combinations
# Key: blade format, Value: list of compatible razor formats
COMPATIBLE_FORMATS = {
    # Standard blade formats
    "DE": [
        "DE",
        "DUAL HALF DE",
        "SHAVETTE (DE)",
        "SHAVETTE (HALF DE)",
        "SHAVETTE",
        "HALF DE",
        "HALF DE (MULTI-BLADE)",
    ],
    "AC": ["AC", "SHAVETTE (AC)", "SHAVETTE"],
    "GEM": ["GEM"],
    "INJECTOR": ["INJECTOR", "SHAVETTE"],
    "CARTRIDGE": ["CARTRIDGE"],
    "DISPOSABLE": ["DISPOSABLE", "SHAVETTE (DISPOSABLE)"],
    "FHS": ["FHS"],
    "HALF DE": ["HALF DE", "HALF DE (MULTI-BLADE)", "SHAVETTE (HALF DE)", "SHAVETTE"],
    "A77": ["SHAVETTE (A77)", "SHAVETTE"],
    "ANTELOPE/A77": ["SHAVETTE (A77)", "SHAVETTE"],
    "HAIR SHAPER": ["SHAVETTE (HAIR SHAPER)", "SHAVETTE"],
    "OTHER": ["OTHER"],
    "STRAIGHT": ["STRAIGHT"],
    # Shavette formats (compatible with generic shavette)
    "SHAVETTE": [
        "SHAVETTE",
        "SHAVETTE (AC)",
        "SHAVETTE (DE)",
        "SHAVETTE (HALF DE)",
        "SHAVETTE (DISPOSABLE)",
        "SHAVETTE (HAIR SHAPER)",
        "SHAVETTE (A77)",
    ],
}

# Define acceptable format combinations (unusual but valid)
# Key: blade format, Value: list of acceptable razor formats
ACCEPTABLE_FORMATS = {
    "INJECTOR": ["AC"],  # Injector blades can be used in AC razors
    "AC": ["INJECTOR"],  # Injector blades can be used in AC razors
}

# Track statistics
stats = {
    "total_records": 0,
    "records_with_blade": 0,
    "records_with_razor": 0,
    "records_with_both": 0,
    "conflicts_found": 0,
    "acceptable_conflicts_found": 0,
    "conflicts_by_type": {},
    "acceptable_conflicts_by_type": {},
}

# Store examples for detailed reporting
conflict_examples: List[Dict[str, Any]] = []
acceptable_conflict_examples: List[Dict[str, Any]] = []


def is_incompatible_format(blade_format: str, razor_format: str) -> bool:
    """Check if blade and razor formats are incompatible."""
    blade_format_upper = blade_format.upper()
    razor_format_upper = razor_format.upper()

    # If either format is unknown, we can't determine compatibility
    if blade_format_upper in ["UNKNOWN", ""] or razor_format_upper in ["UNKNOWN", ""]:
        return False

    # Check if this combination is compatible
    compatible_razor_formats = COMPATIBLE_FORMATS.get(blade_format_upper, [])
    return razor_format_upper not in compatible_razor_formats


def is_acceptable_format(blade_format: str, razor_format: str) -> bool:
    """Check if blade and razor formats are acceptable (unusual but valid)."""
    blade_format_upper = blade_format.upper()
    razor_format_upper = razor_format.upper()

    # If either format is unknown, we can't determine compatibility
    if blade_format_upper in ["UNKNOWN", ""] or razor_format_upper in ["UNKNOWN", ""]:
        return False

    # Check if this combination is known to be acceptable
    acceptable_razor_formats = ACCEPTABLE_FORMATS.get(blade_format_upper, [])
    return razor_format_upper in acceptable_razor_formats


def get_conflict_type(blade_format: str, razor_format: str) -> str:
    """Get a human-readable description of the conflict type."""
    return f"{blade_format.upper()} blade with {razor_format.upper()} razor"


def process_file(filepath: Path) -> None:
    """Process a single matched data file."""
    global stats, conflict_examples, acceptable_conflict_examples

    with filepath.open("r", encoding="utf-8") as f:
        try:
            obj = json.load(f)
            records = obj.get("data", [])
        except Exception as e:
            print(f"Error loading {filepath}: {e}")
            return

        for rec in records:
            stats["total_records"] += 1

            blade = rec.get("blade")
            razor = rec.get("razor")

            # Track records with blade and/or razor
            if blade:
                stats["records_with_blade"] += 1
            if razor:
                stats["records_with_razor"] += 1
            if blade and razor:
                stats["records_with_both"] += 1

            # Skip if we don't have both blade and razor data
            if not blade or not razor:
                continue

            blade_matched = blade.get("matched")
            razor_matched = razor.get("matched")

            # Skip if either doesn't have matched data
            if not isinstance(blade_matched, dict) or not isinstance(razor_matched, dict):
                continue

            blade_format = blade_matched.get("format", "")
            razor_format = razor_matched.get("format", "")

            # Skip if either format is missing
            if not blade_format or not razor_format:
                continue

            # Check for acceptable format combinations first (these override compatibility)
            if is_acceptable_format(blade_format, razor_format):
                stats["acceptable_conflicts_found"] += 1

                conflict_type = get_conflict_type(blade_format, razor_format)
                if conflict_type not in stats["acceptable_conflicts_by_type"]:
                    stats["acceptable_conflicts_by_type"][conflict_type] = 0
                stats["acceptable_conflicts_by_type"][conflict_type] += 1

                # Store example for detailed reporting
                acceptable_conflict_examples.append(
                    {
                        "comment_id": rec.get("id", ""),
                        "comment_url": rec.get("url", ""),
                        "author": rec.get("author", ""),
                        "blade_original": blade.get("original", ""),
                        "blade_brand": blade_matched.get("brand", ""),
                        "blade_model": blade_matched.get("model", ""),
                        "blade_format": blade_format,
                        "blade_pattern": blade.get("pattern", ""),
                        "blade_match_type": blade.get("match_type", ""),
                        "razor_original": razor.get("original", ""),
                        "razor_brand": razor_matched.get("brand", ""),
                        "razor_model": razor_matched.get("model", ""),
                        "razor_format": razor_format,
                        "razor_pattern": razor.get("pattern", ""),
                        "razor_match_type": razor.get("match_type", ""),
                        "conflict_type": conflict_type,
                        "file": filepath.name,
                    }
                )
                continue

            # Check for incompatible format combinations
            if is_incompatible_format(blade_format, razor_format):
                stats["conflicts_found"] += 1

                conflict_type = get_conflict_type(blade_format, razor_format)
                if conflict_type not in stats["conflicts_by_type"]:
                    stats["conflicts_by_type"][conflict_type] = 0
                stats["conflicts_by_type"][conflict_type] += 1

                # Store example for detailed reporting
                conflict_examples.append(
                    {
                        "comment_id": rec.get("id", ""),
                        "comment_url": rec.get("url", ""),
                        "author": rec.get("author", ""),
                        "blade_original": blade.get("original", ""),
                        "blade_brand": blade_matched.get("brand", ""),
                        "blade_model": blade_matched.get("model", ""),
                        "blade_format": blade_format,
                        "blade_pattern": blade.get("pattern", ""),
                        "blade_match_type": blade.get("match_type", ""),
                        "razor_original": razor.get("original", ""),
                        "razor_brand": razor_matched.get("brand", ""),
                        "razor_model": razor_matched.get("model", ""),
                        "razor_format": razor_format,
                        "razor_pattern": razor.get("pattern", ""),
                        "razor_match_type": razor.get("match_type", ""),
                        "conflict_type": conflict_type,
                        "file": filepath.name,
                    }
                )


def get_files_for_months(months: List[Tuple[int, int]]) -> List[Path]:
    """Get list of matched files for the specified months."""
    matched_dir = Path("data/matched")
    files = []
    for year, month in months:
        filename = f"{year:04d}-{month:02d}.json"
        filepath = matched_dir / filename
        if filepath.exists():
            files.append(filepath)
        else:
            print(f"Warning: File not found: {filepath}")
    return files


def print_summary() -> None:
    """Print summary statistics."""
    print("\n" + "=" * 60)
    print("BLADE-RAZOR FORMAT CONFLICT ANALYSIS SUMMARY")
    print("=" * 60)

    print(f"\nTotal records processed: {stats['total_records']:,}")
    print(f"Records with blade data: {stats['records_with_blade']:,}")
    print(f"Records with razor data: {stats['records_with_razor']:,}")
    print(f"Records with both blade and razor: {stats['records_with_both']:,}")

    if stats["records_with_both"] > 0:
        conflict_percentage = 100 * stats["conflicts_found"] / stats["records_with_both"]
        acceptable_conflict_percentage = (
            100 * stats["acceptable_conflicts_found"] / stats["records_with_both"]
        )
        total_conflicts = stats["conflicts_found"] + stats["acceptable_conflicts_found"]
        total_conflict_percentage = 100 * total_conflicts / stats["records_with_both"]

        print(f"\nFormat conflicts found: {stats['conflicts_found']:,}")
        print(f"Conflict percentage: {conflict_percentage:.2f}%")

        if stats["acceptable_conflicts_found"] > 0:
            print(f"Acceptable conflicts found: {stats['acceptable_conflicts_found']:,}")
            print(f"Acceptable conflict percentage: {acceptable_conflict_percentage:.2f}%")
            print(f"Total unusual combinations: {total_conflicts:,}")
            print(f"Total unusual combination percentage: {total_conflict_percentage:.2f}%")

        if stats["conflicts_found"] > 0:
            print("\nIncompatible conflicts by type:")
            for conflict_type, count in sorted(
                stats["conflicts_by_type"].items(), key=lambda x: x[1], reverse=True
            ):
                percentage = 100 * count / stats["conflicts_found"]
                print(f"  {conflict_type}: {count:,} ({percentage:.1f}%)")

        if stats["acceptable_conflicts_found"] > 0:
            print("\nAcceptable conflicts by type:")
            for conflict_type, count in sorted(
                stats["acceptable_conflicts_by_type"].items(), key=lambda x: x[1], reverse=True
            ):
                percentage = 100 * count / stats["acceptable_conflicts_found"]
                print(f"  {conflict_type}: {count:,} ({percentage:.1f}%)")

        if stats["conflicts_found"] == 0 and stats["acceptable_conflicts_found"] == 0:
            print("\n✅ No format conflicts detected!")
        elif stats["conflicts_found"] == 0:
            print("\n✅ No incompatible format conflicts detected!")
            print("ℹ️  Only acceptable/unusual combinations found.")
    else:
        print("\n⚠️  No records with both blade and razor data found.")


def print_detailed_examples(limit: int = 20) -> None:
    """Print detailed examples of conflicts."""
    if not conflict_examples:
        return

    print("\n" + "=" * 60)
    print(f"DETAILED EXAMPLES (showing first {limit})")
    print("=" * 60)

    for i, example in enumerate(conflict_examples[:limit], 1):
        print(f"\n{i}. {example['conflict_type']}")
        print(f"   Comment ID: {example['comment_id']}")
        print(f"   Comment URL: {example['comment_url']}")
        print(f"   Author: {example['author']}")
        print(f"   File: {example['file']}")
        print()
        print("   BLADE:")
        print(f"     Original: '{example['blade_original']}'")
        print(f"     Matched: {example['blade_brand']} {example['blade_model']}")
        print(f"     Format: {example['blade_format']}")
        print(f"     Pattern: '{example['blade_pattern']}'")
        print(f"     Match Type: {example['blade_match_type']}")
        print()
        print("   RAZOR:")
        print(f"     Original: '{example['razor_original']}'")
        print(f"     Matched: {example['razor_brand']} {example['razor_model']}")
        print(f"     Format: {example['razor_format']}")
        print(f"     Pattern: '{example['razor_pattern']}'")
        print(f"     Match Type: {example['razor_match_type']}")
        print("-" * 60)

    if len(conflict_examples) > limit:
        print(f"\n... and {len(conflict_examples) - limit} more examples")


def print_acceptable_conflict_examples(limit: int = 20) -> None:
    """Print detailed examples of acceptable conflicts."""
    if not acceptable_conflict_examples:
        return

    print("\n" + "=" * 60)
    print(f"ACCEPTABLE CONFLICT EXAMPLES (showing first {limit})")
    print("=" * 60)

    for i, example in enumerate(acceptable_conflict_examples[:limit], 1):
        print(f"\n{i}. {example['conflict_type']} (ACCEPTABLE)")
        print(f"   Comment ID: {example['comment_id']}")
        print(f"   Comment URL: {example['comment_url']}")
        print(f"   Author: {example['author']}")
        print(f"   File: {example['file']}")
        print()
        print("   BLADE:")
        print(f"     Original: '{example['blade_original']}'")
        print(f"     Matched: {example['blade_brand']} {example['blade_model']}")
        print(f"     Format: {example['blade_format']}")
        print(f"     Pattern: '{example['blade_pattern']}'")
        print(f"     Match Type: {example['blade_match_type']}")
        print()
        print("   RAZOR:")
        print(f"     Original: '{example['razor_original']}'")
        print(f"     Matched: {example['razor_brand']} {example['razor_model']}")
        print(f"     Format: {example['razor_format']}")
        print(f"     Pattern: '{example['razor_pattern']}'")
        print(f"     Match Type: {example['razor_match_type']}")
        print("-" * 60)

    if len(acceptable_conflict_examples) > limit:
        print(f"\n... and {len(acceptable_conflict_examples) - limit} more examples")


def print_recommendations() -> None:
    """Print recommendations based on findings."""
    if stats["conflicts_found"] == 0 and stats["acceptable_conflicts_found"] == 0:
        return

    print("\n" + "=" * 60)
    print("RECOMMENDATIONS")
    print("=" * 60)

    print("\nBased on the analysis, consider the following:")

    # Check for common conflict patterns
    de_with_cartridge = stats["conflicts_by_type"].get("DE blade with CARTRIDGE razor", 0)
    ac_with_de = stats["conflicts_by_type"].get("AC blade with DE razor", 0)
    gem_with_de = stats["conflicts_by_type"].get("GEM blade with DE razor", 0)

    if de_with_cartridge > 0:
        print(f"\n• {de_with_cartridge:,} DE blades matched with cartridge razors")
        print("  - Review cartridge razor matching logic")
        print("  - Consider if these are actual cartridge razors or DE razors")

    if ac_with_de > 0:
        print(f"\n• {ac_with_de:,} AC blades matched with DE razors")
        print("  - AC blades are incompatible with DE razors")
        print("  - Review AC blade matching patterns")

    if gem_with_de > 0:
        print(f"\n• {gem_with_de:,} GEM blades matched with DE razors")
        print("  - GEM blades are incompatible with DE razors")
        print("  - Review GEM blade matching patterns")

    # Check for acceptable conflict patterns
    injector_with_ac = stats["acceptable_conflicts_by_type"].get("INJECTOR blade with AC razor", 0)
    gem_with_ac = stats["acceptable_conflicts_by_type"].get("GEM blade with AC razor", 0)

    if injector_with_ac > 0:
        print(f"\n• {injector_with_ac:,} Injector blades used with AC razors (ACCEPTABLE)")
        print("  - This is a common practice in the wet shaving community")
        print("  - Injector blades can be modified to fit AC razors")
        print("  - No action needed - this is expected behavior")

    if gem_with_ac > 0:
        print(f"\n• {gem_with_ac:,} GEM blades used with AC razors (ACCEPTABLE)")
        print("  - GEM blades can sometimes be used in AC razors with modification")
        print("  - This is less common but still valid")
        print("  - No action needed - this is expected behavior")

    if stats["conflicts_found"] > 0:
        print(f"\n• Total of {stats['conflicts_found']:,} incompatible format conflicts detected")
        print("  - Review blade and razor format matching logic")
        print("  - Consider adding format validation in the match phase")
        print("  - Check if these are actual user errors or matching issues")

    if stats["acceptable_conflicts_found"] > 0:
        print(
            f"\n• Total of {stats['acceptable_conflicts_found']:,} "
            "acceptable format combinations detected"
        )
        print("  - These are unusual but valid combinations")
        print("  - No action needed - these are expected in the community")
        print("  - Consider documenting these as valid combinations")


def main() -> None:
    """Main analysis function."""
    parser = argparse.ArgumentParser(
        description="Analyze blade-razor format conflicts in matched data"
    )
    parser.add_argument("--month", help="Process specific month (YYYY-MM format)")
    parser.add_argument("--year", type=int, help="Process entire year (YYYY format)")
    parser.add_argument("--start", help="Start month for range (YYYY-MM format)")
    parser.add_argument("--end", help="End month for range (YYYY-MM format)")
    parser.add_argument("--range", help="Month range (YYYY-MM:YYYY-MM format)")
    parser.add_argument(
        "--examples", type=int, default=20, help="Number of detailed examples to show (default: 20)"
    )
    parser.add_argument("--no-examples", action="store_true", help="Skip detailed examples output")

    args = parser.parse_args()

    # Use date_span to get months to process
    try:
        months = month_span(args)
    except ValueError as e:
        print(f"Error: {e}")
        return

    # Get files for the specified months
    files = get_files_for_months(months)

    if not files:
        print("No files found for the specified date range.")
        return

    print(f"Processing {len(files)} files for {len(months)} months...")

    for file in files:
        print(f"Processing {file}")
        process_file(file)

    # Print results
    print_summary()

    if not args.no_examples and conflict_examples:
        print_detailed_examples(args.examples)

    if not args.no_examples and acceptable_conflict_examples:
        print_acceptable_conflict_examples(args.examples)

    print_recommendations()


if __name__ == "__main__":
    main()
