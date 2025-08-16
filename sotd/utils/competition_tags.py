#!/usr/bin/env python3
"""Competition tag utilities for the SOTD pipeline."""

import re
from pathlib import Path
from typing import Dict, List

import yaml

# Module-level cache for competition tags to avoid repeated file loads
_COMPETITION_TAGS_CACHE: Dict[str, List[str]] | None = None


def clear_competition_tags_cache() -> None:
    """Clear the competition tags cache to force reload from file."""
    global _COMPETITION_TAGS_CACHE
    _COMPETITION_TAGS_CACHE = None


def load_competition_tags(tags_path: Path | None = None) -> Dict[str, List[str]]:
    """
    Load competition tags configuration from YAML file.

    Args:
        tags_path: Path to competition tags file. Defaults to data/competition_tags.yaml.

    Returns:
        Dictionary with 'strip_tags' and 'preserve_tags' lists.
    """
    global _COMPETITION_TAGS_CACHE

    # Return cached result if available
    if _COMPETITION_TAGS_CACHE is not None:
        return _COMPETITION_TAGS_CACHE

    if tags_path is None:
        tags_path = Path("data/competition_tags.yaml")

    if not tags_path.exists():
        _COMPETITION_TAGS_CACHE = {"strip_tags": [], "preserve_tags": []}
        return _COMPETITION_TAGS_CACHE

    try:
        with tags_path.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        _COMPETITION_TAGS_CACHE = {
            "strip_tags": data.get("strip_tags", []),
            "preserve_tags": data.get("preserve_tags", []),
        }
        return _COMPETITION_TAGS_CACHE
    except Exception:
        # If tags file is corrupted or can't be loaded, continue without it
        _COMPETITION_TAGS_CACHE = {"strip_tags": [], "preserve_tags": []}
        return _COMPETITION_TAGS_CACHE


def strip_competition_tags(value: str, competition_tags: Dict[str, List[str]] | None = None) -> str:
    """
    Strip competition tags from a string while preserving useful ones.

    Args:
        value: Input string that may contain competition tags
        competition_tags: Configuration of tags to strip/preserve. If None, loads from file.

    Returns:
        String with unwanted competition tags removed
    """
    if not isinstance(value, str):
        return value

    # Load competition tags if not provided
    if competition_tags is None:
        competition_tags = load_competition_tags()

    # Get tags to strip and preserve
    strip_tags = competition_tags.get("strip_tags", [])
    preserve_tags = competition_tags.get("preserve_tags", [])

    if not strip_tags:
        return value

    # Create a list of tags to actually strip (exclude preserve_tags)
    tags_to_strip = [tag for tag in strip_tags if tag not in preserve_tags]

    if not tags_to_strip:
        return value

    # Build regex pattern to match tags with word boundaries
    # This ensures we match whole tags, not partial matches
    # Also handle tags that might be wrapped in backticks or asterisks
    # Match both $ and # prefixes for competition tags
    strip_pattern = r"[`*]*[\$#](" + "|".join(re.escape(tag) for tag in tags_to_strip) + r")\b[`*]*"

    # Remove the tags and clean up extra whitespace
    cleaned = re.sub(strip_pattern, "", value, flags=re.IGNORECASE)
    cleaned = re.sub(r"\s+", " ", cleaned)  # Normalize whitespace
    cleaned = cleaned.strip()

    return cleaned
