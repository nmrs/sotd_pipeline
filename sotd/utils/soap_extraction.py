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
    Normalize common soap suffixes to reduce variations in product matching.

    This function removes or standardizes common suffixes that don't affect
    the core product identification but create unnecessary variations.

    Does NOT normalize version indicators as these distinguish between different products.

    Args:
        text: The soap product text to normalize

    Returns:
        Normalized text with common suffixes removed/standardized
    """
    if not text:
        return text

    # Convert to lowercase for consistent matching
    text_lower = text.lower()

    # Process patterns in order of specificity (longer patterns first)
    # This prevents partial matches from interfering with complete matches

    # Remove sample indicators in parentheses (most specific first)
    sample_patterns = [
        r"\s*\(sample[^)]*\)\s*$",  # (sample), (sample -- thanks!!), etc.
        r"\s*\(tester[^)]*\)\s*$",  # (tester), etc.
        r"\s*\(samp[^)]*\)\s*$",  # (samp), etc.
    ]

    for pattern in sample_patterns:
        text_lower = re.sub(pattern, "", text_lower)

    # Remove size indicators in parentheses
    text_lower = re.sub(r"\s*\(\d+oz\)\s*$", "", text_lower)
    text_lower = re.sub(r"\s*\(big\s+ass\s+og\s+\d+oz[^)]*\)\s*$", "", text_lower)

    # Remove establishment date indicators
    text_lower = re.sub(r"\s*\(est\.\s*\d+[^)]*\)\s*$", "", text_lower)  # (est. 1899), etc.

    # Remove base/formula indicators in parentheses
    base_patterns = [
        r"\s*\(premium\s+base\)\s*$",
        r"\s*\(luxury\s+base\)\s*$",
        r"\s*\(omnibus\s+base\)\s*$",
        r"\s*\(milksteak\)\s*$",
        r"\s*\(tusk\)\s*$",
        r"\s*\(professional\)\s*$",
        r"\s*\(tallow\s+base\)\s*$",
        r"\s*\(tallow\s+formulation\)\s*$",
        r"\s*\(tallow\)\s*$",  # (tallow) standalone
        r"\s*\(vegan\)\s*$",
    ]

    for pattern in base_patterns:
        text_lower = re.sub(pattern, "", text_lower)

    # Remove container type suffixes (longer patterns first)
    container_suffixes = [
        r"\s*-\s*shave\s+stick\s*$",  # "- shave stick" at end
        r"\s+shave\s+stick\s*$",  # "shave stick" at end (without dash)
        r"\s*-\s*stick\s*$",  # "- stick" at end
        r"\s+stick\s*$",  # "stick" at end (without dash)
        r"\s*-\s*tube\s*$",  # "- tube" at end
        r"\s+tube\s*$",  # "tube" at end (without dash)
        r"\s*-\s*hard\s*$",  # "- hard" at end
        r"\s+hard\s*$",  # "hard" at end (without dash)
    ]

    for pattern in container_suffixes:
        text_lower = re.sub(pattern, "", text_lower)

    # Remove product type suffixes (longer patterns first)
    product_suffixes = [
        r"\s*-\s*shaving\s+soap\s*$",  # "- shaving soap" at end
        r"\s*-\s*crema\s+da\s+barba\s*$",  # "- crema da barba" at end
        r"\s+crema\s+da\s+barba\s*$",  # "crema da barba" at end (without dash)
        r"\s*-\s*soap\s*$",  # "- soap" at end
        r"\s*-\s*puck\s*$",  # "- puck" at end
        r"\s*-\s*croap\s*$",  # "- croap" at end
        r"\s+soap\s*$",  # "soap" at end (standalone)
    ]

    # Remove product type suffixes that can appear anywhere (not just at end)
    general_product_suffixes = [
        r"\s+crema\s+da\s+barba\s+",  # "crema da barba" anywhere (with spaces)
    ]

    for pattern in general_product_suffixes:
        text_lower = re.sub(pattern, " ", text_lower)

    for pattern in product_suffixes:
        text_lower = re.sub(pattern, "", text_lower)

    # Remove standalone base/formula indicators (without parentheses)
    standalone_base_patterns = [
        r"\s*-\s*omnibus\s*$",  # "- omnibus" at end
        r"\s+omnibus\s*$",  # "omnibus" at end (without dash)
    ]

    for pattern in standalone_base_patterns:
        text_lower = re.sub(pattern, "", text_lower)

    # Remove trailing sample indicators (without parentheses)
    trailing_sample_patterns = [
        r"\s*-\s*sample\s*$",  # "- sample" at end
        r"\s*-\s*tester\s*$",  # "- tester" at end
        r"\s*-\s*samp\s*$",  # "- samp" at end
        r"\s+sample\s*$",  # "sample" at end (without dash)
        r"\s+tester\s*$",  # "tester" at end (without dash)
        r"\s+samp\s*$",  # "samp" at end (without dash)
    ]

    for pattern in trailing_sample_patterns:
        text_lower = re.sub(pattern, "", text_lower)

    # Clean up extra whitespace and dashes
    text_lower = re.sub(r"\s*-\s*$", "", text_lower)  # Remove trailing dash
    text_lower = re.sub(r"\s+", " ", text_lower)  # Normalize whitespace
    text_lower = text_lower.strip()

    return text_lower
