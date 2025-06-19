#!/usr/bin/env python3
"""Blackbird plate aggregation using the base aggregator pattern."""

from typing import Any, Dict, Optional

from sotd.aggregate.base_aggregator import BaseAggregator


class BlackbirdPlateAggregator(BaseAggregator):
    """Aggregator for Blackbird plate usage statistics."""

    def get_operation_name(self) -> str:
        """Return the operation name for monitoring."""
        return "aggregate_blackbird_plates"

    def get_product_type(self) -> str:
        """Return the product type being aggregated."""
        return "blackbird_plate"

    def get_group_column(self) -> str:
        """Return the column name to group by."""
        return "plate"

    def _extract_from_record(
        self, record: Dict[str, Any], record_index: int
    ) -> Optional[Dict[str, Any]]:
        """
        Extract Blackbird plate data from a single record.

        Args:
            record: Single enriched comment record
            record_index: Index of the record for debugging

        Returns:
            Extracted plate data dictionary or None if invalid
        """
        # Extract razor info
        razor = record.get("razor", {})
        if not isinstance(razor, dict):
            if self.debug:
                print(f"[DEBUG] Record {record_index}: razor is not a dict")
            return None

        # Check for matched data
        matched = razor.get("matched", {})
        if not isinstance(matched, dict):
            if self.debug:
                print(f"[DEBUG] Record {record_index}: matched is not a dict")
            return None

        # Validate match_type if present
        if not self._validate_match_type(matched, record_index):
            if self.debug:
                print(f"[DEBUG] Record {record_index}: match_type invalid or missing")
            return None

        # Check if it's a Blackbird razor
        brand = (matched.get("brand") or "").lower()
        model = (matched.get("model") or "").lower()
        if brand != "blackland" or "blackbird" not in model:
            if self.debug:
                print(
                    f"[DEBUG] Record {record_index}: not a Blackland Blackbird "
                    f"(brand={brand}, model={model})"
                )
            return None

        # Extract enriched data from unified structure
        enriched = razor.get("enriched", {})
        if not isinstance(enriched, dict):
            if self.debug:
                print(f"[DEBUG] Record {record_index}: razor.enriched is not a dict")
            return None

        # Extract plate info
        plate = enriched.get("plate")
        if not plate:
            if self.debug:
                print(f"[DEBUG] Record {record_index}: plate missing in enriched")
            return None

        if self.debug:
            print(f"[DEBUG] Record {record_index}: Found Blackbird plate: {plate}")

        return {
            "plate": plate,
            "user": record.get("author", "Unknown"),
        }


def aggregate_blackbird_plates(
    records: list[dict[str, Any]], debug: bool = False
) -> list[dict[str, Any]]:
    """
    Aggregate Blackbird plate usage statistics using the new base aggregator pattern.

    Args:
        records: List of enriched comment records
        debug: Enable debug logging

    Returns:
        List of Blackbird plate aggregation results

    Raises:
        ValueError: If records list is invalid or contains invalid data
    """
    aggregator = BlackbirdPlateAggregator(debug)
    return aggregator.aggregate(records)
