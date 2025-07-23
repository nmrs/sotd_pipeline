#!/usr/bin/env python3
"""
Script to validate found cache threads and determine which ones are valid for missing dates.
"""

import json
from datetime import datetime


def validate_thread_for_missing_date(thread, missing_date):
    """Validate if a thread is appropriate for a missing date."""
    thread_date = thread.get("created_utc", "")
    if not isinstance(thread_date, str):
        return False, "Invalid thread date format"

    # Extract date from created_utc (format: "2016-05-04 03:06:45")
    thread_date_only = thread_date.split(" ")[0]

    # Check if thread is on the exact missing date
    if thread_date_only == missing_date:
        return True, "Exact date match"

    # Check if thread is on the same date (timezone differences)
    try:
        missing_dt = datetime.strptime(missing_date, "%Y-%m-%d")
        thread_dt = datetime.strptime(thread_date_only, "%Y-%m-%d")
        date_diff = abs((thread_dt - missing_dt).days)

        # Only accept exact matches or same-day threads (timezone differences)
        if date_diff == 0:
            return True, "Same date (timezone difference)"
        else:
            return False, f"Date mismatch ({date_diff} days difference)"
    except ValueError:
        return False, "Invalid date format"

    return False, "No date match"


def validate_thread_content(thread):
    """Validate thread content for SOTD relevance."""
    title = thread.get("title", "").upper()
    body = thread.get("body", "").upper()

    # Check for SOTD indicators in title
    sotd_indicators = ["SOTD", "SHAVE OF THE DAY", "DAILY SHAVE"]
    title_has_sotd = any(indicator in title for indicator in sotd_indicators)

    # Check for SOTD indicators in body
    body_has_sotd = any(indicator in body for indicator in sotd_indicators)

    if not title_has_sotd and not body_has_sotd:
        return False, "No SOTD indicators in title or body"

    # Check for valid day indicators in title
    day_indicators = [
        "MONDAY",
        "TUESDAY",
        "WEDNESDAY",
        "THURSDAY",
        "FRIDAY",
        "SATURDAY",
        "SUNDAY",
        "THEME THURSDAY",
    ]
    has_day_indicator = any(day in title for day in day_indicators)

    if not has_day_indicator:
        return False, "No day indicator in title"

    return True, "Valid SOTD thread"


def validate_threads_for_missing_dates():
    """Validate all found threads for missing dates."""
    # Load cache search results
    try:
        with open("cache_search_results.json", "r") as f:
            cache_results = json.load(f)
        found_threads = cache_results["found_threads"]
    except FileNotFoundError:
        print("Error: cache_search_results.json not found. Run analyze_cache_files.py first.")
        return

    validation_results = {}
    summary_stats = {
        "total_missing_dates": len(found_threads),
        "dates_with_valid_threads": 0,
        "total_threads_checked": 0,
        "valid_threads": 0,
        "rejected_threads": 0,
    }

    print("=== VALIDATING CACHE THREADS ===")

    for missing_date, threads in found_threads.items():
        print(f"\n{missing_date}:")
        validation_results[missing_date] = {
            "valid_threads": [],
            "rejected_threads": [],
            "best_match": None,
        }

        date_has_valid_thread = False

        for thread in threads:
            summary_stats["total_threads_checked"] += 1

            # Validate date relevance
            date_valid, date_reason = validate_thread_for_missing_date(thread, missing_date)

            # Validate content
            content_valid, content_reason = validate_thread_content(thread)

            thread_info = {
                "thread": thread,
                "date_validation": {"valid": date_valid, "reason": date_reason},
                "content_validation": {"valid": content_valid, "reason": content_reason},
                "overall_valid": date_valid and content_valid,
            }

            if thread_info["overall_valid"]:
                validation_results[missing_date]["valid_threads"].append(thread_info)
                summary_stats["valid_threads"] += 1
                date_has_valid_thread = True
                print(f"  ✅ {thread['title']}")
                print(f"     URL: {thread['url']}")
                print(f"     Date: {thread['created_utc']}")
                print(f"     Date validation: {date_reason}")
                print(f"     Content validation: {content_reason}")
            else:
                validation_results[missing_date]["rejected_threads"].append(thread_info)
                summary_stats["rejected_threads"] += 1
                print(f"  ❌ {thread['title']}")
                print(f"     URL: {thread['url']}")
                print(f"     Date validation: {date_reason}")
                print(f"     Content validation: {content_reason}")

        if date_has_valid_thread:
            summary_stats["dates_with_valid_threads"] += 1
            # Select best match (prefer exact date matches)
            valid_threads = validation_results[missing_date]["valid_threads"]
            if valid_threads:
                # Find thread with exact date match, or closest date
                best_match = None
                for thread_info in valid_threads:
                    thread_date = thread_info["thread"]["created_utc"].split(" ")[0]
                    if thread_date == missing_date:
                        best_match = thread_info
                        break

                if not best_match and len(valid_threads) > 0:
                    best_match = valid_threads[0]  # Take first valid thread

                validation_results[missing_date]["best_match"] = best_match

    # Print summary
    print("\n=== VALIDATION SUMMARY ===")
    print(f"Total missing dates checked: {summary_stats['total_missing_dates']}")
    print(f"Dates with valid threads: {summary_stats['dates_with_valid_threads']}")
    success_rate = (
        summary_stats["dates_with_valid_threads"] / summary_stats["total_missing_dates"] * 100
    )
    print(f"Success rate: {success_rate:.1f}%")
    print(f"Total threads checked: {summary_stats['total_threads_checked']}")
    print(f"Valid threads: {summary_stats['valid_threads']}")
    print(f"Rejected threads: {summary_stats['rejected_threads']}")

    # Save validation results
    results = {
        "validation_results": validation_results,
        "summary_stats": summary_stats,
        "validation_timestamp": datetime.now().isoformat(),
    }

    with open("thread_validation_results.json", "w") as f:
        json.dump(results, f, indent=2)

    print("\n=== RESULTS SAVED ===")
    print("Thread validation results saved to: thread_validation_results.json")

    return validation_results, summary_stats


if __name__ == "__main__":
    validation_results, summary_stats = validate_threads_for_missing_dates()
