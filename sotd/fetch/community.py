"""Fetch the full r/wetshaving community record for one or more months.

Every post in the target month (SOTD daily threads included) plus its full
comment tree is stored to ``data/community/YYYY-MM.json``::

    {"meta": {...}, "data": {"posts": [...], "comments": [...]}}

This is a sidecar to the 6-phase pipeline: nothing in extract..report consumes
this data. The ``community_query`` CLI is its access surface (agent consumption
is a later project). The pipeline's own ``data/comments/`` store (top-level SOTD
comments only) is never reused here — everything is fetched fresh from Reddit.
"""

# ruff: noqa: E402  # keep imports after docstring for clarity
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Optional, Set

from sotd.fetch.save import load_month_file
from sotd.utils.data_dir import get_data_dir
from sotd.utils.file_io import load_json_data, save_json_data

logger = logging.getLogger(__name__)


# --------------------------------------------------------------------------- #
# record building                                                             #
# --------------------------------------------------------------------------- #
def _iso(created_utc: float) -> str:
    return datetime.fromtimestamp(created_utc, tz=timezone.utc).isoformat().replace("+00:00", "Z")


def build_post_record(sub, *, in_pipeline: Optional[bool]) -> dict:
    rec = {
        "id": sub.id,
        "title": sub.title,
        "selftext": getattr(sub, "selftext", "") or "",
        "author": str(sub.author) if sub.author else "[deleted]",
        "created_utc": _iso(sub.created_utc),
        "score": int(getattr(sub, "score", 0) or 0),
        "num_comments": int(getattr(sub, "num_comments", 0) or 0),
        "flair": sub.link_flair_text,
        "url": f"https://www.reddit.com{sub.permalink}",
        "locked": bool(getattr(sub, "locked", False)),
        "stickied": bool(getattr(sub, "stickied", False)),
    }
    if in_pipeline is not None:
        rec["in_pipeline"] = in_pipeline
    return rec


def build_comment_record(c, thread_id: str, thread_title: str) -> dict:
    return {
        "id": c.id,
        "thread_id": thread_id,
        "thread_title": thread_title,
        "parent_id": c.parent_id,
        "author": str(c.author) if c.author else "[deleted]",
        "created_utc": _iso(c.created_utc),
        "body": c.body,
        "score": int(getattr(c, "score", 0) or 0),
        "is_submitter": bool(getattr(c, "is_submitter", False)),
    }


# --------------------------------------------------------------------------- #
# file I/O                                                                    #
# --------------------------------------------------------------------------- #
def write_community_file(path, meta: dict, posts: list[dict], comments: list[dict]) -> None:
    save_json_data({"meta": meta, "data": {"posts": posts, "comments": comments}}, path, indent=2)


def load_community_file(path):
    """Return (meta, {"posts": [...], "comments": [...]}) if the file exists, else None."""
    if not path.is_file():
        return None
    try:
        obj = load_json_data(path)
        return obj["meta"], obj["data"]
    except (KeyError, ValueError):
        return None


def load_sotd_ids(data_dir, year: int, month: int) -> Optional[Set[str]]:
    """Return SOTD thread IDs for the month, or None when the threads file is absent."""
    path = get_data_dir(data_dir) / "threads" / f"{year:04d}-{month:02d}.json"
    existing = load_month_file(path)
    if existing is None:
        return None
    return {t["id"] for t in existing[1]}
