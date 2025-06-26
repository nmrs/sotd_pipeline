#!/usr/bin/env python3
"""
Analyze Personna blade matches for 'accu' patterns and format mismatches.

This tool analyzes matched data to identify:
1. Percentage of Personna blade matches containing 'accu' in original strings
2. Potential mismatches where 'accu' blades are matched to DE format but used with GEM razors
3. Specific analysis of Accuforge entries and their razor compatibility
"""

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

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

# Regex to match 'accu' at the start of a word, case-insensitive
accu_regex = re.compile(r"accu.*\b", re.IGNORECASE)
# Specific regex for Accuforge
accuforge_regex = re.compile(r"accuforge.*\b", re.IGNORECASE)

matched_dir = Path("data/matched")

personna_total = 0
personna_accu = 0
accu_de_with_gem_razor = 0
accu_de_total = 0
# Store examples for detailed reporting
accu_de_gem_examples = []

# Accuforge specific tracking
accuforge_total = 0
accuforge_de_with_de_razor = 0
accuforge_de_with_gem_razor = 0
accuforge_examples = []


def is_personna_brand(brand: Any) -> bool:
    """Check if brand is Personna or starts with Personna."""
    return isinstance(brand, str) and brand.lower().startswith("personna")


def is_gem_razor(razor_matched: Any) -> bool:
    """Check if razor is matched to GEM format."""
    if not isinstance(razor_matched, dict):
        return False
    return razor_matched.get("format", "").upper() == "GEM"


def is_de_razor(razor_matched: Any) -> bool:
    """Check if razor is matched to DE format."""
    if not isinstance(razor_matched, dict):
        return False
    return razor_matched.get("format", "").upper() == "DE"


def process_file(filepath: Path) -> None:
    """Process a single matched data file."""
    global personna_total, personna_accu, accu_de_with_gem_razor, accu_de_total
    global accuforge_total, accuforge_de_with_de_razor, accuforge_de_with_gem_razor

    with filepath.open("r", encoding="utf-8") as f:
        try:
            obj = json.load(f)
            records = obj.get("data", [])
        except Exception as e:
            print(f"Error loading {filepath}: {e}")
            return

        for rec in records:
            blade = rec.get("blade")
            razor = rec.get("razor")
            if not blade:
                continue

            matched = blade.get("matched")
            if not isinstance(matched, dict):
                continue

            brand = matched.get("brand")
            if is_personna_brand(brand):
                personna_total += 1
                original = blade.get("original", "")
                blade_format = matched.get("format", "").upper()
                pattern = blade.get("pattern", "unknown")

                # Check for Accuforge specifically
                if accuforge_regex.search(original):
                    accuforge_total += 1

                    if blade_format == "DE":
                        # Check razor format
                        if razor and isinstance(razor.get("matched"), dict):
                            if is_de_razor(razor["matched"]):
                                accuforge_de_with_de_razor += 1
                                accuforge_examples.append(
                                    {
                                        "original": original,
                                        "pattern": pattern,
                                        "file": filepath.name,
                                        "razor_format": "DE",
                                        "status": "correct",
                                    }
                                )
                            elif is_gem_razor(razor["matched"]):
                                accuforge_de_with_gem_razor += 1
                                accuforge_examples.append(
                                    {
                                        "original": original,
                                        "pattern": pattern,
                                        "file": filepath.name,
                                        "razor_format": "GEM",
                                        "status": "mismatch",
                                    }
                                )

                if accu_regex.search(original):
                    personna_accu += 1

                    # Check if this is a DE blade with accu pattern
                    if blade_format == "DE":
                        accu_de_total += 1

                        # Check if used with GEM razor
                        if razor and isinstance(razor.get("matched"), dict):
                            if is_gem_razor(razor["matched"]):
                                accu_de_with_gem_razor += 1
                                # Store example for detailed reporting
                                accu_de_gem_examples.append(
                                    {
                                        "original": original,
                                        "pattern": pattern,
                                        "file": filepath.name,
                                    }
                                )


def get_files_for_months(months: list[tuple[int, int]]) -> list[Path]:
    """Get list of matched files for the specified months."""
    files = []
    for year, month in months:
        filename = f"{year:04d}-{month:02d}.json"
        filepath = matched_dir / filename
        if filepath.exists():
            files.append(filepath)
        else:
            print(f"Warning: File not found: {filepath}")
    return files


def main() -> None:
    """Main analysis function."""
    parser = argparse.ArgumentParser(
        description="Analyze Personna blade matches for 'accu' patterns and format mismatches"
    )
    parser.add_argument("--month", help="Process specific month (YYYY-MM format)")
    parser.add_argument("--year", type=int, help="Process entire year (YYYY format)")
    parser.add_argument("--start", help="Start month for range (YYYY-MM format)")
    parser.add_argument("--end", help="End month for range (YYYY-MM format)")
    parser.add_argument("--range", help="Month range (YYYY-MM:YYYY-MM format)")

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

    if personna_total == 0:
        print("No Personna blade matches found.")
        return

    percent = 100 * personna_accu / personna_total
    print("\nResults:")
    print(f"Total Personna blade matches: {personna_total}")
    print(f"Personna matches with 'accu' in original: {personna_accu}")
    print(f"Percentage: {percent:.2f}%")

    # Accuforge specific analysis
    if accuforge_total > 0:
        print("\nAccuforge specific analysis:")
        print(f"Total Accuforge blade matches: {accuforge_total}")
        print(f"Accuforge DE blades with DE razors: {accuforge_de_with_de_razor}")
        print(f"Accuforge DE blades with GEM razors: {accuforge_de_with_gem_razor}")

        if accuforge_de_with_de_razor > 0:
            de_percent = 100 * accuforge_de_with_de_razor / accuforge_total
            print(f"Percentage Accuforge with DE razors: {de_percent:.2f}%")

        if accuforge_de_with_gem_razor > 0:
            gem_percent = 100 * accuforge_de_with_gem_razor / accuforge_total
            print(f"Percentage Accuforge with GEM razors: {gem_percent:.2f}%")
            print("\n⚠️  Accuforge blades matched to DE format but used with GEM razors")

        print("\nAccuforge examples:")
        for i, example in enumerate(accuforge_examples, 1):
            status_icon = "✅" if example["status"] == "correct" else "❌"
            print(f"  {i}. {status_icon} Original: '{example['original']}'")
            print(f"     Pattern: '{example['pattern']}'")
            print(f"     Razor format: {example['razor_format']}")
            print(f"     File: {example['file']}")
            print()

    if accu_de_total > 0:
        gem_percent = 100 * accu_de_with_gem_razor / accu_de_total
        print("\nAccu DE blade analysis:")
        print(f"Total 'accu' blades matched to DE format: {accu_de_total}")
        print(f"'accu' DE blades used with GEM razors: {accu_de_with_gem_razor}")
        print(f"Percentage of 'accu' DE blades with GEM razors: {gem_percent:.2f}%")

        if accu_de_with_gem_razor > 0:
            print(
                "\n⚠️  Potential mismatch detected: DE blades with 'accu' pattern "
                "used with GEM razors"
            )
            print(
                "   This may indicate incorrect blade format matching for Accutec/Accuforge blades"
            )

            print("\nDetailed examples:")
            for i, example in enumerate(accu_de_gem_examples, 1):
                print(f"  {i}. Original: '{example['original']}'")
                print(f"     Pattern: '{example['pattern']}'")
                print(f"     File: {example['file']}")
                print()


if __name__ == "__main__":
    main()
