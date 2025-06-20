#!/usr/bin/env python3
"""User aggregation for the aggregate phase."""

import re
from calendar import monthrange
from datetime import date
from typing import Any, Dict, List

import pandas as pd


def _extract_date_from_thread_title(thread_title: str) -> date:
    """Extract date from thread title like 'Wednesday SOTD Thread - Jan 01, 2025'."""
    # Pattern to match "Jan 01, 2025" format
    pattern = r"(\w{3})\s+(\d{1,2}),\s+(\d{4})"
    match = re.search(pattern, thread_title)

    if not match:
        raise ValueError(f"Could not extract date from thread title: {thread_title}")

    month_str, day_str, year_str = match.groups()

    # Convert month abbreviation to number
    month_map = {
        "Jan": 1,
        "Feb": 2,
        "Mar": 3,
        "Apr": 4,
        "May": 5,
        "Jun": 6,
        "Jul": 7,
        "Aug": 8,
        "Sep": 9,
        "Oct": 10,
        "Nov": 11,
        "Dec": 12,
    }

    month = month_map.get(month_str)
    if not month:
        raise ValueError(f"Unknown month abbreviation: {month_str}")

    return date(int(year_str), month, int(day_str))


def _get_all_dates_in_month(year: int, month: int) -> List[date]:
    """Get all dates in a given month."""
    # Get the number of days in the month
    _, last_day = monthrange(year, month)

    dates = []
    for day in range(1, last_day + 1):
        dates.append(date(year, month, day))

    return dates


def aggregate_users(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Aggregate user data from enriched records.

    Returns a list of user aggregations sorted by shaves desc, missed_days asc.
    Each item includes position field for delta calculations.
    Calculates missed days by comparing user's posted dates against all dates in the month.

    Args:
        records: List of enriched comment records

    Returns:
        List of user aggregations with position, user, shaves, missed_days,
        and missed_dates fields
    """
    if not records:
        return []

    # Extract user data and their posted dates
    user_data = []
    for record in records:
        author = record.get("author", "").strip()
        thread_title = record.get("thread_title", "")

        # Skip if no author or thread title
        if not author or not thread_title:
            continue

        try:
            posted_date = _extract_date_from_thread_title(thread_title)
            user_data.append({"author": author, "posted_date": posted_date})
        except (ValueError, KeyError):
            # Skip records with invalid thread titles
            continue

    if not user_data:
        return []

    # Convert to DataFrame for efficient aggregation
    df = pd.DataFrame(user_data)

    # Group by author and get unique posted dates
    user_dates = df.groupby("author")["posted_date"].apply(set).reset_index()
    user_dates.columns = ["author", "posted_dates"]

    # Calculate shaves count for each user
    user_shaves = df.groupby("author").size().reset_index()
    user_shaves.columns = ["author", "shaves"]

    # Merge the data
    user_stats = user_dates.merge(user_shaves, on="author")

    # Determine the month from the first record
    first_date = next(iter(user_stats["posted_dates"].iloc[0]))
    year, month = first_date.year, first_date.month

    # Get all dates in the month
    all_dates = set(_get_all_dates_in_month(year, month))

    # Calculate missed days for each user
    results = []
    for _, row in user_stats.iterrows():
        author = row["author"]
        posted_dates = row["posted_dates"]
        shaves = row["shaves"]

        # Calculate missed dates
        missed_dates = all_dates - posted_dates
        missed_days = len(missed_dates)

        # Convert missed dates to YYYY-MM-DD format
        missed_dates_list = sorted([d.strftime("%Y-%m-%d") for d in missed_dates])

        results.append(
            {
                "author": author,
                "shaves": shaves,
                "missed_days": missed_days,
                "missed_dates": missed_dates_list,
            }
        )

    if not results:
        return []

    # Convert to DataFrame for sorting
    result_df = pd.DataFrame(results)

    # Sort by shaves desc, missed_days asc
    result_df = result_df.sort_values(["shaves", "missed_days"], ascending=[False, True])

    # Add position field (1-based rank)
    result_df["position"] = range(1, len(result_df) + 1)

    # Convert to list of dictionaries
    final_results = []
    for _, row in result_df.iterrows():
        final_results.append(
            {
                "position": int(row["position"]),
                "user": row["author"],
                "shaves": int(row["shaves"]),
                "missed_days": int(row["missed_days"]),
                "missed_dates": row["missed_dates"],
            }
        )

    return final_results
