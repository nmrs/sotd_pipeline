#!/usr/bin/env python3
"""User posting analyzer for the SOTD pipeline."""

import json
import logging
from calendar import monthrange
from datetime import date
from pathlib import Path
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


class UserPostingAnalyzer:
    """Analyzer for user posting patterns from enriched data."""

    def __init__(self):
        """Initialize the UserPostingAnalyzer."""
        pass

    def load_enriched_data(self, month: str) -> List[Dict[str, Any]]:
        """Load enriched data for a specific month.

        Args:
            month: Month in YYYY-MM format

        Returns:
            List of enriched comment records
        """
        try:
            # Construct path to enriched data file
            data_path = Path("data/enriched") / f"{month}.json"

            if not data_path.exists():
                logger.warning(f"Enriched data file not found: {data_path}")
                return []

            with open(data_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            return data.get("data", [])

        except Exception as e:
            logger.error(f"Error loading enriched data for {month}: {e}")
            return []

    def _extract_date_from_thread_title(self, thread_title: str) -> date:
        """Extract date from thread title like 'Wednesday SOTD Thread - Jan 01, 2025'.

        Args:
            thread_title: Thread title containing date information

        Returns:
            Extracted date

        Raises:
            ValueError: If date cannot be extracted from title
        """
        # Pattern to match "Jan 01, 2025" format
        import re

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

    def _get_all_dates_in_month(self, year: int, month: int) -> List[date]:
        """Get all dates in a given month.

        Args:
            year: Year
            month: Month (1-12)

        Returns:
            List of all dates in the month
        """
        # Get the number of days in the month
        _, last_day = monthrange(year, month)

        dates = []
        for day in range(1, last_day + 1):
            dates.append(date(year, month, day))

        return dates

    def analyze_user_posting(
        self, username: str, enriched_data: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Analyze posting patterns for a specific user.

        Args:
            username: Username to analyze
            enriched_data: List of enriched comment records

        Returns:
            Dictionary with posting analysis results
        """
        if not enriched_data:
            # Return empty analysis for user with no posts
            return {
                "user": username,
                "posted_days": 0,
                "missed_days": 30,  # Default to 30 days
                "posted_dates": [],
                "comment_ids": [],
            }

        # Filter data for this user
        user_data = [record for record in enriched_data if record.get("author") == username]

        if not user_data:
            # User has no posts in this month
            return {
                "user": username,
                "posted_days": 0,
                "missed_days": 30,  # Default to 30 days
                "posted_dates": [],
                "comment_ids": [],
            }

        # Extract posted dates and comment IDs
        posted_dates = set()
        comment_ids = []

        for record in user_data:
            try:
                posted_date = self._extract_date_from_thread_title(record["thread_title"])
                posted_dates.add(posted_date)
                comment_ids.append(record["id"])
            except ValueError as e:
                logger.warning(
                    f"Could not extract date from thread title: {record['thread_title']} - {e}"
                )
                continue

        # Determine month from first posted date
        if posted_dates:
            first_date = min(posted_dates)
            year, month = first_date.year, first_date.month
        else:
            # Default to current month if no dates found
            from datetime import datetime

            now = datetime.now()
            year, month = now.year, now.month

        # Get all dates in the month
        all_dates = set(self._get_all_dates_in_month(year, month))

        # Calculate missed dates
        missed_dates = all_dates - posted_dates

        return {
            "user": username,
            "posted_days": len(posted_dates),
            "missed_days": len(missed_dates),
            "posted_dates": sorted(list(posted_dates)),
            "comment_ids": comment_ids,
        }
