#!/usr/bin/env python3
"""
Script to prepare validated cache threads for thread_overrides.yaml.
Extracts best matches and formats them for the overrides file.
"""

import json
from datetime import date, datetime

import yaml


def load_validation_results():
    """Load the thread validation results."""
    try:
        with open("thread_validation_results.json", "r") as f:
            results = json.load(f)
        return results["validation_results"]
    except FileNotFoundError:
        print(
            "Error: thread_validation_results.json not found. Run validate_cache_threads.py first."
        )
        return None


def extract_best_matches(validation_results):
    """Extract the best matches for each missing date."""
    best_matches = {}

    for missing_date, date_results in validation_results.items():
        best_match = date_results.get("best_match")
        if best_match:
            thread = best_match["thread"]
            best_matches[missing_date] = {
                "url": thread["url"],
                "title": thread["title"],
                "author": thread["author"],
                "created_utc": thread["created_utc"],
                "source": "cache_validation",
                "validation_status": "valid_sotd_thread",
            }

    return best_matches


def deduplicate_overrides(overrides):
    """Remove duplicate URLs from overrides."""
    deduplicated = {}
    for date_key, urls in overrides.items():
        if urls and isinstance(urls, list):
            # Remove duplicates while preserving order
            seen = set()
            unique_urls = []
            for url in urls:
                if url not in seen:
                    seen.add(url)
                    unique_urls.append(url)
            deduplicated[date_key] = unique_urls
        else:
            deduplicated[date_key] = urls
    return deduplicated


def load_existing_overrides():
    """Load existing overrides from YAML file."""
    try:
        with open("data/thread_overrides.yaml", "r") as f:
            data = yaml.safe_load(f)
            if data is None:
                return {}
            # Convert all keys to strings and deduplicate
            overrides = {}
            for key, value in data.items():
                overrides[str(key)] = value
            return deduplicate_overrides(overrides)
    except FileNotFoundError:
        return {}


def filter_future_dates(missing_dates):
    """Filter out future dates from the missing dates list."""
    today = date.today()
    filtered_dates = []

    for date_str in missing_dates:
        try:
            date_obj = datetime.strptime(date_str, "%Y-%m-%d").date()
            if date_obj <= today:
                filtered_dates.append(date_str)
        except ValueError:
            # Skip invalid date formats
            continue

    return filtered_dates


def load_missing_dates():
    """Load the list of all missing dates from the analysis."""
    try:
        with open("missing_dates_analysis.json", "r") as f:
            data = json.load(f)
            missing_dates = data.get("missing_dates", [])
            # Filter out future dates
            return filter_future_dates(missing_dates)
    except FileNotFoundError:
        print("Warning: missing_dates_analysis.json not found")
        return []


def merge_overrides(existing_overrides, new_overrides, all_missing_dates):
    """Merge existing overrides with new ones, ensuring all missing dates are included."""
    merged = existing_overrides.copy()

    # Add all missing dates first (with empty values if not found)
    for date_key in all_missing_dates:
        if date_key not in merged:
            merged[date_key] = None  # Will be converted to empty entry with comment

    # Add new overrides (these will override empty entries if found)
    for date_key, thread_info in new_overrides.items():
        if date_key in merged and merged[date_key] is not None:
            # Convert to list if it's not already
            existing_value = merged[date_key]
            if isinstance(existing_value, list):
                # Check if URL already exists to avoid duplicates
                if thread_info["url"] not in existing_value:
                    merged[date_key] = existing_value + [thread_info["url"]]
            else:
                # Convert existing value to list and add new URL
                merged[date_key] = [str(existing_value), thread_info["url"]]
        else:
            merged[date_key] = [thread_info["url"]]

    return merged


def save_overrides(overrides, filename="data/thread_overrides.yaml"):
    """Save overrides to YAML file with proper formatting."""
    # Sort by date for consistent output - ensure all keys are strings
    sorted_overrides = {}
    for key in sorted(overrides.keys()):
        sorted_overrides[str(key)] = overrides[key]

    # Write YAML manually to control formatting
    with open(filename, "w") as f:
        f.write("# Manual thread overrides for threads that don't match standard search patterns\n")
        f.write("# Format: YYYY-MM-DD: [list of Reddit URLs]\n")
        f.write(
            '# Example: 2025-06-25: ["https://www.reddit.com/r/Wetshaving/comments/1lk3ooa/wednesday_sotd_25_june/"]\n\n'
        )

        for date_key in sorted(sorted_overrides.keys()):
            urls = sorted_overrides[date_key]
            if urls and isinstance(urls, list) and len(urls) > 0:
                f.write(f"{date_key}:\n")
                for url in urls:
                    f.write(f"  - {url}\n")
                f.write("\n")
            else:
                f.write(f"{date_key}:\n")
                f.write("  # No threads found for this date\n")
                f.write("\n")


def main():
    """Main function to prepare thread overrides."""
    print("=== PREPARING THREAD OVERRIDES ===")

    # Load validation results
    validation_results = load_validation_results()
    if not validation_results:
        return

    # Extract best matches
    best_matches = extract_best_matches(validation_results)

    print(f"Found {len(best_matches)} best matches for missing dates")

    # Load existing overrides
    existing_overrides = load_existing_overrides()
    print(f"Existing overrides: {len(existing_overrides)} dates")

    # Load all missing dates
    all_missing_dates = load_missing_dates()
    print(f"All missing dates: {len(all_missing_dates)}")

    # Merge with existing overrides
    merged_overrides = merge_overrides(existing_overrides, best_matches, all_missing_dates)
    print(f"Total overrides after merge: {len(merged_overrides)} dates")

    # Save updated overrides
    save_overrides(merged_overrides)

    # Print summary of new additions
    new_additions = []
    for date_key, thread_info in best_matches.items():
        if date_key not in existing_overrides:
            new_additions.append((date_key, thread_info))

    print("\n=== NEW ADDITIONS TO THREAD_OVERRIDES.YAML ===")
    print(f"Added {len(new_additions)} new dates:")

    for date_key, thread_info in new_additions:
        print(f"  {date_key}: {thread_info['title']}")
        print(f"    URL: {thread_info['url']}")
        print(f"    Author: {thread_info['author']}")
        print(f"    Created: {thread_info['created_utc']}")

    # Save detailed results
    results = {
        "best_matches": best_matches,
        "new_additions": dict(new_additions) if new_additions else {},
        "total_overrides": len(merged_overrides),
        "cache_recovery_summary": {
            "total_missing_dates": len(validation_results),
            "dates_with_valid_threads": len(best_matches),
            "success_rate": len(best_matches) / len(validation_results) * 100,
        },
        "preparation_timestamp": datetime.now().isoformat(),
    }

    with open("thread_overrides_preparation.json", "w") as f:
        json.dump(results, f, indent=2)

    print("\n=== RESULTS SAVED ===")
    print("Updated thread_overrides.yaml with new cache findings")
    print("Detailed results saved to: thread_overrides_preparation.json")

    return best_matches, new_additions


if __name__ == "__main__":
    result = main()
    if result is not None:
        best_matches, new_additions = result
    else:
        best_matches, new_additions = {}, []
