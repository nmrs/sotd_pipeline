#!/usr/bin/env python3
"""Soap brand+scent diversity aggregator for the SOTD pipeline."""

from typing import Any, Dict, List

import pandas as pd

from ...utils.field_validation import get_field_value, has_required_fields
from ..base_aggregator import BaseAggregator
from .user_diversity_mixin import UserDiversityMixin


class SoapBrandScentDiversityAggregator(BaseAggregator, UserDiversityMixin):
    """Aggregator for soap brand scent diversity data from enriched records."""

    # Override tie_columns for tier-based ranking
    tie_columns = ["unique_combinations", "shaves"]

    @property
    def IDENTIFIER_FIELDS(self) -> List[str]:
        """Fields used for matching/grouping."""
        return ["user"]

    @property
    def METRIC_FIELDS(self) -> List[str]:
        """Calculated/metric fields."""
        return ["unique_combinations", "shaves", "avg_shaves_per_combination"]

    @property
    def RANKING_FIELDS(self) -> List[str]:
        """Fields used for sorting/ranking."""
        return ["unique_combinations", "shaves"]

    def _extract_data(self, records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Extract soap brand scent diversity data from records for aggregation.

        Args:
            records: List of enriched comment records

        Returns:
            List of dictionaries with extracted soap brand scent diversity data fields
        """
        diversity_data = []
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
                diversity_data.append(
                    {
                        "brand": brand,
                        "scent": scent,
                        "author": f"u/{author}",  # Prepend "u/" for Reddit user tagging
                    }
                )

        return diversity_data

    def _create_composite_name(self, df: pd.DataFrame) -> pd.Series:
        """Create composite name from brand and scent.

        Args:
            df: DataFrame with extracted soap brand scent diversity data

        Returns:
            Series with composite names in "Brand - Scent" format
        """
        # Handle None values by converting to empty strings and concatenate properly
        brand = df["brand"].fillna("")
        scent = df["scent"].fillna("")

        # Use pandas string concatenation to avoid Series ambiguity
        # Always concatenate with dash - empty scents will just show as "Brand - "
        return brand.astype(str) + " - " + scent.astype(str)

    def _group_and_aggregate(self, df: pd.DataFrame) -> pd.DataFrame:
        """Group data and calculate aggregation metrics.

        Args:
            df: DataFrame with extracted data and composite name

        Returns:
            DataFrame with grouped and aggregated data
        """
        # Group by author to count unique brand+scent combinations per user
        grouped = (
            df.groupby("author")
            .agg(
                {
                    "brand": "nunique",  # Count unique brands (for reference)
                }
            )
            .reset_index()
        )

        # Rename columns for consistency
        grouped.columns = ["author", "unique_brands"]

        # Count unique brand+scent combinations per user
        # Create composite key for uniqueness counting
        df["brand_scent_key"] = df["brand"].astype(str) + " - " + df["scent"].astype(str)
        brand_scent_counts = df.groupby("author")["brand_scent_key"].nunique().reset_index()
        brand_scent_counts.columns = ["author", "unique_combinations"]

        # Count total shaves per user
        shave_counts = df.groupby("author").size().reset_index(name="shaves")  # type: ignore

        # Merge all the data
        grouped = grouped.merge(brand_scent_counts, on="author")
        grouped = grouped.merge(shave_counts, on="author")

        # Calculate average shaves per combination
        grouped["avg_shaves_per_combination"] = (
            grouped["shaves"] / grouped["unique_combinations"]
        ).round(2)

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
                "unique_combinations": "unique_combinations",
                "shaves": "shaves",
                "avg_shaves_per_combination": "avg_shaves_per_combination",
            },
        )


# Legacy function interface for backward compatibility
def aggregate_soap_brand_scent_diversity(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Aggregate soap brand scent diversity data from enriched records.

    Returns a list of soap brand scent diversity aggregations sorted by shaves desc,
    unique_users desc. Each item includes position field for delta calculations.

    Args:
        records: List of enriched comment records

    Returns:
        List of soap brand scent diversity aggregations with position, name, shaves, and
        unique_users fields
    """
    aggregator = SoapBrandScentDiversityAggregator()
    return aggregator.aggregate(records)
