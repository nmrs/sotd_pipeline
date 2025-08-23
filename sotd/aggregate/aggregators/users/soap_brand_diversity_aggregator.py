#!/usr/bin/env python3
"""Soap brand diversity aggregator for the SOTD pipeline."""

from typing import Any, Dict, List

import pandas as pd

from ..base_aggregator import BaseAggregator
from ...utils.field_validation import has_required_field, get_field_value


class SoapBrandDiversityAggregator(BaseAggregator):
    """Aggregator for soap brand diversity data from enriched records."""

    def _extract_data(self, records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Extract soap brand diversity data from records for aggregation.

        Args:
            records: List of enriched comment records

        Returns:
            List of dictionaries with extracted soap brand diversity data fields
        """
        diversity_data = []
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
                diversity_data.append({"brand": brand, "author": author})

        return diversity_data

    def _create_composite_name(self, df: pd.DataFrame) -> pd.Series:
        """Create composite name from brand.

        Args:
            df: DataFrame with extracted soap brand diversity data

        Returns:
            Series with brand names
        """
        # Handle None values by converting to empty strings
        brand = df["brand"].fillna("")
        return brand

    def _group_and_aggregate(self, df: pd.DataFrame) -> pd.DataFrame:
        """Group data and calculate aggregation metrics.

        Args:
            df: DataFrame with extracted data and composite name

        Returns:
            DataFrame with grouped and aggregated data
        """
        # Group by author to count unique brands per user
        grouped = (
            df.groupby("author")
            .agg(
                {
                    "brand": "nunique",  # Count unique brands
                }
            )
            .reset_index()
        )

        # Rename columns for consistency
        grouped.columns = ["author", "unique_brands"]

        # Count total shaves per user
        shave_counts = df.groupby("author").size().reset_index(name="total_shaves")  # type: ignore

        # Merge the data
        grouped = grouped.merge(shave_counts, on="author")



        return grouped

    def _sort_and_rank(self, grouped: pd.DataFrame) -> List[Dict[str, Any]]:
        """Sort grouped data and add rank rankings.

        Args:
            grouped: DataFrame with grouped and aggregated data

        Returns:
            List of dictionaries with rank, user, unique_brands, total_shaves,
            and unique_users fields
        """
        # Sort by unique_brands desc, total_shaves desc
        grouped = grouped.sort_values(["unique_brands", "total_shaves"], ascending=[False, False])

        # Add rank field (1-based rank)
        grouped = grouped.reset_index(drop=True).assign(rank=lambda df: range(1, len(df) + 1))  # type: ignore

        # Convert to list of dictionaries
        result = []
        for _, row in grouped.iterrows():
            item = {
                "rank": int(row["rank"]),
                "user": str(row["author"]),
                "unique_brands": int(row["unique_brands"]),
                "total_shaves": int(row["total_shaves"]),

            }

            result.append(item)

        return result

    def _get_group_columns(self, df: pd.DataFrame) -> List[str]:
        """Get columns to use for grouping."""
        return ["brand"]


# Legacy function interface for backward compatibility
def aggregate_soap_brand_diversity(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Aggregate soap brand diversity data from enriched records.

    Returns a list of soap brand diversity aggregations sorted by shaves desc,
    unique_users desc. Each item includes position field for delta calculations.

    Args:
        records: List of enriched comment records

    Returns:
        List of soap brand diversity aggregations with position, brand, shaves, and
        unique_users fields
    """
    aggregator = SoapBrandDiversityAggregator()
    return aggregator.aggregate(records)
