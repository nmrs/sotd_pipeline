#!/usr/bin/env python3
"""Generate markdown table showing ranking history for soap brands from 2016-2025."""

import json
from pathlib import Path
from collections import defaultdict

# Find project root (parent of scripts directory)
SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent

# Years to include
YEARS = [2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025]

# Output file
OUTPUT_FILE = PROJECT_ROOT / "soap_brands_2016_2025.md"

# Top N brands to include (only brands that have ever been in top 3)
TOP_N = 3


def load_annual_data(year: int) -> dict:
    """Load aggregated annual data for a given year."""
    file_path = PROJECT_ROOT / "data" / "aggregated" / "annual" / f"{year}.json"
    if not file_path.exists():
        return None

    with open(file_path, "r") as f:
        return json.load(f)


def generate_table():
    """Generate markdown table with soap brand ranking history."""
    # First pass: find all brands that have ever been in top N
    top_brands = set()
    for year in YEARS:
        data = load_annual_data(year)
        if not data:
            continue
        soap_makers = data.get("soap_makers", [])
        for brand in soap_makers:
            if brand.get("rank", 999) <= TOP_N:
                top_brands.add(brand["name"])

    # Second pass: get full ranking history for all brands that were ever in top N
    brand_positions = defaultdict(dict)
    for year in YEARS:
        data = load_annual_data(year)
        if not data:
            continue
        soap_makers = data.get("soap_makers", [])
        # Create a lookup by name
        brand_lookup = {b["name"]: b["rank"] for b in soap_makers}
        # Store rank for all brands that were ever in top N
        for brand in top_brands:
            if brand in brand_lookup:
                brand_positions[brand][year] = brand_lookup[brand]

    # Get all unique brands sorted alphabetically
    all_brands = sorted(brand_positions.keys())

    # Calculate column widths
    brand_width = max(len(b) for b in all_brands) if all_brands else 5
    year_width = 4  # All years are 4 digits

    # Generate markdown content
    lines = []
    lines.append("# Soap Brands Ranking History (2016-2025)")
    lines.append("")
    lines.append("*Data sourced from `data/aggregated/annual/*.json`*")
    lines.append(f"*Shows ranking history for all brands that have ever been in the top 3*")
    lines.append("")

    # Header row
    header = "| " + "Brand".ljust(brand_width) + " |"
    for year in YEARS:
        header += f" {year} |"
    lines.append(header)

    # Separator row
    separator = "|" + "-" * (brand_width + 2) + "|"
    for year in YEARS:
        separator += ":" + "-" * (year_width + 1) + "|"
    lines.append(separator)

    # Data rows
    for brand in all_brands:
        row = "| " + brand.ljust(brand_width) + " |"
        for year in YEARS:
            rank = brand_positions[brand].get(year, "")
            rank_str = str(rank) if rank else ""
            row += f" {rank_str.rjust(year_width)} |"
        lines.append(row)

    # Write to file
    output_content = "\n".join(lines) + "\n"
    OUTPUT_FILE.write_text(output_content)
    print(f"Generated table: {OUTPUT_FILE}")
    print(f"Found {len(all_brands)} brands that have ever been in the top {TOP_N}")


if __name__ == "__main__":
    generate_table()
