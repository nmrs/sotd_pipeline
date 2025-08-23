#!/usr/bin/env python3
"""Soap brand diversity aggregator for the SOTD pipeline."""

from typing import Any, Dict, List

import pandas as pd

from ...utils.field_validation import get_field_value, has_required_field
from ..base_aggregator import BaseAggregator
from .user_diversity_mixin import UserDiversityMixin


class SoapBrandDiversityAggregator(BaseAggregator, UserDiversityMixin):
    """Aggregator for soap brand diversity data from enriched records."""

    # Override tie_columns for tier-based ranking
    tie_columns = ["unique_brands", "shaves"]

    @property
    def IDENTIFIER_FIELDS(self) -> List[str]:
        """Fields used for matching/grouping."""
        return ["user"]

    @property
    def METRIC_FIELDS(self) -> List[str]:
        """Calculated/metric fields."""
        return ["unique_brands", "shaves", "avg_shaves_per_brand"]

    @property
    def RANKING_FIELDS(self) -> List[str]:
        """Fields used for sorting/ranking."""
        return ["unique_brands", "shaves"]

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
                diversity_data.append(
                    {
                        "brand": brand,
                        "author": f"u/{author}",  # Prepend "u/" for Reddit user tagging
                    }
                )

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
        shave_counts = df.groupby("author").size().reset_index(name="shaves")  # type: ignore

        # Merge the data
        grouped = grouped.merge(shave_counts, on="author")

        # Calculate average shaves per soap brand for each user
        grouped["avg_shaves_per_brand"] = (grouped["shaves"] / grouped["unique_brands"]).round(1)

        # Use mixin to prepare for base class ranking
        grouped = self._prepare_for_base_ranking(grouped)

        return grouped

    def _get_group_columns(self, df: pd.DataFrame) -> List[str]:
        """Get columns to use for grouping."""
        return ["name"]

    def _call_base_aggregate(self, records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Call the base class aggregate method."""
        return super().aggregate(records)

    def aggregate(self, records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Aggregate data using tier-based ranking with custom output format."""
        return self.aggregate_with_tier_ranking(
            records,
            {
                "unique_brands": "unique_brands",
                "shaves": "shaves",
                "avg_shaves_per_brand": "avg_shaves_per_brand",
            },
        )


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
