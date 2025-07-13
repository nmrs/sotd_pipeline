#!/usr/bin/env python3
"""Competition tag utilities for the SOTD pipeline."""

import re
from pathlib import Path
from typing import Dict, List, Optional

import yaml

# Module-level cache for competition tags to avoid repeated file loads
_COMPETITION_TAGS_CACHE: Dict[str, List[str]] | None = None


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
    leading_blade_count_pattern = r"^\s*(?:[\(\[\{])\s*(?:x)?(\d+)(?:x)?\s*[\)\]\}]"
    cleaned = re.sub(leading_blade_count_pattern, "", cleaned, flags=re.IGNORECASE)

    # Pattern for usage count with 'x': (3x), [x3], {2x}, (x4), etc.
    usage_count_x_pattern = r"(?:[\(\[\{])\s*(?:x)?(\d+)(?:x)?\s*[\)\]\}]"
    cleaned = re.sub(usage_count_x_pattern, "", cleaned, flags=re.IGNORECASE)

    # Pattern for "times" usage: (4 times), [5 times], {3 times}, etc.
    usage_times_pattern = r"(?:[\(\[\{])\s*(\d+)\s+times?\s*[\)\]\}]"
    cleaned = re.sub(usage_times_pattern, "", cleaned, flags=re.IGNORECASE)

    # Pattern for ordinal usage: (7th use), [3rd use], {2nd use}, (1st use), (4th use), etc.
    usage_ordinal_pattern = r"(?:[\(\[\{])\s*(\d+)(?:st|nd|rd|th)\s+use\s*[\)\]\}]"
    cleaned = re.sub(usage_ordinal_pattern, "", cleaned, flags=re.IGNORECASE)

    # Pattern for standalone ordinal numbers: (2nd), [3rd], {4th}, etc. (without "use")
    # This pattern must match the full bracket structure to avoid false positives
    standalone_ordinal_pattern = r"(?:[\(\[\{])\s*(\d+)(?:st|nd|rd|th)\s*[\)\]\}]"
    cleaned = re.sub(standalone_ordinal_pattern, "", cleaned, flags=re.IGNORECASE)

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

    # Pattern for "new" (meaning 1st use) - ONLY in parentheses/brackets/braces
    new_pattern = r"(?:[\(\[\{])\s*new\s*[\)\]\}]"
    cleaned = re.sub(new_pattern, "", cleaned, flags=re.IGNORECASE)

    # Special case: remove any double spaces left behind
    cleaned = re.sub(r"\s+", " ", cleaned).strip()

    # Pattern for unknown blade count: (?), [?], {?}
    unknown_count_pattern = r"(?:[\(\[\{])\s*\?\s*[\)\]\}]"
    cleaned = re.sub(unknown_count_pattern, "", cleaned, flags=re.IGNORECASE)

    # Pattern for ordinal use without brackets: 3rd use, 2nd use, etc.
    # Match ordinal use patterns that are standalone or at the end of a string
    ordinal_use_pattern = r"(?:^|\s)(\d+)(?:st|nd|rd|th)\s+use(?:\s|$)"
    cleaned = re.sub(ordinal_use_pattern, "", cleaned, flags=re.IGNORECASE)

    # Pattern for escaped bracket patterns: [2\], [3\], etc.
    escaped_bracket_pattern = r"\[(\d+)\\]"
    cleaned = re.sub(escaped_bracket_pattern, "", cleaned, flags=re.IGNORECASE)

    # Pattern for superscript ordinal patterns: (2^(nd) use), (3^(rd) use), etc.
    superscript_ordinal_pattern = (
        r"(?:[\(\[\{])\s*(\d+)\^\(\s*(?:st|nd|rd|th)\s*\)\s+use\s*[\)\]\}]"
    )
    cleaned = re.sub(superscript_ordinal_pattern, "", cleaned, flags=re.IGNORECASE)

    # Pattern for superscript ordinal patterns without 'use': (2^(nd)), (3^(rd)), etc.
    superscript_ordinal_no_use_pattern = (
        r"(?:[\(\[\{])\s*(\d+)\^\(\s*(?:st|nd|rd|th)\s*\)\s*[\)\]\}]"
    )
    cleaned = re.sub(superscript_ordinal_no_use_pattern, "", cleaned, flags=re.IGNORECASE)

    # Clean up extra whitespace and normalize
    cleaned = re.sub(r"\s+", " ", cleaned)  # Normalize whitespace
    cleaned = cleaned.strip()

    return cleaned


