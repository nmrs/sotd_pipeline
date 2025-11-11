#!/usr/bin/env python3
"""Shared regex patterns for blade use count extraction and normalization."""

import re
from typing import Pattern


def get_incomplete_usage_pattern() -> Pattern[str]:
    """
    Get regex pattern for incomplete usage counts: (1, [2, {3, etc. (missing closing bracket)

    This pattern matches incomplete parentheses/brackets/braces with numbers that are likely
    blade use counts, but only when we're confident they're actually incomplete (at end of string
    or followed by space and end of string). This prevents matching legitimate specifications
    like "(27 mm × 51 mm Manchurian badger)".

    Returns:
        Compiled regex pattern for incomplete usage counts
    """
    return re.compile(r"(?:[\(\[\{])\s*(?!19\d{2}|20\d{2})\d+\s*$")


def get_complete_usage_pattern() -> Pattern[str]:
    """
    Get regex pattern for complete usage counts: (1), [2], {3}, etc.

    This pattern matches complete parentheses/brackets/braces with numbers that are likely
    blade use counts, excluding 4-digit numbers that are likely years (1900-2099).

    Returns:
        Compiled regex pattern for complete usage counts
    """
    return re.compile(r"(?:[\(\[\{])\s*(?!19\d{2}|20\d{2})\d+\s*[\)\]\}]")


def get_usage_x_pattern() -> Pattern[str]:
    """
    Get regex pattern for usage counts with 'x': (2x), (3x), [4x], etc.

    Returns:
        Compiled regex pattern for usage counts with 'x'
    """
    return re.compile(r"(?:[\(\[\{])\s*\d+x\s*[\)\]\}]")


def get_usage_x_prefix_pattern() -> Pattern[str]:
    """
    Get regex pattern for usage counts with 'x' prefix: (x2), (x3), [x4], etc.

    Returns:
        Compiled regex pattern for usage counts with 'x' prefix
    """
    return re.compile(r"(?:[\(\[\{])\s*x\d+\s*[\)\]\}]")


def get_usage_use_pattern() -> Pattern[str]:
    """
    Get regex pattern for usage counts with 'use': (1 use), (2 use), etc.

    Returns:
        Compiled regex pattern for usage counts with 'use'
    """
    return re.compile(r"(?:[\(\[\{])\s*\d+\s+use\s*[\)\]\}]", re.IGNORECASE)


def get_usage_uses_pattern() -> Pattern[str]:
    """
    Get regex pattern for usage counts with 'uses': (107 uses), (108 uses), etc.

    Returns:
        Compiled regex pattern for usage counts with 'uses'
    """
    return re.compile(r"(?:[\(\[\{])\s*\d+\s+uses\s*[\)\]\}]", re.IGNORECASE)


def get_ordinal_shave_pattern() -> Pattern[str]:
    """
    Get regex pattern for ordinal usage: (1st shave), (2nd shave), (10th shave), etc.

    Returns:
        Compiled regex pattern for ordinal shave usage
    """
    return re.compile(r"(?:[\(\[\{])\s*\d+(?:st|nd|rd|th)\s+shave\s*[\)\]\}]", re.IGNORECASE)


def get_ordinal_pattern() -> Pattern[str]:
    """
    Get regex pattern for ordinal usage: (1st), (2nd), (10th), etc.

    Returns:
        Compiled regex pattern for ordinal usage
    """
    return re.compile(r"(?:[\(\[\{])\s*\d+(?:st|nd|rd|th)\s*[\)\]\}]", re.IGNORECASE)


def get_superscript_ordinal_pattern() -> Pattern[str]:
    """
    Get regex pattern for superscript ordinal usage: (2^(nd)), (3^(rd)), (1^(st)), etc.
    Also handles patterns like (2^(nd) use), (3^(rd) use), etc.

    Returns:
        Compiled regex pattern for superscript ordinal usage
    """
    return re.compile(
        r"(?:[\(\[\{])\s*\d+\^?\(?(?:st|nd|rd|th)\)?" r"(?:\s+[^\)\]\}]+)?\s*[\)\]\}]",
        re.IGNORECASE,
    )


def get_completion_pattern() -> Pattern[str]:
    """
    Get regex pattern for completion indicators: (1 and done), (1 and last), (1st and final), etc.

    Returns:
        Compiled regex pattern for completion indicators
    """
    return re.compile(
        r"(?:[\(\[\{])\s*\d+(?:st|nd|rd|th)?(?:\s+[^\)\]\}]+)?\s+"
        r"(?:and\s+(?:done|last|final|probably\s+last))\s*[\)\]\}]",
        re.IGNORECASE,
    )


def get_speculation_pattern() -> Pattern[str]:
    """
    Get regex pattern for user speculation: (10 I think), (3 I think),
    (7, I think), (30+ I think), etc.

    Returns:
        Compiled regex pattern for user speculation
    """
    return re.compile(r"(?:[\(\[\{])\s*\d+[+,\s]+\s*I\s+think\s*[\)\]\}]", re.IGNORECASE)


def get_speculation_question_pattern() -> Pattern[str]:
    """
    Get regex pattern for user speculation with question marks: (5? I think), etc.

    Returns:
        Compiled regex pattern for user speculation with question marks
    """
    return re.compile(r"(?:[\(\[\{])\s*\d+\?\s*I\s+think\s*[\)\]\}]", re.IGNORECASE)


