#!/usr/bin/env python3
"""Blade pattern extraction utilities for the SOTD pipeline.

This module provides priority-based extraction of blade counts and use counts
from user comments, reusing existing patterns and adding validation logic.
"""

import re
from typing import Optional, Tuple


def extract_simple_delimiters(text: str) -> Optional[int]:
    """Extract use count from simple delimiter patterns: (3), [4], {5}.

    Args:
        text: Input string that may contain simple delimiter patterns

    Returns:
        The use count as an integer, or None if no pattern is found
    """
    if not isinstance(text, str) or not text:
        return None

    # Pattern for simple delimiters: (3), [4], {5}, (X3), [X5], etc.
    simple_pattern = r"[\(\[\{]\s*(?:[A-Za-z]*)?(\d+)\s*[\)\]\}]"
    match = re.search(simple_pattern, text, re.IGNORECASE)
    if match:
        count = int(match.group(1))
        if validate_usage_count(count):
            return count

    return None


def extract_explicit_usage(text: str) -> Optional[int]:
    """Extract use count from explicit usage patterns: (3rd use), (10th shave).

    Args:
        text: Input string that may contain explicit usage patterns

    Returns:
        The use count as an integer, or None if no pattern is found
    """
    if not isinstance(text, str) or not text:
        return None

    # Pattern for explicit usage: (3rd use), (10th shave), etc.
    usage_pattern = r"[\(\[\{]\s*(\d+)(?:st|nd|rd|th)\s+(?:use|shave)\s*[\)\]\}]"
    match = re.search(usage_pattern, text, re.IGNORECASE)
    if match:
        count = int(match.group(1))
        if validate_usage_count(count):
            return count

    # Pattern for ordinal use without brackets: 3rd use, 2nd use, etc.
    # Must have some text before the pattern to indicate it's a blade description
    ordinal_pattern = r".+\b(\d+)(?:st|nd|rd|th)\s+(?:use|shave)\b"
    match = re.search(ordinal_pattern, text, re.IGNORECASE)
    if match:
        count = int(match.group(1))
        if validate_usage_count(count):
            return count

    return None


def extract_multipliers(text: str) -> Optional[int]:
    """Extract count from multiplier patterns: (2x), (x3).

    Args:
        text: Input string that may contain multiplier patterns

    Returns:
        The count as an integer, or None if no pattern is found
    """
    if not isinstance(text, str) or not text:
        return None

    # Pattern for multipliers: (2x), (x3), [4x], {x5}
    multiplier_pattern = r"[\(\[\{]\s*(?:x)?(\d+)(?:x)?\s*[\)\]\}]"
    match = re.search(multiplier_pattern, text, re.IGNORECASE)
    if match:
        count = int(match.group(1))
        if validate_usage_count(count):
            return count

    # Pattern for standalone multipliers: x4, 2x
    # Must have some text before the pattern to indicate it's a blade description
    standalone_pattern = r".+(?:\s|^)(?:x)?(\d+)(?:x)?(?:\s|$)"
    match = re.search(standalone_pattern, text, re.IGNORECASE)
    if match:
        count = int(match.group(1))
        if validate_usage_count(count):
            return count

    return None


def extract_hash_numbers(text: str) -> Optional[int]:
    """Extract count from hash number patterns: #15, #2.

    Args:
        text: Input string that may contain hash number patterns

    Returns:
        The count as an integer, or None if no pattern is found
    """
    if not isinstance(text, str) or not text:
        return None

    # Pattern for hash numbers: #15, #2
    # Must have some text before the pattern to indicate it's a blade description
    hash_pattern = r".+#(\d+)"
    match = re.search(hash_pattern, text)
    if match:
        count = int(match.group(1))
        if validate_usage_count(count):
            return count

    return None


def extract_semantic_patterns(text: str) -> Optional[int]:
    """Extract use count from semantic patterns: (NEW), (fresh).

    Args:
        text: Input string that may contain semantic patterns

    Returns:
        The use count as 1 for semantic patterns, or None if no pattern is found
    """
    if not isinstance(text, str) or not text:
        return None

    # Pattern for semantic usage (equivalent to first use)
    semantic_patterns = [
        r"[\(\[]\s*new\s*[\)\]]",  # (NEW), [new]
        r"[\(\[]\s*fresh\s*[\)\]]",  # (Fresh), [fresh]
        r"[\(\[]\s*new\s+blade\s*[\)\]]",  # (new blade)
        r"[\(\[]\s*fresh\s+blade\s*[\)\]]",  # (fresh blade)
        r"[\(\[]\s*first\s+time\s*[\)\]]",  # (first time)
        r"[\(\[]\s*brand\s+new\s*[\)\]]",  # (brand new)
    ]

    for pattern in semantic_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            return 1

    # Standalone semantic words
    # Must have some text before the pattern to indicate it's a blade description
    standalone_patterns = [
        r".+\bnew\b",
        r".+\bfresh\b",
        r".+\bfirst\s+time\b",
        r".+\bbrand\s+new\b",
    ]

    for pattern in standalone_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            return 1

    return None


def extract_month_usage(text: str) -> Optional[int]:
    """Extract use count from month usage patterns: 15/31, 20/31.

    Args:
        text: Input string that may contain month usage patterns

    Returns:
        The use count as an integer, or None if no pattern is found
    """
    if not isinstance(text, str) or not text:
        return None

    # Pattern for month-based usage tracking: n/31, n/30, n/28, n/29
    # Must have some text before the pattern to indicate it's a blade description
    month_pattern = r".+\b(\d+)/(?:28|29|30|31)\b"
    match = re.search(month_pattern, text)
    if match:
        count = int(match.group(1))
        if validate_usage_count(count):
            return count

    return None


