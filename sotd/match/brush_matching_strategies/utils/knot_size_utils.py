import re
from typing import Optional


def parse_knot_size(text: str) -> Optional[float]:
    """
    Extract the knot size in mm from a string.

    Rules:
    - Look for patterns like '30mm', '27.5', or '28x50'
    - Prefer the first number in 'NxM' patterns
    - Return as float
    """
    if not text:
        return None

    # Look for patterns like '27x50' or '27.5x50'
    match = re.search(r"(\d+(?:\.\d+)?)\s*[x×]\s*\d+(?:\.\d+)?", text)
    if match:
        return float(match.group(1))

    # Look for standalone number with optional 'mm'
    match = re.search(r"\b(\d+(?:\.\d+)?)\s*mm?\b", text, re.IGNORECASE)
    if match:
        return float(match.group(1))

    # Fallback: any number in the text
    match = re.search(r"\b(\d+(?:\.\d+)?)\b", text)
    if match:
        return float(match.group(1))

    return None
