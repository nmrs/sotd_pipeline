"""
Helpers for reading / writing a month-sized JSON corpus.

File layout:
{
  "meta": {...},
  "data": [{...}]
}
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, List, Tuple


def write_month_file(path: Path, meta: dict[str, Any], data: List[dict[str, Any]]) -> None:
    """Pretty-print *meta* + *data* to *path* (indent-2, UTF-8)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {"meta": meta, "data": data}
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False),
        encoding="utf-8",
    )


def load_month_file(path: Path) -> Tuple[dict[str, Any], List[dict[str, Any]]] | None:  # noqa: D401
    """Return (meta, data) if file exists, else ``None``."""
    if not path.is_file():
        return None
    obj = json.loads(path.read_text(encoding="utf-8"))
    return obj["meta"], obj["data"]