def get_complex_usage_pattern() -> Pattern[str]:
    """
    Get regex pattern for complex usage descriptions: (10+?; At least four months old), etc.

    Returns:
        Compiled regex pattern for complex usage descriptions
    """
    return re.compile(r"(?:[\(\[\{])\s*\d+\+?\?[^\)\]\}]*[\)\]\}]", re.IGNORECASE)


def get_celebration_pattern() -> Pattern[str]:
    """
    Get regex pattern for celebration patterns: (100...woohoo!), etc.

    Returns:
        Compiled regex pattern for celebration patterns
    """
    return re.compile(r"(?:[\(\[\{])\s*\d+\.{3}[^\)\]\}]*[\)\]\}]", re.IGNORECASE)


def get_partial_usage_pattern() -> Pattern[str]:
    """
    Get regex pattern for partial usage: (<1 and done), etc.

    Returns:
        Compiled regex pattern for partial usage
    """
    return re.compile(r"(?:[\(\[\{])\s*<\s*\d+\s+and\s+done\s*[\)\]\}]", re.IGNORECASE)


def get_location_condition_pattern() -> Pattern[str]:
    """
    Get regex pattern for location/condition indicators: (Thailand, new), (India), etc.
    Only matches specific location/condition patterns, not all parenthetical content.

    Returns:
        Compiled regex pattern for location/condition indicators
    """
    return re.compile(
        r"(?:[\(\[\{])\s*(?:Thailand|India|China|Russia|Turkey|Germany|Japan|USA|UK|"
        r"new|old|vintage|sample|test)(?:\s*,\s*[^\)\]\}]+)*\s*[\)\]\}]",
        re.IGNORECASE,
    )


def get_country_origin_pattern() -> Pattern[str]:
    """
    Get regex pattern for country of origin indicators using combined regex.
    Combine all country origin patterns into a single regex for better performance.

    Returns:
        Compiled regex pattern for country of origin indicators
    """
    return re.compile(
        r"(?:[\(\[\{])\s*(?:"
        r"Indian|Russian|Made\s+in\s+Germany|Made\s+in\s+China|"
        r"russia\s+green|Czechoslovakian|Poland"
        r")\s*[\)\]\}]",
        re.IGNORECASE,
    )


def get_decimal_usage_pattern() -> Pattern[str]:
    """
    Get regex pattern for decimal usage counts: [3.5], [.5], (2.5), etc.

    Returns:
        Compiled regex pattern for decimal usage counts
    """
    return re.compile(r"(?:[\(\[\{])\s*\d*\.\d+\s*[\)\]\}]")


def get_hash_usage_pattern() -> Pattern[str]:
    """
    Get regex pattern for hash usage counts: (#3), (#12), (#2 use), etc.
    These are semantically equivalent to (3), (12) - blade usage counts that should be stripped.

    Returns:
        Compiled regex pattern for hash usage counts
    """
    return re.compile(r"(?:[\(\[\{])\s*#\d+(?:\s+[^\)\]\}]+)?\s*[\)\]\}]")


def get_shave_hash_pattern() -> Pattern[str]:
    """
    Get regex pattern for "shave #n" usage counts: (shave #3), (shave #12), etc.

    Returns:
        Compiled regex pattern for "shave #n" usage counts
    """
    return re.compile(r"(?:[\(\[\{])\s*shave\s+#\d+(?:\s+[^\)\]\}]+)?\s*[\)\]\}]")


def get_x_usage_pattern() -> Pattern[str]:
    """
    Get regex pattern for "X" usage counts: (16X), (17X), etc.
    These are semantically equivalent to (16), (17) - blade usage counts that should be stripped.

    Returns:
        Compiled regex pattern for "X" usage counts
    """
    return re.compile(r"(?:[\(\[\{])\s*\d+X\s*[\)\]\}]")


def get_maybe_usage_pattern() -> Pattern[str]:
    """
    Get regex pattern for "maybe" usage counts: (17 maybe), etc.

    Returns:
        Compiled regex pattern for "maybe" usage counts
    """
    return re.compile(r"(?:[\(\[\{])\s*\d+\s+maybe\s*[\)\]\}]", re.IGNORECASE)


def get_approximate_number_pattern() -> Pattern[str]:
    """
    Get regex pattern for approximate number patterns: (10ish), (5ish?), (11-ish), ( 10ish ?), etc.
    These are user approximations that should be normalized out.
    Catches variations like: (10ish), (5ish?), (11-ish), ( 10ish ?), [3ish], {2ish}, etc.

    Returns:
        Compiled regex pattern for approximate number patterns
    """
    return re.compile(r"[\(\[\{]\s*\d+\s*[-]?\s*ish\s*\??\s*[\)\]\}]", re.IGNORECASE)


def get_ordinal_use_pattern() -> Pattern[str]:
    """
    Get regex pattern for ordinal usage without brackets: "1st use", "2nd use", etc.
    This catches patterns like "treet platinum , 1st use" -> "treet platinum , "
    (cleanup handles trailing punctuation)

    Returns:
        Compiled regex pattern for ordinal usage without brackets
    """
    return re.compile(r"\d+(?:st|nd|rd|th)\s+use\b", re.IGNORECASE)


def get_basic_usage_pattern() -> Pattern[str]:
    """
    Get regex pattern for basic usage counts: (1), (2), [3], {4}, etc.

    This pattern matches complete parentheses/brackets/braces with numbers that are likely
    blade use counts, excluding 4-digit numbers that are likely years (1900-2099).

    Returns:
        Compiled regex pattern for basic usage counts
    """
    return re.compile(r"(?:[\(\[\{])\s*(?!19\d{2}|20\d{2})\d+\s*[\)\]\}]")
