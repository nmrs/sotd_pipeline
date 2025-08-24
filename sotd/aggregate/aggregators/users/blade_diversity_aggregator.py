#!/usr/bin/env python3
"""Blade diversity aggregator for the SOTD pipeline."""

from typing import Any, Dict, List

import pandas as pd

from ...utils.field_validation import get_field_value, has_required_fields
from ..base_aggregator import BaseAggregator


class BladeDiversityAggregator(BaseAggregator):
    """Aggregator for blade diversity data from enriched records."""

    @property
    def IDENTIFIER_FIELDS(self) -> List[str]:
        """Fields used for matching/grouping."""
        return ["user"]

    @property
    def METRIC_FIELDS(self) -> List[str]:
        """Calculated/metric fields."""
        return ["unique_blades", "shaves", "avg_shaves_per_blade"]

    @property
    def RANKING_FIELDS(self) -> List[str]:
        """Fields used for sorting/ranking."""
        return ["unique_blades", "shaves"]

    def _extract_data(self, records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Extract blade diversity data from records for aggregation.

        Args:
            records: List of enriched comment records

        Returns:
            List of dictionaries with extracted blade diversity data fields
        """
        diversity_data = []
        for record in records:
            blade = record.get("blade") or {}
            matched = blade.get("matched", {})

            # Skip if no matched blade data or missing required fields
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
            df: DataFrame with extracted blade diversity data

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
        # Group by author to count unique blade brand+model combinations per user
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
        df["blade_key"] = df["brand"].astype(str) + " " + df["model"].astype(str)
        blade_counts = df.groupby("author")["blade_key"].nunique().reset_index()
        blade_counts.columns = ["author", "unique_blades"]

        # Count total shaves per user
        shave_counts = df.groupby("author").size().reset_index(name="shaves")  # type: ignore

        # Merge all the data
        grouped = grouped.merge(blade_counts, on="author")
        grouped = grouped.merge(shave_counts, on="author")

        # Calculate average shaves per blade for each user
        grouped["avg_shaves_per_blade"] = (grouped["shaves"] / grouped["unique_blades"]).round(1)

        return grouped

    def _sort_and_rank(self, grouped: pd.DataFrame) -> List[Dict[str, Any]]:
        """Sort grouped data and add rank rankings."""
        grouped = grouped.sort_values(["unique_blades", "shaves"], ascending=[False, False])
        grouped = grouped.reset_index(drop=True).assign(
            rank=lambda df: range(1, len(df) + 1)
        )  # type: ignore

        # OPTIMIZED: Use pandas operations to rename and convert types
        # Rename columns using pandas operations
        grouped = grouped.rename(columns={"author": "user"})

        # Convert data types using pandas operations
        grouped["rank"] = grouped["rank"].astype(int)
        grouped["unique_blades"] = grouped["unique_blades"].astype(int)
        grouped["shaves"] = grouped["shaves"].astype(int)
        grouped["avg_shaves_per_blade"] = grouped["avg_shaves_per_blade"].astype(float)

        # Convert to list of dictionaries - no manual processing needed
        # Type conversion to ensure str keys
        result = [{str(k): v for k, v in item.items()} for item in grouped.to_dict("records")]

        return result

    def _get_group_columns(self, df: pd.DataFrame) -> List[str]:
        """Get columns to use for grouping."""
        return ["brand", "model"]


# Legacy function interface for backward compatibility
def aggregate_blade_diversity(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Aggregate blade diversity data from enriched records.

    Returns a list of blade diversity aggregations sorted by shaves desc,
    unique_users desc. Each item includes position field for delta calculations.

    Args:
        records: List of enriched comment records

    Returns:
        List of blade diversity aggregations with position, name, shaves, and
        unique_users fields
    """
    aggregator = BladeDiversityAggregator()
    return aggregator.aggregate(records)
