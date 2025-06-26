#!/usr/bin/env python3
"""Competition tag utilities for the SOTD pipeline."""

import re
from pathlib import Path
from typing import Dict, List, Optional

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


def strip_blade_count_patterns(value: str) -> str:
    """
    Strip blade count and usage count patterns from blade strings.

    This removes patterns like:
    - Blade count: [2x], (2x), {2x}, [X2], (x2), etc. at the start
    - Usage count: (3x), [x3], (4 times), {7th use}, (second use), etc.
    - Standalone: x4, 2x without brackets
    - Special patterns: "new" (meaning 1st use), "3rd use", "[2\\]", etc.

    Args:
        value: Input string that may contain blade count/usage patterns

    Returns:
        String with blade count and usage patterns removed
    """
    if not isinstance(value, str):
        return value

    # Start with the original value
    cleaned = value

    # Pattern for leading blade count: e.g. [2x], (2x), {2x}, [X2], (x2), etc.
    leading_blade_count_pattern = r"^\s*(?:[\(\[\{])\s*(?:x)?(\d+)(?:x)?\s*[\)\]\}]\s*"
    cleaned = re.sub(leading_blade_count_pattern, "", cleaned, flags=re.IGNORECASE)

    # Pattern for usage count with 'x': (3x), [x3], {2x}, (x4), etc.
    usage_count_x_pattern = r"(?:[\(\[\{])\s*(?:x)?(\d+)(?:x)?\s*[\)\]\}]"
    cleaned = re.sub(usage_count_x_pattern, "", cleaned, flags=re.IGNORECASE)

    # Pattern for "times" usage: (4 times), [5 times], {3 times}, (1 time), etc.
    usage_times_pattern = r"(?:[\(\[\{])\s*(\d+)\s+times?\s*[\)\]\}]"
    cleaned = re.sub(usage_times_pattern, "", cleaned, flags=re.IGNORECASE)

    # Pattern for ordinal usage: (7th use), [3rd use], {2nd use}, (1st use), (4th use), etc.
    usage_ordinal_pattern = r"(?:[\(\[\{])\s*(\d+)(?:st|nd|rd|th)\s+use\s*[\)\]\}]"
    cleaned = re.sub(usage_ordinal_pattern, "", cleaned, flags=re.IGNORECASE)

    # Pattern for word-based ordinal usage: (second use), [third use], {fourth use}, etc.
    usage_word_pattern = (
        r"(?:[\(\[\{])\s*(first|second|third|fourth|fifth|sixth|seventh|eighth|"
        r"ninth|tenth|eleventh|twelfth|thirteenth|fourteenth|fifteenth|sixteenth|"
        r"seventeenth|eighteenth|nineteenth|twentieth)\s+use\s*[\)\]\}]"
    )
    cleaned = re.sub(usage_word_pattern, "", cleaned, flags=re.IGNORECASE)

    # Pattern for standalone usage: x4, 2x without brackets
    standalone_pattern = r"\b(?:x(\d+)|(\d+)x)\b"
    cleaned = re.sub(standalone_pattern, "", cleaned, flags=re.IGNORECASE)

    # Pattern for "new" (meaning 1st use) - standalone word or in parentheses
    new_pattern = r"(?:[\(\[\{])\s*new\s*[\)\]\}]|\bnew\b"
    cleaned = re.sub(new_pattern, "", cleaned, flags=re.IGNORECASE)

    # Pattern for ordinal use without brackets: 3rd use, 2nd use, etc.
    ordinal_use_pattern = r"\b(\d+)(?:st|nd|rd|th)\s+use\b"
    cleaned = re.sub(ordinal_use_pattern, "", cleaned, flags=re.IGNORECASE)

    # Pattern for escaped bracket patterns: [2\], [3\], etc.
    escaped_bracket_pattern = r"\[(\d+)\\]"
    cleaned = re.sub(escaped_bracket_pattern, "", cleaned, flags=re.IGNORECASE)

    # Clean up extra whitespace and normalize
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

    # For blade strings, also strip blade count and usage patterns
    # This prevents bloat in correct_matches.yaml by removing patterns like (3x), [2x], etc.
    # Note: We can't easily detect if this is a blade string here, so we'll apply it generally
    # The blade enricher will handle the actual extraction of counts
    normalized = strip_blade_count_patterns(normalized)

    return normalized


