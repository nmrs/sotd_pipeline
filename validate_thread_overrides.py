#!/usr/bin/env python3
"""Validate threads in thread_overrides.yaml by checking their content.

This script validates that all threads in thread_overrides.yaml are actual SOTD threads
and have relevant content by analyzing their titles and checking for SOTD-related content.
"""

import json
import re
import yaml
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

THREADS_CACHE_DIR = Path("/Users/jmoore/Documents/Projects/sotd-report/cache/threads")
COMMENTS_CACHE_DIR = Path("/Users/jmoore/Documents/Projects/sotd-report/cache/comments")


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


def extract_thread_id_from_url(url: str) -> Optional[str]:
    """Extract thread ID from Reddit URL."""
    # Format: https://www.reddit.com/r/Wetshaving/comments/THREAD_ID/...
    match = re.search(r"/comments/([a-zA-Z0-9]+)/", url)
    return match.group(1) if match else None


def is_sotd_thread(title: str, body: str = "") -> bool:
    """Check if a thread is SOTD-related."""
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


def find_thread_in_cache(thread_id: str, threads_cache: List[Dict]) -> Optional[Dict]:
    """Find thread details in cache by ID."""
    for thread in threads_cache:
        if thread.get("id") == thread_id:
            return thread
    return None


def find_comments_for_thread(thread_id: str, comments_cache: List[Dict]) -> List[Dict]:
    """Find comments for a specific thread."""
    thread_comments = []
    for comment in comments_cache:
        comment_url = comment.get("url", "")
        if comment_url and thread_id in comment_url:
            thread_comments.append(comment)
    return thread_comments


def validate_thread(
    thread_url: str, target_date: str, threads_cache: List[Dict], comments_cache: List[Dict]
) -> Dict:
    """Validate a single thread."""
    thread_id = extract_thread_id_from_url(thread_url)
    if not thread_id:
        return {
            "valid": False,
            "error": "Could not extract thread ID from URL",
            "url": thread_url,
            "date": target_date,
        }

    # Find thread in cache
    thread_data = find_thread_in_cache(thread_id, threads_cache)
    if not thread_data:
        return {
            "valid": False,
            "error": "Thread not found in cache",
            "url": thread_url,
            "date": target_date,
            "thread_id": thread_id,
        }

    # Check if it's an SOTD thread
    title = thread_data.get("title", "")
    body = thread_data.get("body", "")
    is_sotd = is_sotd_thread(title, body)

    # Find comments for this thread
    comments = find_comments_for_thread(thread_id, comments_cache)

    # Check if thread was created around the target date
    created_utc = thread_data.get("created_utc", "")
    date_match = False
    if created_utc:
        try:
            thread_date = datetime.fromisoformat(created_utc.replace("Z", "+00:00"))
            target_dt = datetime.fromisoformat(target_date)
            date_diff = abs((thread_date.date() - target_dt.date()).days)
            date_match = date_diff <= 1  # Allow ±1 day
        except Exception:
            date_match = False

    return {
        "valid": is_sotd and date_match,
        "url": thread_url,
        "date": target_date,
        "thread_id": thread_id,
        "title": title,
        "is_sotd": is_sotd,
        "date_match": date_match,
        "created_utc": created_utc,
        "comment_count": len(comments),
        "error": None if (is_sotd and date_match) else f"SOTD: {is_sotd}, Date match: {date_match}",
    }


def main():
    """Main validation function."""
    print("Validating threads in thread_overrides.yaml...")

    # Load thread overrides
    overrides_file = Path("data/thread_overrides.yaml")
    overrides = load_yaml_file(overrides_file)

    if not overrides:
        print("[ERROR] Could not load thread_overrides.yaml")
        return

    results = []
    total_threads = 0
    valid_threads = 0

    # Process each date
    for date_obj, urls in overrides.items():
        if not isinstance(urls, list):
            continue

        date_str = convert_date_to_string(date_obj)
        print(f"\n=== Validating {date_str} ===")

        # Load cache files for this date
        year, month = date_str.split("-")[:2]
        threads_file = THREADS_CACHE_DIR / f"{year}{month.zfill(2)}.json"
        comments_file = COMMENTS_CACHE_DIR / f"{year}{month.zfill(2)}.json"

        threads_cache = []
        comments_cache = []

        if threads_file.exists():
            try:
                with open(threads_file, "r", encoding="utf-8") as f:
                    threads_cache = json.load(f)
            except Exception as e:
                print(f"[WARN] Could not load {threads_file}: {e}")

        if comments_file.exists():
            try:
                with open(comments_file, "r", encoding="utf-8") as f:
                    comments_cache = json.load(f)
            except Exception as e:
                print(f"[WARN] Could not load {comments_file}: {e}")

        # Validate each URL for this date
        for url in urls:
            total_threads += 1
            result = validate_thread(url, date_str, threads_cache, comments_cache)
            results.append(result)

            if result["valid"]:
                valid_threads += 1
                print(f"✅ {url}")
                print(f"   Title: {result['title']}")
                print(f"   Comments: {result['comment_count']}")
            else:
                print(f"❌ {url}")
                print(f"   Error: {result['error']}")
                if result.get("title"):
                    print(f"   Title: {result['title']}")

    # Summary
    print("\n" + "=" * 60)
    print("VALIDATION SUMMARY")
    print("=" * 60)
    print(f"Total threads: {total_threads}")
    print(f"Valid threads: {valid_threads}")
    print(f"Invalid threads: {total_threads - valid_threads}")
    print(
        f"Success rate: {(valid_threads / total_threads) * 100:.1f}%"
        if total_threads > 0
        else "N/A"
    )

    # Show invalid threads
    invalid_threads = [r for r in results if not r["valid"]]
    if invalid_threads:
        print(f"\n❌ INVALID THREADS ({len(invalid_threads)}):")
        for result in invalid_threads:
            print(f"  {result['date']}: {result['url']}")
            print(f"    Error: {result['error']}")

    # Show valid threads summary
    valid_results = [r for r in results if r["valid"]]
    if valid_results:
        print(f"\n✅ VALID THREADS ({len(valid_results)}):")
        for result in valid_results:
            print(f"  {result['date']}: {result['title']} ({result['comment_count']} comments)")


if __name__ == "__main__":
    main()
