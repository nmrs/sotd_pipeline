#!/usr/bin/env python3
"""Competition tag utilities for the SOTD pipeline."""

import re
from pathlib import Path
from typing import Dict, List

import yaml


def load_competition_tags(tags_path: Path | None = None) -> Dict[str, List[str]]:
    """
    Load competition tags configuration from YAML file.

    Args:
        tags_path: Path to competition tags file. Defaults to data/competition_tags.yaml.

    Returns:
        Dictionary with 'strip_tags' and 'preserve_tags' lists.
    """
    if tags_path is None:
        tags_path = Path("data/competition_tags.yaml")

    if not tags_path.exists():
        return {"strip_tags": [], "preserve_tags": []}

    try:
        with tags_path.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        return {
            "strip_tags": data.get("strip_tags", []),
            "preserve_tags": data.get("preserve_tags", []),
        }
    except Exception:
        # If tags file is corrupted or can't be loaded, continue without it
        return {"strip_tags": [], "preserve_tags": []}


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


def normalize_for_storage(value: str, competition_tags: Dict[str, List[str]] | None = None) -> str:
    """
    Normalize a string for storage in correct_matches.yaml.

    This strips competition tags and normalizes whitespace to prevent
    bloat and duplicates in the file.

    Args:
        value: Input string to normalize
        competition_tags: Competition tags configuration. If None, loads from file.

    Returns:
        Normalized string ready for storage
    """
    if not isinstance(value, str):
        return value

    # Strip competition tags and normalize
    normalized = strip_competition_tags(value, competition_tags)

    return normalized
