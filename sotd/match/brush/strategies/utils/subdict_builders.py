"""Factory functions for building handle/knot sub-dicts.

These helpers eliminate the repeated inline construction of
``{"handle": {...}, "knot": {...}}`` dicts across 10+ call sites.

Two shapes exist:
  * **Minimal** — only positional args (brand, model, …).
  * **Rich**    — positional + keyword metadata (source_text, matched_by, pattern, priority).

Metadata keys are only included when non-None, keeping minimal dicts clean.
"""

from typing import Any, Optional


def build_handle_subdict(
    brand: Optional[str],
    model: Optional[str],
    *,
    source_text: Optional[str] = None,
    matched_by: Optional[str] = None,
    pattern: Optional[str] = None,
    priority: Optional[Any] = None,
) -> dict:
    """Build a handle sub-dict, omitting None-valued metadata keys."""
    d: dict[str, Any] = {
        "brand": brand,
        "model": model,
    }
    if source_text is not None:
        d["source_text"] = source_text
    if matched_by is not None:
        d["_matched_by"] = matched_by
    if pattern is not None:
        d["_pattern"] = pattern
    if priority is not None:
        d["priority"] = priority
    return d


def build_knot_subdict(
    brand: Optional[str],
    model: Optional[str],
    fiber: Optional[str] = None,
    knot_size_mm: Optional[float] = None,
    *,
    source_text: Optional[str] = None,
    matched_by: Optional[str] = None,
    pattern: Optional[str] = None,
    priority: Optional[Any] = None,
) -> dict:
    """Build a knot sub-dict, omitting None-valued metadata keys."""
    d: dict[str, Any] = {
        "brand": brand,
        "model": model,
        "fiber": fiber,
        "knot_size_mm": knot_size_mm,
    }
    if source_text is not None:
        d["source_text"] = source_text
    if matched_by is not None:
        d["_matched_by"] = matched_by
    if pattern is not None:
        d["_pattern"] = pattern
    if priority is not None:
        d["priority"] = priority
    return d
