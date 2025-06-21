"""
Helpers for reading / writing a month-sized JSON corpus.

File layout:
{
  "meta": {...},
  "data": [{...}]
}
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, List, Tuple

from sotd.utils.file_io import load_json_data, save_json_data


def write_month_file(path: Path, meta: dict[str, Any], data: List[dict[str, Any]]) -> None:
    """Pretty-print *meta* + *data* to *path* (indent-2, UTF-8)."""
    payload = {"meta": meta, "data": data}
    save_json_data(payload, path, indent=2)


def load_month_file(path: Path) -> Tuple[dict[str, Any], List[dict[str, Any]]] | None:  # noqa: D401
    """Return (meta, data) if file exists, else ``None``."""
    if not path.is_file():
        return None
    try:
        obj = load_json_data(path)
        return obj["meta"], obj["data"]
    except (KeyError, ValueError):
        # Return None for JSON parsing errors and missing keys
        # This maintains compatibility with existing tests
        return None
    # Let file system errors (PermissionError, OSError) propagate
    # This maintains compatibility with existing tests that expect exceptions
