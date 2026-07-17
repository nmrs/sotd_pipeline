from typing import Any, Dict, List

import pandas as pd

from ...utils.field_validation import get_field_value, has_required_field
from ..base_aggregator import BaseAggregator


class SuperSpeedVariantAggregator(BaseAggregator):
    """Aggregator for Super Speed variant data from enriched records."""

    @property
    def IDENTIFIER_FIELDS(self) -> List[str]:
        """Fields used for matching/grouping."""
        return ["super_speed_variant"]

    @property
    def METRIC_FIELDS(self) -> List[str]:
        """Calculated/metric fields."""
        return ["shaves", "unique_users"]

    @property
    def RANKING_FIELDS(self) -> List[str]:
        """Fields used for sorting/ranking."""
        return ["shaves", "unique_users"]

    def _extract_data(self, records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Extract Super Speed variant data from records for aggregation.

        Args:
            records: List of enriched comment records

        Returns:
            List of dictionaries with extracted Super Speed variant data fields
        """
        variant_data = []
        for record in records:
            razor = record.get("razor") or {}
            enriched = razor.get("enriched", {})

            # Skip if no enriched razor data or missing required fields
            # Note: Empty strings are valid values, only None is invalid
            if not enriched or not has_required_field(enriched, "super_speed_variant"):
                continue

            variant = get_field_value(enriched, "super_speed_variant")
            author = get_field_value(record, "author")

            if variant and author:  # variant can be empty string, which is valid
                variant_data.append({"super_speed_variant": variant, "author": author})

        return variant_data

    def _create_composite_name(self, df: pd.DataFrame) -> pd.Series:
        """Create composite name from super_speed_variant.

        Args:
            df: DataFrame with extracted Super Speed variant data

        Returns:
            Series with super_speed_variant values
        """
        variant_series: pd.Series = df["super_speed_variant"]  # type: ignore
        variant = variant_series.fillna("")
        return variant.astype(str)

    def _get_group_columns(self, df: pd.DataFrame) -> List[str]:
        """Get columns to use for grouping."""
        return ["super_speed_variant"]


def aggregate_super_speed_variants(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Aggregate Super Speed variant data from enriched records.

    Returns a list of Super Speed variant aggregations sorted by shaves desc,
    unique_users desc. Each item includes position field for delta calculations.

    Args:
        records: List of enriched comment records

    Returns:
        List of Super Speed variant aggregations with position, super_speed_variant,
        shaves, and unique_users fields
    """
    aggregator = SuperSpeedVariantAggregator()
    return aggregator.aggregate(records)
