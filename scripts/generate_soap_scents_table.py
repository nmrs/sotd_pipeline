#!/usr/bin/env python3
"""Generate markdown table showing ranking history for soap scents from 2016-2025."""

import json
from pathlib import Path
from collections import defaultdict

# Find project root (parent of scripts directory)
SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent

# Years to include
YEARS = [2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025]

# Output file
OUTPUT_FILE = PROJECT_ROOT / "soap_scents_2016_2025.md"

# Top N scents to include (only scents that have ever been in top 3)
TOP_N = 3


def load_annual_data(year: int) -> dict:
    """Load aggregated annual data for a given year."""
    file_path = PROJECT_ROOT / "data" / "aggregated" / "annual" / f"{year}.json"
    if not file_path.exists():
        return None

    with open(file_path, "r") as f:
        return json.load(f)


def generate_table():
    """Generate markdown table with soap scent ranking history."""
    # First pass: find all scents that have ever been in top N
    top_scents = set()
    for year in YEARS:
        data = load_annual_data(year)
        if not data:
            continue
        soaps = data.get("soaps", [])
        for soap in soaps:
            if soap.get("rank", 999) <= TOP_N:
                top_scents.add(soap["name"])

    # Second pass: get full ranking history for all scents that were ever in top N
    scent_positions = defaultdict(dict)
    for year in YEARS:
        data = load_annual_data(year)
        if not data:
            continue
        soaps = data.get("soaps", [])
        # Create a lookup by name
        soap_lookup = {s["name"]: s["rank"] for s in soaps}
        # Store rank for all scents that were ever in top N
        for scent in top_scents:
            if scent in soap_lookup:
                scent_positions[scent][year] = soap_lookup[scent]

    # Get all unique scents sorted alphabetically
    all_scents = sorted(scent_positions.keys())

    # Calculate column widths
    scent_width = max(len(s) for s in all_scents) if all_scents else 5
    year_width = 4  # All years are 4 digits

    # Generate markdown content
    lines = []
    lines.append("# Soap Scents Ranking History (2016-2025)")
    lines.append("")
    lines.append("*Data sourced from `data/aggregated/annual/*.json`*")
    lines.append("*Shows ranking history for all scents that have ever been in the top 3*")
    lines.append("")

    # Header row
    header = "| " + "Soap".ljust(scent_width) + " |"
    for year in YEARS:
        header += f" {year} |"
    lines.append(header)

    # Separator row
    separator = "|" + "-" * (scent_width + 2) + "|"
    for year in YEARS:
        separator += ":" + "-" * (year_width + 1) + "|"
    lines.append(separator)

    # Data rows
    for scent in all_scents:
        row = "| " + scent.ljust(scent_width) + " |"
        for year in YEARS:
            rank = scent_positions[scent].get(year, "")
            rank_str = str(rank) if rank else ""
            row += f" {rank_str.rjust(year_width)} |"
        lines.append(row)

    # Write to file
    output_content = "\n".join(lines) + "\n"
    OUTPUT_FILE.write_text(output_content)
    print(f"Generated table: {OUTPUT_FILE}")
    print(f"Found {len(all_scents)} scents that have ever been in the top {TOP_N}")


if __name__ == "__main__":
    generate_table()