def extract_blade_use_count(text: str) -> Optional[int]:
    """
    Extract blade use count from various patterns in text.

    This function recognizes all the patterns that the blade enricher currently handles,
    plus the new patterns we've added for normalization.

    Args:
        text: Input string that may contain blade use count patterns

    Returns:
        The use count as an integer, or None if no pattern is found
    """
    if not isinstance(text, str) or not text:
        return None

    # Pattern 1: (3x), [x3], {2x}, etc.
    pattern1 = r"(?:[\(\[\{])\s*(?:x)?(\d+)(?:x)?\s*[\)\]\}]"
    match = re.search(pattern1, text, re.IGNORECASE)
    if match:
        return int(match.group(1))

    # Pattern 2: (4 times), [5 times], {3 times}, etc.
    pattern2 = r"(?:[\(\[\{])\s*(\d+)\s+times?\s*[\)\]\}]"
    match = re.search(pattern2, text, re.IGNORECASE)
    if match:
        return int(match.group(1))

    # Pattern 3: (7th use), [3rd use], {2nd use}, etc.
    pattern3 = r"(?:[\(\[\{])\s*(\d+)(?:st|nd|rd|th)\s+use\s*[\)\]\}]"
    match = re.search(pattern3, text, re.IGNORECASE)
    if match:
        return int(match.group(1))

    # Pattern 4: (second use), [third use], {fourth use}, etc.
    ordinal_words = {
        "first": 1,
        "second": 2,
        "third": 3,
        "fourth": 4,
        "fifth": 5,
        "sixth": 6,
        "seventh": 7,
        "eighth": 8,
        "ninth": 9,
        "tenth": 10,
        "eleventh": 11,
        "twelfth": 12,
        "thirteenth": 13,
        "fourteenth": 14,
        "fifteenth": 15,
        "sixteenth": 16,
        "seventeenth": 17,
        "eighteenth": 18,
        "nineteenth": 19,
        "twentieth": 20,
    }
    pattern4 = r"(?:[\(\[\{])\s*(" + "|".join(ordinal_words.keys()) + r")\s+use\s*[\)\]\}]"
    match = re.search(pattern4, text, re.IGNORECASE)
    if match:
        ordinal = match.group(1).lower()
        return ordinal_words.get(ordinal)

    # Pattern 5: (use 3), [use 5], {use 2}, etc.
    pattern5 = r"(?:[\(\[\{])\s*use\s+(\d+)\s*[\)\]\}]"
    match = re.search(pattern5, text, re.IGNORECASE)
    if match:
        return int(match.group(1))

    # Pattern 6: x4, 2x (standalone patterns without brackets)
    pattern6 = r"(?:^|\s)(?:x)?(\d+)(?:x)?(?:\s|$)"
    match = re.search(pattern6, text, re.IGNORECASE)
    if match:
        return int(match.group(1))

    # Pattern 7: "new" (meaning 1st use) - standalone word or in parentheses
    new_pattern = r"(?:[\(\[\{])\s*new\s*[\)\]\}]|\bnew\b"
    if re.search(new_pattern, text, re.IGNORECASE):
        return 1

    # Pattern 8: ordinal use without brackets: 3rd use, 2nd use, etc.
    ordinal_use_pattern = r"\b(\d+)(?:st|nd|rd|th)\s+use\b"
    match = re.search(ordinal_use_pattern, text, re.IGNORECASE)
    if match:
        return int(match.group(1))

    # Pattern 9: escaped bracket patterns: [2\], [3\], etc.
    escaped_bracket_pattern = r"\[(\d+)\\]"
    match = re.search(escaped_bracket_pattern, text, re.IGNORECASE)
    if match:
        return int(match.group(1))

    return None


def extract_blade_count(text: str) -> Optional[int]:
    """
    Extract blade count (number of blades) from text.

    This looks for patterns at the very beginning of the text that indicate
    multiple blades are loaded.

    Args:
        text: Input string that may contain blade count patterns

    Returns:
        The blade count as an integer, or None if no pattern is found
    """
    if not isinstance(text, str) or not text:
        return None

    # Pattern for leading blade count: e.g. [2x], (2x), {2x}, [X2], (x2), etc.
    leading_blade_count_pattern = r"^\s*(?:[\(\[\{])\s*(?:x)?(\d+)(?:x)?\s*[\)\]\}]"
    match = re.match(leading_blade_count_pattern, text, re.IGNORECASE)
    if match:
        return int(match.group(1))

    return None


def extract_blade_and_use_count(text: str) -> tuple[Optional[int], Optional[int]]:
    """
    Extract both blade count and use count from text.

    This is a convenience function that combines extract_blade_count and extract_blade_use_count.
    It handles the case where a leading blade count should be stripped before looking for use count.

    Args:
        text: Input string that may contain blade count and use count patterns

    Returns:
        Tuple of (blade_count, use_count), where each can be None
    """
    if not isinstance(text, str) or not text:
        return None, None

    # First extract blade count from the beginning
    blade_count = extract_blade_count(text)

    # If we found a blade count, strip it from the front before looking for use count
    if blade_count is not None:
        # Strip the leading blade count pattern
        leading_blade_count_pattern = r"^\s*(?:[\(\[\{])\s*(?:x)?(\d+)(?:x)?\s*[\)\]\}]"
        stripped = re.sub(leading_blade_count_pattern, "", text, flags=re.IGNORECASE)
        stripped = stripped.strip()
        use_count = extract_blade_use_count(stripped)
    else:
        # No blade count found, look for use count in the original text
        use_count = extract_blade_use_count(text)

    return blade_count, use_count