def strip_handle_indicators(value: str) -> str:
    """
    Strip handle swap/modification indicators from razor strings.

    This removes patterns like:
    - "w/ [brand] handle" or "with [brand] handle"
    - "handle: [brand]" or "handle [brand]"
    - "using [brand] handle"
    - "w/ [brand] [model] handle"
    - "Razor / [brand] handle" or "Razor / *[brand]* handle"

    Args:
        value: Input string that may contain handle indicators

    Returns:
        String with handle indicators removed
    """
    if not isinstance(value, str):
        return value

    # Start with the original value
    cleaned = value

    # Pattern for "w/ [brand] handle" or "with [brand] handle"
    handle_pattern = r"\s+(?:w/|with)\s+([^,\s]+(?:\s+[^,\s]+)*?)\s+handle\b"
    cleaned = re.sub(handle_pattern, "", cleaned, flags=re.IGNORECASE)

    # Pattern for "handle: [brand]" or "handle [brand]"
    handle_colon_pattern = r"\s+handle\s*:\s*([^,\s]+(?:\s+[^,\s]+)*?)\b"
    cleaned = re.sub(handle_colon_pattern, "", cleaned, flags=re.IGNORECASE)

    # Pattern for "using [brand] handle"
    using_pattern = r"\s+using\s+([^,\s]+(?:\s+[^,\s]+)*?)\s+handle\b"
    cleaned = re.sub(using_pattern, "", cleaned, flags=re.IGNORECASE)

    # Pattern for "on [brand] handle"
    # (e.g., "Charcoal Goods LVL II SS on Triad Aristocrat SS handle")
    on_handle_pattern = r"\s+on\s+([^,\s]+(?:\s+[^,\s]+)*?)\s+handle\b"
    cleaned = re.sub(on_handle_pattern, "", cleaned, flags=re.IGNORECASE)

    # Pattern for "Razor / [brand] handle" or "Razor / *[brand]* handle"
    slash_handle_pattern = r"\s*/\s*(?:[*`\"']*)?([^,\s]+(?:\s+[^,\s]+)*?)(?:[*`\"']*)?\s+handle\b"
    cleaned = re.sub(slash_handle_pattern, "", cleaned, flags=re.IGNORECASE)

    # Pattern for "[brand] handle / [brand] head" (handle first, then head)
    # (e.g., "EJ DE89 handle / Muhle R41 head")
    handle_first_pattern = (
        r"^([^,\s]+(?:\s+[^,\s]+)*?)\s+handle\s*/\s*([^,\s]+(?:\s+[^,\s]+)*?)\s+head\b"
    )
    cleaned = re.sub(handle_first_pattern, r"\2", cleaned, flags=re.IGNORECASE)

    # Pattern for "[brand] handle with [brand] head" (handle first, then head)
    # (e.g., "EJ DE89 handle with Muhle R41 head")
    handle_first_with_pattern = (
        r"^([^,\s]+(?:\s+[^,\s]+)*?)\s+handle\s+with\s+([^,\s]+(?:\s+[^,\s]+)*?)\s+head\b"
    )
    cleaned = re.sub(handle_first_with_pattern, r"\2", cleaned, flags=re.IGNORECASE)

    # Clean up extra whitespace and normalize
    cleaned = re.sub(r"\s+", " ", cleaned)  # Normalize whitespace
    cleaned = cleaned.strip()

    return cleaned


def strip_razor_use_counts(value: str) -> str:
    """
    Strip use count patterns from razor strings.

    This removes patterns like:
    - "(6)", "(12)", "(23)" - use counts in parentheses
    - "[5]", "[10]" - use counts in brackets
    - "(new)" - new razor indicators
    - Cleans up empty parentheses

    Args:
        value: Input string that may contain use count patterns

    Returns:
        String with use count patterns removed
    """
    if not isinstance(value, str):
        return value

    cleaned = value

    # Remove use counts like (6), (12), (23) anywhere in the string
    cleaned = re.sub(r"\(\d+\)", "", cleaned)

    # Remove use counts like [5], [10] anywhere in the string
    cleaned = re.sub(r"\[\d+\]", "", cleaned)

    # Remove new razor indicators like (new)
    cleaned = re.sub(r"\(\s*new\s*\)", "", cleaned, flags=re.IGNORECASE)

    # Clean up empty parentheses left behind
    cleaned = re.sub(r"\(\s*\)", "", cleaned)

    # Clean up extra whitespace and normalize
    cleaned = re.sub(r"\s+", " ", cleaned)
    cleaned = cleaned.strip()

    return cleaned


# --- CANONICAL NORMALIZATION FUNCTION ---
# All correct match lookups in the SOTD Pipeline must use this function.
# See docs/product_matching_validation.md for details and examples.


