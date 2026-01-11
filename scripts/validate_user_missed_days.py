#!/usr/bin/env python3
"""Validate user missed days by checking actual match files."""

import json
import sys
from calendar import monthrange
from datetime import date
from pathlib import Path


def get_all_dates_in_year(year: int) -> set[date]:
    """Get all dates in a year."""
    all_dates = set()
    for month in range(1, 13):
        days_in_month = monthrange(year, month)[1]
        for day in range(1, days_in_month + 1):
            all_dates.add(date(year, month, day))
    return all_dates


def extract_date_from_thread_title(thread_title: str) -> date:
    """Extract date from thread title using the same logic as the pipeline."""
    import re
    from datetime import datetime

    # Month name lookup (full and abbreviated)
    month_names = {
        "january": 1,
        "february": 2,
        "march": 3,
        "april": 4,
        "may": 5,
        "june": 6,
        "july": 7,
        "august": 8,
        "september": 9,
        "october": 10,
        "november": 11,
        "december": 12,
        "jan": 1,
        "feb": 2,
        "mar": 3,
        "apr": 4,
        "may": 5,
        "jun": 6,
        "jul": 7,
        "aug": 8,
        "sep": 9,
        "oct": 10,
        "nov": 11,
        "dec": 12,
    }

    title_l = thread_title.lower()

    # Pattern 1: "Jun 01, 2025" or "June 1, 2025" (standard format)
    pattern1 = r"(\w+)\s+(\d{1,2}),\s+(\d{4})"
    match = re.search(pattern1, title_l)
    if match:
        try:
            month_str = match.group(1).lower()
            day = int(match.group(2))
            year = int(match.group(3))
            month_num = month_names.get(month_str)
            if month_num and 1 <= day <= 31:
                return date(year, month_num, day)
        except (ValueError, KeyError):
            pass

    # Pattern 2: "25. June" or "25. June 2025" (European format with period)
    pattern2 = r"(\d{1,2})\.\s+(\w+)(?:\s+(\d{4}))?"
    match = re.search(pattern2, title_l)
    if match:
        try:
            day = int(match.group(1))
            month_str = match.group(2).lower().rstrip(".")
            year = int(match.group(3)) if match.group(3) else 2025  # Default to 2025 for our data
            month_num = month_names.get(month_str)
            if month_num and 1 <= day <= 31:
                return date(year, month_num, day)
        except (ValueError, KeyError):
            pass

    # Pattern 3: "25 June" or "25 June 2025" (European format without period)
    pattern3 = r"(\d{1,2})\s+(\w+)(?:\s+(\d{4}))?"
    match = re.search(pattern3, title_l)
    if match:
        try:
            day = int(match.group(1))
            month_str = match.group(2).lower().rstrip(".")
            year = int(match.group(3)) if match.group(3) else 2025
            month_num = month_names.get(month_str)
            if month_num and 1 <= day <= 31:
                return date(year, month_num, day)
        except (ValueError, KeyError):
            pass

    raise ValueError(f"Cannot parse date from thread title: {thread_title}")


def validate_user_missed_days(users: list[str], year: int, data_dir: Path) -> dict[str, dict]:
    """Validate missed days for specific users by checking match files."""
    all_dates_in_year = get_all_dates_in_year(year)
    results = {}

    # Initialize results for each user
    for user in users:
        results[user] = {
            "posted_dates": set(),
            "total_posts": 0,
            "unique_days_posted": 0,
            "missed_days": 0,
            "missed_dates": [],
            "monthly_breakdown": {},
        }

    # Process each month
    for month in range(1, 13):
        month_str = f"{year}-{month:02d}"
        match_file = data_dir / "matched" / f"{month_str}.json"

        if not match_file.exists():
            print(f"Warning: {match_file} not found, skipping", file=sys.stderr)
            continue

        print(f"Processing {month_str}...", file=sys.stderr)

        with open(match_file) as f:
            match_data = json.load(f)

        records = match_data.get("data", [])

        # Track posts per user for this month
        month_dates = set()
        days_in_month = monthrange(year, month)[1]

        for record in records:
            author = record.get("author", "").strip()
            thread_title = record.get("thread_title", "")

            if not author or not thread_title:
                continue

            if author not in users:
                continue

            try:
                posted_date = extract_date_from_thread_title(thread_title)
                results[author]["posted_dates"].add(posted_date)
                results[author]["total_posts"] += 1
                month_dates.add(posted_date)
            except (ValueError, KeyError):
                continue

        # Calculate monthly stats for each user
        all_dates_in_month = {date(year, month, day) for day in range(1, days_in_month + 1)}

        for user in users:
            user_month_dates = {d for d in results[user]["posted_dates"] if d.month == month}
            user_month_missed = all_dates_in_month - user_month_dates
            results[user]["monthly_breakdown"][month_str] = {
                "posts": len([d for d in results[user]["posted_dates"] if d.month == month]),
                "unique_days": len(user_month_dates),
                "missed_days": len(user_month_missed),
                "days_in_month": days_in_month,
            }

    # Calculate final stats for each user
    for user in users:
        user_posted_dates = results[user]["posted_dates"]
        user_missed_dates = all_dates_in_year - user_posted_dates

        results[user]["unique_days_posted"] = len(user_posted_dates)
        results[user]["missed_days"] = len(user_missed_dates)
        results[user]["missed_dates"] = sorted([d.strftime("%Y-%m-%d") for d in user_missed_dates])

    return results


