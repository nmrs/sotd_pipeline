from typing import Any, Dict, List

import pandas as pd

from ...utils.field_validation import get_field_value, has_required_field
from ..base_aggregator import BaseAggregator


class SoapMakerAggregator(BaseAggregator):
    """Aggregator for soap maker data from enriched records."""

    @property
    def IDENTIFIER_FIELDS(self) -> List[str]:
        """Fields used for matching/grouping."""
        return ["name"]

    @property
    def METRIC_FIELDS(self) -> List[str]:
        """Calculated/metric fields."""
        return ["shaves", "unique_users"]

    @property
    def RANKING_FIELDS(self) -> List[str]:
        """Fields used for sorting/ranking."""
        return ["shaves", "unique_users"]

    def _extract_data(self, records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Extract soap maker data from records for aggregation.

        Args:
            records: List of enriched comment records

        Returns:
            List of dictionaries with extracted soap maker data fields
        """
        maker_data = []
        for record in records:
            soap = record.get("soap") or {}
            matched = soap.get("matched", {})

            # Skip if no matched soap data or missing required fields
            # Note: Empty strings are valid values, only None is invalid
            if not matched or not has_required_field(matched, "brand"):
                continue

            brand = get_field_value(matched, "brand")
            author = get_field_value(record, "author")

            if brand and author:  # brand can be empty string, which is valid
                maker_data.append({"brand": brand, "author": author})

        return maker_data

    def _create_composite_name(self, df: pd.DataFrame) -> pd.Series:
        """Create composite name from brand.

        Args:
            df: DataFrame with extracted soap maker data

        Returns:
            Series with brand names
        """
        # Handle None values by converting to empty strings
        # Ensure we get a Series, not DataFrame
        brand_series: pd.Series = df["brand"]  # type: ignore
        brand = brand_series.fillna("")
        return brand

    def _get_group_columns(self, df: pd.DataFrame) -> List[str]:
        """Get columns to use for grouping."""
        return ["brand"]


# Legacy function interface for backward compatibility
def aggregate_soap_makers(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Aggregate soap maker data from enriched records.

    Returns a list of soap maker aggregations sorted by shaves desc,
    unique_users desc. Each item includes position field for delta calculations.

    Args:
        records: List of enriched comment records

    Returns:
        List of soap maker aggregations with position, brand, shaves, and
        unique_users fields
    """
    aggregator = SoapMakerAggregator()
    return aggregator.aggregate(records)
