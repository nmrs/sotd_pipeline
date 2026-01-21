#!/usr/bin/env python3
"""Generate markdown table showing full ranking history for all razor manufacturers that have ever been in the top 3."""

import json
from pathlib import Path
from collections import defaultdict

# Find project root (parent of scripts directory)
SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent

# Years to include
YEARS = [2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025]

# Output file
OUTPUT_FILE = PROJECT_ROOT / "top_3_razor_manufacturers_2016_2025.md"


def load_annual_data(year: int) -> dict:
    """Load aggregated annual data for a given year."""
    file_path = PROJECT_ROOT / "data" / "aggregated" / "annual" / f"{year}.json"
    if not file_path.exists():
        return None

    with open(file_path, "r") as f:
        return json.load(f)


def generate_table():
    """Generate markdown table with top 3 razor manufacturers ranking history."""
    # First pass: find all manufacturers that have ever been in top 3
    top_3_manufacturers = set()
    for year in YEARS:
        data = load_annual_data(year)
        if not data:
            continue
        manufacturers = data.get("razor_manufacturers", [])
        for mfg in manufacturers:
            if mfg.get("rank", 999) <= 3:
                top_3_manufacturers.add(mfg["name"])

    # Second pass: get full ranking history for all manufacturers that were ever in top 3
    manufacturer_positions = defaultdict(dict)
    for year in YEARS:
        data = load_annual_data(year)
        if not data:
            continue
        manufacturers = data.get("razor_manufacturers", [])
        # Create a lookup by name
        manufacturer_lookup = {mfg["name"]: mfg["rank"] for mfg in manufacturers}
        # Store rank for all manufacturers that were ever in top 3
        for manufacturer in top_3_manufacturers:
            if manufacturer in manufacturer_lookup:
                manufacturer_positions[manufacturer][year] = manufacturer_lookup[manufacturer]

    # Get all unique manufacturers sorted alphabetically
    all_manufacturers = sorted(manufacturer_positions.keys())

    # Calculate column widths
    manufacturer_width = max(len(mfg) for mfg in all_manufacturers) if all_manufacturers else 5
    year_width = 4  # All years are 4 digits

    # Generate markdown content
    lines = []
    lines.append("# Top 3 Razor Manufacturers by Year (2016-2025)")
    lines.append("")
    lines.append("*Data sourced from `data/aggregated/annual/*.json`*")
    lines.append(
        "*Shows full ranking history for all razor manufacturers that have ever been in the top 3*"
    )
    lines.append("")

    # Header row
    header = "| " + "Manufacturer".ljust(manufacturer_width) + " |"
    for year in YEARS:
        header += f" {year} |"
    lines.append(header)

    # Separator row
    separator = "|" + "-" * (manufacturer_width + 2) + "|"
    for year in YEARS:
        separator += ":" + "-" * (year_width + 1) + "|"
    lines.append(separator)

    # Data rows
    for manufacturer in all_manufacturers:
        row = "| " + manufacturer.ljust(manufacturer_width) + " |"
        for year in YEARS:
            rank = manufacturer_positions[manufacturer].get(year, "")
            rank_str = str(rank) if rank else ""
            row += f" {rank_str.rjust(year_width)} |"
        lines.append(row)

    # Write to file
    output_content = "\n".join(lines) + "\n"
    OUTPUT_FILE.write_text(output_content)
    print(f"Generated table: {OUTPUT_FILE}")
    print(f"Found {len(all_manufacturers)} manufacturers that have ever been in the top 3")


if __name__ == "__main__":
    generate_table()
