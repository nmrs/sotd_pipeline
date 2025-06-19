#!/usr/bin/env python3
"""Razor-specific aggregation using the base aggregator pattern."""

from typing import Any, Dict, Optional

from sotd.aggregate.base_aggregator import BaseAggregator


class RazorAggregator(BaseAggregator):
    """Aggregator for razor usage statistics."""

    def get_operation_name(self) -> str:
        """Return the operation name for monitoring."""
        return "aggregate_razors"

    def get_product_type(self) -> str:
        """Return the product type being aggregated."""
        return "razor"

    def get_group_column(self) -> str:
        """Return the column name to group by."""
        return "name"

    def _extract_from_record(
        self, record: Dict[str, Any], record_index: int
    ) -> Optional[Dict[str, Any]]:
        """
        Extract razor data from a single record.

        Args:
            record: Single enriched comment record
            record_index: Index of the record for debugging

        Returns:
            Extracted razor data dictionary or None if invalid
        """
        if "razor" not in record:
            return None

        razor_info = record["razor"]
        if not isinstance(razor_info, dict) or "matched" not in razor_info:
            return None

        matched = razor_info["matched"]
        if not isinstance(matched, dict) or not matched.get("brand"):
            return None

        # Validate match_type if present
        if not self._validate_match_type(matched, record_index):
            return None

        # Extract razor name from matched data
        brand = matched.get("brand", "")
        model = matched.get("model", "")
        format_type = matched.get("format", "")

        # Create a descriptive razor name
        razor_name_parts = []
        if brand:
            razor_name_parts.append(brand)
        if model:
            razor_name_parts.append(model)
        if format_type:
            razor_name_parts.append(format_type)

        razor_name = " ".join(razor_name_parts) if razor_name_parts else "Unknown Razor"

        return {
            "name": razor_name,
            "brand": brand,
            "model": model,
            "format": format_type,
            "user": record.get("author", "Unknown"),
        }


def aggregate_razors(records: list[dict[str, Any]], debug: bool = False) -> list[dict[str, Any]]:
    """
    Aggregate razor usage statistics using the new base aggregator pattern.

    Args:
        records: List of enriched comment records
        debug: Enable debug logging

    Returns:
        List of razor aggregation results

    Raises:
        ValueError: If records list is invalid or contains invalid data
    """
    aggregator = RazorAggregator(debug)
    return aggregator.aggregate(records)
