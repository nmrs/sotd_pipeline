#!/usr/bin/env python3
"""Analyze remaining missing threads after adding overrides.

This script compares the data/threads folder with data/comments to identify
what threads are still missing after adding the thread_overrides.yaml entries.
"""

import json
import yaml
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Set

THREADS_DIR = Path("data/threads")
COMMENTS_DIR = Path("data/comments")
OVERRIDES_FILE = Path("data/thread_overrides.yaml")


def load_yaml_file(file_path: Path) -> Dict:
    """Load YAML file and return the data."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    except Exception as e:
        print(f"[ERROR] Could not load {file_path}: {e}")
        return {}


def convert_date_to_string(date_obj) -> str:
    """Convert date object to string format."""
    if isinstance(date_obj, datetime):
        return date_obj.strftime("%Y-%m-%d")
    elif hasattr(date_obj, "strftime"):
        return date_obj.strftime("%Y-%m-%d")
    else:
        return str(date_obj)


def get_thread_dates_from_folder(folder_path: Path) -> Dict[str, Set[str]]:
    """Get all thread dates from a folder of JSON files."""
    thread_dates = {}

    for json_file in sorted(folder_path.glob("*.json")):
        try:
            with open(json_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            # Extract month from filename (YYYY-MM.json)
            month = json_file.stem

            # Get all thread dates from this month
            dates = set()
            if isinstance(data, dict) and "data" in data:
                for thread in data["data"]:
                    created_utc = thread.get("created_utc", "")
                    if created_utc:
                        try:
                            thread_dt = datetime.fromisoformat(created_utc.replace("Z", "+00:00"))
                            dates.add(thread_dt.strftime("%Y-%m-%d"))
                        except Exception:
                            continue

            if dates:
                thread_dates[month] = dates

        except Exception as e:
            print(f"[WARN] Could not process {json_file}: {e}")

    return thread_dates


def get_missing_dates_from_comments() -> Dict[str, List[str]]:
    """Get missing dates from comments metadata."""
    missing_dates = {}

    for json_file in sorted(COMMENTS_DIR.glob("*.json")):
        try:
            with open(json_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            meta = data.get("meta", {})
            month = meta.get("month")
            missing_days = meta.get("missing_days", [])

            if missing_days:
                missing_dates[month] = missing_days

        except Exception as e:
            print(f"[WARN] Could not process {json_file}: {e}")

    return missing_dates


def get_override_dates() -> Set[str]:
    """Get all dates that have overrides."""
    overrides = load_yaml_file(OVERRIDES_FILE)
    override_dates = set()

    for date_obj in overrides.keys():
        date_str = convert_date_to_string(date_obj)
        override_dates.add(date_str)

    return override_dates


def analyze_remaining_missing():
    """Analyze what threads are still missing after overrides."""
    print("Analyzing remaining missing threads...")

    # Get thread dates from data/threads
    print("\n1. Loading thread dates from data/threads...")
    thread_dates = get_thread_dates_from_folder(THREADS_DIR)
    print(f"   Found {len(thread_dates)} months with thread data")

    # Get missing dates from comments
    print("\n2. Loading missing dates from data/comments...")
    missing_dates = get_missing_dates_from_comments()
    print(f"   Found {len(missing_dates)} months with missing dates")

    # Get override dates
    print("\n3. Loading override dates...")
    override_dates = get_override_dates()
    print(f"   Found {len(override_dates)} override dates")

    # Analyze each month
    print("\n4. Analyzing remaining missing threads...")
    print("=" * 60)

    all_missing_before_overrides = set()
    all_missing_after_overrides = set()
    all_missing_after_threads = set()

    for month, missing_days in missing_dates.items():
        print(f"\n=== {month} ===")

        # Get thread dates for this month
        month_thread_dates = thread_dates.get(month, set())

        # Convert missing days to full dates
        missing_full_dates = []
        for day in missing_days:
            if "-" in day:  # Already full date
                missing_full_dates.append(day)
            else:  # Just day number, need to construct full date
                try:
                    day_num = int(day)
                    year, month_num = month.split("-")
                    full_date = f"{year}-{month_num.zfill(2)}-{day_num:02d}"
                    missing_full_dates.append(full_date)
                except Exception:
                    continue

        missing_before_overrides = set(missing_full_dates)
        all_missing_before_overrides.update(missing_before_overrides)

        # Remove dates that have overrides
        missing_after_overrides = missing_before_overrides - override_dates
        all_missing_after_overrides.update(missing_after_overrides)

        # Remove dates that are actually in threads folder
        missing_after_threads = missing_after_overrides - month_thread_dates

        print(f"   Missing before overrides: {len(missing_before_overrides)}")
        print(f"   Missing after overrides: {len(missing_after_overrides)}")
        print(f"   Missing after threads: {len(missing_after_threads)}")

        if missing_after_threads:
            print(f"   Still missing: {sorted(missing_after_threads)}")
        else:
            print("   ✅ All missing dates resolved!")

    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Total missing dates before overrides: {len(all_missing_before_overrides)}")
    print(f"Total missing dates after overrides: {len(all_missing_after_overrides)}")
    print(f"Total missing dates after threads: {len(all_missing_after_threads)}")

    if all_missing_after_threads:
        print(f"\n❌ STILL MISSING ({len(all_missing_after_threads)}):")
        for missing_date in sorted(all_missing_after_threads):
            print(f"  {missing_date}")
    else:
        print("\n✅ ALL MISSING DATES RESOLVED!")

    # Show what overrides helped with
    resolved_by_overrides = all_missing_before_overrides & override_dates
    if resolved_by_overrides:
        print(f"\n✅ RESOLVED BY OVERRIDES ({len(resolved_by_overrides)}):")
        for resolved_date in sorted(resolved_by_overrides):
            print(f"  {resolved_date}")


def main():
    """Main function."""
    analyze_remaining_missing()


if __name__ == "__main__":
    main()
