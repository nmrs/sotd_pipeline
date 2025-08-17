#!/usr/bin/env python3
"""Blade-specific extraction utilities for the SOTD pipeline."""

import re
from typing import Optional, Tuple


def extract_blade_use_count(text: str, blade_model: Optional[str] = None) -> Optional[int]:
    """
    Extract blade use count from various patterns in text.

    This function recognizes all the patterns that the blade enricher currently handles,
    plus the new patterns we've added for normalization.

    Args:
        text: Input string that may contain blade use count patterns
        blade_model: Optional blade model from catalog matching for validation

    Returns:
        The use count as an integer, or None if no pattern is found
    """
    if not isinstance(text, str) or not text:
        return None

    # Pattern 1: (3x), [x3], {2x}, etc.
    pattern1 = r"(?:[\(\[\{])\s*(?:x)?(\d+)(?:x)?\s*[\)\]\}]"
    match = re.search(pattern1, text, re.IGNORECASE)
    if match:
        use_count = int(match.group(1))
        # Validate against blade model if provided
        if blade_model and str(use_count) in blade_model:
            return None  # This is likely a model number, not a usage count
        return use_count

    # Pattern 2: (4 times), [5 times], {3 times}, etc.
    pattern2 = r"(?:[\(\[\{])\s*(\d+)\s+times?\s*[\)\]\}]"
    match = re.search(pattern2, text, re.IGNORECASE)
    if match:
        use_count = int(match.group(1))
        # Validate against blade model if provided
        if blade_model and str(use_count) in blade_model:
            return None  # This is likely a model number, not a usage count
        return use_count

    # Pattern 3: (7th use), [3rd use], {2nd use}, etc.
    pattern3 = r"(?:[\(\[\{])\s*(\d+)(?:st|nd|rd|th)\s+use\s*[\)\]\}]"
    match = re.search(pattern3, text, re.IGNORECASE)
    if match:
        use_count = int(match.group(1))
        # Validate against blade model if provided
        if blade_model and str(use_count) in blade_model:
            return None  # This is likely a model number, not a usage count
        return use_count

    # Pattern 3.5: (2nd), [3rd], {4th}, etc. (standalone ordinal numbers)
    pattern3_5 = r"(?:[\(\[\{])\s*(\d+)(?:st|nd|rd|th)\s*[\)\]\}]"
    match = re.search(pattern3_5, text, re.IGNORECASE)
    if match:
        use_count = int(match.group(1))
        # Validate against blade model if provided
        if blade_model and str(use_count) in blade_model:
            return None  # This is likely a model number, not a usage count
        return use_count

    # Pattern 4: Hash numbers: #15, #2, etc.
    pattern4 = r"#(\d+)"
    match = re.search(pattern4, text, re.IGNORECASE)
    if match:
        use_count = int(match.group(1))
        # Validate against blade model if provided
        if blade_model and str(use_count) in blade_model:
            return None  # This is likely a model number, not a usage count
        return use_count

    # Pattern 5: Month usage: 15/31, 20/31, etc.
    pattern5 = r"(\d+)/31"
    match = re.search(pattern5, text, re.IGNORECASE)
    if match:
        use_count = int(match.group(1))
        # Validate against blade model if provided
        if blade_model and str(use_count) in blade_model:
            return None  # This is likely a model number, not a usage count
        return use_count

    # Pattern 6: Ordinal patterns: 3rd, 2nd, etc.
    pattern6 = r"\b(\d+)(?:st|nd|rd|th)\b"
    match = re.search(pattern6, text, re.IGNORECASE)
    if match:
        use_count = int(match.group(1))
        # Validate against blade model if provided
        if blade_model and str(use_count) in blade_model:
            return None  # This is likely a model number, not a usage count
        return use_count

    # Pattern 7: "new" (meaning 1st use) - standalone word or in parentheses
    new_pattern = r"(?:[\(\[\{])\s*new\s*[\)\]\}]|\bnew\b"
    if re.search(new_pattern, text, re.IGNORECASE):
        return 1

    # Pattern 8: ordinal use without brackets: 3rd use, 2nd use, etc.
    ordinal_use_pattern = r"\b(\d+)(?:st|nd|rd|th)\s+use\b"
    match = re.search(ordinal_use_pattern, text, re.IGNORECASE)
    if match:
        use_count = int(match.group(1))
        # Validate against blade model if provided
        if blade_model and str(use_count) in blade_model:
            return None  # This is likely a model number, not a usage count
        return use_count

    # Pattern 9: escaped bracket patterns: [2\], [3\], etc.
    escaped_bracket_pattern = r"\[(\d+)\\]"
    match = re.search(escaped_bracket_pattern, text, re.IGNORECASE)
    if match:
        use_count = int(match.group(1))
        # Validate against blade model if provided
        if blade_model and str(use_count) in blade_model:
            return None  # This is likely a model number, not a usage count
        return use_count

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
        use_count = int(match.group(1))
        # Validate against blade model if provided
        if blade_model and str(use_count) in blade_model:
            return None  # This is likely a model number, not a usage count
        return use_count

    # Pattern 12: Semantic patterns like (fresh), (new blade), etc.
    semantic_patterns = [
        r"[\(\[]\s*fresh\s*[\)\]]",  # (Fresh), [fresh]
        r"[\(\[]\s*new\s+blade\s*[\)\]]",  # (new blade)
        r"[\(\[]\s*fresh\s+blade\s*[\)\]]",  # (fresh blade)
        r"[\(\[]\s*first\s+time\s*[\)\]]",  # (first time)
        r"[\(\[]\s*brand\s+new\s*[\)\]]",  # (brand new)
    ]

    for pattern in semantic_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            return 1

    # No pattern found
    return None


