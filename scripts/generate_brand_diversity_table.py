#!/usr/bin/env python3
"""Generate markdown table showing brand diversity for Stirling, Barrister and Mann, and Catie's Bubbles by month."""

import json
from pathlib import Path

# Find project root (parent of scripts directory)
SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent

# Brands to track
BRANDS = ["Stirling Soap Co.", "Barrister and Mann", "Catie's Bubbles"]

# Months in 2025
MONTHS = [
    "2025-01",
    "2025-02",
    "2025-03",
    "2025-04",
    "2025-05",
    "2025-06",
    "2025-07",
    "2025-08",
    "2025-09",
    "2025-10",
    "2025-11",
    "2025-12",
]


def load_month_data(month: str) -> dict:
    """Load aggregated data for a given month."""
    file_path = PROJECT_ROOT / "data" / "aggregated" / f"{month}.json"
    if not file_path.exists():
        return None

    with open(file_path, "r") as f:
        return json.load(f)


def extract_brand_diversity(data: dict, brand: str) -> tuple:
    """Extract unique_soaps count and rank for a given brand.

    Returns:
        Tuple of (unique_soaps, rank) or (None, None) if not found
    """
    if not data or "data" not in data:
        return (None, None)

    brand_diversity = data["data"].get("brand_diversity", [])
    for entry in brand_diversity:
        if entry.get("brand") == brand:
            return (entry.get("unique_soaps"), entry.get("rank"))

    return (0, None)  # Brand not found in this month


def generate_table():
    """Generate markdown table with brand diversity data."""
    results = {}

    # Collect data for all months
    for month in MONTHS:
        data = load_month_data(month)
        results[month] = {}
        for brand in BRANDS:
            unique_soaps, rank = extract_brand_diversity(data, brand)
            results[month][brand] = (unique_soaps, rank)

    # Track monthly wins
    stirling_wins = 0
    bam_wins = 0
    ties = 0

    # Generate markdown table
    print("| Month | Stirling Soap Co. | Barrister and Mann | Catie's Bubbles | Winner |")
    print("|-------|-------------------|---------------------|----------------|--------|")

    for month in MONTHS:
        stirling_data = results[month].get("Stirling Soap Co.")
        bam_data = results[month].get("Barrister and Mann")
        cb_data = results[month].get("Catie's Bubbles")

        stirling_count, stirling_rank = stirling_data if stirling_data else (None, None)
        bam_count, bam_rank = bam_data if bam_data else (None, None)
        cb_count, cb_rank = cb_data if cb_data else (None, None)

        # Format output with count and rank
        if stirling_count is None:
            stirling_str = "N/A"
        elif stirling_rank is not None:
            stirling_str = f"{stirling_count} ({stirling_rank})"
        else:
            stirling_str = str(stirling_count)

        if bam_count is None:
            bam_str = "N/A"
        elif bam_rank is not None:
            bam_str = f"{bam_count} ({bam_rank})"
        else:
            bam_str = str(bam_count)

        if cb_count is None:
            cb_str = "N/A"
        elif cb_rank is not None:
            cb_str = f"{cb_count} ({cb_rank})"
        else:
            cb_str = str(cb_count)

        # Determine winner between Stirling and B&M (track wins for summary)
        if stirling_count is None or bam_count is None:
            winner = "N/A"
        elif stirling_count > bam_count:
            winner = "Stirling"
            stirling_wins += 1
        elif bam_count > stirling_count:
            winner = "B&M"
            bam_wins += 1
        else:
            winner = "Tie"
            ties += 1

        print(f"| {month} | {stirling_str} | {bam_str} | {cb_str} | {winner} |")

    # Print summary
    print()
    print("## Summary")
    print()

    # Determine overall winner based on monthly wins
    if stirling_wins > bam_wins:
        overall_winner = "Stirling Soap Co."
    elif bam_wins > stirling_wins:
        overall_winner = "Barrister and Mann"
    else:
        overall_winner = "Tie"

    print(f"**Overall Winner:** {overall_winner}")
    print()
    print(f"**Monthly Wins:**")
    print(f"- Stirling: {stirling_wins} months")
    print(f"- B&M: {bam_wins} months")
    print(f"- Ties: {ties} months")


if __name__ == "__main__":
    generate_table()
