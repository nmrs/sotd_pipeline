#!/usr/bin/env python3
"""Razor and blade combination aggregation using the base aggregator pattern."""

from typing import Any, Dict, Optional

from sotd.aggregate.base_aggregator import BaseAggregator


class RazorBladeComboAggregator(BaseAggregator):
    """Aggregator for razor and blade combination usage statistics."""

    def get_operation_name(self) -> str:
        """Return the operation name for monitoring."""
        return "aggregate_razor_blade_combinations"

    def get_product_type(self) -> str:
        """Return the product type being aggregated."""
        return "razor_blade_combo"

    def get_group_column(self) -> str:
        """Return the column name to group by."""
        return "combination"

    def _extract_from_record(
        self, record: Dict[str, Any], record_index: int
    ) -> Optional[Dict[str, Any]]:
        """
        Extract razor and blade combination data from a single record.

        Args:
            record: Single enriched comment record
            record_index: Index of the record for debugging

        Returns:
            Extracted combination data dictionary or None if invalid
        """
        # Extract razor info
        razor = record.get("razor", {})
        if not isinstance(razor, dict) or "matched" not in razor:
            return None

        razor_matched = razor["matched"]
        if not isinstance(razor_matched, dict):
            return None

        razor_brand = razor_matched.get("brand")
        razor_model = razor_matched.get("model")
        if not razor_brand or not razor_model:
            return None

        # Validate razor match_type if present
        if not self._validate_match_type(razor_matched, record_index):
            return None

        # Extract blade info
        blade = record.get("blade", {})
        if not isinstance(blade, dict) or "matched" not in blade:
            return None

        blade_matched = blade["matched"]
        if not isinstance(blade_matched, dict):
            return None

        blade_brand = blade_matched.get("brand")
        blade_model = blade_matched.get("model")
        if not blade_brand or not blade_model:
            return None

        # Validate blade match_type if present
        if not self._validate_match_type(blade_matched, record_index):
            return None

        # Create combination name
        combination = f"{razor_brand} {razor_model} + {blade_brand} {blade_model}"

        return {
            "combination": combination,
            "razor_brand": razor_brand,
            "razor_model": razor_model,
            "blade_brand": blade_brand,
            "blade_model": blade_model,
            "user": record.get("author", "Unknown"),
        }


def aggregate_razor_blade_combinations(
    records: list[dict[str, Any]], debug: bool = False
) -> list[dict[str, Any]]:
    """
    Aggregate razor and blade combination usage statistics using the new base aggregator pattern.

    Args:
        records: List of enriched comment records
        debug: Enable debug logging

    Returns:
        List of razor and blade combination aggregation results

    Raises:
        ValueError: If records list is invalid or contains invalid data
    """
    aggregator = RazorBladeComboAggregator(debug)
    return aggregator.aggregate(records)
