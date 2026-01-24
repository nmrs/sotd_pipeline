"""Reddit thread search functionality via HTML/JSON API.

Phase 2: Thread discovery using Reddit's search API.
"""

from __future__ import annotations

import calendar
import re
from collections import defaultdict
from datetime import date
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

from sotd.fetch_via_json.json_scraper import get_reddit_cookies, get_reddit_json, get_reddit_session
from sotd.fetch_via_json.parser import filter_valid_threads_json, parse_thread_from_json
from sotd.utils import parse_thread_date
from sotd.utils.yaml_loader import load_yaml_with_nfc


def search_reddit_json(
    subreddit: str,
    query: str,
    limit: int = 100,
    cookies: Optional[dict] = None,
    session: Optional[Any] = None,
) -> List[Dict[str, Any]]:
    """Search Reddit using JSON API.

    Args:
        subreddit: Subreddit name (e.g., "wetshaving")
        query: Search query (e.g., "flair:SOTD jan 2025")
        limit: Maximum number of results (default 100, Reddit's max)
        cookies: Optional cookies for authentication
        session: Optional requests.Session

    Returns:
        List of thread dictionaries parsed from JSON
    """
    # Build search URL
    # Reddit search: https://www.reddit.com/r/{subreddit}/search.json?q={query}&restrict_sr=1&sort=relevance&limit={limit}
    base_url = f"https://www.reddit.com/r/{subreddit}/search.json"
    params = {
        "q": query,
        "restrict_sr": "1",  # Restrict to subreddit
        "sort": "relevance",
        "limit": str(min(limit, 100)),  # Reddit max is 100
    }

    # Build URL with query parameters
    query_string = "&".join(f"{k}={v}" for k, v in params.items())
    url = f"{base_url}?{query_string}"

    # Fetch JSON
    json_data = get_reddit_json(url, cookies=cookies, session=session)

    # Parse response structure
    # Reddit JSON structure: {"kind": "Listing", "data": {"children": [...]}}
    if "data" in json_data and "children" in json_data["data"]:
        children = json_data["data"]["children"]
    else:
        children = []

    # Parse each child (submission)
    threads = []
    for child in children:
        parsed = parse_thread_from_json(child)
        if parsed:
            threads.append(parsed)

    return threads


