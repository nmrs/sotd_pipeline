#!/usr/bin/env python3
"""Extraction phase normalization utilities for the SOTD pipeline."""

import re
from typing import Dict, List

from .competition_tags import strip_competition_tags


def normalize_parentheses_whitespace(value: str) -> str:
    """
    Normalize whitespace inside parentheses, brackets, and braces.

    This function:
    - Removes leading/trailing whitespace inside parentheses: ( fresh ) → (fresh)
    - Removes leading/trailing whitespace inside brackets: [ new ] → [new]
    - Removes leading/trailing whitespace inside braces: { fresh } → {fresh}
    - Preserves internal whitespace in multi-word content: (fresh blade) stays (fresh blade)

    Args:
        value: Input string that may contain parentheses with whitespace

    Returns:
        String with normalized parentheses whitespace
    """
    if not isinstance(value, str):
        return value

    # Pattern to match parentheses/brackets/braces with optional leading/trailing whitespace
    # Group 1: opening bracket, Group 2: content, Group 3: closing bracket
    pattern = r"([\(\[\{])\s*([^\)\]\}]*?)\s*([\)\]\}])"

    def normalize_match(match):
        opening = match.group(1)
        content = match.group(2).strip()  # Strip leading/trailing whitespace from content
        closing = match.group(3)
        return f"{opening}{content}{closing}"

    return re.sub(pattern, normalize_match, value)


