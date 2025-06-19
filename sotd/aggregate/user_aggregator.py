#!/usr/bin/env python3
"""User-specific aggregation using the base aggregator pattern."""

from typing import Any, Dict, List, Optional

import pandas as pd

from sotd.aggregate.base_aggregator import BaseAggregator


class UserAggregator(BaseAggregator):
    """Aggregator for user participation statistics."""

    def get_operation_name(self) -> str:
        """Return the operation name for monitoring."""
        return "aggregate_users"

    def get_product_type(self) -> str:
        """Return the product type being aggregated."""
        return "user"

    def get_group_column(self) -> str:
        """Return the column name to group by."""
        return "username"

    def _extract_from_record(
        self, record: Dict[str, Any], record_index: int
    ) -> Optional[Dict[str, Any]]:
        """
        Extract user data from a single record.

        Args:
            record: Single enriched comment record
            record_index: Index of the record for debugging

        Returns:
            Extracted user data dictionary or None if invalid
        """
        username = record.get("author")
        if not username or username == "Unknown":
            return None

        # Count products used in this shave
        products_used = 0
        for product_type in ["razor", "blade", "brush", "soap"]:
            product_info = record.get(product_type, {})
            if isinstance(product_info, dict) and "matched" in product_info:
                matched = product_info["matched"]
                if isinstance(matched, dict) and any(matched.values()):
                    products_used += 1

        return {
            "username": username,
            "products_used": products_used,
            "user": username,  # Required for base aggregator pattern
        }

    def _post_process_results(self, grouped: pd.DataFrame) -> List[Dict[str, Any]]:
        """
        Post-process aggregation results to add user-specific metrics.

        Args:
            grouped: Grouped DataFrame from pandas aggregation

        Returns:
            Enhanced results with additional user metrics
        """
        # Rename columns to standard format
        grouped.columns = [self.get_group_column(), "shaves", "unique_users"]

        # Calculate average products per shave
        products_sum = grouped["products_used"].sum() if "products_used" in grouped else 0
        grouped["avg_products_per_shave"] = (products_sum / grouped["shaves"]).round(2)

        # Sort by shaves (descending), then by unique_users (descending)
        grouped = grouped.sort_values(["shaves", "unique_users"], ascending=[False, False])

        # Drop the products_used column before converting to dict
        if "products_used" in grouped:
            grouped = grouped.drop(columns=["products_used"])

        return list(grouped.to_dict("records"))  # type: ignore


def aggregate_users(records: list[dict[str, Any]], debug: bool = False) -> list[dict[str, Any]]:
    """
    Aggregate user participation statistics using the new base aggregator pattern.

    Args:
        records: List of enriched comment records
        debug: Enable debug logging

    Returns:
        List of user aggregation results

    Raises:
        ValueError: If records list is invalid or contains invalid data
    """
    aggregator = UserAggregator(debug)
    return aggregator.aggregate(records)
