#!/usr/bin/env python3
"""Brush knot size aggregation using the base aggregator pattern."""

from typing import Any, Dict, Optional

from sotd.aggregate.base_aggregator import BaseAggregator


class KnotSizeAggregator(BaseAggregator):
    """Aggregator for brush knot size usage statistics."""

    def get_operation_name(self) -> str:
        """Return the operation name for monitoring."""
        return "aggregate_brush_knot_sizes"

    def get_product_type(self) -> str:
        """Return the product type being aggregated."""
        return "brush_knot_size"

    def get_group_column(self) -> str:
        """Return the column name to group by."""
        return "knot_size_mm"

    def _extract_from_record(
        self, record: Dict[str, Any], record_index: int
    ) -> Optional[Dict[str, Any]]:
        """
        Extract brush knot size data from a single record.

        Args:
            record: Single enriched comment record
            record_index: Index of the record for debugging

        Returns:
            Extracted knot size data dictionary or None if invalid
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

        # Extract knot size info
        knot_size = matched.get("knot_size_mm")
        if not knot_size:
            return None

        # Format knot size as string (no mm suffix)
        knot_size_str = str(knot_size)

        return {
            "knot_size_mm": knot_size_str,
            "user": record.get("author", "Unknown"),
        }


def aggregate_brush_knot_sizes(
    records: list[dict[str, Any]], debug: bool = False
) -> list[dict[str, Any]]:
    """
    Aggregate brush knot size usage statistics using the new base aggregator pattern.

    Args:
        records: List of enriched comment records
        debug: Enable debug logging

    Returns:
        List of brush knot size aggregation results

    Raises:
        ValueError: If records list is invalid or contains invalid data
    """
    aggregator = KnotSizeAggregator(debug)
    return aggregator.aggregate(records)
