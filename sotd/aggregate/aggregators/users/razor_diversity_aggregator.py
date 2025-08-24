#!/usr/bin/env python3
"""Razor diversity aggregator for the SOTD pipeline."""

from typing import Any, Dict, List

import pandas as pd

from ...utils.field_validation import get_field_value, has_required_fields
from ..base_aggregator import BaseAggregator


class RazorDiversityAggregator(BaseAggregator):
    """Aggregator for razor diversity data from enriched records."""

    @property
    def IDENTIFIER_FIELDS(self) -> List[str]:
        """Fields used for matching/grouping."""
        return ["user"]

    @property
    def METRIC_FIELDS(self) -> List[str]:
        """Calculated/metric fields."""
        return ["unique_razors", "shaves", "avg_shaves_per_razor"]

    @property
    def RANKING_FIELDS(self) -> List[str]:
        """Fields used for sorting/ranking."""
        return ["unique_razors", "shaves"]

    def _extract_data(self, records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Extract razor diversity data from records for aggregation.

        Args:
            records: List of enriched comment records

        Returns:
            List of dictionaries with extracted razor diversity data fields
        """
        diversity_data = []
        for record in records:
            razor = record.get("razor") or {}
            matched = razor.get("matched", {})

            # Skip if no matched razor data or missing required fields
            # Note: Empty strings are valid values, only None is invalid
            if not matched or not has_required_fields(matched, "brand", "model"):
                continue

            brand = get_field_value(matched, "brand")
            model = get_field_value(matched, "model")
            author = get_field_value(record, "author")

            if brand and author:  # model can be empty string, which is valid
                diversity_data.append({"brand": brand, "model": model, "author": author})

        return diversity_data

    def _create_composite_name(self, df: pd.DataFrame) -> pd.Series:
        """Create composite name from brand and model.

        Args:
            df: DataFrame with extracted razor diversity data

        Returns:
            Series with composite names in "Brand Model" format
        """
        # Handle None values by converting to empty strings and concatenate properly
        brand = df["brand"].fillna("")
        model = df["model"].fillna("")
        # Use pandas string concatenation to avoid Series ambiguity
        return brand.astype(str) + " " + model.astype(str)

    def _group_and_aggregate(self, df: pd.DataFrame) -> pd.DataFrame:
        """Group data and calculate aggregation metrics.

        Args:
            df: DataFrame with extracted data and composite name

        Returns:
            DataFrame with grouped and aggregated data
        """
        # Group by author to count unique razor brand+model combinations per user
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

        # Count unique brand+model combinations per user
        # Create composite key for uniqueness counting
        df["razor_key"] = df["brand"].astype(str) + " " + df["model"].astype(str)
        razor_counts = df.groupby("author")["razor_key"].nunique().reset_index()
        razor_counts.columns = ["author", "unique_razors"]

        # Count total shaves per user
        shave_counts = df.groupby("author").size().reset_index(name="shaves")  # type: ignore

        # Merge all the data
        grouped = grouped.merge(razor_counts, on="author")
        grouped = grouped.merge(shave_counts, on="author")

        # Calculate average shaves per razor for each user
        grouped["avg_shaves_per_razor"] = (grouped["shaves"] / grouped["unique_razors"]).round(1)

        return grouped

    def _sort_and_rank(self, grouped: pd.DataFrame) -> List[Dict[str, Any]]:
        """Sort grouped data and add rank rankings."""
        grouped = grouped.sort_values(["unique_razors", "shaves"], ascending=[False, False])
        grouped = grouped.reset_index(drop=True).assign(rank=lambda df: range(1, len(df) + 1))  # type: ignore

        # OPTIMIZED: Use pandas operations to rename and convert types
        # Rename columns using pandas operations
        grouped = grouped.rename(columns={"author": "user"})

        # Convert data types using pandas operations
        grouped["rank"] = grouped["rank"].astype(int)
        grouped["unique_razors"] = grouped["unique_razors"].astype(int)
        grouped["shaves"] = grouped["shaves"].astype(int)
        grouped["avg_shaves_per_razor"] = grouped["avg_shaves_per_razor"].astype(float)

        # Convert to list of dictionaries - no manual processing needed
        # Type conversion to ensure str keys
        result = [{str(k): v for k, v in item.items()} for item in grouped.to_dict("records")]

        return result

    def _get_group_columns(self, df: pd.DataFrame) -> List[str]:
        """Get columns to use for grouping."""
        return ["brand", "model"]


# Legacy function interface for backward compatibility
def aggregate_razor_diversity(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Aggregate razor diversity data from enriched records.

    Returns a list of razor diversity aggregations sorted by shaves desc,
    unique_users desc. Each item includes position field for delta calculations.

    Args:
        records: List of enriched comment records

    Returns:
        List of razor diversity aggregations with position, name, shaves, and
        unique_users fields
    """
    aggregator = RazorDiversityAggregator()
    return aggregator.aggregate(records)
