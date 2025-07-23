#!/usr/bin/env python3
"""Fuzzy search for missing SOTD threads in cache files.

This script searches for any threads that might be SOTD-related on missing dates,
accounting for non-standard titles and posting date variations.
"""

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple

CACHE_DIR = Path("/Users/jmoore/Documents/Projects/sotd-report/cache/threads")


def load_cache_file(cache_file: Path) -> List[Dict]:
    """Load a cache file and return the threads."""
    try:
        with open(cache_file, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"[WARN] Could not load {cache_file}: {e}")
        return []


def parse_date_from_title(title: str) -> Tuple[int, int, int] | None:
    """Extract date from thread title using fuzzy matching."""
    # Try various date patterns
    patterns = [
        r"(\w{3})\s+(\d{1,2}),?\s+(\d{4})",  # "May 01, 2022" or "May 01 2022"
        r"(\d{1,2})/(\d{1,2})/(\d{4})",  # "05/01/2022"
        r"(\d{4})-(\d{1,2})-(\d{1,2})",  # "2022-05-01"
    ]

    title_lower = title.lower()
    month_names = {
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

    for pattern in patterns:
        match = re.search(pattern, title_lower)
        if match:
            if pattern == patterns[0]:  # Month name format
                month_str, day_str, year_str = match.groups()
                month = month_names.get(month_str[:3])
                if month:
                    return int(year_str), month, int(day_str)
            else:  # Numeric format
                if pattern == patterns[1]:  # MM/DD/YYYY
                    month, day, year = match.groups()
                else:  # YYYY-MM-DD
                    year, month, day = match.groups()
                return int(year), int(month), int(day)

    return None


def is_sotd_related(title: str, body: str = "") -> bool:
    """Check if a thread is SOTD-related using fuzzy matching."""
    text = (title + " " + body).lower()

    # SOTD-related keywords
    sotd_keywords = [
        "sotd",
        "shave of the day",
        "shave of the day thread",
        "daily shave",
        "shave thread",
        "shaving thread",
        "share your shave",
        "what did you shave with",
    ]

    # Check for SOTD keywords
    for keyword in sotd_keywords:
        if keyword in text:
            return True

    # Check for day-of-week + SOTD pattern
    days = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
    for day in days:
        if day in text and ("sotd" in text or "shave" in text):
            return True

    return False


def find_threads_for_date(cache_file: Path, target_date: datetime) -> List[Dict]:
    """Find threads for a specific date with fuzzy matching."""
    threads = load_cache_file(cache_file)
    found_threads = []

    # Check threads within ±1 day of target date
    for thread in threads:
        try:
            # Parse created_utc
            created_str = thread.get("created_utc", "")
            if created_str:
                created_dt = datetime.fromisoformat(created_str.replace("Z", "+00:00"))

                # Check if thread is within ±1 day of target
                date_diff = abs((created_dt.date() - target_date.date()).days)
                if date_diff <= 1:
                    # Check if it's SOTD-related
                    if is_sotd_related(thread.get("title", ""), thread.get("body", "")):
                        found_threads.append(thread)

        except Exception:
            continue

    return found_threads


def main():
    """Main function to find missing threads."""
    # Get missing dates from our original analysis
    missing_dates = {
        "2016-05": ["2016-05-01", "2016-05-02", "2016-05-03"],
        "2016-08": ["2016-08-01"],
        "2018-02": ["2018-02-15"],
        "2018-07": ["2018-07-11"],
        "2018-11": ["2018-11-01"],
        "2018-12": ["2018-12-06", "2018-12-13", "2018-12-20", "2018-12-27"],
        "2019-07": ["2019-07-29"],
        "2019-09": ["2019-09-02"],
        "2019-11": ["2019-11-04"],
        "2020-02": ["2020-02-24"],
        "2020-03": ["2020-03-02", "2020-03-04"],
        "2020-04": ["2020-04-04"],
        "2021-01": ["2021-01-22", "2021-01-23", "2021-01-24"],
        "2021-09": ["2021-09-01"],
        "2022-04": ["2022-04-09"],
        "2022-05": [
            "2022-05-01",
            "2022-05-02",
            "2022-05-03",
            "2022-05-04",
            "2022-05-05",
            "2022-05-06",
            "2022-05-07",
            "2022-05-08",
            "2022-05-09",
            "2022-05-10",
            "2022-05-11",
            "2022-05-12",
            "2022-05-13",
            "2022-05-14",
            "2022-05-15",
        ],
    }

    found_threads = {}

    for month, dates in missing_dates.items():
        year, month_num = month.split("-")
        cache_file = CACHE_DIR / f"{year}{month_num.zfill(2)}.json"

        if not cache_file.exists():
            print(f"[INFO] No cache file for {month}")
            continue

        print(f"\n=== Checking {month} ===")

        for date_str in dates:
            try:
                target_date = datetime.fromisoformat(date_str)
                threads = find_threads_for_date(cache_file, target_date)

                if threads:
                    print(f"✅ {date_str}: Found {len(threads)} thread(s)")
                    for thread in threads:
                        print(f"   - {thread.get('title', 'No title')}")
                        print(f"     URL: {thread.get('url', 'No URL')}")
                        print(f"     Created: {thread.get('created_utc', 'Unknown')}")

                    found_threads[date_str] = threads
                else:
                    print(f"❌ {date_str}: No threads found")

            except Exception as e:
                print(f"❌ {date_str}: Error - {e}")

    # Generate thread_overrides.yaml content
    print("\n" + "=" * 50)
    print("THREAD OVERRIDES YAML CONTENT:")
    print("=" * 50)

    for date_str, threads in found_threads.items():
        if threads:
            print(f"\n{date_str}:")
            for thread in threads:
                print(f'  - "{thread.get("url", "")}"')

    print(f"\nTotal missing dates checked: {sum(len(dates) for dates in missing_dates.values())}")
    print(f"Total threads found: {len(found_threads)}")


if __name__ == "__main__":
    main()
