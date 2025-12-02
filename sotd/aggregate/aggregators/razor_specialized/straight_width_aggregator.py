from typing import Any, Dict, List

import pandas as pd

from ...utils.field_validation import get_field_value, has_required_field
from ..base_aggregator import BaseAggregator


class StraightWidthAggregator(BaseAggregator):
    """Aggregator for straight razor width data from enriched records."""

    @property
    def IDENTIFIER_FIELDS(self) -> List[str]:
        """Fields used for matching/grouping."""
        return ["width"]

    @property
    def METRIC_FIELDS(self) -> List[str]:
        """Calculated/metric fields."""
        return ["shaves", "unique_users"]

    @property
    def RANKING_FIELDS(self) -> List[str]:
        """Fields used for sorting/ranking."""
        return ["shaves", "unique_users"]

    def _extract_data(self, records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Extract straight razor width data from records for aggregation.

        Args:
            records: List of enriched comment records

        Returns:
            List of dictionaries with extracted straight razor width data fields
        """
        width_data = []
        for record in records:
            razor = record.get("razor") or {}
            enriched = razor.get("enriched", {})

            # Skip if no enriched razor data or missing required fields
            # Note: Empty strings are valid values, only None is invalid
            if not enriched or not has_required_field(enriched, "width"):
                continue

            width = get_field_value(enriched, "width")
            author = get_field_value(record, "author")

            if width and author:  # width can be empty string, which is valid
                width_data.append({"width": width, "author": author})

        return width_data

    def _create_composite_name(self, df: pd.DataFrame) -> pd.Series:
        """Create composite name from width.

        Args:
            df: DataFrame with extracted straight razor width data

        Returns:
            Series with width values
        """
        # Handle None values by converting to empty strings and concatenate properly
        # Ensure we get a Series, not DataFrame
        width_series: pd.Series = df["width"]  # type: ignore
        width = width_series.fillna("")
        # Use pandas string conversion to avoid Series ambiguity
        return width.astype(str)

    def _get_group_columns(self, df: pd.DataFrame) -> List[str]:
        """Get columns to use for grouping."""
        return ["width"]


# Legacy function interface for backward compatibility
def aggregate_straight_widths(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Aggregate straight razor width data from enriched records.

    Returns a list of straight razor width aggregations sorted by shaves desc,
    unique_users desc. Each item includes position field for delta calculations.

    Args:
        records: List of enriched comment records

    Returns:
        List of straight razor width aggregations with position, width, shaves, and
        unique_users fields
    """
    aggregator = StraightWidthAggregator()
    return aggregator.aggregate(records)
