#!/usr/bin/env python3
"""Match phase utilities for the SOTD pipeline."""

import re


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
