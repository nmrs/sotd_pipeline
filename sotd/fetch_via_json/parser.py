"""JSON parsing utilities for Reddit content.

Thread and comment parsing from Reddit's JSON API responses.
"""

from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Any, Dict, List, Optional

from sotd.utils import parse_thread_date


def parse_thread_from_json(json_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Parse a Reddit submission from JSON API response.

    Reddit's JSON API returns submissions in this structure:
    {
        "data": {
            "id": "abc123",
            "title": "SOTD - January 1, 2025",
            "author": "username",
            "created_utc": 1704067200.0,
            "num_comments": 42,
            "permalink": "/r/wetshaving/comments/abc123/...",
            "link_flair_text": "SOTD",
            ...
        }
    }

    Args:
        json_data: Dictionary from Reddit JSON API (either direct data or wrapped)

    Returns:
        Dictionary with thread fields matching existing format, or None if invalid
    """
    # Handle both direct data and wrapped responses
    if "data" in json_data and isinstance(json_data["data"], dict):
        data = json_data["data"]
    elif "kind" in json_data and json_data["kind"] == "t3":
        data = json_data.get("data", {})
    else:
        data = json_data

    # Extract required fields
    thread_id = data.get("id")
    if not thread_id:
        return None

    # Handle permalink - ensure it starts with /r/
    permalink = data.get("permalink", "")
    if permalink and not permalink.startswith("/r/"):
        # Sometimes permalink is relative, sometimes absolute
        if permalink.startswith("http"):
            # Extract path from URL
            from urllib.parse import urlparse

            parsed = urlparse(permalink)
            permalink = parsed.path

    # Build URL
    if permalink:
        url = f"https://www.reddit.com{permalink}" if permalink.startswith("/") else permalink
    else:
        # Fallback: construct URL from subreddit and ID
        subreddit = data.get("subreddit", "wetshaving")
        url = f"https://www.reddit.com/r/{subreddit}/comments/{thread_id}/"

    # Parse created_utc timestamp
    created_utc = data.get("created_utc", 0)
    if isinstance(created_utc, (int, float)):
        created_dt = datetime.utcfromtimestamp(created_utc).replace(tzinfo=timezone.utc)
        created_utc_iso = created_dt.isoformat().replace("+00:00", "Z")
    else:
        created_utc_iso = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

    # Get author (handle deleted users)
    author = data.get("author")
    if author is None or author == "[deleted]":
        author = "[deleted]"
    else:
        author = str(author)

    return {
        "id": thread_id,
        "title": data.get("title", ""),
        "url": url,
        "author": author,
        "created_utc": created_utc_iso,
        "num_comments": data.get("num_comments", 0),
        "flair": data.get("link_flair_text"),
    }


def filter_valid_threads_json(
    threads: List[Dict[str, Any]], year: int, month: int, *, debug: bool = False
) -> List[Dict[str, Any]]:
    """Filter threads to only those matching the specified year/month.

    Uses the same date parsing logic as the existing PRAW implementation.

    Args:
        threads: List of thread dictionaries
        year: Target year
        month: Target month
        debug: Enable debug output

    Returns:
        Filtered and sorted list of valid threads
    """
    kept: List[Dict[str, Any]] = []

    for thread in threads:
        title = thread.get("title", "")
        d = parse_thread_date(title, year)

        # Check for override date (if present)
        if d is None and "_override_date" in thread:
            try:
                d = datetime.strptime(thread["_override_date"], "%Y-%m-%d").date()
                if debug:
                    print(f"[DEBUG] Used fallback date for {title}: {d}")
            except Exception:
                d = None

        if d is None:
            if debug:
                print(f"[DEBUG] Skip (no-date) {title}")
            continue

        if (d.year, d.month) != (year, month):
            if debug:
                print(f"[DEBUG] Skip (wrong-month) {title}")
            continue

        kept.append(thread)

    # Sort by date (using parse_thread_date as key)
    def sort_key(t: Dict[str, Any]) -> date:
        d = parse_thread_date(t.get("title", ""), year)
        if d is None and "_override_date" in t:
            try:
                d = datetime.strptime(t["_override_date"], "%Y-%m-%d").date()
            except Exception:
                d = None
        return d or date.min

    kept.sort(key=sort_key)

    if debug:
        print(f"[DEBUG] Valid threads: {len(kept)}")

    return kept
