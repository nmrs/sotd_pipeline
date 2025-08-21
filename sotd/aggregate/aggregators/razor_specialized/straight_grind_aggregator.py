from typing import Any, Dict, List

import pandas as pd

from ..base_aggregator import BaseAggregator
from ...utils.field_validation import has_required_field, get_field_value


class StraightGrindAggregator(BaseAggregator):
    """Aggregator for straight razor grind data from enriched records."""

    def _extract_data(self, records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Extract straight razor grind data from records for aggregation.

        Args:
            records: List of enriched comment records

        Returns:
            List of dictionaries with extracted straight razor grind data fields
        """
        grind_data = []
        for record in records:
            razor = record.get("razor") or {}
            enriched = razor.get("enriched", {})

            # Skip if no enriched razor data or missing required fields
            # Note: Empty strings are valid values, only None is invalid
            if not enriched or not has_required_field(enriched, "grind"):
                continue

            grind = get_field_value(enriched, "grind")
            author = get_field_value(record, "author")

            if grind and author:  # grind can be empty string, which is valid
                grind_data.append({"grind": grind, "author": author})

        return grind_data

    def _create_composite_name(self, df: pd.DataFrame) -> pd.Series:
        """Create composite name from grind.

        Args:
            df: DataFrame with extracted straight razor grind data

        Returns:
            Series with grind values
        """
        # Handle None values by converting to empty strings and concatenate properly
        grind = df["grind"].fillna("")
        # Use pandas string conversion to avoid Series ambiguity
        return grind.astype(str)

    def _get_group_columns(self, df: pd.DataFrame) -> List[str]:
        """Get columns to use for grouping."""
        return ["grind"]


# Legacy function interface for backward compatibility
def aggregate_straight_grinds(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Aggregate straight razor grind data from enriched records.

    Returns a list of straight razor grind aggregations sorted by shaves desc,
    unique_users desc. Each item includes position field for delta calculations.

    Args:
        records: List of enriched comment records

    Returns:
        List of straight razor grind aggregations with position, grind, shaves, and
        unique_users fields
    """
    aggregator = StraightGrindAggregator()
    return aggregator.aggregate(records)
