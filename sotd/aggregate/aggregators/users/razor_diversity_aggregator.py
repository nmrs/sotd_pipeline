#!/usr/bin/env python3
"""Razor diversity aggregator for the SOTD pipeline."""

from typing import Any, Dict, List

import pandas as pd

from ..base_aggregator import BaseAggregator


class RazorDiversityAggregator(BaseAggregator):
    """Aggregator for razor diversity grouped by user from enriched records."""

    def _extract_data(self, records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Extract razor brand+model data from records for aggregation.

        Args:
            records: List of enriched comment records

        Returns:
            List of dictionaries with extracted razor brand+model data fields
        """
        razor_data = []
        for record in records:
            razor = record.get("razor", {})
            matched = razor.get("matched", {})

            # Skip if no matched razor data or no brand/model
            if not matched or not matched.get("brand") or not matched.get("model"):
                continue

            brand = matched.get("brand", "").strip()
            model = matched.get("model", "").strip()
            author = record.get("author", "").strip()

            if brand and model and author:
                razor_data.append({"brand": brand, "model": model, "author": author})

        return razor_data

    def _create_composite_name(self, df: pd.DataFrame) -> pd.Series:
        """Create composite name from brand and model.

        Args:
            df: DataFrame with extracted razor brand+model data

        Returns:
            Series with composite names in "Brand Model" format
        """
        # Handle None values by converting to empty strings
        brand = df["brand"].fillna("")
        model = df["model"].fillna("")
        return brand + " " + model

    def _group_and_aggregate(self, df: pd.DataFrame) -> pd.DataFrame:
        """Group data and calculate aggregation metrics.

        Args:
            df: DataFrame with extracted data and composite name

        Returns:
            DataFrame with grouped and aggregated data
        """
        # Group by author to count unique razor brand+model combinations per user
        grouped = df.groupby("author").agg({
            "brand": "nunique",  # Count unique brands (for reference)
        }).reset_index()

        # Rename columns for consistency
        grouped.columns = ["author", "unique_brands"]

        # Count unique brand+model combinations per user
        # Create composite key for uniqueness counting
        df["razor_key"] = df["brand"] + " " + df["model"]
        razor_counts = df.groupby("author")["razor_key"].nunique().reset_index()
        razor_counts.columns = ["author", "unique_razors"]

        # Count total shaves per user
        shave_counts = df.groupby("author").size().reset_index(name="total_shaves")  # type: ignore
        
        # Merge all the data
        grouped = grouped.merge(razor_counts, on="author")
        grouped = grouped.merge(shave_counts, on="author")

        # Add unique_users field (always 1 for user aggregators)
        grouped["unique_users"] = 1

        return grouped

    def _sort_and_rank(self, grouped: pd.DataFrame) -> List[Dict[str, Any]]:
        """Sort grouped data and add position rankings.

        Args:
            grouped: DataFrame with grouped and aggregated data

        Returns:
            List of dictionaries with position, user, unique_razors, total_shaves,
            and unique_users fields
        """
        # Sort by unique_razors desc, total_shaves desc
        grouped = grouped.sort_values(
            ["unique_razors", "total_shaves"], ascending=[False, False]
        )

        # Add position field (1-based rank)
        grouped = grouped.reset_index(drop=True).assign(
            position=lambda df: range(1, len(df) + 1)
        )  # type: ignore

        # Convert to list of dictionaries
        result = []
        for _, row in grouped.iterrows():
            item = {
                "position": int(row["position"]),
                "user": str(row["author"]),
                "unique_razors": int(row["unique_razors"]),
                "total_shaves": int(row["total_shaves"]),
                "unique_users": int(row["unique_users"]),
            }

            result.append(item)

        return result

    def _get_group_columns(self, df: pd.DataFrame) -> List[str]:
        """Get columns to use for grouping.

        Args:
            df: DataFrame with extracted data

        Returns:
            List of column names for grouping
        """
        # Group by author for user-focused analysis
        return ["author"]


# Legacy function interface for backward compatibility
def aggregate_razor_diversity(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Aggregate razor diversity by user from enriched records.

    Returns a list of razor diversity aggregations sorted by unique_razors desc,
    total_shaves desc. Each item includes position field for delta calculations.

    Args:
        records: List of enriched comment records

    Returns:
        List of razor diversity aggregations with position, user, unique_razors,
        total_shaves, and unique_users fields
    """
    aggregator = RazorDiversityAggregator()
    return aggregator.aggregate(records)
