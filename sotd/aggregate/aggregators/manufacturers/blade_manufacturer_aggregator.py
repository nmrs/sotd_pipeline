from typing import Any, Dict, List

import pandas as pd

from ..base_aggregator import BaseAggregator
from ...utils.field_validation import has_required_field, get_field_value


class BladeManufacturerAggregator(BaseAggregator):
    """Aggregator for blade manufacturer data from enriched records."""

    @property
    def IDENTIFIER_FIELDS(self) -> List[str]:
        """Fields used for matching/grouping."""
        return ["brand"]

    @property
    def METRIC_FIELDS(self) -> List[str]:
        """Calculated/metric fields."""
        return ["shaves", "unique_users"]

    @property
    def RANKING_FIELDS(self) -> List[str]:
        """Fields used for sorting/ranking."""
        return ["shaves", "unique_users"]

    def _extract_data(self, records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Extract blade manufacturer data from records for aggregation.

        Args:
            records: List of enriched comment records

        Returns:
            List of dictionaries with extracted blade manufacturer data fields
        """
        manufacturer_data = []
        for record in records:
            blade = record.get("blade") or {}
            matched = blade.get("matched", {})

            # Skip if no matched blade data or missing required fields
            # Note: Empty strings are valid values, only None is invalid
            if not matched or not has_required_field(matched, "brand"):
                continue

            brand = get_field_value(matched, "brand")
            author = get_field_value(record, "author")

            if brand and author:  # brand can be empty string, which is valid
                manufacturer_data.append({"brand": brand, "author": author})

        return manufacturer_data

    def _create_composite_name(self, df: pd.DataFrame) -> pd.Series:
        """Create composite name from brand.

        Args:
            df: DataFrame with extracted blade manufacturer data

        Returns:
            Series with brand names
        """
        # Handle None values by converting to empty strings
        brand = df["brand"].fillna("")
        return brand

    def _get_group_columns(self, df: pd.DataFrame) -> List[str]:
        """Get columns to use for grouping."""
        return ["brand"]


# Legacy function interface for backward compatibility
def aggregate_blade_manufacturers(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Aggregate blade manufacturer data from enriched records.

    Returns a list of blade manufacturer aggregations sorted by shaves desc,
    unique_users desc. Each item includes position field for delta calculations.

    Args:
        records: List of enriched comment records

    Returns:
        List of blade manufacturer aggregations with position, brand, shaves, and
        unique_users fields
    """
    aggregator = BladeManufacturerAggregator()
    return aggregator.aggregate(records)