def strip_trailing_periods(value: str | None) -> str:
    """
    Strip trailing periods from a string.

    This removes periods that appear at the end of strings, which are common
    in SOTD comments where users end their product listings with periods.

    Args:
        value: Input string that may have trailing periods

    Returns:
        String with trailing periods removed, or empty string if input is None
    """
    if not isinstance(value, str):
        return ""

    # Remove trailing periods and any trailing whitespace
    cleaned = re.sub(r"\.\s*$", "", value)
    # Also strip any remaining trailing whitespace
    cleaned = cleaned.rstrip()
    return cleaned


def normalize_for_matching(
    value: str, competition_tags: Dict[str, List[str]] | None = None, field: str | None = None
) -> str:
    """
    Canonical normalization function for correct match lookups.

    This is the single source of truth for normalizing strings when performing
    correct match lookups in matchers, analyzers, and any other consumers.
    All components must use this function to ensure consistent normalization.

    - Strips competition tags and normalizes whitespace to prevent bloat and duplicates in the file.
    - Strips trailing periods that are common in SOTD comments.
    - For blades only, strips blade count/usage patterns (including 'new' as usage).
    - For razors only, strips handle swap/modification indicators.
    - For soaps only, strips soap-related patterns (sample, puck, croap, cream, etc.).
    - Preserves case to maintain consistency with stored correct_matches.yaml entries.

    Args:
        value: Input string to normalize
        competition_tags: Competition tags configuration. If None, loads from file.
        field: The product field (e.g., 'blade', 'razor', 'soap', etc.)

    Returns:
        Normalized string ready for correct match lookups

    Note:
        This function replaces normalize_for_storage() and should be used by all
        components that perform correct match lookups to ensure consistency.
    """
    if not isinstance(value, str):
        return ""

    # Strip competition tags and normalize
    normalized = strip_competition_tags(value, competition_tags)

    # Strip trailing periods (common in SOTD comments)
    normalized = strip_trailing_periods(normalized)

    # For blade strings, also strip blade count and usage patterns (including 'new')
    if field == "blade":
        normalized = strip_blade_count_patterns(normalized)

    # For razor strings, also strip handle indicators and use counts
    if field == "razor":
        normalized = strip_handle_indicators(normalized)
        normalized = strip_razor_use_counts(normalized)

    # For soap strings, also strip soap-related patterns
    if field == "soap":
        normalized = strip_soap_patterns(normalized)

    return normalized


def strip_soap_patterns(value: str) -> str:
    """
    Strip soap-related patterns from soap strings.

    This removes patterns like:
    - "soap", "puck", "croap", "cream", "shaving soap", "shaving cream"
      (at the end or surrounded by whitespace/punctuation)
    - Sample markers like "(sample)" or "sample" at the end
    - Use counts like "(23)" anywhere in the string
    - Cleans up empty parentheses

    Args:
        value: Input string that may contain soap-related patterns

    Returns:
        String with soap-related patterns removed
    """
    if not isinstance(value, str):
        return value

    cleaned = value
    original = value

    # Remove sample markers like (sample) (case-insensitive)
    cleaned = re.sub(r"\(\s*sample\s*\)", "", cleaned, flags=re.IGNORECASE)

    # Remove use counts like (23) anywhere in the string
    cleaned = re.sub(r"\(\d+\)", "", cleaned)

    # Remove soap-related suffixes at the end (with optional whitespace/punctuation)
    cleaned = re.sub(
        r"[\s\-_/,:;]*(soap( sample)?|croap|puck|cream|shav.*soap|shav.*cream)[\s\-_/,:;]*$",
        "",
        cleaned,
        flags=re.IGNORECASE,
    )
    # Remove croap/puck/cream/soap as last word, even if surrounded by whitespace or punctuation
    cleaned = re.sub(
        r"[\s\-_/,:;]*(croap|puck|cream|soap)[\s\-_/,:;]*$",
        "",
        cleaned,
        flags=re.IGNORECASE,
    )
    # Remove 'sample' only if at the end (not in the middle)
    cleaned = re.sub(
        r"[\s\-_/,:;]*sample[\s\-_/,:;]*$",
        "",
        cleaned,
        flags=re.IGNORECASE,
    )
    # Clean up empty parentheses left behind
    cleaned = re.sub(r"\(\s*\)", "", cleaned)
    # Remove croap/puck/cream/soap as last word again after cleaning up parentheses
    cleaned = re.sub(
        r"[\s\-_/,:;]*(croap|puck|cream|soap)[\s\-_/,:;]*$",
        "",
        cleaned,
        flags=re.IGNORECASE,
    )
    # Clean up extra whitespace and normalize
    cleaned = re.sub(r"\s+", " ", cleaned)
    cleaned = cleaned.strip()
    # If result is empty and original started with 'soap', return 'soap'
    if not cleaned and original.strip().lower().startswith("soap"):
        return "soap"
    return cleaned


