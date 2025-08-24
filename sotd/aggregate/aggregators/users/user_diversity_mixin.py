#!/usr/bin/env python3
"""Mixin for user diversity aggregators to use tier-based ranking consistently."""

from typing import Any, Dict, List

import pandas as pd


class UserDiversityMixin:
    """Mixin providing common functionality for user diversity aggregators.

    This mixin ensures all user diversity aggregators use the base class's
    tier-based ranking system consistently while maintaining their expected
    output format.
    """

    def _prepare_for_base_ranking(self, grouped: pd.DataFrame) -> pd.DataFrame:
        """Prepare grouped data for base class tier-based ranking.

        Args:
            grouped: DataFrame with grouped and aggregated data

        Returns:
            DataFrame with columns renamed to match base class expectations
        """
        # Rename author to name for base class
        grouped = grouped.rename(columns={"author": "name"})
        return grouped

    def _transform_base_output(
        self, base_result: List[Dict[str, Any]], output_fields: Dict[str, str]
    ) -> List[Dict[str, Any]]:
        """Transform base class output to expected format.

        Args:
            base_result: Result from base class aggregation
            output_fields: Mapping of base class fields to output fields
                           e.g., {"unique_combinations": "unique_combinations", "shaves": "shaves"}

        Returns:
            List of dictionaries with transformed field names
        """
        if not base_result:
            return []

        # OPTIMIZED: Use pandas operations for field transformation
        # Convert to DataFrame for vectorized operations
        df = pd.DataFrame(base_result)

        # Rename columns using pandas operations
        df = df.rename(columns={"name": "user"})

        # Select and rename fields based on output_fields mapping
        # Start with required fields
        columns_to_keep = ["rank", "user"]
        rename_mapping = {}

        # Add mapped fields
        for base_field, output_field in output_fields.items():
            if base_field in df.columns:
                columns_to_keep.append(base_field)
                if base_field != output_field:
                    rename_mapping[base_field] = output_field

        # Select columns and apply renaming
        df = df[columns_to_keep]
        if rename_mapping:
            df = df.rename(columns=rename_mapping)

        # Convert back to list of dictionaries
        # Type conversion to ensure str keys
        result = [{str(k): v for k, v in item.items()} for item in df.to_dict("records")]

        return result

    def aggregate_with_tier_ranking(
        self, records: List[Dict[str, Any]], output_fields: Dict[str, str]
    ) -> List[Dict[str, Any]]:
        """Aggregate data using base class tier-based ranking with custom output format.

        Args:
            records: List of enriched comment records
            output_fields: Mapping of base class fields to output fields

        Returns:
            List of aggregations with rank, user, and custom fields
        """
        # Get base aggregation result - this will be called on the actual aggregator instance
        base_result = self._call_base_aggregate(records)

        # Transform to expected output format
        return self._transform_base_output(base_result, output_fields)

    def _call_base_aggregate(self, records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Call the base class aggregate method.

        This method should be overridden by the actual aggregator class
        to call super().aggregate(records).
        """
        raise NotImplementedError("Subclasses must implement _call_base_aggregate")
