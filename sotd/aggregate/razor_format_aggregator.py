#!/usr/bin/env python3
"""Razor format-specific aggregation using the base aggregator pattern."""

from typing import Any, Dict, Optional

from sotd.aggregate.base_aggregator import BaseAggregator


class RazorFormatAggregator(BaseAggregator):
    """Aggregator for razor format usage statistics."""

    def get_operation_name(self) -> str:
        """Return the operation name for monitoring."""
        return "aggregate_razor_formats"

    def get_product_type(self) -> str:
        """Return the product type being aggregated."""
        return "razor_format"

    def get_group_column(self) -> str:
        """Return the column name to group by."""
        return "format"

    def _extract_from_record(
        self, record: Dict[str, Any], record_index: int
    ) -> Optional[Dict[str, Any]]:
        """
        Extract razor format data from a single record.

        Args:
            record: Single enriched comment record
            record_index: Index of the record for debugging

        Returns:
            Extracted razor format data dictionary or None if invalid
        """
        if "razor" not in record:
            return None

        razor_info = record["razor"]
        if not isinstance(razor_info, dict) or "matched" not in razor_info:
            return None

        matched = razor_info["matched"]
        if not isinstance(matched, dict) or not matched.get("format"):
            return None

        # Validate match_type if present
        if not self._validate_match_type(matched, record_index):
            return None

        format_type = matched.get("format", "")
        if not format_type:
            return None

        return {
            "format": format_type,
            "user": record.get("author", "Unknown"),
        }


def aggregate_razor_formats(
    records: list[dict[str, Any]], debug: bool = False
) -> list[dict[str, Any]]:
    """
    Aggregate razor format usage statistics using the new base aggregator pattern.

    Args:
        records: List of enriched comment records
        debug: Enable debug logging

    Returns:
        List of razor format aggregation results

    Raises:
        ValueError: If records list is invalid or contains invalid data
    """
    aggregator = RazorFormatAggregator(debug)
    return aggregator.aggregate(records)