def strip_blade_count_patterns(value: str) -> str:
    """Strip blade count patterns and other non-product information from blade names."""
    if not value or not isinstance(value, str):
        return value

    cleaned = value
    # Remove all asterisks (markdown formatting and product name asterisks)
    cleaned = re.sub(r"\*+", "", cleaned)

    # Pattern for basic usage counts: (1), (2), [3], {4}, etc.
    basic_usage_pattern = r"(?:[\(\[\{])\s*\d+\s*[\)\]\}]"
    cleaned = re.sub(basic_usage_pattern, "", cleaned)

    # Pattern for usage counts with 'x': (2x), (3x), [4x], etc.
    usage_x_pattern = r"(?:[\(\[\{])\s*\d+x\s*[\)\]\}]"
    cleaned = re.sub(usage_x_pattern, "", cleaned)

    # Pattern for usage counts with 'use': (1 use), (2 use), etc.
    usage_use_pattern = r"(?:[\(\[\{])\s*\d+\s+use\s*[\)\]\}]"
    cleaned = re.sub(usage_use_pattern, "", cleaned, flags=re.IGNORECASE)

    # Pattern for ordinal usage: (1st shave), (2nd shave), (10th shave), etc.
    ordinal_shave_pattern = r"(?:[\(\[\{])\s*\d+(?:st|nd|rd|th)\s+shave\s*[\)\]\}]"
    cleaned = re.sub(ordinal_shave_pattern, "", cleaned, flags=re.IGNORECASE)

    # Pattern for ordinal usage: (1st), (2nd), (10th), etc.
    ordinal_pattern = r"(?:[\(\[\{])\s*\d+(?:st|nd|rd|th)\s*[\)\]\}]"
    cleaned = re.sub(ordinal_pattern, "", cleaned, flags=re.IGNORECASE)

    # Pattern for superscript ordinal usage: (2^(nd)), (3^(rd)), (1^(st)), etc.
    # Also handles patterns like (2^(nd) use), (3^(rd) use), etc.
    superscript_ordinal_pattern = (
        r"(?:[\(\[\{])\s*\d+\^?\(?(?:st|nd|rd|th)\)?" r"(?:\s+[^\)\]\}]+)?\s*[\)\]\}]"
    )
    cleaned = re.sub(superscript_ordinal_pattern, "", cleaned, flags=re.IGNORECASE)

    # Pattern for completion indicators: (1 and done), (1 and last), (1st and final), etc.
    completion_pattern = (
        r"(?:[\(\[\{])\s*\d+(?:st|nd|rd|th)?(?:\s+[^\)\]\}]+)?\s+"
        r"(?:and\s+(?:done|last|final|probably\s+last))\s*[\)\]\}]"
    )
    cleaned = re.sub(completion_pattern, "", cleaned, flags=re.IGNORECASE)

    # Pattern for user speculation: (10 I think), (3 I think), (7, I think), (30+ I think), etc.
    speculation_pattern = r"(?:[\(\[\{])\s*\d+[+,\s]+\s*I\s+think\s*[\)\]\}]"
    cleaned = re.sub(speculation_pattern, "", cleaned, flags=re.IGNORECASE)

    # Pattern for user speculation with question marks: (5? I think), etc.
    speculation_question_pattern = r"(?:[\(\[\{])\s*\d+\?\s*I\s+think\s*[\)\]\}]"
    cleaned = re.sub(speculation_question_pattern, "", cleaned, flags=re.IGNORECASE)

    # Pattern for complex usage descriptions: (10+?; At least four months old), etc.
    complex_usage_pattern = r"(?:[\(\[\{])\s*\d+\+?\?[^\)\]\}]*[\)\]\}]"
    cleaned = re.sub(complex_usage_pattern, "", cleaned, flags=re.IGNORECASE)

    # Pattern for celebration patterns: (100...woohoo!), etc.
    celebration_pattern = r"(?:[\(\[\{])\s*\d+\.{3}[^\)\]\}]*[\)\]\}]"
    cleaned = re.sub(celebration_pattern, "", cleaned, flags=re.IGNORECASE)

    # Pattern for partial usage: (<1 and done), etc.
    partial_usage_pattern = r"(?:[\(\[\{])\s*<\s*\d+\s+and\s+done\s*[\)\]\}]"
    cleaned = re.sub(partial_usage_pattern, "", cleaned, flags=re.IGNORECASE)

    # Pattern for location/condition indicators: (Thailand, new), (India), etc.
    # Only match specific location/condition patterns, not all parenthetical content
    location_condition_pattern = (
        r"(?:[\(\[\{])\s*(?:Thailand|India|China|Russia|Turkey|Germany|Japan|USA|UK|"
        r"new|old|vintage|sample|test)(?:\s*,\s*[^\)\]\}]+)*\s*[\)\]\}]"
    )
    cleaned = re.sub(location_condition_pattern, "", cleaned, flags=re.IGNORECASE)

    # Pattern for country of origin indicators: (Indian), (Russian), (Made in Germany), etc.
    country_origin_patterns = [
        r"(?:[\(\[\{])\s*Indian\s*[\)\]\}]",  # (Indian)
        r"(?:[\(\[\{])\s*Russian\s*[\)\]\}]",  # (Russian)
        r"(?:[\(\[\{])\s*Made\s+in\s+Germany\s*[\)\]\}]",  # (Made in Germany)
        r"(?:[\(\[\{])\s*Made\s+in\s+China\s*[\)\]\}]",  # (Made in China)
        r"(?:[\(\[\{])\s*russia\s+green\s*[\)\]\}]",  # (russia green)
        r"(?:[\(\[\{])\s*Czechoslovakian\s*[\)\]\}]",  # (Czechoslovakian)
        r"(?:[\(\[\{])\s*Poland\s*[\)\]\}]",  # (Poland)
    ]
    for pattern in country_origin_patterns:
        cleaned = re.sub(pattern, "", cleaned, flags=re.IGNORECASE)

    # Pattern for decimal usage counts: [3.5], [.5], (2.5), etc.
    decimal_usage_pattern = r"(?:[\(\[\{])\s*\d*\.\d+\s*[\)\]\}]"
    cleaned = re.sub(decimal_usage_pattern, "", cleaned, flags=re.IGNORECASE)

    # Pattern for hash usage counts: (#3), (#12), (#2 use), etc.
    # These are semantically equivalent to (3), (12) - blade usage counts that should be stripped
    hash_usage_pattern = r"(?:[\(\[\{])\s*#\d+(?:\s+[^\)\]\}]+)?\s*[\)\]\}]"
    cleaned = re.sub(hash_usage_pattern, "", cleaned, flags=re.IGNORECASE)

    # Pattern for "shave #n" usage counts: (shave #3), (shave #12), etc.
    shave_hash_pattern = r"(?:[\(\[\{])\s*shave\s+#\d+(?:\s+[^\)\]\}]+)?\s*[\)\]\}]"
    cleaned = re.sub(shave_hash_pattern, "", cleaned, flags=re.IGNORECASE)

    # Pattern for "X" usage counts: (16X), (17X), etc.
    # These are semantically equivalent to (16), (17) - blade usage counts that should be stripped
    x_usage_pattern = r"(?:[\(\[\{])\s*\d+X\s*[\)\]\}]"
    cleaned = re.sub(x_usage_pattern, "", cleaned, flags=re.IGNORECASE)

    # Pattern for "maybe" usage counts: (17 maybe), etc.
    maybe_usage_pattern = r"(?:[\(\[\{])\s*\d+\s+maybe\s*[\)\]\}]"
    cleaned = re.sub(maybe_usage_pattern, "", cleaned, flags=re.IGNORECASE)

    # Pattern for approximate number patterns: (10ish), (5ish?), (11-ish), ( 10ish ?), etc.
    # These are user approximations that should be normalized out
    # Catches variations like: (10ish), (5ish?), (11-ish), ( 10ish ?), [3ish], {2ish}, etc.
    approximate_number_pattern = r"[\(\[\{]\s*\d+\s*[-]?\s*ish\s*\??\s*[\)\]\}]"
    cleaned = re.sub(approximate_number_pattern, "", cleaned, flags=re.IGNORECASE)

    # Special case: remove any double spaces left behind
    cleaned = re.sub(r"\s+", " ", cleaned).strip()

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
        r"\s*\(\d+\)",  # Basic numbers like (6), (12), (23)
        r"\s*\[\d+\]",  # Numbers in brackets like [5], [10]
        r"\s*\(new\)",  # New indicators
        r"\s*\(NEW\)",  # NEW indicators
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
    - Standalone sample indicators: "sample", "tester" at the end
    - Size indicators: (travel size), (mini), etc.
    - Product type indicators: "Shave Soap", "Shaving Soap", "soap", etc.
    - Delimiters and punctuation: leading/trailing -, :, /, etc.

    Args:
        value: Input string that may contain soap-related patterns

    Returns:
        String with soap-related patterns removed and ready for matching
    """
    if not isinstance(value, str):
        return value

    cleaned = value

    # First remove complete phrases like "Shave Soap", "Shaving Soap", etc.
    shaving_patterns = [
        r"\b(shave soap|shaving soap|shave cream|shaving cream|"
        r"shave splash|shaving splash|shave balm|shaving balm|"
        r"shave aftershave|shaving aftershave)\b",
    ]
    for pattern in shaving_patterns:
        cleaned = re.sub(pattern, "", cleaned, flags=re.IGNORECASE)

    # Then remove individual product type indicators
    product_patterns = [
        r"\b(soap|cream|splash|balm|aftershave|puck|croap)\b",
    ]
    for pattern in product_patterns:
        cleaned = re.sub(pattern, "", cleaned, flags=re.IGNORECASE)

    # Pattern for soap-related indicators in parentheses
    soap_patterns = [
        r"\s*\(sample\)",
        r"\s*\(tester\)",
        r"\s*\(travel\s+size\)",
        r"\s*\(mini\)",
        r"\s*\(small\)",
    ]
    for pattern in soap_patterns:
        cleaned = re.sub(pattern, "", cleaned, flags=re.IGNORECASE)

    # Pattern for standalone sample indicators at the end
    standalone_sample_patterns = [
        r"\s+sample\s*[.!?]*\s*$",  # "sample" at the end (with optional punctuation)
        r"\s+tester\s*[.!?]*\s*$",  # "tester" at the end (with optional punctuation)
    ]
    for pattern in standalone_sample_patterns:
        cleaned = re.sub(pattern, "", cleaned, flags=re.IGNORECASE)

    # Clean up any leading/trailing delimiters and punctuation that the matcher needs
    # This ensures the normalized field is truly ready for matching
    cleaned = re.sub(r"^[\s\-:*/_,~`\\\.]+", "", cleaned)
    cleaned = re.sub(r"[\s\-:*/_,~`\\\.]+$", "", cleaned)

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


def strip_trailing_periods(value: str | None) -> str | None:
    """
    Strip trailing periods and other punctuation from strings.

    Args:
        value: Input string that may have trailing punctuation

    Returns:
        String with trailing punctuation removed, or None if input is None
    """
    if not isinstance(value, str):
        return value

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
        # Remove empty parentheses, brackets, and braces for soap fields
        normalized = re.sub(r"\(\s*\)", "", normalized)  # Empty parentheses
        normalized = re.sub(r"\[\s*\]", "", normalized)  # Empty brackets
        normalized = re.sub(r"\{\s*}", "", normalized)  # Empty braces

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


def normalize_remainder_text_preserve_locations(value: str) -> str:
    """
    Normalize remainder text while preserving location information for future enrichment.

    This function is similar to normalize_remainder_text but keeps location indicators
    like (china), (germany), etc. so they can be extracted during blade enrichment.

    Args:
        value: The remainder text to normalize

    Returns:
        Cleaned remainder text with locations preserved for enrichment

    Examples:
        >>> normalize_remainder_text_preserve_locations("(3) (china)")
        "(3) (china)"
        >>> normalize_remainder_text_preserve_locations("*****(10) (germany)")
        "(10) (germany)"
        >>> normalize_remainder_text_preserve_locations("(2x) (india) .")
        "(2x) (india)"
    """
    if not isinstance(value, str):
        return ""

    # Remove all hashtags (#sometag) and dollar-tags ($sometag) - but NOT location tags
    cleaned = re.sub(r"[#\$][a-zA-Z0-9_]+", "", value)

    # Remove all URLs (http://, https://, www.)
    cleaned = re.sub(r"https?://[^\s]+", "", cleaned)
    cleaned = re.sub(r"www\.[^\s]+", "", cleaned)

    # Remove empty parentheses, brackets, and braces
    cleaned = re.sub(r"\(\s*\)", "", cleaned)  # Empty parentheses
    cleaned = re.sub(r"\[\s*\]", "", cleaned)  # Empty brackets
    cleaned = re.sub(r"\{\s*}", "", cleaned)  # Empty braces

    # Remove all asterisks
    cleaned = cleaned.replace("*", "")

    # Standardize × to x for consistency
    cleaned = cleaned.replace("×", "x")

    # Remove trailing periods and other common trailing punctuation
    cleaned = re.sub(r"[\.\!\?]+$", "", cleaned)

    # Remove ~ and ? characters that don't provide meaningful value
    cleaned = cleaned.replace("~", "").replace("?", "")

    # Normalize whitespace inside parentheses/brackets/braces
    cleaned = normalize_parentheses_whitespace(cleaned)

    # Final cleanup: normalize whitespace and strip
    cleaned = re.sub(r"\s+", " ", cleaned).strip()

    return cleaned


def normalize_remainder_text(value: str) -> str:
    """
    Normalize remainder text by stripping asterisks, trailing punctuation, hashtags,
    dollar-tags, URLs, empty parentheses, and location indicators for clean analysis.

    This function is designed for analysis purposes and strips location information
    to focus on blade count patterns. For enrichment purposes, use
    normalize_remainder_text_preserve_locations instead.

    Args:
        value: The remainder text to normalize

    Returns:
        Cleaned remainder text with asterisks, trailing punctuation, hashtags,
        dollar-tags, URLs, empty parentheses, and location indicators removed

    Examples:
        >>> normalize_remainder_text("(3) (china)")
        "(3)"
        >>> normalize_remainder_text("*****(10) (germany)")
        "(10)"
        >>> normalize_remainder_text("(2x) (india) .")
        "(2x)"
    """
    if not isinstance(value, str):
        return ""

    # Remove hashtags (#sometag) and dollar-tags ($sometag), but preserve numeric hashtags
    # like #4, #2.5. This preserves blade use count indicators while removing other tags
    cleaned = re.sub(r"[#\$](?![0-9]+(?:\.[0-9]+)?\b)[a-zA-Z0-9_]+", "", value)

    # Remove all URLs (http://, https://, www.)
    cleaned = re.sub(r"https?://[^\s]+", "", cleaned)
    cleaned = re.sub(r"www\.[^\s]+", "", cleaned)

    # Remove condition indicators for clean analysis
    # These will be preserved in normalize_remainder_text_preserve_locations
    condition_patterns = [
        r"\(vintage\)",
        r"\(sample\)",
        r"\(test\)",
        r"\(old\)",
    ]
    for pattern in condition_patterns:
        cleaned = re.sub(pattern, "", cleaned, flags=re.IGNORECASE)

    # Remove empty parentheses, brackets, and braces
    cleaned = re.sub(r"\(\s*\)", "", cleaned)  # Empty parentheses
    cleaned = re.sub(r"\[\s*\]", "", cleaned)  # Empty brackets
    cleaned = re.sub(r"\{\s*}", "", cleaned)  # Empty braces

    # Remove all asterisks
    cleaned = cleaned.replace("*", "")

    # Standardize × to x for consistency
    cleaned = cleaned.replace("×", "x")

    # Remove trailing periods and other common trailing punctuation
    cleaned = re.sub(r"[\.\!\?]+$", "", cleaned)

    # Remove ~ and ? characters that don't provide meaningful value
    cleaned = cleaned.replace("~", "").replace("?", "")

    # Normalize whitespace inside parentheses/brackets/braces
    cleaned = normalize_parentheses_whitespace(cleaned)

    # Final cleanup: normalize whitespace and strip
    cleaned = re.sub(r"\s+", " ", cleaned).strip()

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
