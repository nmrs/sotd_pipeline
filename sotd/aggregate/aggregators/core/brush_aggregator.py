from typing import Any, Dict, List

import pandas as pd

from ...utils.field_validation import get_field_value, has_required_fields
from ..base_aggregator import BaseAggregator


class BrushAggregator(BaseAggregator):
    """Aggregator for brush data from enriched records."""

    @property
    def IDENTIFIER_FIELDS(self) -> List[str]:
        """Fields used for matching/grouping."""
        return ["name", "fiber"]

    @property
    def METRIC_FIELDS(self) -> List[str]:
        """Calculated/metric fields."""
        return ["shaves", "unique_users"]

    @property
    def RANKING_FIELDS(self) -> List[str]:
        """Fields used for sorting/ranking."""
        return ["shaves", "unique_users"]

    def _extract_data(self, records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Extract brush data from records for aggregation.

        Args:
            records: List of enriched comment records

        Returns:
            List of dictionaries with extracted brush data fields
        """
        brush_data = []
        for record in records:
            brush = record.get("brush") or {}
            matched = brush.get("matched", {})

            # Skip if no matched brush data or missing required fields
            # Note: Empty strings are valid values, only None is invalid
            if not matched or not has_required_fields(matched, "brand", "model"):
                continue

            brand = get_field_value(matched, "brand")
            model = get_field_value(matched, "model")
            # Look for fiber in nested knot structure, with fallback to root level
            knot = matched.get("knot", {})
            fiber = get_field_value(knot, "fiber") or get_field_value(matched, "fiber")
            author = get_field_value(record, "author")

            if brand and author:  # model and fiber can be empty strings, which is valid
                brush_data.append(
                    {"brand": brand, "model": model, "fiber": fiber, "author": author}
                )

        return brush_data

    def _create_composite_name(self, df: pd.DataFrame) -> pd.Series:
        """Create composite name from brand and model.

        Args:
            df: DataFrame with extracted brush data

        Returns:
            Series with composite names in "Brand Model" format
        """
        # Handle None values by converting to empty strings and concatenate properly
        brand = df["brand"].fillna("")
        model = df["model"].fillna("")
        # Use pandas string concatenation to avoid Series ambiguity
        return brand.astype(str) + " " + model.astype(str)

    def _get_group_columns(self, df: pd.DataFrame) -> List[str]:
        """Get columns to use for grouping.

        Args:
            df: DataFrame with extracted brush data

        Returns:
            List of column names for grouping (name and fiber)
        """
        return ["name", "fiber"]


# Legacy function interface for backward compatibility
def aggregate_brushes(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Aggregate brush data from enriched records.

    Returns a list of brush aggregations sorted by shaves desc, unique_users desc.
    Each item includes position field for delta calculations.

    Args:
        records: List of enriched comment records

    Returns:
        List of brush aggregations with position, name, shaves, and unique_users fields
    """
    aggregator = BrushAggregator()
    return aggregator.aggregate(records)
