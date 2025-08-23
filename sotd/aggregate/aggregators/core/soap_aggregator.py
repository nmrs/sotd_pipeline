from typing import Any, Dict, List

import pandas as pd

from ..base_aggregator import BaseAggregator
from ...utils.field_validation import has_required_fields, get_field_value


class SoapAggregator(BaseAggregator):
    """Aggregator for soap data from enriched records."""

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
        """Extract soap data from records for aggregation.

        Args:
            records: List of enriched comment records

        Returns:
            List of dictionaries with extracted soap data fields
        """
        soap_data = []
        for record in records:
            soap = record.get("soap") or {}
            matched = soap.get("matched", {})

            # Skip if no matched soap data or missing required fields
            # Note: Empty strings are valid values, only None is invalid
            if not matched or not has_required_fields(matched, "brand", "scent"):
                continue

            brand = get_field_value(matched, "brand")
            scent = get_field_value(matched, "scent")
            author = get_field_value(record, "author")

            if brand and author:  # scent can be empty string, which is valid
                # Preserve original case for display, create normalized versions for grouping
                original_brand = brand.strip()
                original_scent = scent.strip()

                soap_data.append(
                    {
                        "brand": original_brand,
                        "scent": original_scent,
                        "author": author,
                        # Add normalized versions for case-insensitive grouping
                        "brand_normalized": original_brand.lower(),
                        "scent_normalized": original_scent.lower(),
                    }
                )

        return soap_data

    def _get_group_columns(self, df: pd.DataFrame) -> List[str]:
        """Get columns to use for grouping.

        Use normalized brand+scent for case-insensitive grouping while preserving
        original display format.

        Args:
            df: DataFrame with extracted soap data

        Returns:
            List of column names for grouping
        """
        # Group by normalized brand+scent for case-insensitive counting
        # but preserve original brand+scent for display
        return ["brand_normalized", "scent_normalized"]

    def _group_and_aggregate(self, df: pd.DataFrame) -> pd.DataFrame:
        """Group data and calculate aggregation metrics.

        Override to handle case-insensitive grouping while preserving original display values.

        Args:
            df: DataFrame with extracted data and composite name

        Returns:
            DataFrame with grouped and aggregated data
        """
        # Group by normalized fields for case-insensitive counting
        group_columns = self._get_group_columns(df)

        # Group by normalized brand+scent and aggregate
        grouped = (
            df.groupby(group_columns)
            .agg(
                {
                    "author": ["count", "nunique"],
                    "brand": "first",  # Keep first occurrence of original case
                    "scent": "first",  # Keep first occurrence of original case
                    "name": "first",  # Keep the composite name for display
                }
            )
            .reset_index()
        )

        # Flatten column names
        grouped.columns = list(group_columns) + ["shaves", "unique_users", "brand", "scent", "name"]

        return grouped

    def _create_composite_name(self, df: pd.DataFrame) -> pd.Series:
        """Create composite name from brand and scent.

        Args:
            df: DataFrame with extracted soap data

        Returns:
            Series with composite names in "Brand - Scent" format
        """
        # Handle None values by converting to empty strings and concatenate properly
        brand = df["brand"].fillna("")
        scent = df["scent"].fillna("")

        # Use pandas string concatenation to avoid Series ambiguity
        # Always concatenate with dash - empty scents will just show as "Brand - "
        return brand.astype(str) + " - " + scent.astype(str)


# Legacy function interface for backward compatibility
def aggregate_soaps(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Aggregate soap data from enriched records.

    Returns a list of soap aggregations sorted by shaves desc, unique_users desc.
    Each item includes position field for delta calculations.

    Args:
        records: List of enriched comment records

    Returns:
        List of soap aggregations with position, name, shaves, and unique_users fields
    """
    aggregator = SoapAggregator()
    return aggregator.aggregate(records)
