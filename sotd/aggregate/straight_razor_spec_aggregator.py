#!/usr/bin/env python3
"""Straight razor specification aggregation using the base aggregator pattern."""

from typing import Any, Dict, Optional

from sotd.aggregate.base_aggregator import BaseAggregator


class StraightRazorSpecAggregator(BaseAggregator):
    """Aggregator for straight razor specification usage statistics."""

    def get_operation_name(self) -> str:
        """Return the operation name for monitoring."""
        return "aggregate_straight_razor_specs"

    def get_product_type(self) -> str:
        """Return the product type being aggregated."""
        return "straight_razor_spec"

    def get_group_column(self) -> str:
        """Return the column name to group by."""
        return "specs"

    def _extract_from_record(
        self, record: Dict[str, Any], record_index: int
    ) -> Optional[Dict[str, Any]]:
        """
        Extract straight razor specification data from a single record.

        Args:
            record: Single enriched comment record
            record_index: Index of the record for debugging

        Returns:
            Extracted specification data dictionary or None if invalid
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

        # Check if it's a straight razor
        format_type = (matched.get("format") or "").lower()
        if format_type != "straight":
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

        # Extract specifications
        grind = enriched.get("grind")
        width = enriched.get("width")
        point = enriched.get("point")

        # Build specification parts
        spec_parts = []
        if grind:
            spec_parts.append(f"Grind: {grind}")
        if width:
            spec_parts.append(f"Width: {width}")
        if point:
            spec_parts.append(f"Point: {point}")

        # Skip if no specifications found
        if not spec_parts:
            return None

        # Join specifications
        specs = " | ".join(spec_parts)

        return {
            "specs": specs,
            "grind": grind,
            "width": width,
            "point": point,
            "user": record.get("author", "Unknown"),
        }


def aggregate_straight_razor_specs(
    records: list[dict[str, Any]], debug: bool = False
) -> list[dict[str, Any]]:
    """
    Aggregate straight razor specification usage statistics using the new base aggregator pattern.

    Args:
        records: List of enriched comment records
        debug: Enable debug logging

    Returns:
        List of straight razor specification aggregation results

    Raises:
        ValueError: If records list is invalid or contains invalid data
    """
    aggregator = StraightRazorSpecAggregator(debug)
    return aggregator.aggregate(records)