def search_threads_json(
    subreddit_name: str,
    year: int,
    month: int,
    *,
    debug: bool = False,
    cookies: Optional[dict] = None,
) -> List[Dict[str, Any]]:
    """Search for SOTD threads using Reddit's JSON API.

    This is the JSON-based equivalent of the PRAW search_threads function.
    It uses the same search strategy: broad queries first, then day-specific
    if we hit the 100-result limit.

    Args:
        subreddit_name: Subreddit to search (e.g., "wetshaving")
        year: Target year
        month: Target month (1-12)
        debug: Enable debug output
        cookies: Optional cookies for authentication

    Returns:
        List of thread dictionaries matching the year/month
    """
    if cookies is None:
        cookies = get_reddit_cookies()

    session = get_reddit_session(cookies=cookies)

    month_abbr = calendar.month_abbr[month].lower()
    month_name = calendar.month_name[month].lower()

    # Improved search strategy: use day-specific queries to avoid 100-result limit
    # First try broad searches, then fall back to day-specific if we hit the limit
    broad_queries = [
        f"flair:SOTD {month_abbr} {month_name} {year}",
        f"flair:SOTD {month_abbr} {month_name} {year}SOTD",
    ]

    all_results: Dict[str, Dict[str, Any]] = {}
    hit_limit = False

    # Try broad searches first
    for query in broad_queries:
        if debug:
            print(f"[DEBUG] Search query: {query!r}")

        try:
            raw_results = search_reddit_json(
                subreddit_name, query, limit=100, cookies=cookies, session=session
            )
            if debug:
                print(f"[DEBUG] JSON raw results for {query!r}: {len(raw_results)}")

            # Check if we hit the 100-result limit (indicates there might be more results)
            if len(raw_results) >= 100:
                hit_limit = True
                if debug:
                    print(
                        f"[DEBUG] Hit 100-result limit with {query!r}, will use day-specific searches"
                    )

            # Dedupe by Reddit submission ID
            for thread in raw_results:
                all_results[thread["id"]] = thread
        except Exception as e:
            if debug:
                print(f"[WARN] Search query {query!r} failed: {e}")
            continue

    # If we hit the limit, use smart pattern detection to find missing threads
    if hit_limit:
        if debug:
            print("[DEBUG] Analyzing thread patterns to identify missing days")

        # First filter the broad results to only current year/month
        filtered_results = filter_valid_threads_json(
            list(all_results.values()), year, month, debug=debug
        )

        # Analyze filtered results to determine expected threads per day
        # Group filtered threads by day
        threads_by_day = defaultdict(list)
        for thread in filtered_results:
            title = thread.get("title", "")
            d = parse_thread_date(title, year)
            if d is not None and d.month == month:
                threads_by_day[d.day].append(thread)

        # Find the maximum number of threads per day
        max_threads_per_day = (
            max(len(threads) for threads in threads_by_day.values()) if threads_by_day else 0
        )

        if debug:
            print(f"[DEBUG] Found max {max_threads_per_day} threads per day")
            for day in sorted(threads_by_day.keys()):
                count = len(threads_by_day[day])
                print(f"[DEBUG] Day {day}: {count} threads")

        # Find days that are missing threads
        # For current month, only check up to current date
        today = date.today()
        is_current_month = year == today.year and month == today.month
        max_day_to_check = today.day if is_current_month else 31

        missing_days = []
        for day in range(1, max_day_to_check + 1):
            current_count = len(threads_by_day[day])
            if current_count < max_threads_per_day:
                missing_count = max_threads_per_day - current_count
                missing_days.append((day, missing_count))
                if debug:
                    print(
                        f"[DEBUG] Day {day}: missing {missing_count} threads "
                        f"(has {current_count}, need {max_threads_per_day})"
                    )

        # Search for missing threads on specific days
        if missing_days:
            if debug:
                print(f"[DEBUG] Searching for missing threads on {len(missing_days)} days")

            for day, missing_count in missing_days:
                day_queries = [
                    f"flair:SOTD {month_abbr} {day:02d} {year}",
                    f"flair:SOTD {month_abbr} {day} {year}",
                    f"flair:SOTD {month_name} {day:02d} {year}",
                    f"flair:SOTD {month_name} {day} {year}",
                ]

                for query in day_queries:
                    if debug:
                        print(f"[DEBUG] Missing thread query: {query!r}")
                    try:
                        raw_results = search_reddit_json(
                            subreddit_name, query, limit=100, cookies=cookies, session=session
                        )
                        if debug:
                            print(f"[DEBUG] JSON raw results for {query!r}: {len(raw_results)}")

                        # Dedupe by Reddit submission ID
                        for thread in raw_results:
                            all_results[thread["id"]] = thread
                    except Exception as e:
                        if debug:
                            print(f"[WARN] Search query {query!r} failed: {e}")
                        continue

    combined = list(all_results.values())
    if debug:
        print(f"[DEBUG] Combined raw results (deduped): {len(combined)}")

    # Process thread overrides (JSON version - no PRAW)
    month_str = f"{year:04d}-{month:02d}"
    override_threads = process_thread_overrides_json(
        month_str, cookies=cookies, session=session, debug=debug
    )

    # Add override threads to results (deduplication by ID)
    for override_thread in override_threads:
        all_results[override_thread["id"]] = override_thread

    if debug and override_threads:
        print(f"[DEBUG] Added {len(override_threads)} override threads")

    # Re-combine and filter
    combined = list(all_results.values())
    if debug:
        print(f"[DEBUG] Combined results with overrides: {len(combined)}")

    # Filter to valid threads for this year/month
    valid_threads = filter_valid_threads_json(combined, year, month, debug=debug)

    return valid_threads


def extract_thread_id_from_url(url: str) -> Optional[str]:
    """Extract Reddit thread ID from a Reddit URL.

    Examples:
        https://www.reddit.com/r/Wetshaving/comments/1lk3ooa/wednesday_sotd_25_june/
        -> 1lk3ooa

        /r/wetshaving/comments/1lk3ooa/
        -> 1lk3ooa
    """
    # Parse URL
    parsed = urlparse(url)
    path = parsed.path

    # Pattern: /r/{subreddit}/comments/{thread_id}/...
    match = re.search(r"/comments/([a-z0-9]+)", path)
    if match:
        return match.group(1)

    return None


