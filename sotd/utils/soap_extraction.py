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

    # Pattern 7: (sample -- thanks!!) or similar gratitude patterns
    gratitude_sample_match = re.search(r"\(sample[^)]*thanks[^)]*\)", remainder_lower)
    if gratitude_sample_match:
        return "sample", None, None

    # Pattern 8: (sample) with trailing punctuation
    trailing_punct_match = re.search(r"\(sample\)[^\w]", remainder_lower)
    if trailing_punct_match:
        return "sample", None, None

    # Pattern 9: (sample) with emojis or special characters
    emoji_sample_match = re.search(r"\(sample[^)]*[^\w\s][^)]*\)", remainder_lower)
    if emoji_sample_match:
        return "sample", None, None

    return None, None, None


def normalize_soap_suffixes(text: str) -> str:
    """
    Normalize soap text by removing common suffixes and indicators using iterative approach.

    This function removes various suffixes and indicators that are commonly
    found in soap descriptions but don't affect the core product identification.
    Uses a loop-based approach to ensure all patterns are applied until no more
    changes occur.

    Args:
        text: The soap text to normalize

    Returns:
        The normalized soap text with original case preserved
    """
    if not text or not text.strip():
        return text

    # Work with original case to preserve it
    current_text = text

    # Define all normalization patterns in order of priority
    # Higher priority patterns are applied first
    # Use case-insensitive matching with re.IGNORECASE flag
    normalization_patterns = [
        # Sample indicators in parentheses (highest priority)
        (r"\s*\(sample[^)]*\)\s*", re.IGNORECASE),  # (sample), (sample -- thanks!!), etc.
        (r"\s*\(tester[^)]*\)\s*", re.IGNORECASE),  # (tester), etc.
        (r"\s*\(samp[^)]*\)\s*", re.IGNORECASE),  # (samp), etc.
        # Size indicators in parentheses
        (r"\s*\(\d+oz\)\s*", re.IGNORECASE),  # (2oz), (4oz), etc.
        (r"\s*\(big\s+ass\s+og\s+\d+oz[^)]*\)\s*", re.IGNORECASE),  # (big ass og 4oz), etc.
        # Establishment date indicators
        (r"\s*\(est\.\s*\d+[^)]*\)\s*", re.IGNORECASE),  # (est. 1899), etc.
        # Base/formula indicators in parentheses
        (r"\s*\(premium\s+base\)\s*", re.IGNORECASE),
        (r"\s*\(luxury\s+base\)\s*", re.IGNORECASE),
        (r"\s*\(omnibus\s+base\)\s*", re.IGNORECASE),
        (r"\s*\(milksteak\)\s*", re.IGNORECASE),
        (r"\s*\(tusk\)\s*", re.IGNORECASE),
        (r"\s*\(professional\)\s*", re.IGNORECASE),
        (r"\s*\(tallow\s+base\)\s*", re.IGNORECASE),
        (r"\s*\(tallow\s+formulation\)\s*", re.IGNORECASE),
        (r"\s*\(tallow\)\s*", re.IGNORECASE),  # (tallow) standalone
        (r"\s*\(vegan\)\s*", re.IGNORECASE),
        # Trailing sample indicators (without parentheses)
        (r"\s*-\s*sample\s*$", re.IGNORECASE),  # "- sample" at end
        (r"\s*-\s*tester\s*$", re.IGNORECASE),  # "- tester" at end
        (r"\s*-\s*samp\s*$", re.IGNORECASE),  # "- samp" at end
        (r"\s+sample\s*$", re.IGNORECASE),  # "sample" at end (without dash)
        (r"\s+tester\s*$", re.IGNORECASE),  # "tester" at end (without dash)
        (r"\s+samp\s*$", re.IGNORECASE),  # "samp" at end (without dash)
        # Container type suffixes
        (
            r"\s*-\s*shave\s+stick\s*[.!?]*\s*$",
            re.IGNORECASE,
        ),  # "- shave stick" at end (with optional punctuation)
        (
            r"\s+shave\s+stick\s*[.!?]*\s*$",
            re.IGNORECASE,
        ),  # "shave stick" at end (without dash, with optional punctuation)
        (
            r"\s*-\s*stick\s*[.!?]*\s*$",
            re.IGNORECASE,
        ),  # "- stick" at end (with optional punctuation)
        (
            r"\s+stick\s*[.!?]*\s*$",
            re.IGNORECASE,
        ),  # "stick" at end (without dash, with optional punctuation)
        (r"\s*-\s*tube\s*[.!?]*\s*$", re.IGNORECASE),  # "- tube" at end (with optional punctuation)
        (
            r"\s+tube\s*[.!?]*\s*$",
            re.IGNORECASE,
        ),  # "tube" at end (without dash, with optional punctuation)
        (r"\s*-\s*hard\s*[.!?]*\s*$", re.IGNORECASE),  # "- hard" at end (with optional punctuation)
        (
            r"\s+hard\s*[.!?]*\s*$",
            re.IGNORECASE,
        ),  # "hard" at end (without dash, with optional punctuation)
        # Product type suffixes
        (
            r"\s*-\s*shaving\s+soap\s*[.!?]*\s*$",
            re.IGNORECASE,
        ),  # "- shaving soap" at end (with optional punctuation)
        (
            r"\s*-\s*crema\s+da\s+barba\s*[.!?]*\s*$",
            re.IGNORECASE,
        ),  # "- crema da barba" at end (with optional punctuation)
        (
            r"\s+crema\s+da\s+barba\s*[.!?]*\s*$",
            re.IGNORECASE,
        ),  # "crema da barba" at end (without dash, with optional punctuation)
        (r"\s*-\s*soap\s*[.!?]*\s*$", re.IGNORECASE),  # "- soap" at end (with optional punctuation)
        (r"\s*-\s*puck\s*[.!?]*\s*$", re.IGNORECASE),  # "- puck" at end (with optional punctuation)
        (
            r"\s+puck\s*[.!?]*\s*$",
            re.IGNORECASE,
        ),  # "puck" at end (without dash, with optional punctuation)
        (
            r"\s*-\s*croap\s*[.!?]*\s*$",
            re.IGNORECASE,
        ),  # "- croap" at end (with optional punctuation)
        (
            r"\s+soap\s*[.!?]*\s*$",
            re.IGNORECASE,
        ),  # "soap" at end (standalone, with optional punctuation)
        # General product suffixes that can appear anywhere
        (r"\s+crema\s+da\s+barba\s+", re.IGNORECASE),  # "crema da barba" anywhere (with spaces)
        # Standalone base/formula indicators (without parentheses)
        (r"\s*-\s*omnibus\s*$", re.IGNORECASE),  # "- omnibus" at end
        (r"\s+omnibus\s*$", re.IGNORECASE),  # "omnibus" at end (without dash)
        # Additional product type suffixes
        (
            r"\s*-\s*shaving\s*[.!?]*\s*$",
            re.IGNORECASE,
        ),  # "- shaving" at end (with optional punctuation)
        (
            r"\s+shaving\s*[.!?]*\s*$",
            re.IGNORECASE,
        ),  # "shaving" at end (without dash, with optional punctuation)
    ]

    # Apply normalization iteratively until no more changes occur
    previous_text = ""

    while previous_text != current_text:
        previous_text = current_text

        # Apply all patterns in order
        for pattern, flags in normalization_patterns:
            current_text = re.sub(pattern, "", current_text, flags=flags)

        # Clean up extra whitespace and dashes after each iteration
        current_text = re.sub(r"\s+", " ", current_text)  # Multiple spaces to single space
        current_text = re.sub(r"\s*-\s*$", "", current_text)  # Remove trailing dash
        current_text = re.sub(r"^\s*-\s*", "", current_text)  # Remove leading dash
        current_text = current_text.strip()

    return current_text
