#!/usr/bin/env python3
"""
Script to analyze cache files and search for missing threads.
Searches cache files for threads that match missing dates.
"""

import glob
import json
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path


def analyze_cache_structure():
    """Analyze the structure of cache files in both directories."""
    threads_cache_dir = Path("/Users/jmoore/Documents/Projects/sotd-report/cache/threads")
    comments_cache_dir = Path("/Users/jmoore/Documents/Projects/sotd-report/cache/comments")

    # Get all JSON files from both directories
    threads_cache_files = glob.glob(str(threads_cache_dir / "*.json"))
    comments_cache_files = glob.glob(str(comments_cache_dir / "*.json"))

    threads_cache_files.sort()
    comments_cache_files.sort()

    print(f"Found {len(threads_cache_files)} threads cache files")
    print(f"Found {len(comments_cache_files)} comments cache files")

    if threads_cache_files:
        print(
            f"Threads cache date range: {Path(threads_cache_files[0]).stem} to "
            f"{Path(threads_cache_files[-1]).stem}"
        )
    if comments_cache_files:
        print(
            f"Comments cache date range: {Path(comments_cache_files[0]).stem} to "
            f"{Path(comments_cache_files[-1]).stem}"
        )

    # Analyze file sizes and content
    file_stats = {"threads_cache": {}, "comments_cache": {}}

    # Analyze threads cache
    for file_path in threads_cache_files:
        file_size = Path(file_path).stat().st_size
        filename = Path(file_path).stem

        try:
            with open(file_path, "r") as f:
                data = json.load(f)

            thread_count = len(data) if isinstance(data, list) else 0
            file_stats["threads_cache"][filename] = {
                "size": file_size,
                "thread_count": thread_count,
                "path": file_path,
            }

        except Exception as e:
            print(f"Error reading {file_path}: {e}")

    # Analyze comments cache
    for file_path in comments_cache_files:
        file_size = Path(file_path).stat().st_size
        filename = Path(file_path).stem

        try:
            with open(file_path, "r") as f:
                data = json.load(f)

            comment_count = len(data) if isinstance(data, list) else 0
            file_stats["comments_cache"][filename] = {
                "size": file_size,
                "comment_count": comment_count,
                "path": file_path,
            }

        except Exception as e:
            print(f"Error reading {file_path}: {e}")

    return file_stats


def search_cache_for_missing_dates(missing_dates):
    """Search cache files for missing dates."""
    threads_cache_dir = Path("/Users/jmoore/Documents/Projects/sotd-report/cache/threads")
    comments_cache_dir = Path("/Users/jmoore/Documents/Projects/sotd-report/cache/comments")
    found_threads = {}
    cache_coverage = defaultdict(list)

    print(f"\nSearching cache files for {len(missing_dates)} missing dates...")

    for missing_date in missing_dates:
        year_month = missing_date[:7].replace("-", "")  # Convert 2016-05-02 to 201605
        threads_cache_file = threads_cache_dir / f"{year_month}.json"
        comments_cache_file = comments_cache_dir / f"{year_month}.json"

        matching_threads = []

        # Search threads cache
        if threads_cache_file.exists():
            try:
                with open(threads_cache_file, "r") as f:
                    threads = json.load(f)

                # Search for threads on the missing date
                for thread in threads:
                    thread_date = thread.get("created_utc", "")
                    if isinstance(thread_date, str):
                        # Extract date from created_utc (format: "2016-05-04 03:06:45")
                        thread_date_only = thread_date.split(" ")[0]

                        # Check exact date match
                        if thread_date_only == missing_date:
                            matching_threads.append(thread)

                        # Check for adjacent dates (day before/after)
                        elif thread_date_only in [
                            (
                                datetime.strptime(missing_date, "%Y-%m-%d") - timedelta(days=1)
                            ).strftime("%Y-%m-%d"),
                            (
                                datetime.strptime(missing_date, "%Y-%m-%d") + timedelta(days=1)
                            ).strftime("%Y-%m-%d"),
                        ]:
                            matching_threads.append(thread)

            except Exception as e:
                print(f"  ❌ {missing_date}: Error reading threads cache {year_month}.json - {e}")

        # Search comments cache for thread references
        if comments_cache_file.exists():
            try:
                with open(comments_cache_file, "r") as f:
                    comments = json.load(f)

                # Look for comments on the missing date that reference SOTD threads
                for comment in comments:
                    comment_date = comment.get("created_utc", "")
                    if isinstance(comment_date, str):
                        comment_date_only = comment_date.split(" ")[0]

                        if comment_date_only == missing_date:
                            # Check if comment is in an SOTD thread
                            thread_title = comment.get("thread_title", "")
                            if "SOTD" in thread_title.upper():
                                # Create thread object from comment data
                                thread_info = {
                                    "id": comment.get("thread_id", ""),
                                    "title": thread_title,
                                    "url": comment.get("url", "").split("/i")[0] + "/",
                                    "author": comment.get("author", ""),
                                    "created_utc": comment_date,
                                    "source": "comments_cache",
                                }
                                matching_threads.append(thread_info)

            except Exception as e:
                print(f"  ❌ {missing_date}: Error reading comments cache {year_month}.json - {e}")

        if matching_threads:
            found_threads[missing_date] = matching_threads
            cache_coverage[year_month].append(missing_date)
            print(f"  ✅ {missing_date}: Found {len(matching_threads)} threads")
        else:
            print(f"  ❌ {missing_date}: No threads found in cache")

    return found_threads, cache_coverage


def main():
    """Main analysis function."""
    # Load missing dates from our previous analysis
    try:
        with open("missing_dates_analysis.json", "r") as f:
            analysis = json.load(f)
        missing_dates = analysis["missing_dates"]
    except FileNotFoundError:
        print("Error: missing_dates_analysis.json not found. Run analyze_missing_dates.py first.")
        return

    print("=== CACHE FILE STRUCTURE ANALYSIS ===")
    file_stats = analyze_cache_structure()

    print("\n=== SEARCHING CACHE FOR MISSING THREADS ===")
    found_threads, cache_coverage = search_cache_for_missing_dates(missing_dates)

    # Print results
    print("\n=== CACHE SEARCH RESULTS ===")
    print(f"Total missing dates: {len(missing_dates)}")
    print(f"Dates with threads found in cache: {len(found_threads)}")
    print(f"Success rate: {len(found_threads) / len(missing_dates) * 100:.1f}%")

    print("\n=== FOUND THREADS BY DATE ===")
    for date, threads in found_threads.items():
        print(f"{date}:")
        for thread in threads:
            print(f"  - {thread['title']}")
            print(f"    URL: {thread['url']}")
            print(f"    Author: {thread['author']}")
            print(f"    Created: {thread['created_utc']}")
            if "source" in thread:
                print(f"    Source: {thread['source']}")

    # Save results
    results = {
        "cache_file_stats": file_stats,
        "found_threads": found_threads,
        "cache_coverage": dict(cache_coverage),
        "search_timestamp": datetime.now().isoformat(),
    }

    with open("cache_search_results.json", "w") as f:
        json.dump(results, f, indent=2)

    print("\n=== RESULTS SAVED ===")
    print("Cache search results saved to: cache_search_results.json")


if __name__ == "__main__":
    main()
