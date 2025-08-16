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
