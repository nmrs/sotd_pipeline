#!/usr/bin/env python3
"""User posting analyzer for the SOTD pipeline."""

import json
import logging
from calendar import monthrange
from datetime import date
from pathlib import Path
from typing import Any, Dict, List, Optional

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
            # Get project root directory (4 levels up from this file)
            project_root = Path(__file__).parent.parent.parent.parent.parent
            data_path = project_root / "data" / "enriched" / f"{month}.json"

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
        # Pattern to match both "Jan 01, 2025" and "25. June" formats
        import re

        # Try standard format first: "Jan 01, 2025"
        pattern1 = r"(\w{3})\s+(\d{1,2}),\s+(\d{4})"
        match = re.search(pattern1, thread_title)

        if match:
            month_str, day_str, year_str = match.groups()
        else:
            # Try alternative format: "25. June" (day. month)
            pattern2 = r"(\d{1,2})\.\s+(\w+)"
            match = re.search(pattern2, thread_title)

            if not match:
                raise ValueError(f"Could not extract date from thread title: {thread_title}")

            day_str, month_str = match.groups()
            # For alternative format, assume current year since it's not specified
            year_str = "2025"  # This should be extracted from the month parameter

        # Convert month abbreviation or full name to number
        month_map = {
            # Abbreviations
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
        self,
        username: str,
        enriched_data: List[Dict[str, Any]],
        requested_month: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Analyze posting patterns for a specific user.

        Args:
            username: Username to analyze
            enriched_data: List of enriched comment records
            requested_month: Month to analyze in YYYY-MM format (optional)

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
                "comments_by_date": {},
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
                "comments_by_date": {},
            }

        # Extract posted dates and comment IDs, grouped by date
        posted_dates = set()
        comment_ids = []
        comments_by_date = {}

        for record in user_data:
            try:
                posted_date = self._extract_date_from_thread_title(record["thread_title"])
                posted_dates.add(posted_date)
                comment_ids.append(record["id"])

                # Group comment IDs by date
                date_str = posted_date.isoformat()
                if date_str not in comments_by_date:
                    comments_by_date[date_str] = []
                comments_by_date[date_str].append(record["id"])
            except ValueError as e:
                logger.warning(
                    f"Could not extract date from thread title: {record['thread_title']} - {e}"
                )
                continue

        # Determine month to analyze
        if requested_month:
            # Use the requested month from the API call
            year, month = map(int, requested_month.split("-"))
        elif posted_dates:
            # Fallback to first posted date if no month specified
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
            "comments_by_date": comments_by_date,
        }
