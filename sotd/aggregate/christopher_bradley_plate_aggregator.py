#!/usr/bin/env python3
"""Christopher Bradley plate aggregation using the base aggregator pattern."""

from typing import Any, Dict, Optional

from sotd.aggregate.base_aggregator import BaseAggregator


class ChristopherBradleyPlateAggregator(BaseAggregator):
    """Aggregator for Christopher Bradley plate usage statistics."""

    def get_operation_name(self) -> str:
        """Return the operation name for monitoring."""
        return "aggregate_christopher_bradley_plates"

    def get_product_type(self) -> str:
        """Return the product type being aggregated."""
        return "christopher_bradley_plate"

    def get_group_column(self) -> str:
        """Return the column name to group by."""
        return "plate"

    def _extract_from_record(
        self, record: Dict[str, Any], record_index: int
    ) -> Optional[Dict[str, Any]]:
        """
        Extract Christopher Bradley plate data from a single record.

        Args:
            record: Single enriched comment record
            record_index: Index of the record for debugging

        Returns:
            Extracted plate data dictionary or None if invalid
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

        # Check if it's a Christopher Bradley razor
        brand = (matched.get("brand") or "").lower()
        model = (matched.get("model") or "").lower()
        if brand != "karve" or "christopher bradley" not in model:
            return None

        # Try to extract enriched data from both possible locations
        enriched = record.get("enriched", {}).get("razor", {})
        if isinstance(enriched, dict) and enriched:
            if self.debug:
                print(f"[DEBUG] Record {record_index}: using record.enriched.razor")
        else:
            enriched = razor.get("enriched", {})
            if isinstance(enriched, dict) and enriched:
                if self.debug:
                    print(f"[DEBUG] Record {record_index}: using razor.enriched")
            else:
                if self.debug:
                    print(f"[DEBUG] Record {record_index}: no enriched data found")
                return None

        # Extract plate info
        plate_level = enriched.get("plate_level")
        plate_type = enriched.get("plate_type", "SB")
        if not plate_level:
            return None
        plate = f"{plate_level} {plate_type}".strip()
        return {
            "plate": plate,
            "user": record.get("author", "Unknown"),
        }


def aggregate_christopher_bradley_plates(
    records: list[dict[str, Any]], debug: bool = False
) -> list[dict[str, Any]]:
    """
    Aggregate Christopher Bradley plate usage statistics using the new base aggregator pattern.

    Args:
        records: List of enriched comment records
        debug: Enable debug logging

    Returns:
        List of Christopher Bradley plate aggregation results

    Raises:
        ValueError: If records list is invalid or contains invalid data
    """
    aggregator = ChristopherBradleyPlateAggregator(debug)
    return aggregator.aggregate(records)
