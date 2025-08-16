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

    # Remove all asterisks (markdown formatting and product name asterisks)
    cleaned = re.sub(r"\*+", "", cleaned)

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

    # Pattern for country of origin indicators: (Indian), (Russian), (Made in Germany), etc.
    # This catches the specific country patterns we found in the analysis
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
    # This catches decimal patterns like [3.5], [.5], (1.5), etc.
    decimal_usage_pattern = r"(?:[\(\[\{])\s*\d*\.\d+\s*[\)\]\}]"
    cleaned = re.sub(decimal_usage_pattern, "", cleaned, flags=re.IGNORECASE)

    # Pattern for hash usage counts: (#3), (#12), etc.
    # But preserve numeric hashtags that represent blade use counts
    # TEMPORARILY DISABLED: hash_usage_pattern = (
    #     r"(?:[\(\[\{])\s*#(?![0-9]+(?:\.[0-9]+)?\b)[a-zA-Z0-9_]+\s*[\)\]\}]"
    # )
    # cleaned = re.sub(hash_usage_pattern, "", cleaned, flags=re.IGNORECASE)

    # Pattern for "shave #n" usage counts: (shave #3), (shave #12), etc.
    # But preserve numeric hashtags that represent blade use counts
    # TEMPORARILY DISABLED: shave_hash_pattern = (
    #     r"(?:[\(\[\{])\s*shave\s+#(?![0-9]+(?:\.[0-9]+)?\b)[a-zA-Z0-9_]+\s*[\)\]\}]"
    # )
    # cleaned = re.sub(shave_hash_pattern, "", cleaned, flags=re.IGNORECASE)

    # Now preserve numeric hashtags by removing the # symbol but keeping the number
    # This converts (shave #4) to (shave 4) so it can be processed by other patterns
    # TEMPORARILY DISABLED: numeric_hashtag_pattern = r"#(\d+(?:\.\d+)?)"
    # cleaned = re.sub(numeric_hashtag_pattern, r"\1", cleaned)

    # Pattern for approximate number patterns: (10ish), (5ish?), (3ish), etc.
    # These are user approximations that should be normalized out
    approximate_number_pattern = r"(?:[\(\[\{])\s*\d+ish\??\s*[\)\]\}]"
    cleaned = re.sub(approximate_number_pattern, "", cleaned, flags=re.IGNORECASE)

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
