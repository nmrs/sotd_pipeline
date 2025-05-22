"""Deduplicate records by *id*, keeping newest ``created_utc``."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List


def _iso_to_dt(iso: str) -> datetime:
    return datetime.fromisoformat(iso.replace("Z", "+00:00")).astimezone(timezone.utc)


def merge_records(existing: List[dict], new: List[dict]) -> List[dict]:
    """
    Merge *new* onto *existing* by ``id``.

    • For duplicates, keep record whose ``created_utc`` is later.
    • Return list sorted by ``created_utc`` ascending.
    """
    bucket: Dict[str, dict[str, Any]] = {r["id"]: r for r in existing}
    for rec in new:
        rid = rec["id"]
        if rid not in bucket or _iso_to_dt(rec["created_utc"]) > _iso_to_dt(
            bucket[rid]["created_utc"]
        ):
            bucket[rid] = rec
    return sorted(bucket.values(), key=lambda r: r["created_utc"])
