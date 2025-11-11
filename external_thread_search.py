#!/usr/bin/env python3
"""
Script to perform external searches for missing SOTD thread URLs.
This implements Phase 2 of the missing thread URL recovery plan.
"""

import json
from datetime import datetime
from urllib.parse import quote_plus


def search_reddit_external(date_str):
    """Search Reddit externally for SOTD threads on a specific date."""
    # Convert date to search-friendly format
    date_obj = datetime.strptime(date_str, "%Y-%m-%d")

    # Create search queries
    search_queries = [
        f"flair:SOTD {date_obj.strftime('%B %d, %Y')}",
        f"flair:SOTD {date_obj.strftime('%b %d, %Y')}",
        f"SOTD Thread {date_obj.strftime('%B %d, %Y')}",
        f"SOTD Thread {date_obj.strftime('%b %d, %Y')}",
        f"Shave of the Day {date_obj.strftime('%B %d, %Y')}",
        f"Daily SOTD {date_obj.strftime('%B %d, %Y')}",
        f"Daily SOTD {date_obj.strftime('%b %d, %Y')}",
        f"subreddit:wetshaving {date_obj.strftime('%B %d, %Y')} SOTD",
        f"subreddit:wetshaving {date_obj.strftime('%b %d, %Y')} SOTD",
    ]

    results = []

    for query in search_queries:
        try:
            # Note: This would require Reddit API credentials for actual implementation
            # For now, we'll document the search patterns
            encoded_query = quote_plus(query)
            search_url = f"https://www.reddit.com/r/Wetshaving/search.json?q={encoded_query}&restrict_sr=on&sort=relevance&t=all"

            results.append(
                {"query": query, "search_url": search_url, "status": "documented_for_manual_search"}
            )

        except Exception as e:
            results.append({"query": query, "error": str(e), "status": "failed"})

    return {
        "date": date_str,
        "search_queries": results,
        "search_timestamp": datetime.now().isoformat(),
    }


def search_wayback_machine(date_str):
    """Search Wayback Machine for archived Reddit threads."""
    # Create Wayback Machine search URLs
    wayback_urls = [
        f"https://web.archive.org/web/{date_str}*/https://www.reddit.com/r/Wetshaving/",
        f"https://web.archive.org/web/{date_str}*/https://old.reddit.com/r/Wetshaving/",
    ]

    return {
        "date": date_str,
        "wayback_urls": wayback_urls,
        "search_timestamp": datetime.now().isoformat(),
    }


def search_external_resources(date_str):
    """Search external wetshaving resources."""
    date_obj = datetime.strptime(date_str, "%Y-%m-%d")

    # External resources to search
    external_resources = [
        {
            "name": "Djudge Portal",
            "url": "https://djudge.com/",
            "search_pattern": f"site:djudge.com {date_obj.strftime('%B %d, %Y')} SOTD",
        },
        {
            "name": "DamnFineShave",
            "url": "https://damnfineshave.com/",
            "search_pattern": f"site:damnfineshave.com {date_obj.strftime('%B %d, %Y')} SOTD",
        },
        {
            "name": "Google Site Search",
            "url": "https://www.google.com/search",
            "search_pattern": f"site:reddit.com/r/Wetshaving {date_obj.strftime('%B %d, %Y')} SOTD",
        },
    ]

    return {
        "date": date_str,
        "external_resources": external_resources,
        "search_timestamp": datetime.now().isoformat(),
    }


def get_missing_dates():
    """Get the list of dates that need external search."""
    missing_dates = [
        "2016-05-02",
        "2016-05-03",
        "2016-08-01",
        "2018-02-15",
        "2018-07-11",
        "2018-11-01",
        "2019-07-29",
        "2019-09-02",
        "2019-11-04",
        "2020-02-24",
        "2020-03-02",
        "2020-03-04",
        "2020-04-04",
        "2021-01-22",
        "2021-01-23",
        "2021-01-24",
        "2021-09-01",
        "2022-04-09",
        "2022-05-08",
        "2022-05-12",
        # Removed 5 July 2025 dates that were found in updated fetch results:
        # "2025-07-18", "2025-07-19", "2025-07-20", "2025-07-21", "2025-07-22"
    ]
    return missing_dates


def main():
    """Main function to perform external searches."""
    print("=== EXTERNAL THREAD SEARCH - PHASE 2 ===")

    missing_dates = get_missing_dates()
    print(f"Found {len(missing_dates)} dates requiring external search")

    external_search_results = {}

    for date in missing_dates:
        print(f"\nSearching for {date}...")

        # Perform different types of searches
        reddit_results = search_reddit_external(date)
        wayback_results = search_wayback_machine(date)
        external_results = search_external_resources(date)

        external_search_results[date] = {
            "reddit_search": reddit_results,
            "wayback_search": wayback_results,
            "external_resources": external_results,
        }

    # Save results
    with open("external_search_results.json", "w") as f:
        json.dump(external_search_results, f, indent=2)

    print("\n=== EXTERNAL SEARCH COMPLETE ===")
    print(f"Searched {len(missing_dates)} missing dates")
    print("Results saved to: external_search_results.json")
    print("\nNext steps:")
    print("1. Manually review search URLs for each date")
    print("2. Validate found threads against criteria")
    print("3. Add valid threads to thread_overrides.yaml")
    print("4. Update plan with external search results")

    return external_search_results


if __name__ == "__main__":
    results = main()
