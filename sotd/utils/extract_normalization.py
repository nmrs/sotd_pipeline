#!/usr/bin/env python3
"""Extraction phase normalization utilities for the SOTD pipeline."""

import re
from typing import Dict, List

from .competition_tags import strip_competition_tags


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

    # Pattern for semantic usage indicators (meaning 1st use) - expanded to include
    # fresh, new blade, etc.
    semantic_patterns = [
        r"(?:[\(\[\{])\s*fresh\s*[\)\]\}]",  # (fresh)
        r"(?:[\(\[\{])\s*new\s+blade\s*[\)\]\}]",  # (new blade)
        r"(?:[\(\[\{])\s*fresh\s+blade\s*[\)\]\}]",  # (fresh blade)
        r"(?:[\(\[\{])\s*brand\s+new\s*[\)\]\}]",  # (brand new)
        r"(?:[\(\[\{])\s*first\s+time\s*[\)\]\}]",  # (first time)
    ]

    for pattern in semantic_patterns:
        cleaned = re.sub(pattern, "", cleaned, flags=re.IGNORECASE)

    # Pattern for location/condition indicators: (Thailand, new), (India), etc.
    # Only match specific location/condition patterns, not all parenthetical content
    location_condition_pattern = (
        r"(?:[\(\[\{])\s*(?:Thailand|India|China|Russia|Turkey|Germany|Japan|USA|UK|"
        r"new|old|vintage|sample|test)(?:\s*,\s*[^\)\]\}]+)*\s*[\)\]\}]"
    )
    cleaned = re.sub(location_condition_pattern, "", cleaned, flags=re.IGNORECASE)

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
    Strip handle-related indicators from razor strings.

    This removes patterns like:
    - Handle indicators: (in handle), (with handle), etc.
    - Handle descriptions: (ebony handle), (wooden handle), etc.

    Args:
        value: Input string that may contain handle indicators

    Returns:
        String with handle indicators removed
    """
    if not isinstance(value, str):
        return value

    # Pattern for handle indicators
    handle_patterns = [
        r"\s*\(in\s+handle\)",
        r"\s*\(with\s+handle\)",
        r"\s*\(.*\s+handle\)",
        r"\s*\(handle.*\)",
    ]

    cleaned = value
    for pattern in handle_patterns:
        cleaned = re.sub(pattern, "", cleaned, flags=re.IGNORECASE)

    # Clean up extra whitespace
    cleaned = re.sub(r"\s+", " ", cleaned).strip()

    return cleaned


def strip_razor_use_counts(value: str) -> str:
    """
    Strip razor use count patterns from razor strings.

    This removes patterns like:
    - Use counts: (3rd use), (5th use), etc.
    - Usage indicators: (used), (worn), etc.

    Args:
        value: Input string that may contain razor use count patterns

    Returns:
        String with razor use count patterns removed
    """
    if not isinstance(value, str):
        return value

    # Pattern for razor use counts
    use_count_patterns = [
        r"\s*\(\d+(?:st|nd|rd|th)\s+use\)",
        r"\s*\(used\)",
        r"\s*\(worn\)",
        r"\s*\(old\)",
    ]

    cleaned = value
    for pattern in use_count_patterns:
        cleaned = re.sub(pattern, "", cleaned, flags=re.IGNORECASE)

    # Clean up extra whitespace
    cleaned = re.sub(r"\s+", " ", cleaned).strip()

    return cleaned


def strip_soap_patterns(value: str) -> str:
    """
    Strip soap-related patterns from soap strings.

    This removes patterns like:
    - Sample indicators: (sample), (tester), etc.
    - Size indicators: (travel size), (mini), etc.

    Args:
        value: Input string that may contain soap-related patterns

    Returns:
        String with soap-related patterns removed
    """
    if not isinstance(value, str):
        return value

    # Pattern for soap-related indicators
    soap_patterns = [
        r"\s*\(sample\)",
        r"\s*\(tester\)",
        r"\s*\(travel\s+size\)",
        r"\s*\(mini\)",
        r"\s*\(small\)",
    ]

    cleaned = value
    for pattern in soap_patterns:
        cleaned = re.sub(pattern, "", cleaned, flags=re.IGNORECASE)

    # Clean up extra whitespace
    cleaned = re.sub(r"\s+", " ", cleaned).strip()

    return cleaned


def strip_link_markup(value: str) -> str:
    """
    Strip link markup from strings.

    This removes patterns like:
    - Markdown links: [text](url)
    - Plain URLs: http://example.com
    - Link indicators: (link), (url), etc.

    Args:
        value: Input string that may contain link markup

    Returns:
        String with link markup removed
    """
    if not isinstance(value, str):
        return value

    # Pattern for markdown links
    markdown_link_pattern = r"\[([^\]]+)\]\([^)]+\)"
    cleaned = re.sub(markdown_link_pattern, r"\1", value)

    # Pattern for plain URLs
    url_pattern = r"https?://[^\s]+"
    cleaned = re.sub(url_pattern, "", cleaned)

    # Pattern for link indicators
    link_indicator_pattern = r"\s*\(link\)|\s*\(url\)"
    cleaned = re.sub(link_indicator_pattern, "", cleaned, flags=re.IGNORECASE)

    # Clean up extra whitespace
    cleaned = re.sub(r"\s+", " ", cleaned).strip()

    return cleaned


def strip_trailing_periods(value: str | None) -> str:
    """
    Strip trailing periods and other punctuation from strings.

    Args:
        value: Input string that may have trailing punctuation

    Returns:
        String with trailing punctuation removed
    """
    if not isinstance(value, str):
        return ""

    # Remove trailing periods, exclamation marks, and question marks
    cleaned = re.sub(r"[\.\!\?]+$", "", value)

    return cleaned.strip()


def normalize_for_matching(
    value: str, competition_tags: Dict[str, List[str]] | None = None, field: str | None = None
) -> str:
    """
    Normalize a string for matching by stripping various patterns.

    This function applies a series of normalization steps to prepare strings
    for matching operations.

    Args:
        value: Input string to normalize
        competition_tags: Competition tags configuration
        field: Field type for field-specific normalization

    Returns:
        Normalized string ready for matching
    """
    if not isinstance(value, str):
        return ""

    # Start with competition tag stripping
    normalized = strip_competition_tags(value, competition_tags)

    # Strip link markup
    normalized = strip_link_markup(normalized)

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

    # Final cleanup
    normalized = re.sub(r"\s+", " ", normalized).strip()

    return normalized


def normalize_for_storage(
    value: str, competition_tags: Dict[str, List[str]] | None = None, field: str | None = None
) -> str:
    """
    Normalize a string for storage by applying matching normalization.

    This function currently applies the same normalization as matching,
    but could be extended with storage-specific normalization in the future.

    Args:
        value: Input string to normalize
        competition_tags: Competition tags configuration
        field: Field type for field-specific normalization

    Returns:
        Normalized string ready for storage
    """
    return normalize_for_matching(value, competition_tags, field)


def normalize_remainder_text(value: str) -> str:
    """
    Normalize remainder text by stripping asterisks, trailing periods, and cleaning up
    separator patterns.

    This function is designed to clean up extraction remainders that may contain
    asterisk separators, trailing punctuation, or other formatting artifacts. Examples:
    - "*****(20)" -> "(20)"
    - "****" -> ""
    - "*** (15)" -> " (15)"
    - "2nd use." -> "2nd use"
    - "3rd use." -> "3rd use"
    - "Normal text (5)" -> "Normal text (5)" (unchanged)

    Args:
        value: Input remainder text that may contain asterisks and trailing punctuation

    Returns:
        Cleaned remainder text with asterisks and trailing punctuation removed
    """
    if not isinstance(value, str):
        return ""

    # Remove all asterisks
    cleaned = value.replace("*", "")

    # Standardize × to x for consistency
    cleaned = cleaned.replace("×", "x")

    # Remove trailing periods and other common trailing punctuation
    cleaned = re.sub(r"[\.\!\?]+$", "", cleaned)

    # Clean up any extra whitespace that might result
    cleaned = re.sub(r"\s+", " ", cleaned)
    cleaned = cleaned.strip()

    return cleaned


def strip_asterisk_markup(value: str) -> str:
    """
    Strip asterisk markup from strings.

    This removes patterns like:
    - Asterisk separators: ****, ***, etc.
    - Asterisk-wrapped text: *text*, **text**, etc.

    Args:
        value: Input string that may contain asterisk markup

    Returns:
        String with asterisk markup removed
    """
    if not isinstance(value, str):
        return value

    # Remove all asterisks and clean up whitespace
    cleaned = value.replace("*", "")
    cleaned = re.sub(r"\s+", " ", cleaned)
    cleaned = cleaned.strip()

    return cleaned
