#!/usr/bin/env python3
"""Super Speed tip aggregation using the base aggregator pattern."""

from typing import Any, Dict, Optional

from sotd.aggregate.base_aggregator import BaseAggregator


class SuperSpeedTipAggregator(BaseAggregator):
    """Aggregator for Super Speed tip usage statistics."""

    def get_operation_name(self) -> str:
        """Return the operation name for monitoring."""
        return "aggregate_super_speed_tips"

    def get_product_type(self) -> str:
        """Return the product type being aggregated."""
        return "super_speed_tip"

    def get_group_column(self) -> str:
        """Return the column name to group by."""
        return "tip"

    def _extract_from_record(
        self, record: Dict[str, Any], record_index: int
    ) -> Optional[Dict[str, Any]]:
        """
        Extract Super Speed tip data from a single record.

        Args:
            record: Single enriched comment record
            record_index: Index of the record for debugging

        Returns:
            Extracted tip data dictionary or None if invalid
        """
        # Extract razor info
        razor = record.get("razor", {})
        if not isinstance(razor, dict):
            return None

        # Check for matched data
        matched = razor.get("matched", {})
        if not isinstance(matched, dict):
            return None

        # Validate match_type if present
        if not self._validate_match_type(matched, record_index):
            return None

        # Check if it's a Super Speed razor
        brand = (matched.get("brand") or "").lower()
        model = (matched.get("model") or "").lower()
        if brand != "gillette" or "super speed" not in model:
            return None

        # Extract enriched data
        enriched = razor.get("enriched", {})
        if not isinstance(enriched, dict):
            return None

        # Extract tip info
        tip = enriched.get("super_speed_tip")
        if not tip:
            return None

        return {
            "tip": tip,
            "user": record.get("author", "Unknown"),
        }


def aggregate_super_speed_tips(
    records: list[dict[str, Any]], debug: bool = False
) -> list[dict[str, Any]]:
    """
    Aggregate Super Speed tip usage statistics using the new base aggregator pattern.

    Args:
        records: List of enriched comment records
        debug: Enable debug logging

    Returns:
        List of Super Speed tip aggregation results

    Raises:
        ValueError: If records list is invalid or contains invalid data
    """
    aggregator = SuperSpeedTipAggregator(debug)
    return aggregator.aggregate(records)
