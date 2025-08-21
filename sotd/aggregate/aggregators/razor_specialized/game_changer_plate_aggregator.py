from typing import Any, Dict, List

import pandas as pd

from ..base_aggregator import BaseAggregator
from ...utils.field_validation import has_required_field, get_field_value


class GameChangerPlateAggregator(BaseAggregator):
    """Aggregator for Game Changer plate gap data from enriched records."""

    def _extract_data(self, records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Extract Game Changer plate gap data from records for aggregation.

        Args:
            records: List of enriched comment records

        Returns:
            List of dictionaries with extracted Game Changer plate gap data fields
        """
        gap_data = []
        for record in records:
            razor = record.get("razor") or {}
            enriched = razor.get("enriched", {})

            # Skip if no enriched razor data or missing required fields
            # Note: Empty strings are valid values, only None is invalid
            if not enriched or not has_required_field(enriched, "gap"):
                continue

            gap = get_field_value(enriched, "gap")
            author = get_field_value(record, "author")

            if gap and author:  # gap can be empty string, which is valid
                gap_data.append({"gap": gap, "author": author})

        return gap_data

    def _create_composite_name(self, df: pd.DataFrame) -> pd.Series:
        """Create composite name from gap.

        Args:
            df: DataFrame with extracted Game Changer plate gap data

        Returns:
            Series with gap values
        """
        # Handle None values by converting to empty strings
        gap = df["gap"].fillna("")
        return gap

    def _get_group_columns(self, df: pd.DataFrame) -> List[str]:
        """Get columns to use for grouping."""
        return ["gap"]


# Legacy function interface for backward compatibility
def aggregate_game_changer_plates(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Aggregate Game Changer plate gap data from enriched records.

    Returns a list of Game Changer plate gap aggregations sorted by shaves desc,
    unique_users desc. Each item includes position field for delta calculations.

    Args:
        records: List of enriched comment records

    Returns:
        List of Game Changer plate gap aggregations with position, gap, shaves, and
        unique_users fields
    """
    aggregator = GameChangerPlateAggregator()
    return aggregator.aggregate(records)
