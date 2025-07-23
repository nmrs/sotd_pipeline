#!/usr/bin/env python3
"""
Script to analyze missing dates from data/comments/ metadata.
Extracts all missing dates from the metadata sections of comment files.
"""

import glob
import json
from collections import defaultdict
from datetime import datetime
from pathlib import Path


def analyze_missing_dates():
    """Analyze all comment files and extract missing dates."""
    comments_dir = Path("data/comments")
    missing_dates = []
    monthly_stats = defaultdict(dict)

    # Get all JSON files in the comments directory
    comment_files = glob.glob(str(comments_dir / "*.json"))
    comment_files.sort()  # Sort chronologically

    print(f"Analyzing {len(comment_files)} comment files...")

    for file_path in comment_files:
        try:
            with open(file_path, "r") as f:
                data = json.load(f)

            # Extract metadata
            meta = data.get("meta", {})
            month = meta.get("month", "unknown")
            missing_days = meta.get("missing_days", [])
            thread_count = meta.get("thread_count_with_comments", 0)
            comment_count = meta.get("comment_count", 0)

            # Store monthly statistics
            monthly_stats[month] = {
                "missing_days": missing_days,
                "thread_count": thread_count,
                "comment_count": comment_count,
                "file": Path(file_path).name,
            }

            # Add missing dates to overall list
            missing_dates.extend(missing_days)

            print(
                f"  {month}: {len(missing_days)} missing days, "
                f"{thread_count} threads, {comment_count} comments"
            )

        except Exception as e:
            print(f"Error processing {file_path}: {e}")

    # Remove duplicates and sort
    missing_dates = sorted(list(set(missing_dates)))

    # Group by year for better analysis
    yearly_missing = defaultdict(list)
    for date in missing_dates:
        year = date.split("-")[0]
        yearly_missing[year].append(date)

    # Print comprehensive results
    print("\n=== COMPREHENSIVE MISSING DATES ANALYSIS ===")
    print(f"Total unique missing dates: {len(missing_dates)}")
    print(f"Date range: {min(missing_dates)} to {max(missing_dates)}")

    print("\n=== MISSING DATES BY YEAR ===")
    for year in sorted(yearly_missing.keys()):
        dates = yearly_missing[year]
        print(f"{year}: {len(dates)} missing dates")
        for date in dates:
            print(f"  {date}")

    print("\n=== MONTHLY STATISTICS ===")
    for month in sorted(monthly_stats.keys()):
        stats = monthly_stats[month]
        print(
            f"{month}: {len(stats['missing_days'])} missing, "
            f"{stats['thread_count']} threads, {stats['comment_count']} comments"
        )

    # Save results to file
    results = {
        "total_missing_dates": len(missing_dates),
        "missing_dates": missing_dates,
        "yearly_breakdown": dict(yearly_missing),
        "monthly_statistics": dict(monthly_stats),
        "analysis_timestamp": datetime.now().isoformat(),
    }

    with open("missing_dates_analysis.json", "w") as f:
        json.dump(results, f, indent=2)

    print("\n=== RESULTS SAVED ===")
    print("Detailed analysis saved to: missing_dates_analysis.json")
    print(f"Total missing dates to investigate: {len(missing_dates)}")

    return missing_dates, monthly_stats


if __name__ == "__main__":
    missing_dates, monthly_stats = analyze_missing_dates()