def fetch_thread_by_url(
    url: str, cookies: Optional[dict] = None, session: Optional[Any] = None
) -> Optional[Dict[str, Any]]:
    """Fetch a Reddit thread by URL using JSON API (no PRAW).

    Args:
        url: Reddit thread URL
        cookies: Optional cookies for authentication
        session: Optional requests.Session

    Returns:
        Thread dictionary or None if not found
    """
    # Extract thread ID from URL
    thread_id = extract_thread_id_from_url(url)
    if not thread_id:
        return None

    # Build JSON URL: https://www.reddit.com/r/wetshaving/comments/{thread_id}/.json
    # Or use the original URL with .json appended
    if url.endswith("/"):
        json_url = url.rstrip("/") + ".json"
    else:
        json_url = url + ".json"

    try:
        # Fetch JSON
        json_data = get_reddit_json(json_url, cookies=cookies, session=session)

        # Reddit's comment thread JSON structure:
        # [{"kind": "Listing", "data": {"children": [{"kind": "t3", "data": {...}}]}}]
        if isinstance(json_data, list) and len(json_data) > 0:
            # First element is the thread itself
            thread_listing = json_data[0]
            if "data" in thread_listing and "children" in thread_listing["data"]:
                children = thread_listing["data"]["children"]
                if children and len(children) > 0:
                    # First child is the thread (t3 = submission)
                    thread_data = children[0]
                    parsed = parse_thread_from_json(thread_data)
                    return parsed

        # Fallback: try direct parsing
        parsed = parse_thread_from_json(json_data)
        return parsed
    except Exception as e:
        print(f"[WARN] Failed to fetch thread from {url}: {e}")
        return None


def process_thread_overrides_json(
    month: str,
    *,
    cookies: Optional[dict] = None,
    session: Optional[Any] = None,
    debug: bool = False,
) -> List[Dict[str, Any]]:
    """Process thread overrides from YAML file using JSON API (no PRAW).

    This is the JSON-based equivalent of process_thread_overrides.
    It loads the same YAML file and fetches threads via JSON API.

    Args:
        month: Month string in YYYY-MM format
        cookies: Optional cookies for authentication
        session: Optional requests.Session
        debug: Enable debug output

    Returns:
        List of thread dictionaries
    """
    override_path = Path("data/thread_overrides.yaml")
    if not override_path.exists():
        if debug:
            print(f"[DEBUG] No thread overrides found for {month}")
        return []

    try:
        data = load_yaml_with_nfc(override_path)
        if not data:
            if debug:
                print(f"[DEBUG] No thread overrides found for {month}")
            return []
    except Exception as e:
        print(f"[WARN] Failed to load thread overrides: {e}")
        return []

    # Build list of (date_key, url) for the month
    url_date_pairs = []
    for date_key, url_list in data.items():
        # Convert date_key to string (handle datetime.date or str)
        if hasattr(date_key, "isoformat"):
            date_str = date_key.isoformat()
        else:
            date_str = str(date_key)
        if date_str.startswith(month):
            if isinstance(url_list, list):
                for url in url_list:
                    url_date_pairs.append((date_str, url))
            else:
                url_date_pairs.append((date_str, url_list))

    if not url_date_pairs:
        if debug:
            print(f"[DEBUG] No thread overrides found for {month}")
        return []

    if debug:
        print(f"[DEBUG] Processing {len(url_date_pairs)} thread overrides for {month}")

    if session is None:
        if cookies is None:
            cookies = get_reddit_cookies()
        session = get_reddit_session(cookies=cookies)

    valid_threads = []

    for date_str, url in url_date_pairs:
        try:
            thread = fetch_thread_by_url(url, cookies=cookies, session=session)
            if thread:
                # Attach the YAML date as _override_date for fallback
                thread["_override_date"] = date_str
                valid_threads.append(thread)
                if debug:
                    print(f"[DEBUG] Validated override: {thread.get('title', 'Unknown')}")
            else:
                print(f"[WARN] Failed to fetch thread override: {url}")
        except Exception as e:
            print(f"[WARN] Failed to fetch thread override: {url} - {e}")
            continue

    if debug:
        print(
            f"[DEBUG] Successfully processed {len(valid_threads)}/{len(url_date_pairs)} overrides"
        )

    return valid_threads
