"""Manual include / exclude overrides for SOTD thread discovery.

The JSON file ``overrides/sotd_thread_overrides.json`` must follow:

{
  "include": [
    {"id": "t3_abc123", "title": "...", "url": "...", "reason": "optional"}
  ],
  "exclude": [
    {"id": "t3_def456", "title": "...", "url": "..."}
  ]
}
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Sequence, Tuple

logger = logging.getLogger(__name__)

import praw
from praw.models import Submission
from prawcore.exceptions import NotFound

from sotd.fetch.reddit import filter_valid_threads, safe_call

# ruff: noqa: E402


OVERRIDE_PATH = Path("overrides/sotd_thread_overrides.json")


# ------------------------------------------------------------------ #
# Loader                                                             #
# ------------------------------------------------------------------ #
def load_overrides(
    path: Path = OVERRIDE_PATH,
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """
    Return ``(include_by_id, exclude_by_id)``.

    Dicts are empty when *path* does not exist or is malformed.
    """
    if not path.is_file():
        return {}, {}

    try:
        obj = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        # Log-friendly error; propagate up
        raise RuntimeError(f"Invalid JSON in overrides file: {path}") from None

    include = {e["id"]: e for e in obj.get("include", []) if "id" in e}
    exclude = {e["id"]: e for e in obj.get("exclude", []) if "id" in e}
    return include, exclude


# ------------------------------------------------------------------ #
# Apply                                                              #
# ------------------------------------------------------------------ #
def apply_overrides(
    threads: Sequence[Submission],
    include: Dict[str, Any],
    exclude: Dict[str, Any],
    *,
    reddit: praw.Reddit,
    year: int,
    month: int,
    debug: bool = False,
) -> List[Submission]:
    """
    Apply *include* / *exclude* to *threads* list.

    • Remove any thread whose ID appears in *exclude*
    • Add each *include* ID not already present using ``reddit.submission``
    • Return list deduplicated and sorted via :func:`filter_valid_threads`
    """
    # 1️⃣ apply exclusion
    kept: List[Submission] = [t for t in threads if t.id not in exclude]

    # 2️⃣ apply inclusion
    present_ids = {t.id for t in kept}
    for tid in include:
        if tid in present_ids:
            continue
        try:
            sub = safe_call(reddit.submission, tid)
            if sub is not None:
                kept.append(sub)
                present_ids.add(tid)
                if debug:
                    logger.debug(f"Override include added {tid}")
            else:
                if debug:
                    logger.warning(f"Override include id {tid} could not be fetched (None)")
        except NotFound:
            if debug:
                logger.warning(f"Override include id {tid} not found")

    # 3️⃣ deduplicate (should be no dups now) & sort by parsed date
    unique: Dict[str, Submission] = {t.id: t for t in kept}
    return filter_valid_threads(list(unique.values()), year, month, debug=False)
