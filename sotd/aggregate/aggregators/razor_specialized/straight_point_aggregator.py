from typing import Any, Dict, List

import pandas as pd

from ..base_aggregator import BaseAggregator
from ...utils.field_validation import has_required_field, get_field_value


class StraightPointAggregator(BaseAggregator):
    """Aggregator for straight razor point data from enriched records."""

    def _extract_data(self, records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Extract straight razor point data from records for aggregation.

        Args:
            records: List of enriched comment records

        Returns:
            List of dictionaries with extracted straight razor point data fields
        """
        point_data = []
        for record in records:
            razor = record.get("razor") or {}
            enriched = razor.get("enriched", {})

            # Skip if no enriched razor data or missing required fields
            # Note: Empty strings are valid values, only None is invalid
            if not enriched or not has_required_field(enriched, "point"):
                continue

            point = get_field_value(enriched, "point")
            author = get_field_value(record, "author")

            if point and author:  # point can be empty string, which is valid
                point_data.append({"point": point, "author": author})

        return point_data

    def _create_composite_name(self, df: pd.DataFrame) -> pd.Series:
        """Create composite name from point.

        Args:
            df: DataFrame with extracted straight razor point data

        Returns:
            Series with point values
        """
        # Handle None values by converting to empty strings and concatenate properly
        point = df["point"].fillna("")
        # Use pandas string conversion to avoid Series ambiguity
        return point.astype(str)

    def _get_group_columns(self, df: pd.DataFrame) -> List[str]:
        """Get columns to use for grouping."""
        return ["point"]


# Legacy function interface for backward compatibility
def aggregate_straight_points(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Aggregate straight razor point data from enriched records.

    Returns a list of straight razor point aggregations sorted by shaves desc,
    unique_users desc. Each item includes position field for delta calculations.

    Args:
        records: List of enriched comment records

    Returns:
        List of straight razor point aggregations with position, point, shaves, and
        unique_users fields
    """
    aggregator = StraightPointAggregator()
    return aggregator.aggregate(records)
