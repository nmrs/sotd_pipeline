"""
Reddit API helper utilities for the SOTD pipeline.

Only authentication and basic thread search live here; higher-level
filtering is implemented elsewhere.
"""

from __future__ import annotations

import calendar
import os
from typing import List

import praw
from praw.models import Submission

ENV_VARS = ("REDDIT_CLIENT_ID", "REDDIT_CLIENT_SECRET", "REDDIT_USER_AGENT")


def _require_env(var: str) -> str:
    """Return the value of *var* or raise a helpful error."""
    try:
        return os.environ[var]
    except KeyError as exc:  # pragma: no cover
        missing = ", ".join(ENV_VARS)
        raise RuntimeError(f"Missing Reddit creds.  Set env vars: {missing}") from exc


def get_reddit() -> praw.Reddit:  # noqa: D401
    """Return an authenticated :class:`praw.Reddit` instance."""
    return praw.Reddit(
        client_id=_require_env("REDDIT_CLIENT_ID"),
        client_secret=_require_env("REDDIT_CLIENT_SECRET"),
        user_agent=_require_env("REDDIT_USER_AGENT"),
    )


def search_threads(
    subreddit: str,
    year: int,
    month: int,
    *,
    debug: bool = False,
) -> List[Submission]:
    """
    Query *subreddit* for SOTD threads in *month* / *year*.

    This is a **loose** search that relies on flair:SOTD plus both the
    short and long month names. Down-stream filters will refine results.
    """
    short = calendar.month_abbr[month].lower()  # e.g. "mar"
    long = calendar.month_name[month].lower()  # e.g. "march"
    query = f"flair:SOTD {short} {long} {year}"

    reddit = get_reddit()
    sub = reddit.subreddit(subreddit)

    if debug:
        print(f"[DEBUG] PRAW search query -> '{query}'")

    results: List[Submission] = list(sub.search(query, sort="new", syntax="lucene"))

    if debug:
        print(f"[DEBUG] PRAW returned {len(results)} results")

    return results
