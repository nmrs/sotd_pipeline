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
        result = []
        for item in base_result:
            transformed_item = {"rank": item["rank"], "user": item["name"]}

            # Map the ranking fields back to their original names
            for base_field, output_field in output_fields.items():
                transformed_item[output_field] = item[base_field]

            result.append(transformed_item)

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
