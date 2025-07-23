#!/usr/bin/env python3
"""
Script to prepare validated cache threads for thread_overrides.yaml.
Extracts best matches and formats them for the overrides file.
"""

import json
from datetime import datetime
from pathlib import Path

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


def load_existing_overrides():
    """Load existing thread_overrides.yaml file."""
    overrides_file = Path("data/thread_overrides.yaml")
    if overrides_file.exists():
        with open(overrides_file, "r") as f:
            raw_overrides = yaml.safe_load(f)
            # Convert all keys to strings to avoid sorting issues
            overrides = {}
            for key, value in raw_overrides.items():
                overrides[str(key)] = value
            return overrides
    else:
        return {}


def load_missing_dates():
    """Load the list of all missing dates from the analysis."""
    try:
        with open("missing_dates_analysis.json", "r") as f:
            data = json.load(f)
            return data.get("missing_dates", [])
    except FileNotFoundError:
        print("Warning: missing_dates_analysis.json not found")
        return []


def merge_overrides(existing_overrides, new_overrides, all_missing_dates):
    """Merge existing overrides with new ones, ensuring all missing dates are included."""
    merged = existing_overrides.copy()

    # Add all missing dates first (with empty values if not found)
    for date in all_missing_dates:
        if date not in merged:
            merged[date] = None  # Will be converted to empty entry with comment

    # Add new overrides (these will override empty entries if found)
    for date, thread_info in new_overrides.items():
        if date in merged and merged[date] is not None:
            # Convert to list if it's not already
            existing_value = merged[date]
            if isinstance(existing_value, list):
                merged[date] = existing_value + [thread_info["url"]]
            else:
                merged[date] = [str(existing_value), thread_info["url"]]
        else:
            merged[date] = [thread_info["url"]]

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

        for date in sorted(sorted_overrides.keys()):
            urls = sorted_overrides[date]
            if urls and isinstance(urls, list) and len(urls) > 0:
                f.write(f"{date}:\n")
                for url in urls:
                    f.write(f"  - {url}\n")
                f.write("\n")
            else:
                f.write(f"{date}:\n")
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
    for date, thread_info in best_matches.items():
        if date not in existing_overrides:
            new_additions.append((date, thread_info))

    print("\n=== NEW ADDITIONS TO THREAD_OVERRIDES.YAML ===")
    print(f"Added {len(new_additions)} new dates:")

    for date, thread_info in new_additions:
        print(f"  {date}: {thread_info['title']}")
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
    best_matches, new_additions = main()
