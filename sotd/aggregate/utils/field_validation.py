#!/usr/bin/env python3
"""Field validation utilities for SOTD pipeline aggregators.

This module provides utilities for properly validating required fields in aggregator data,
distinguishing between missing fields (None) and empty values (empty strings, etc.).
"""

from typing import Any, Dict


def has_required_field(data: Dict[str, Any], field: str) -> bool:
    """Check if a required field exists and is not None (empty string is OK).

    Args:
        data: Dictionary containing the data to check
        field: Field name to check

    Returns:
        True if field exists and is not None, False otherwise

    Examples:
        >>> has_required_field({"brand": "Gillette", "model": ""}, "brand")
        True
        >>> has_required_field({"brand": "Gillette", "model": ""}, "model")
        True  # Empty string is valid
        >>> has_required_field({"brand": "Gillette", "model": ""}, "format")
        False  # Field doesn't exist
        >>> has_required_field({"brand": "Gillette", "model": None}, "model")
        False  # None is not valid
    """
    return field in data and data[field] is not None


def has_required_fields(data: Dict[str, Any], *fields: str) -> bool:
    """Check if multiple required fields exist and are not None.

    Args:
        data: Dictionary containing the data to check
        *fields: Field names to check

    Returns:
        True if all fields exist and are not None, False otherwise

    Examples:
        >>> has_required_fields({"brand": "Gillette", "model": ""}, "brand", "model")
        True
        >>> has_required_fields({"brand": "Gillette", "model": ""}, "brand", "format")
        False  # format field missing
    """
    return all(has_required_field(data, field) for field in fields)


def get_field_value(data: Dict[str, Any], field: str, default: str = "") -> str:
    """Get a field value as a stripped string, with proper None handling.

    Args:
        data: Dictionary containing the data
        field: Field name to get
        default: Default value if field is missing or None

    Returns:
        Stripped string value, or default if field is missing/None

    Examples:
        >>> get_field_value({"brand": "  Gillette  ", "model": ""}, "brand")
        "Gillette"
        >>> get_field_value({"brand": "  Gillette  ", "model": ""}, "model")
        ""  # Empty string preserved
        >>> get_field_value({"brand": "  Gillette  "}, "format")
        ""  # Default for missing field
    """
    value = data.get(field)
    if value is None:
        return default

    return str(value).strip()


def validate_aggregator_data(data: Dict[str, Any], required_fields: list[str]) -> bool:
    """Validate that aggregator data has all required fields.

    Args:
        data: Dictionary containing the data to validate
        required_fields: List of field names that must be present and not None

    Returns:
        True if all required fields are valid, False otherwise
    """
    return has_required_fields(data, *required_fields)
