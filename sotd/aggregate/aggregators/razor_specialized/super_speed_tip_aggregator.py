from typing import Any, Dict, List

import pandas as pd

from ...utils.field_validation import get_field_value, has_required_field
from ..base_aggregator import BaseAggregator


class SuperSpeedTipAggregator(BaseAggregator):
    """Aggregator for Super Speed tip data from enriched records."""

    @property
    def IDENTIFIER_FIELDS(self) -> List[str]:
        """Fields used for matching/grouping."""
        return ["tip"]

    @property
    def METRIC_FIELDS(self) -> List[str]:
        """Calculated/metric fields."""
        return ["shaves", "unique_users"]

    @property
    def RANKING_FIELDS(self) -> List[str]:
        """Fields used for sorting/ranking."""
        return ["shaves", "unique_users"]

    def _extract_data(self, records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Extract Super Speed tip data from records for aggregation.

        Args:
            records: List of enriched comment records

        Returns:
            List of dictionaries with extracted Super Speed tip data fields
        """
        tip_data = []
        for record in records:
            razor = record.get("razor") or {}
            enriched = razor.get("enriched", {})

            # Skip if no enriched razor data or missing required fields
            # Note: Empty strings are valid values, only None is invalid
            if not enriched or not has_required_field(enriched, "super_speed_tip"):
                continue

            tip = get_field_value(enriched, "super_speed_tip")
            author = get_field_value(record, "author")

            if tip and author:  # tip can be empty string, which is valid
                tip_data.append({"super_speed_tip": tip, "author": author})

        return tip_data

    def _create_composite_name(self, df: pd.DataFrame) -> pd.Series:
        """Create composite name from super_speed_tip.

        Args:
            df: DataFrame with extracted Super Speed tip data

        Returns:
            Series with super_speed_tip values
        """
        # Handle None values by converting to empty strings and concatenate properly
        tip = df["super_speed_tip"].fillna("")
        # Use pandas string conversion to avoid Series ambiguity
        return tip.astype(str)

    def _get_group_columns(self, df: pd.DataFrame) -> List[str]:
        """Get columns to use for grouping."""
        return ["super_speed_tip"]


# Legacy function interface for backward compatibility
def aggregate_super_speed_tips(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Aggregate Super Speed tip data from enriched records.

    Returns a list of Super Speed tip aggregations sorted by shaves desc,
    unique_users desc. Each item includes position field for delta calculations.

    Args:
        records: List of enriched comment records

    Returns:
        List of Super Speed tip aggregations with position, super_speed_tip, shaves, and
        unique_users fields
    """
    aggregator = SuperSpeedTipAggregator()
    return aggregator.aggregate(records)
