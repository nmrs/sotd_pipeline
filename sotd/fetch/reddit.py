"""
Reddit interface utilities for the SOTD pipeline.

• Auth uses `praw.ini` default section.
• Search helpers parse titles → calendar dates.
• Comment fetcher returns only top-level comments.
"""

from __future__ import annotations

import calendar
from typing import List, Tuple

import praw
from praw.models import Comment, Submission

from sotd.utils import parse_thread_date

# ------------------------------------------------------------------ #
# Authentication                                                     #
# ------------------------------------------------------------------ #


def get_reddit() -> praw.Reddit:  # noqa: D401
    """Return a PRAW instance (reads default section from praw.ini)."""
    return praw.Reddit()


# ------------------------------------------------------------------ #
# Search & filter helpers                                            #
# ------------------------------------------------------------------ #


def _build_query(year: int, month: int) -> str:
    short = calendar.month_abbr[month].lower()
    long = calendar.month_name[month].lower()
    return f"flair:SOTD {short} {long} {year}"


def filter_valid_threads(
    threads: List[Submission],
    year: int,
    month: int,
    *,
    debug: bool = False,
) -> List[Submission]:
    """
    Return only submissions whose title parses to a date in *year*-*month*,
    sorted by that date ascending.
    """
    valid_pairs: list[Tuple] = []

    for sub in threads:
        dt = parse_thread_date(sub.title, year)
        if dt and dt.year == year and dt.month == month:
            valid_pairs.append((dt, sub))
        elif debug:
            reason = "no-date" if dt is None else "wrong-month"
            print(f"[DEBUG] Skip ({reason}) {sub.title}")

    # Sort by parsed date; dt is guaranteed non-None here
    valid_pairs.sort(key=lambda tup: tup[0])
    return [sub for _, sub in valid_pairs]


def search_threads(
    subreddit: str,
    year: int,
    month: int,
    *,
    debug: bool = False,
) -> List[Submission]:
    reddit = get_reddit()
    sub = reddit.subreddit(subreddit)
    query = _build_query(year, month)
    raw = list(sub.search(query, sort="new", syntax="lucene"))
    if debug:
        print(f"[DEBUG] PRAW raw results: {len(raw)}")
    valids = filter_valid_threads(raw, year, month, debug=debug)
    if debug:
        print(f"[DEBUG] Valid threads:     {len(valids)}")
    return valids


# ------------------------------------------------------------------ #
# Comment fetcher                                                    #
# ------------------------------------------------------------------ #


def fetch_top_level_comments(submission: Submission) -> list[Comment]:
    """
    Return a list of top-level comments for *submission*.

    • Skips :class:`praw.models.MoreComments`
    • Ensures `Comment.is_root` is True
    """
    submission.comments.replace_more(limit=0)
    return [c for c in submission.comments.list() if isinstance(c, Comment) and c.is_root]
