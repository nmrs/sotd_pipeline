#!/usr/bin/env python3
"""Brush fiber aggregation using the base aggregator pattern."""

from typing import Any, Dict, Optional

from sotd.aggregate.base_aggregator import BaseAggregator


class FiberAggregator(BaseAggregator):
    """Aggregator for brush fiber usage statistics."""

    def get_operation_name(self) -> str:
        """Return the operation name for monitoring."""
        return "aggregate_brush_fibers"

    def get_product_type(self) -> str:
        """Return the product type being aggregated."""
        return "brush_fiber"

    def get_group_column(self) -> str:
        """Return the column name to group by."""
        return "fiber"

    def _extract_from_record(
        self, record: Dict[str, Any], record_index: int
    ) -> Optional[Dict[str, Any]]:
        """
        Extract brush fiber data from a single record.

        Args:
            record: Single enriched comment record
            record_index: Index of the record for debugging

        Returns:
            Extracted fiber data dictionary or None if invalid
        """
        # Extract brush info
        brush = record.get("brush", {})
        if not isinstance(brush, dict):
            return None

        # Check for matched data
        matched = brush.get("matched", {})
        if not isinstance(matched, dict):
            return None

        # Validate match_type if present
        if not self._validate_match_type(matched, record_index):
            return None

        # Extract fiber info
        fiber = matched.get("fiber")
        if not fiber:
            return None

        return {
            "fiber": fiber,
            "user": record.get("author", "Unknown"),
        }


def aggregate_brush_fibers(
    records: list[dict[str, Any]], debug: bool = False
) -> list[dict[str, Any]]:
    """
    Aggregate brush fiber usage statistics using the new base aggregator pattern.

    Args:
        records: List of enriched comment records
        debug: Enable debug logging

    Returns:
        List of brush fiber aggregation results

    Raises:
        ValueError: If records list is invalid or contains invalid data
    """
    aggregator = FiberAggregator(debug)
    return aggregator.aggregate(records)
