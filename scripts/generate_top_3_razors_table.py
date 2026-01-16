#!/usr/bin/env python3
"""Generate markdown table showing full ranking history for all razors that have ever been in the top 3."""

import json
from pathlib import Path
from collections import defaultdict

# Find project root (parent of scripts directory)
SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent

# Years to include
YEARS = [2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025]

# Output file
OUTPUT_FILE = PROJECT_ROOT / "top_3_razors_2016_2025.md"


def load_annual_data(year: int) -> dict:
    """Load aggregated annual data for a given year."""
    file_path = PROJECT_ROOT / "data" / "aggregated" / "annual" / f"{year}.json"
    if not file_path.exists():
        return None

    with open(file_path, "r") as f:
        return json.load(f)


def generate_table():
    """Generate markdown table with top 3 razors ranking history."""
    # First pass: find all razors that have ever been in top 3
    top_3_razors = set()
    for year in YEARS:
        data = load_annual_data(year)
        if not data:
            continue
        razors = data.get("razors", [])
        for r in razors:
            if r.get("rank", 999) <= 3:
                top_3_razors.add(r["name"])

    # Second pass: get full ranking history for all razors that were ever in top 3
    razor_positions = defaultdict(dict)
    for year in YEARS:
        data = load_annual_data(year)
        if not data:
            continue
        razors = data.get("razors", [])
        # Create a lookup by name
        razor_lookup = {r["name"]: r["rank"] for r in razors}
        # Store rank for all razors that were ever in top 3
        for razor in top_3_razors:
            if razor in razor_lookup:
                razor_positions[razor][year] = razor_lookup[razor]

    # Get all unique razors sorted alphabetically
    all_razors = sorted(razor_positions.keys())

    # Calculate column widths
    razor_width = max(len(r) for r in all_razors) if all_razors else 5
    year_width = 4  # All years are 4 digits

    # Generate markdown content
    lines = []
    lines.append("# Top 3 Razors by Year (2016-2025)")
    lines.append("")
    lines.append("*Data sourced from `data/aggregated/annual/*.json`*")
    lines.append("*Shows full ranking history for all razors that have ever been in the top 3*")
    lines.append("")

    # Header row
    header = "| " + "Razor".ljust(razor_width) + " |"
    for year in YEARS:
        header += f" {year} |"
    lines.append(header)

    # Separator row
    separator = "|" + "-" * (razor_width + 2) + "|"
    for year in YEARS:
        separator += ":" + "-" * (year_width + 1) + "|"
    lines.append(separator)

    # Data rows
    for razor in all_razors:
        row = "| " + razor.ljust(razor_width) + " |"
        for year in YEARS:
            rank = razor_positions[razor].get(year, "")
            rank_str = str(rank) if rank else ""
            row += f" {rank_str.rjust(year_width)} |"
        lines.append(row)

    # Write to file
    output_content = "\n".join(lines) + "\n"
    OUTPUT_FILE.write_text(output_content)
    print(f"Generated table: {OUTPUT_FILE}")
    print(f"Found {len(all_razors)} razors that have ever been in the top 3")


if __name__ == "__main__":
    generate_table()
