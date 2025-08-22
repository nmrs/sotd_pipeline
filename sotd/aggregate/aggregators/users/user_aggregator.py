#!/usr/bin/env python3
"""User aggregation for the aggregate phase."""

import re
from calendar import monthrange
from datetime import date
from typing import Any, Dict, List

import pandas as pd


def _extract_date_from_thread_title(thread_title: str) -> date:
    """Extract date from thread title like 'Wednesday SOTD Thread - Jan 01, 2025'."""
    # Try standard format first: "Jan 01, 2025"
    pattern1 = r"(\w{3})\s+(\d{1,2}),\s+(\d{4})"
    match = re.search(pattern1, thread_title)

    if match:
        month_str, day_str, year_str = match.groups()

        # Convert month abbreviation to number
        month_map = {
            "Jan": 1,
            "January": 1,
            "Feb": 2,
            "February": 2,
            "Mar": 3,
            "March": 3,
            "Apr": 4,
            "April": 4,
            "May": 5,
            "May": 5,
            "Jun": 6,
            "June": 6,
            "Jul": 7,
            "July": 7,
            "Aug": 8,
            "August": 8,
            "Sep": 9,
            "September": 9,
            "Oct": 10,
            "October": 10,
            "Nov": 11,
            "November": 11,
            "Dec": 12,
            "December": 12,
        }

        month = month_map.get(month_str)
        if not month:
            raise ValueError(f"Unknown month abbreviation: {month_str}")

        return date(int(year_str), month, int(day_str))

    # Try alternative format: "25. June" (day. month)
    pattern2 = r"(\d{1,2})\.\s+(\w+)"
    match = re.search(pattern2, thread_title)

    if match:
        day_str, month_str = match.groups()

        # Convert month name to number
        month_map = {
            "Jan": 1,
            "January": 1,
            "Feb": 2,
            "February": 2,
            "Mar": 3,
            "March": 3,
            "Apr": 4,
            "April": 4,
            "May": 5,
            "May": 5,
            "Jun": 6,
            "June": 6,
            "Jul": 7,
            "July": 7,
            "Aug": 8,
            "August": 8,
            "Sep": 9,
            "September": 9,
            "Oct": 10,
            "October": 10,
            "Nov": 11,
            "November": 11,
            "Dec": 12,
            "December": 12,
        }

        month = month_map.get(month_str)
        if not month:
            raise ValueError(f"Unknown month name: {month_str}")

        # Assume current year for alternative format (thread titles don't include year)
        from datetime import datetime

        year = datetime.now().year

        return date(year, month, int(day_str))

    # If neither format matches, raise error
    raise ValueError(f"Could not extract date from thread title: {thread_title}")


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
    Each item includes rank field for delta calculations.
    Calculates missed days by comparing user's posted dates against all dates in the month.

    Args:
        records: List of enriched comment records

    Returns:
        List of user aggregations with rank, user, shaves, missed_days,
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

    # Add competition ranking based on both shaves and missed_days
    # Users with same shaves AND same missed_days get tied ranks
    # Users with different shaves or different missed_days get different ranks
    result_df = result_df.reset_index(drop=True)

    # Create a composite key for ranking that preserves the order
    # Use sequential ranks, then group by shaves+missed_days to get same rank for ties
    result_df["temp_rank"] = range(1, len(result_df) + 1)
    result_df["rank"] = result_df.groupby(["shaves", "missed_days"], sort=False)[
        "temp_rank"
    ].transform("min")
    result_df = result_df.drop("temp_rank", axis=1)

    # Sort by ranking first, then by author for consistent ordering of tied entries
    result_df = result_df.sort_values(["rank", "author"], ascending=[True, True])
    result_df = result_df.reset_index(drop=True)

    # Convert to list of dictionaries
    final_results = []
    for _, row in result_df.iterrows():
        final_results.append(
            {
                "rank": int(row["rank"]),
                "user": row["author"],
                "shaves": int(row["shaves"]),
                "missed_days": int(row["missed_days"]),
                "missed_dates": row["missed_dates"],
            }
        )

    return final_results
