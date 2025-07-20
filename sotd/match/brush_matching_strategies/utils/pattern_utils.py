"""Pattern utilities for brush matching strategies.

This module provides common pattern compilation, validation, and matching logic
used across brush matching strategies to ensure consistency and maintainability.
"""

import re
from typing import Any, Dict, List, Optional

from sotd.match.brush_matching_strategies.utils.fiber_utils import match_fiber
from sotd.match.types import MatchResult, create_match_result


def validate_string_input(value: Any) -> Optional[str]:
    """Validate and normalize string input for pattern matching.

    Args:
        value: Input value to validate

    Returns:
        Normalized string if valid, None if invalid
    """
    if not isinstance(value, str):
        return None
    return value.strip()


def compile_patterns_with_metadata(
    patterns_data: List[Dict[str, Any]], sort_by_length: bool = True
) -> List[Dict[str, Any]]:
    """Compile regex patterns with metadata and optional sorting.

    Args:
        patterns_data: List of pattern dictionaries with 'pattern' key and metadata
        sort_by_length: Whether to sort patterns by length (descending)

    Returns:
        List of compiled patterns with metadata

    Example:
        patterns_data = [
            {
                'pattern': r'brand.*model',
                'brand': 'Brand',
                'model': 'Model',
                'fiber': 'Badger'
            }
        ]
    """
    compiled_patterns = []

    for pattern_data in patterns_data:
        if "pattern" not in pattern_data:
            continue

        pattern = pattern_data["pattern"]
        compiled = re.compile(pattern, re.IGNORECASE)

        compiled_pattern = {
            "compiled": compiled,
            "pattern": pattern,
            **{k: v for k, v in pattern_data.items() if k != "pattern"},
        }
        compiled_patterns.append(compiled_pattern)

    if sort_by_length:
        compiled_patterns.sort(key=lambda x: len(x["pattern"]), reverse=True)

    return compiled_patterns


def compile_catalog_patterns(
    catalog: Dict[str, Any],
    pattern_field: str = "patterns",
    metadata_fields: Optional[List[str]] = None,
) -> List[Dict[str, Any]]:
    """Compile patterns from a catalog structure with brand-level defaults.

    Args:
        catalog: Catalog dictionary with brand -> model -> metadata structure
        pattern_field: Field name containing the patterns list
        metadata_fields: Optional list of metadata fields to include

    Returns:
        List of compiled patterns with metadata

    Example catalog structure with brand-level defaults:
        {
            'Brand': {
                'fiber': 'Badger',           # Brand-level default
                'knot_size_mm': 28.0,        # Brand-level default
                'Model': {
                    'patterns': [r'brand.*model']
                    # Inherits fiber and knot_size_mm from brand level
                }
            }
        }
    """
    if metadata_fields is None:
        metadata_fields = ["fiber", "knot_size_mm", "handle_maker"]

    all_patterns = []

    for brand, models in catalog.items():
        if not isinstance(models, dict):
            continue

        # Extract brand-level defaults
        brand_defaults = {}
        for field in metadata_fields:
            if field in models:
                brand_defaults[field] = models[field]

        for model, metadata in models.items():
            if not isinstance(metadata, dict):
                continue

            patterns = metadata.get(pattern_field, [])
            if not patterns:
                continue

            # Extract metadata fields with brand-level defaults as fallback
            pattern_metadata = {
                "brand": brand,
                "model": model if model else None,
            }

            # Add metadata fields, using model-level values or brand-level defaults
            for field in metadata_fields:
                pattern_metadata[field] = metadata.get(field, brand_defaults.get(field))

            # Create pattern entries
            for pattern in patterns:
                pattern_entry = {"pattern": pattern, **pattern_metadata}
                all_patterns.append(pattern_entry)

    return compile_patterns_with_metadata(all_patterns)


def match_patterns_against_text(
    patterns: List[Dict[str, Any]], text: str, return_first_match: bool = True
) -> Optional[Dict[str, Any]]:
    """Match compiled patterns against text.

    Args:
        patterns: List of compiled patterns with metadata
        text: Text to match against
        return_first_match: Whether to return first match or continue searching

    Returns:
        Matched pattern with metadata if found, None otherwise
    """
    normalized_text = text.strip().lower()

    for pattern_entry in patterns:
        compiled_pattern = pattern_entry["compiled"]
        if compiled_pattern.search(normalized_text):
            return pattern_entry

        if return_first_match:
            break

    return None


def create_default_match_structure(
    brand: Optional[str] = None,
    model: Optional[str] = None,
    fiber: Optional[str] = None,
    knot_size_mm: Optional[float] = None,
    handle_maker: Optional[str] = None,
    source_text: Optional[str] = None,
    source_type: Optional[str] = None,
) -> Dict[str, Any]:
    """Create a standardized default match structure.

    Args:
        brand: Brand name
        model: Model name
        fiber: Fiber type
        knot_size_mm: Knot size in mm
        handle_maker: Handle maker
        source_text: Source text that was matched
        source_type: Type of match (e.g., 'exact', 'partial')

    Returns:
        Standardized match structure
    """
    return {
        "brand": brand,
        "model": model,
        "fiber": fiber,
        "knot_size_mm": knot_size_mm,
        "handle_maker": handle_maker,
        "source_text": source_text,
        "source_type": source_type,
    }