def extract_blade_count(text: str) -> Optional[int]:
    """
    Extract blade count from text.

    Args:
        text: Input string that may contain blade count patterns

    Returns:
        The blade count as an integer, or None if no pattern is found
    """
    if not isinstance(text, str) or not text:
        return None

    # Pattern for blade count: [2x], (2x), {2x}, etc.
    pattern = r"(?:[\(\[\{])\s*(?:x)?(\d+)(?:x)?\s*[\)\]\}]"
    match = re.search(pattern, text, re.IGNORECASE)
    if match:
        try:
            return int(match.group(1))
        except ValueError:
            pass

    return None


def extract_blade_and_use_count(
    text: str, blade_model: Optional[str] = None
) -> Tuple[Optional[int], Optional[int]]:
    """
    Extract both blade count and use count from text.

    Args:
        text: Input string that may contain blade count and use count patterns
        blade_model: Optional blade model from catalog matching for validation

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
        use_count = extract_blade_use_count(stripped, blade_model)
    else:
        # No blade count found, look for use count in the original text
        use_count = extract_blade_use_count(text, blade_model)

    return blade_count, use_count


def extract_blade_use_count_via_normalization(
    original_text: str, normalized_text: str, blade_model: Optional[str] = None
) -> Tuple[Optional[int], Optional[str]]:
    """
    Extract blade use count by removing normalized text from original text.

    This approach avoids confusion between model numbers (like "74" in "Personna - 74 - Injector")
    and actual use counts by leveraging the already-done normalization work.

    Args:
        original_text: The original blade text from user comment
        normalized_text: The normalized blade text (with counts stripped)
        blade_model: Optional blade model from catalog matching for validation

    Returns:
        Tuple of (use_count, remainder_text) where:
        - use_count: The use count as an integer, or None if no pattern is found
        - remainder_text: The text that remains after stripping normalized from original
    """
    if not original_text or not normalized_text:
        return None, None

    # Strip whitespace from both texts for comparison
    original_stripped = original_text.strip()
    normalized_stripped = normalized_text.strip()

    # Find the normalized text within the original text
    # Use case-insensitive search to handle minor case differences
    original_lower = original_stripped.lower()
    normalized_lower = normalized_stripped.lower()

    # Find the position of the normalized text in the original
    pos = original_lower.find(normalized_lower)
    if pos == -1:
        # Normalized text not found in original - this shouldn't happen in normal operation
        return None, None

    # Extract the remainder text (what comes before and after the normalized text)
    before_normalized = original_stripped[:pos]
    after_normalized = original_stripped[pos + len(normalized_stripped) :]

    # Combine the remainder parts
    remainder = (before_normalized + after_normalized).strip()

    # If no remainder, no count was found
    if not remainder:
        return None, remainder

    # Try to extract a number from the remainder
    # Look for common count patterns in the remainder
    import re

    # Pattern 1: Simple parentheses with number (39), (2x), etc.
    paren_match = re.search(r"\((\d+(?:x)?)\)", remainder)
    if paren_match:
        count_str = paren_match.group(1)
        if count_str.endswith("x"):
            # Handle "2x" format
            try:
                return int(count_str[:-1]), remainder
            except ValueError:
                pass
        else:
            # Handle simple number
            try:
                return int(count_str), remainder
            except ValueError:
                pass

    # Pattern 2: Square brackets with number [5], [2x], etc.
    bracket_match = re.search(r"\[(\d+(?:x)?)\]", remainder)
    if bracket_match:
        count_str = bracket_match.group(1)
        if count_str.endswith("x"):
            try:
                return int(count_str[:-1]), remainder
            except ValueError:
                pass
        else:
            try:
                return int(count_str), remainder
            except ValueError:
                pass

    # Pattern 3: Curly braces with number {3}, {1x}, etc.
    brace_match = re.search(r"\{(\d+(?:x)?)\}", remainder)
    if brace_match:
        count_str = brace_match.group(1)
        if count_str.endswith("x"):
            try:
                return int(count_str[:-1]), remainder
            except ValueError:
                pass
        else:
            try:
                return int(count_str), remainder
            except ValueError:
                pass

    # Pattern 4: Standalone number (for cases like "Feather 3rd use")
    standalone_match = re.search(r"\b(\d+)\b", remainder)
    if standalone_match:
        try:
            return int(standalone_match.group(1)), remainder
        except ValueError:
            pass

    # Pattern 5: Ordinal patterns (1st, 2nd, 3rd, etc.)
    ordinal_match = re.search(r"\b(\d+)(?:st|nd|rd|th)\b", remainder, re.IGNORECASE)
    if ordinal_match:
        try:
            return int(ordinal_match.group(1)), remainder
        except ValueError:
            pass

    # Pattern 6: Special patterns like "x4", "x2", etc.
    special_match = re.search(r"x(\d+)", remainder, re.IGNORECASE)
    if special_match:
        try:
            return int(special_match.group(1)), remainder
        except ValueError:
            pass

    # Pattern 7: Hashtag patterns like #4, #2.5, etc.
    hashtag_match = re.search(r"#(\d+(?:\.\d+)?)", remainder)
    if hashtag_match:
        try:
            return int(float(hashtag_match.group(1))), remainder
        except ValueError:
            pass

    # No count pattern found in remainder
    return None, remainder
