#!/usr/bin/env python3
"""Soap sample brand aggregator for the SOTD pipeline."""

from typing import Any, Dict, List

import pandas as pd

from ..base_aggregator import BaseAggregator


class SoapSampleBrandAggregator(BaseAggregator):
    """Aggregator for soap sample data grouped by brand from enriched records."""

    def _extract_data(self, records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Extract soap sample data from records for aggregation.

        Args:
            records: List of enriched comment records

        Returns:
            List of dictionaries with extracted soap sample data fields
        """
        sample_data = []
        for record in records:
            soap = record.get("soap", {})
            enriched = soap.get("enriched", {})
            matched = soap.get("matched", {})

            # Skip if no sample enrichment data
            if not enriched or "sample_type" not in enriched:
                continue

            # Extract sample information
            sample_type = enriched.get("sample_type", "").strip()
            sample_number = enriched.get("sample_number")
            total_samples = enriched.get("total_samples")

            # Extract soap identification
            brand = matched.get("brand", "").strip() if matched else ""
            author = record.get("author", "").strip()

            if sample_type and author:
                sample_data.append(
                    {
                        "sample_type": sample_type,
                        "sample_number": sample_number,
                        "total_samples": total_samples,
                        "brand": brand,
                        "author": author,
                    }
                )

        return sample_data

    def _create_composite_name(self, df: pd.DataFrame) -> pd.Series:
        """Create composite name from sample type and brand.

        Args:
            df: DataFrame with extracted soap sample data

        Returns:
            Series with composite names in "Sample Type - Brand" format
        """
        # Handle None values by converting to empty strings
        sample_type = df["sample_type"].fillna("")
        brand = df["brand"].fillna("")

        # Create composite name using pandas operations
        import numpy as np

        # Create the composite name based on whether brand exists
        composite_name = np.where(
            brand != "",
            sample_type + " - " + brand,
            sample_type,
        )

        return pd.Series(composite_name)

    def _group_and_aggregate(self, df: pd.DataFrame) -> pd.DataFrame:
        """Group data and calculate aggregation metrics.

        Args:
            df: DataFrame with extracted data and composite name

        Returns:
            DataFrame with grouped and aggregated data
        """
        # Group by sample type and brand
        group_columns = ["sample_type", "brand"]

        # Group by columns and calculate metrics
        grouped = df.groupby(group_columns).agg({"author": ["count", "nunique"]}).reset_index()

        # Flatten column names
        grouped.columns = ["sample_type", "brand", "shaves", "unique_users"]

        # Create composite name for consistent interface
        grouped["name"] = grouped.apply(
            lambda row: self._create_single_composite_name(row["sample_type"], row["brand"]),
            axis=1,
        )

        return grouped

    def _create_single_composite_name(self, sample_type: str, brand: str) -> str:
        """Create composite name for a single row.

        Args:
            sample_type: The sample type
            brand: The soap brand

        Returns:
            Composite name string
        """
        if brand:
            return f"{sample_type} - {brand}"
        else:
            return sample_type

    def _get_group_columns(self, df: pd.DataFrame) -> List[str]:
        """Get columns to use for grouping.

        Args:
            df: DataFrame with extracted data

        Returns:
            List of column names for grouping
        """
        # Group by sample type and brand for brand-focused analysis
        return ["sample_type", "brand"]


# Legacy function interface for backward compatibility
def aggregate_soap_sample_brands(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Aggregate soap sample data by brand from enriched records.

    Returns a list of soap sample brand aggregations sorted by shaves desc, unique_users desc.
    Each item includes position field for delta calculations.

    Args:
        records: List of enriched comment records

    Returns:
        List of soap sample brand aggregations with position, name, shaves, and unique_users fields
    """
    aggregator = SoapSampleBrandAggregator()
    return aggregator.aggregate(records)