def create_strategy_result(
    original_value: Any,
    matched_data: Optional[Dict[str, Any]],
    pattern: Optional[str],
    strategy_name: str,
    match_type: Optional[str] = None,
) -> MatchResult:
    """Create a standardized strategy result as a MatchResult."""
    return create_match_result(
        original=original_value,
        matched=matched_data,
        match_type=match_type,
        pattern=pattern,
    )


def validate_catalog_structure(
    catalog: Dict[str, Any], required_fields: List[str], catalog_name: str = "catalog"
) -> None:
    """Validate catalog structure for brush strategies.

    Args:
        catalog: Catalog to validate
        required_fields: List of required fields for each entry
        catalog_name: Name of the catalog for error messages

    Raises:
        ValueError: If catalog structure is invalid
    """
    if not isinstance(catalog, dict):
        raise ValueError(f"{catalog_name} must be a dictionary")

    for brand, metadata in catalog.items():
        if not isinstance(metadata, dict):
            raise ValueError(
                f"Invalid {catalog_name} structure for brand '{brand}': must be a dictionary"
            )

        missing_fields = [field for field in required_fields if field not in metadata]
        if missing_fields:
            raise ValueError(
                f"Missing required fields for brand '{brand}' in {catalog_name}: {missing_fields}"
            )

        # Validate patterns field if present
        if "patterns" in metadata:
            patterns = metadata["patterns"]
            if not isinstance(patterns, list):
                raise ValueError(
                    f"'patterns' field must be a list for brand '{brand}' in {catalog_name}"
                )


def extract_pattern_metadata(
    pattern_entry: Dict[str, Any],
    text: str,
    default_fiber: Optional[str] = None,
    default_knot_size_mm: Optional[float] = None,
) -> Dict[str, Any]:
    """Extract metadata from a pattern match with defaults.

    Args:
        pattern_entry: Pattern entry with metadata
        text: Original text that was matched
        default_fiber: Default fiber type if not in pattern entry
        default_knot_size_mm: Default knot size if not in pattern entry

    Returns:
        Extracted metadata dictionary
    """
    metadata = {
        "brand": pattern_entry.get("brand"),
        "model": pattern_entry.get("model"),
        "fiber": pattern_entry.get("fiber", default_fiber),
        "knot_size_mm": pattern_entry.get("knot_size_mm", default_knot_size_mm),
        "handle_maker": pattern_entry.get("handle_maker"),
        "source_text": text,
        "source_type": "exact",
    }

    # Remove None values
    return {k: v for k, v in metadata.items() if v is not None}


def extract_knot_size(text: str) -> Optional[float]:
    """Extract knot size in mm from text.

    This is a shared utility used by both brush matcher and brush enricher.
    """
    if not text:
        return None

    # Look for standalone number with 'mm' (highest priority)
    match = re.search(r"\b(\d+(?:\.\d+)?)\s*mm?\b", text, re.IGNORECASE)
    if match:
        return float(match.group(1))

    # Look for patterns like '27x50' or '27.5x50' (take first number)
    match = re.search(r"(\d+(?:\.\d+)?)\s*[x×]\s*\d+(?:\.\d+)?", text)
    if match:
        return float(match.group(1))

    # Fallback: any number in the text (but be more conservative)
    # Only match numbers that could reasonably be knot sizes (20-35mm range)
    # Include decimals in the range
    match = re.search(r"\b(2[0-9](?:\.\d+)?|3[0-5](?:\.\d+)?)\b", text)
    if match:
        return float(match.group(1))

    return None


def has_knot_indicators(text: str) -> bool:
    """Check if text has indicators that suggest it's a knot rather than a handle."""
    if not text:
        return False

    # Check for fiber types
    if match_fiber(text):
        return True

    # Check for size patterns
    if extract_knot_size(text):
        return True

    # Check for version patterns (V20, B15, etc.)
    if re.search(r"\b[vb]\d+\b", text.lower()):
        return True

    return False


def has_handle_indicators(text: str) -> bool:
    """Check if text has indicators that suggest it's a handle rather than a knot."""
    if not text:
        return False

    # Explicit handle keyword
    if "handle" in text.lower():
        return True

    # Handle-specific terms
    handle_terms = ["stock", "turned", "wood", "resin"]
    for term in handle_terms:
        if term in text.lower():
            return True

    return False


def score_match_type(text: str, match_type: str, pattern_score: int) -> int:
    """Score a potential match based on text indicators.

    Args:
        text: The text being matched
        match_type: Either "handle" or "knot"
        pattern_score: Base score from pattern matching

    Returns:
        Adjusted score - higher scores favor the match type
    """
    score = pattern_score

    if match_type == "handle":
        # Handle indicators increase score for handle matches
        if has_handle_indicators(text):
            score += 10
    elif match_type == "knot":
        # Knot indicators decrease score for handle matches (increase for knot matches)
        if has_knot_indicators(text):
            score -= 8

    return score
