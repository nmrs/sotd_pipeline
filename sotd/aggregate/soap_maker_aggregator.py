#!/usr/bin/env python3
"""Soap maker-specific aggregation using the base aggregator pattern."""

from typing import Any, Dict, Optional

from sotd.aggregate.base_aggregator import BaseAggregator


class SoapMakerAggregator(BaseAggregator):
    """Aggregator for soap maker usage statistics."""

    def get_operation_name(self) -> str:
        """Return the operation name for monitoring."""
        return "aggregate_soap_makers"

    def get_product_type(self) -> str:
        """Return the product type being aggregated."""
        return "soap_maker"

    def get_group_column(self) -> str:
        """Return the column name to group by."""
        return "maker"

    def _extract_from_record(
        self, record: Dict[str, Any], record_index: int
    ) -> Optional[Dict[str, Any]]:
        """
        Extract soap maker data from a single record.

        Args:
            record: Single enriched comment record
            record_index: Index of the record for debugging

        Returns:
            Extracted soap maker data dictionary or None if invalid
        """
        if "soap" not in record:
            return None

        soap_info = record["soap"]
        if not isinstance(soap_info, dict) or "matched" not in soap_info:
            return None

        matched = soap_info["matched"]
        if not isinstance(matched, dict) or not matched.get("maker"):
            return None

        # Validate match_type if present
        if not self._validate_match_type(matched, record_index):
            return None

        maker = matched.get("maker", "")
        if not maker:
            return None

        return {
            "maker": maker,
            "user": record.get("author", "Unknown"),
        }


def aggregate_soap_makers(
    records: list[dict[str, Any]], debug: bool = False
) -> list[dict[str, Any]]:
    """
    Aggregate soap maker usage statistics using the new base aggregator pattern.

    Args:
        records: List of enriched comment records
        debug: Enable debug logging

    Returns:
        List of soap maker aggregation results

    Raises:
        ValueError: If records list is invalid or contains invalid data
    """
    aggregator = SoapMakerAggregator(debug)
    return aggregator.aggregate(records)
