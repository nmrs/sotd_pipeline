#!/usr/bin/env python3
"""Analyze comments cache to get accurate details about missing threads.

This script examines the comments cache to understand what actually happened
on missing dates and get more accurate thread information.
"""

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple

COMMENTS_CACHE_DIR = Path("/Users/jmoore/Documents/Projects/sotd-report/cache/comments")
THREADS_CACHE_DIR = Path("/Users/jmoore/Documents/Projects/sotd-report/cache/threads")


def load_cache_file(cache_file: Path) -> List[Dict]:
    """Load a cache file and return the data."""
    try:
        with open(cache_file, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"[WARN] Could not load {cache_file}: {e}")
        return []


def extract_date_from_filename(filename: str) -> Tuple[int, int] | None:
    """Extract year and month from cache filename."""
    # Format: YYYYMM.json
    match = re.match(r"(\d{4})(\d{2})\.json", filename)
    if match:
        return int(match.group(1)), int(match.group(2))
    return None


def find_threads_in_comments(comments_data: List[Dict], target_date: datetime) -> List[Dict]:
    """Find threads that have comments on the target date."""
    found_threads = {}

    for comment in comments_data:
        try:
            # Parse comment timestamp
            created_str = comment.get("created_utc", "")
            if created_str:
                comment_dt = datetime.fromisoformat(created_str.replace("Z", "+00:00"))

                # Check if comment is on target date
                if comment_dt.date() == target_date.date():
                    # Extract thread URL from comment URL
                    comment_url = comment.get("url", "")
                    if comment_url:
                        # Extract thread ID from comment URL
                        # Format: https://www.reddit.com/r/Wetshaving/comments/THREAD_ID/
                        # comment/COMMENT_ID/
                        match = re.search(r"/comments/([a-zA-Z0-9]+)/", comment_url)
                        if match:
                            thread_id = match.group(1)
                            if thread_id not in found_threads:
                                found_threads[thread_id] = {
                                    "thread_id": thread_id,
                                    "thread_url": (
                                        f"https://www.reddit.com/r/Wetshaving/comments/{thread_id}/"
                                    ),
                                    "comments": [],
                                    "comment_count": 0,
                                    "first_comment": comment_dt,
                                    "last_comment": comment_dt,
                                }

                            found_threads[thread_id]["comments"].append(comment)
                            found_threads[thread_id]["comment_count"] += 1
                            found_threads[thread_id]["last_comment"] = comment_dt

        except Exception:
            continue

    return list(found_threads.values())


def get_thread_details(thread_id: str, threads_cache: List[Dict]) -> Dict | None:
    """Get thread details from threads cache."""
    for thread in threads_cache:
        if thread.get("id") == thread_id.replace("t3_", ""):
            return thread
    return None


def analyze_missing_dates():
    """Analyze comments cache for missing dates."""
    # Missing dates from our analysis
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

    results = {}

    for month, dates in missing_dates.items():
        year, month_num = month.split("-")
        comments_file = COMMENTS_CACHE_DIR / f"{year}{month_num.zfill(2)}.json"
        threads_file = THREADS_CACHE_DIR / f"{year}{month_num.zfill(2)}.json"

        if not comments_file.exists():
            print(f"[INFO] No comments cache for {month}")
            continue

        print(f"\n=== Analyzing {month} ===")

        comments_data = load_cache_file(comments_file)
        threads_data = load_cache_file(threads_file)

        for date_str in dates:
            try:
                target_date = datetime.fromisoformat(date_str)
                thread_activity = find_threads_in_comments(comments_data, target_date)

                if thread_activity:
                    print(f"✅ {date_str}: Found {len(thread_activity)} active thread(s)")

                    for activity in thread_activity:
                        thread_details = get_thread_details(activity["thread_id"], threads_data)
                        if thread_details:
                            print(f"   - {thread_details.get('title', 'No title')}")
                            print(f"     URL: {thread_details.get('url', 'No URL')}")
                            print(f"     Comments: {activity['comment_count']}")
                            print(
                                f"     Thread created: {thread_details.get('created_utc', 'Unknown')}"
                            )
                            print(f"     First comment: {activity['first_comment']}")
                            print(f"     Last comment: {activity['last_comment']}")

                            # Sample some comments
                            sample_comments = activity["comments"][:3]
                            print(f"     Sample comments:")
                            for comment in sample_comments:
                                body = comment.get("body", "")[:100]
                                if body:
                                    print(f"       - {body}...")

                            results[date_str] = {
                                "thread_details": thread_details,
                                "activity": activity,
                            }
                else:
                    print(f"❌ {date_str}: No comment activity found")

            except Exception as e:
                print(f"❌ {date_str}: Error - {e}")

    return results


def generate_accurate_overrides(results: Dict) -> str:
    """Generate accurate thread overrides based on comment analysis."""
    yaml_content = []
    yaml_content.append("# Accurate thread overrides based on comment analysis")
    yaml_content.append("# These threads had actual comment activity on the missing dates")
    yaml_content.append("")

    for date_str, data in sorted(results.items()):
        thread_details = data["thread_details"]
        activity = data["activity"]

        yaml_content.append(f"{date_str}:")
        yaml_content.append(f'  - "{thread_details.get("url", "")}"')
        yaml_content.append(f"    # Comments: {activity['comment_count']}")
        yaml_content.append(f"    # Thread: {thread_details.get('title', 'No title')}")
        yaml_content.append("")

    return "\n".join(yaml_content)


def main():
    """Main function to analyze comments and generate accurate overrides."""
    print("Analyzing comments cache for missing thread activity...")

    results = analyze_missing_dates()

    print("\n" + "=" * 60)
    print("ACCURATE THREAD OVERRIDES BASED ON COMMENT ANALYSIS")
    print("=" * 60)

    yaml_content = generate_accurate_overrides(results)
    print(yaml_content)

    print(f"\nTotal dates with comment activity: {len(results)}")
    print(
        f"Total comment activity found: {sum(len(r['activity']['comments']) for r in results.values())}"
    )


if __name__ == "__main__":
    main()