# --- DEPRECATED: DO NOT USE ---
# This function is retained for backward compatibility only.
# All new code must use normalize_for_matching. See docs/product_matching_validation.md.
def normalize_for_storage(
    value: str, competition_tags: Dict[str, List[str]] | None = None, field: str | None = None
) -> str:
    """
    Deprecated: Use normalize_for_matching() instead.

    This function is kept for backward compatibility but should be replaced
    with normalize_for_matching() in all new code.

    For backward compatibility, this function automatically detects field type
    based on content patterns when field is not specified:
    - Contains blade patterns (3x), (new), etc. -> blade field
    - Contains handle indicators (/ [brand] handle) -> razor field
    - Contains soap patterns (sample, puck, croap) -> soap field
    """
    import warnings

    warnings.warn(
        "normalize_for_storage() is deprecated, use normalize_for_matching() instead",
        DeprecationWarning,
        stacklevel=2,
    )

    # Auto-detect field type for backward compatibility
    if field is None and isinstance(value, str):
        # Check for blade patterns
        # Define ordinal words for word-based patterns
        ordinal_words = (
            "first|second|third|fourth|fifth|sixth|seventh|eighth|ninth|tenth|"
            "eleventh|twelfth|thirteenth|fourteenth|fifteenth|sixteenth|"
            "seventeenth|eighteenth|nineteenth|twentieth"
        )
        blade_patterns = [
            r"\(\d+x?\)",
            r"\[\d*x?\]",
            r"\{\d*x?\}",  # (3x), [x3], {2x}
            r"\(\d+\s+times?\)",
            r"\[\d+\s+times?\]",
            r"\{\d+\s+times?\}",  # (4 times)
            r"\(\d+(?:st|nd|rd|th)\s+use\)",
            r"\[\d+(?:st|nd|rd|th)\s+use\]",  # (7th use)
            r"\(\s*new\s*\)",
            r"\[\s*new\s*\]",
            r"\{\s*new\s*\}",  # (new)
            r"\bnew\b",  # standalone "new"
            r"\d+(?:st|nd|rd|th)\s+use\b",  # 3rd use
            r"x\d+",
            r"\d+x",  # x4, 2x
            # Word-based ordinal patterns
            r"\(\s*(" + ordinal_words + r")\s+use\s*\)",
            r"\[\s*(" + ordinal_words + r")\s+use\s*\]",
            r"\{\s*(" + ordinal_words + r")\s+use\s*\}",
        ]
        for pattern in blade_patterns:
            if re.search(pattern, value, re.IGNORECASE):
                field = "blade"
                break

        # Check for razor handle indicators
        if field is None:
            handle_patterns = [
                r"/\s*\[.*?\]\s*handle",
                r"with\s+\[.*?\]\s*handle",
                r"handle\s+swap",
                r"handle\s+modification",
            ]
            for pattern in handle_patterns:
                if re.search(pattern, value, re.IGNORECASE):
                    field = "razor"
                    break

        # Check for soap patterns
        if field is None:
            soap_patterns = [
                r"\(\s*sample\s*\)",
                r"\bsample\b",
                r"\bpuck\b",
                r"\bcroap\b",
                r"\bcream\b",
                r"shav.*soap",
                r"shav.*cream",
            ]
            for pattern in soap_patterns:
                if re.search(pattern, value, re.IGNORECASE):
                    field = "soap"
                    break

    return normalize_for_matching(value, competition_tags, field)


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

    # Pattern 3.5: (2nd), [3rd], {4th}, etc. (standalone ordinal numbers)
    pattern3_5 = r"(?:[\(\[\{])\s*(\d+)(?:st|nd|rd|th)\s*[\)\]\}]"
    match = re.search(pattern3_5, text, re.IGNORECASE)
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

    # Pattern 10: superscript ordinal patterns: (2^(nd) use), (3^(rd) use), etc.
    superscript_ordinal_pattern = (
        r"(?:[\(\[\{])\s*(\d+)\^\(\s*(?:st|nd|rd|th)\s*\)\s+use\s*[\)\]\}]"
    )
    match = re.search(superscript_ordinal_pattern, text, re.IGNORECASE)
    if match:
        return int(match.group(1))

    # Pattern 11: superscript ordinal patterns without "use": (2^(nd)), (3^(rd)), etc.
    superscript_ordinal_no_use_pattern = (
        r"(?:[\(\[\{])\s*(\d+)\^\(\s*(?:st|nd|rd|th)\s*\)\s*[\)\]\}]"
    )
    match = re.search(superscript_ordinal_no_use_pattern, text, re.IGNORECASE)
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
