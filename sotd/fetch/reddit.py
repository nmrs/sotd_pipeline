"""Reddit‐helpers: authentication, searching, comment harvesting – plus
a small `safe_call` wrapper that handles Reddit's `RateLimitExceeded`.
"""

from __future__ import annotations

import calendar
import os
import time
from datetime import date as _date
from typing import List, Sequence, TypeVar, cast

import praw
from praw.models import Comment, Submission
from prawcore.exceptions import RequestException, NotFound

# PRAW 7.x has RateLimitExceeded; newer prawcore switched to TooManyRequests.
try:
    from prawcore.exceptions import RateLimitExceeded  # type: ignore[attr-defined]
except ImportError:  # pragma: no cover
    from prawcore.exceptions import TooManyRequests as RateLimitExceeded  # type: ignore

from sotd.utils import parse_thread_date

T = TypeVar("T")


# --------------------------------------------------------------------------- #
# rate-limit wrapper                                                          #
# --------------------------------------------------------------------------- #
def safe_call(fn, *args, **kwargs):  # type: ignore[no-untyped-def]
    """Call *fn* once; if `RateLimitExceeded`, sleep & retry once.

    Prints a human-readable warning:

        [WARN] Reddit rate-limit hit; sleeping 8m 20s…

    If the retry also fails, the exception propagates.
    Returns None if any other exception occurs.
    """
    retry = False
    while True:
        try:
            return fn(*args, **kwargs)
        except RateLimitExceeded as exc:
            if retry:
                raise
            # Determine sleep time: prefer .sleep_time, fallback to .retry_after, default 60s
            sec = getattr(exc, "sleep_time", None)
            if sec is None:
                sec = getattr(exc, "retry_after", None)
            if sec is None:
                sec = 60
            sec = int(sec)
            mins, secs = divmod(sec, 60)
            print(f"[WARN] Reddit rate-limit hit; sleeping {mins}m {secs}s…")
            time.sleep(sec + 1)
            retry = True
        except (ConnectionError, RuntimeError, RequestException, NotFound, ValueError) as exc:
            print(f"[WARN] Reddit API error: {exc}")
            return None


# --------------------------------------------------------------------------- #
# auth                                                                        #
# --------------------------------------------------------------------------- #
def _require_env(key: str) -> str:
    val = os.getenv(key)
    if not val:
        raise RuntimeError(f"Missing environment variable: {key}")
    return val


def get_reddit() -> praw.Reddit:  # noqa: D401
    """Return a PRAW instance using the section in praw.ini."""
    return praw.Reddit()  # relies on praw.ini in project root


# --------------------------------------------------------------------------- #
# searching & filtering                                                       #
# --------------------------------------------------------------------------- #
def search_threads(
    subreddit_name: str, year: int, month: int, *, debug: bool = False
) -> List[Submission]:
    reddit = get_reddit()
    subreddit = reddit.subreddit(subreddit_name)

    month_abbr = calendar.month_abbr[month].lower()
    month_name = calendar.month_name[month].lower()
    # Two search patterns: normal and "yearSOTD" style
    queries = [
        f"flair:SOTD {month_abbr} {month_name} {year}",
        f"flair:SOTD {month_abbr} {month_name} {year}SOTD",
    ]

    all_results = {}
    for query in queries:
        if debug:
            print(f"[DEBUG] Search query: {query!r}")
        raw_results = safe_call(subreddit.search, query, sort="relevance", syntax="lucene")
        if raw_results is None:
            raw_results = []
        raw_results = list(raw_results)
        if debug:
            print(f"[DEBUG] PRAW raw results for {query!r}: {len(raw_results)}")
        for sub in raw_results:
            all_results[sub.id] = sub  # dedupe by Reddit submission ID

    combined = list(all_results.values())
    if debug:
        print(f"[DEBUG] Combined raw results (deduped): {len(combined)}")

    valid = filter_valid_threads(combined, year, month, debug=debug)
    return valid


def filter_valid_threads(
    threads: Sequence[Submission], year: int, month: int, *, debug: bool = False
) -> List[Submission]:
    kept: List[Submission] = []
    for sub in threads:
        d = parse_thread_date(sub.title, year)
        if d is None:
            if debug:
                print(f"[DEBUG] Skip (no-date) {sub.title}")
            continue
        if (d.year, d.month) != (year, month):
            if debug:
                print(f"[DEBUG] Skip (wrong-month) {sub.title}")
            continue
        kept.append(sub)

    kept.sort(key=lambda s: parse_thread_date(s.title, year) or _date.min)
    if debug:
        print(f"[DEBUG] Valid threads:     {len(kept)}")
    return kept


# --------------------------------------------------------------------------- #
# comments                                                                    #
# --------------------------------------------------------------------------- #
def fetch_top_level_comments(submission: Submission) -> List[Comment]:
    """Return only root comments (shaves)."""
    safe_call(submission.comments.replace_more, limit=None)

    return cast(
        List[Comment],
        [c for c in submission.comments.list() if getattr(c, "is_root", False)],
    )
