#!/usr/bin/env python3
"""Brush handle maker aggregation using the base aggregator pattern."""

from typing import Any, Dict, Optional

from sotd.aggregate.base_aggregator import BaseAggregator


class HandleMakerAggregator(BaseAggregator):
    """Aggregator for brush handle maker usage statistics."""

    def get_operation_name(self) -> str:
        """Return the operation name for monitoring."""
        return "aggregate_brush_handle_makers"

    def get_product_type(self) -> str:
        """Return the product type being aggregated."""
        return "brush_handle_maker"

    def get_group_column(self) -> str:
        """Return the column name to group by."""
        return "handle_maker"

    def _extract_from_record(
        self, record: Dict[str, Any], record_index: int
    ) -> Optional[Dict[str, Any]]:
        """
        Extract brush handle maker data from a single record.

        Args:
            record: Single enriched comment record
            record_index: Index of the record for debugging

        Returns:
            Extracted handle maker data dictionary or None if invalid
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

        # Extract handle maker info
        handle_maker = matched.get("handle_maker")
        if not handle_maker:
            return None

        return {
            "handle_maker": handle_maker,
            "user": record.get("author", "Unknown"),
        }


def aggregate_brush_handle_makers(
    records: list[dict[str, Any]], debug: bool = False
) -> list[dict[str, Any]]:
    """
    Aggregate brush handle maker usage statistics using the new base aggregator pattern.

    Args:
        records: List of enriched comment records
        debug: Enable debug logging

    Returns:
        List of brush handle maker aggregation results

    Raises:
        ValueError: If records list is invalid or contains invalid data
    """
    aggregator = HandleMakerAggregator(debug)
    return aggregator.aggregate(records)