def extract_ordinal_patterns(text: str) -> Optional[int]:
    """Extract use count from ordinal patterns: 3rd, 2nd.

    Args:
        text: Input string that may contain ordinal patterns

    Returns:
        The use count as an integer, or None if no pattern is found
    """
    if not isinstance(text, str) or not text:
        return None

    # Pattern for ordinal numbers: 3rd, 2nd, 1st, etc.
    # Must have some text before the pattern to indicate it's a blade description
    ordinal_pattern = r".+\b(\d+)(?:st|nd|rd|th)\b"
    match = re.search(ordinal_pattern, text)
    if match:
        count = int(match.group(1))
        if validate_usage_count(count):
            return count

    return None


def extract_escaped_brackets(text: str) -> Optional[int]:
    """Extract use count from escaped bracket patterns: [2\], [3\].

    Args:
        text: Input string that may contain escaped bracket patterns

    Returns:
        The use count as an integer, or None if no pattern is found
    """
    if not isinstance(text, str) or not text:
        return None

    # Pattern for escaped brackets: [2\], [3\]
    # Must have some text before the pattern to indicate it's a blade description
    escaped_pattern = r".+\[(\d+)\\\]"
    match = re.search(escaped_pattern, text)
    if match:
        count = int(match.group(1))
        if validate_usage_count(count):
            return count

    return None


def extract_superscript_ordinals(text: str) -> Optional[int]:
    """Extract use count from superscript ordinal patterns: (2^(nd)), (3^(rd)).

    Args:
        text: Input string that may contain superscript ordinal patterns

    Returns:
        The use count as an integer, or None if no pattern is found
    """
    if not isinstance(text, str) or not text:
        return None

    # Pattern for superscript ordinals with "use": (2^(nd) use), (3^(rd) use)
    # Must have some text before the pattern to indicate it's a blade description
    superscript_use_pattern = r".+[\(\[\{]\s*(\d+)\^\(\s*(?:st|nd|rd|th)\s*\)\s+use\s*[\)\]\}]"
    match = re.search(superscript_use_pattern, text, re.IGNORECASE)
    if match:
        count = int(match.group(1))
        if validate_usage_count(count):
            return count

    # Pattern for superscript ordinals without "use": (2^(nd)), (3^(rd))
    # Must have some text before the pattern to indicate it's a blade description
    superscript_pattern = r".+[\(\[\{]\s*(\d+)\^\(\s*(?:st|nd|rd|th)\s*\)\s*[\)\]\}]"
    match = re.search(superscript_pattern, text, re.IGNORECASE)
    if match:
        count = int(match.group(1))
        if validate_usage_count(count):
            return count

    return None


def validate_usage_count(count: int) -> bool:
    """Validate that a usage count is realistic.

    Args:
        count: The usage count to validate

    Returns:
        True if the count is valid, False otherwise

    Business Rules:
    - Must be less than 800 (realistic blade usage)
    - Must not be 4+ digits (likely model numbers, not usage counts)
    """
    if count < 1:
        return False

    if count >= 800:
        return False

    # Check for 4+ digit numbers (likely model numbers)
    if count >= 1000:
        return False

    return True


def extract_blade_count(text: str) -> Optional[int]:
    """Extract blade count (number of blades) from text.

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
    leading_blade_count_pattern = r"^\s*[\(\[\{]\s*(?:x)?(\d+)(?:x)?\s*[\)\]\}]"
    match = re.match(leading_blade_count_pattern, text, re.IGNORECASE)
    if match:
        count = int(match.group(1))
        if validate_usage_count(count):
            return count

    return None


def extract_blade_counts(text: str) -> Tuple[Optional[int], Optional[int]]:
    """Extract both blade count and use count from text with priority logic.

    This function implements priority-based extraction that reuses existing
    patterns and adds validation logic.

    Priority Order (highest to lowest):
    1. Simple delimiters: (3), [4], {5}
    2. Explicit usage: (3rd use), (10th shave)
    3. Multipliers: (2x), (x3)
    4. Hash numbers: #15, #2
    5. Semantic patterns: (NEW), (fresh)
    6. Month usage: 15/31, 20/31
    7. Ordinal patterns: 3rd, 2nd
    8. Escaped brackets: [2\], [3\]
    9. Superscript ordinals: (2^(nd)), (3^(rd))

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
        leading_blade_count_pattern = r"^\s*[\(\[\{]\s*(?:x)?(\d+)(?:x)?\s*[\)\]\}]"
        stripped = re.sub(leading_blade_count_pattern, "", text, flags=re.IGNORECASE)
        stripped = stripped.strip()
        use_count = _extract_use_count_with_priority(stripped)
    else:
        # No blade count found, look for use count in the original text
        use_count = _extract_use_count_with_priority(text)

    return blade_count, use_count


def _extract_use_count_with_priority(text: str) -> Optional[int]:
    """Extract use count using priority-based pattern matching.

    This is an internal function that implements the priority logic
    for use count extraction.

    Args:
        text: Input string that may contain use count patterns

    Returns:
        The use count as an integer, or None if no pattern is found
    """
    # Try patterns in priority order
    extractors = [
        extract_simple_delimiters,
        extract_explicit_usage,
        extract_multipliers,
        extract_hash_numbers,
        extract_semantic_patterns,
        extract_month_usage,
        extract_ordinal_patterns,
        extract_escaped_brackets,
        extract_superscript_ordinals,
    ]

    for extractor in extractors:
        result = extractor(text)
        if result is not None:
            return result

    return None