def compare_with_aggregated_data(results: dict[str, dict], year: int, data_dir: Path) -> None:
    """Compare validation results with aggregated data."""
    aggregated_file = data_dir / "aggregated" / "annual" / f"{year}.json"

    if not aggregated_file.exists():
        print(f"Warning: {aggregated_file} not found, cannot compare", file=sys.stderr)
        return

    with open(aggregated_file) as f:
        aggregated_data = json.load(f)

    users_data = aggregated_data.get("users", [])
    aggregated_by_user = {u["user"]: u for u in users_data}

    print("\n" + "=" * 80)
    print("VALIDATION RESULTS")
    print("=" * 80)

    for user, validation in results.items():
        aggregated = aggregated_by_user.get(user, {})
        agg_shaves = aggregated.get("shaves", 0)
        agg_missed = aggregated.get("missed_days", 0)

        val_posts = validation["total_posts"]
        val_unique_days = validation["unique_days_posted"]
        val_missed = validation["missed_days"]

        print(f"\n{user}:")
        print(f"  Validation (from match files):")
        print(f"    Total posts: {val_posts}")
        print(f"    Unique days posted: {val_unique_days}")
        print(f"    Missed days: {val_missed}")
        if val_missed > 0:
            print(f"    Missed dates: {', '.join(validation['missed_dates'][:10])}")
            if len(validation["missed_dates"]) > 10:
                print(f"    ... and {len(validation['missed_dates']) - 10} more")

        print(f"  Aggregated data:")
        print(f"    Shaves: {agg_shaves}")
        print(f"    Missed days: {agg_missed}")

        # Compare
        posts_match = val_posts == agg_shaves
        missed_match = val_missed == agg_missed

        print(f"  Comparison:")
        print(f"    Posts match: {posts_match} {'✓' if posts_match else '✗'}")
        print(f"    Missed days match: {missed_match} {'✓' if missed_match else '✗'}")

        if not posts_match:
            print(f"      Difference: {abs(val_posts - agg_shaves)} posts")
        if not missed_match:
            print(f"      Difference: {abs(val_missed - agg_missed)} days")

        # Show monthly breakdown for users with discrepancies
        if not missed_match or not posts_match:
            print(f"  Monthly breakdown:")
            for month, stats in sorted(validation["monthly_breakdown"].items()):
                print(
                    f"    {month}: {stats['posts']} posts, {stats['unique_days']} unique days, "
                    f"{stats['missed_days']} missed (out of {stats['days_in_month']} days)"
                )


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage: validate_user_missed_days.py <user1> [user2] [user3] ...", file=sys.stderr)
        print(
            "Example: validate_user_missed_days.py Impressive_Donut114 brokenjaw622",
            file=sys.stderr,
        )
        sys.exit(1)

    users = sys.argv[1:]
    year = 2025
    data_dir = Path("data")

    print(f"Validating missed days for {len(users)} users in {year}...", file=sys.stderr)
    print(f"Users: {', '.join(users)}", file=sys.stderr)

    results = validate_user_missed_days(users, year, data_dir)
    compare_with_aggregated_data(results, year, data_dir)


if __name__ == "__main__":
    main()
