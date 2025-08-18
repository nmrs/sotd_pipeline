#!/usr/bin/env python3
"""Soap brand diversity aggregator for the SOTD pipeline."""

from typing import Any, Dict, List

import pandas as pd

from ..base_aggregator import BaseAggregator


class SoapBrandDiversityAggregator(BaseAggregator):
    """Aggregator for soap brand diversity grouped by user from enriched records."""

    def _extract_data(self, records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Extract soap brand data from records for aggregation.

        Args:
            records: List of enriched comment records

        Returns:
            List of dictionaries with extracted soap brand data fields
        """
        soap_data = []
        for record in records:
            soap = record.get("soap", {})
            matched = soap.get("matched", {})

            # Skip if no matched soap data or no brand
            if not matched or not matched.get("brand"):
                continue

            brand = matched.get("brand", "").strip()
            author = record.get("author", "").strip()

            if brand and author:
                soap_data.append({"brand": brand, "author": author})

        return soap_data

    def _create_composite_name(self, df: pd.DataFrame) -> pd.Series:
        """Create composite name from brand.

        Args:
            df: DataFrame with extracted soap brand data

        Returns:
            Series with brand names
        """
        # Handle None values by converting to empty strings
        result = df["brand"].fillna("")
        # Ensure we return a Series
        if isinstance(result, pd.Series):
            return result
        else:
            return pd.Series(result, index=df.index)

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
        shave_counts = (
            df.groupby("author").size().reset_index(name="total_shaves")  # type: ignore
        )

        # Merge the data
        grouped = grouped.merge(shave_counts, on="author")

        # Add unique_users field (always 1 for user aggregators)
        grouped["unique_users"] = 1

        return grouped

    def _sort_and_rank(self, grouped: pd.DataFrame) -> List[Dict[str, Any]]:
        """Sort grouped data and add position rankings.

        Args:
            grouped: DataFrame with grouped and aggregated data

        Returns:
            List of dictionaries with position, user, unique_brands, total_shaves,
            and unique_users fields
        """
        # Sort by unique_brands desc, total_shaves desc
        grouped = grouped.sort_values(["unique_brands", "total_shaves"], ascending=[False, False])

        # Add position field (1-based rank)
        grouped = (
            grouped.reset_index(drop=True)
            .assign(position=lambda df: range(1, len(df) + 1))  # type: ignore
        )

        # Convert to list of dictionaries
        result = []
        for _, row in grouped.iterrows():
            item = {
                "position": int(row["position"]),
                "user": str(row["author"]),
                "unique_brands": int(row["unique_brands"]),
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
def aggregate_soap_brand_diversity(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Aggregate soap brand diversity by user from enriched records.

    Returns a list of soap brand diversity aggregations sorted by unique_brands desc,
    total_shaves desc. Each item includes position field for delta calculations.

    Args:
        records: List of enriched comment records

    Returns:
        List of soap brand diversity aggregations with position, user, unique_brands,
        total_shaves, and unique_users fields
    """
    aggregator = SoapBrandDiversityAggregator()
    return aggregator.aggregate(records)
