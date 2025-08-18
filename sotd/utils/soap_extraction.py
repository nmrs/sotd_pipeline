#!/usr/bin/env python3
"""Soap-specific extraction utilities for the SOTD pipeline."""

import re
from typing import Optional, Tuple


def extract_soap_sample_via_normalization(
    original_text: str, normalized_text: str
) -> Tuple[Optional[str], Optional[int], Optional[int], Optional[str]]:
    """
    Extract soap sample information by removing normalized text from original text.

    This approach leverages the already-done normalization work to find sample indicators
    that remain after the normalized product text is stripped out.

    Args:
        original_text: The original soap text from user comment
        normalized_text: The normalized soap text (with sample indicators stripped)

    Returns:
        Tuple of (sample_type, sample_number, total_samples, remainder_text) where:
        - sample_type: The type of sample ("sample", "tester", etc.) or None
        - sample_number: The sample number if specified, or None
        - total_samples: The total number of samples if specified, or None
        - remainder_text: The text that remains after stripping normalized from original
    """
    if not original_text or not normalized_text:
        return None, None, None, None

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
        return None, None, None, None

    # Extract the remainder text (what comes before and after the normalized text)
    before_normalized = original_stripped[:pos]
    after_normalized = original_stripped[pos + len(normalized_stripped) :]

    # Combine the remainder parts
    remainder = (before_normalized + after_normalized).strip()

    # If no remainder, no sample info was found
    if not remainder:
        return None, None, None, remainder

    # Extract sample information from the remainder
    sample_type, sample_number, total_samples = _extract_sample_patterns(remainder)

    return sample_type, sample_number, total_samples, remainder


def _extract_sample_patterns(remainder: str) -> Tuple[Optional[str], Optional[int], Optional[int]]:
    """
    Extract sample patterns from remainder text.

    Args:
        remainder: Text remaining after stripping normalized product text

    Returns:
        Tuple of (sample_type, sample_number, total_samples)
    """
    if not remainder:
        return None, None, None

    # Convert to lowercase for case-insensitive matching
    remainder_lower = remainder.lower()

    # Pattern 1: (sample), (tester)
    basic_sample_match = re.search(r"\((\w+)\)", remainder_lower)
    if basic_sample_match:
        sample_type = basic_sample_match.group(1)
        if sample_type in ["sample", "samp", "tester"]:
            # Normalize samp to sample
            if sample_type == "samp":
                sample_type = "sample"
            return sample_type, None, None

    # Pattern 2: (sample #23), (sample #5)
    numbered_sample_match = re.search(r"\(sample\s+#(\d+)\)", remainder_lower)
    if numbered_sample_match:
        try:
            sample_number = int(numbered_sample_match.group(1))
            return "sample", sample_number, None
        except ValueError:
            pass

    # Pattern 3: (sample 5 of 10), (sample 3 of 15)
    range_sample_match = re.search(r"\(sample\s+(\d+)\s+of\s+(\d+)\)", remainder_lower)
    if range_sample_match:
        try:
            sample_number = int(range_sample_match.group(1))
            total_samples = int(range_sample_match.group(2))
            return "sample", sample_number, total_samples
        except ValueError:
            pass

    # Pattern 4: (sample 5/10), (sample 3/15)
    fraction_sample_match = re.search(r"\(sample\s+(\d+)/(\d+)\)", remainder_lower)
    if fraction_sample_match:
        try:
            sample_number = int(fraction_sample_match.group(1))
            total_samples = int(fraction_sample_match.group(2))
            return "sample", sample_number, total_samples
        except ValueError:
            pass

    # Pattern 5: trailing "sample" or "tester" (e.g., "Brand - Scent - sample")
    trailing_sample_match = re.search(r"\b(sample|samp|tester)\b$", remainder_lower)
    if trailing_sample_match:
        sample_type = trailing_sample_match.group(1)
        if sample_type == "samp":
            sample_type = "sample"
        return sample_type, None, None

    # Pattern 6: (sample) with any whitespace variations
    loose_sample_match = re.search(r"\(\s*(sample|samp|tester)\s*\)", remainder_lower)
    if loose_sample_match:
        sample_type = loose_sample_match.group(1)
        if sample_type == "samp":
            sample_type = "sample"
        return sample_type, None, None

    return None, None, None
