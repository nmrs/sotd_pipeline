#!/usr/bin/env python3
"""Annual aggregator for combining monthly aggregated data into yearly summaries."""

from typing import Any, Dict, List

import pandas as pd

from .base_aggregator import BaseAggregator


class AnnualAggregator(BaseAggregator):
    """Aggregator for annual data from monthly aggregated records."""

    @property
    def IDENTIFIER_FIELDS(self) -> List[str]:
        """Fields used for matching/grouping."""
        return ["name"]

    @property
    def METRIC_FIELDS(self) -> List[str]:
        """Calculated/metric fields."""
        return ["shaves", "unique_users"]

    @property
    def RANKING_FIELDS(self) -> List[str]:
        """Fields used for sorting/ranking."""
        return ["shaves", "unique_users"]



    def __init__(self, category: str):
        """Initialize annual aggregator for a specific category.

        Args:
            category: Product category to aggregate (razors, blades, brushes, soaps)
        """
        self.category = category

    def aggregate_from_monthly_data(self, monthly_data: Dict[str, Dict]) -> List[Dict[str, Any]]:
        """Aggregate data from monthly aggregated data.

        Args:
            monthly_data: Dictionary of monthly data keyed by month

        Returns:
            List of aggregated data sorted by shaves desc, unique_users desc
        """
        if not monthly_data:
            return []

        # Convert monthly data to records format expected by BaseAggregator
        records = self._convert_monthly_to_records(monthly_data)

        # Use BaseAggregator's aggregation logic
        return self.aggregate(records)

    def _convert_monthly_to_records(self, monthly_data: Dict[str, Dict]) -> List[Dict[str, Any]]:
        """Convert monthly aggregated data to records format for BaseAggregator.

        Args:
            monthly_data: Dictionary of monthly data keyed by month

        Returns:
            List of records in format expected by BaseAggregator
        """
        records = []

        for month, data in monthly_data.items():
            if "data" in data and isinstance(data["data"], dict):
                data_section = data["data"]
                if self.category in data_section and isinstance(data_section[self.category], list):
                    for item in data_section[self.category]:
                        if isinstance(item, dict) and "name" in item:
                            # Convert monthly item to record format
                            record = {
                                "name": item["name"],
                                "shaves": item.get("shaves", 0),
                                "unique_users": item.get("unique_users", 0),
                                "rank": item.get("rank", 0),  # Use rank field instead of position
                            }
                            records.append(record)

        return records

    def _extract_data(self, records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Extract data from records for aggregation.

        Args:
            records: List of records (already in correct format from monthly data)

        Returns:
            List of dictionaries with extracted data fields
        """
        # For annual aggregation, records are already in the correct format
        # Just ensure they have the required fields
        extracted_data = []
        for record in records:
            if "name" in record and "shaves" in record and "unique_users" in record:
                extracted_data.append(
                    {
                        "name": record["name"],
                        "shaves": record["shaves"],
                        "unique_users": record["unique_users"],
                    }
                )

        return extracted_data

    def _create_composite_name(self, df: pd.DataFrame) -> pd.Series:
        """Create composite name from extracted data.

        Args:
            df: DataFrame with extracted data

        Returns:
            Series with composite names
        """
        # For annual aggregation, name is already composite
        return df["name"]  # type: ignore[return-value]

    def _group_and_aggregate(self, df: pd.DataFrame) -> pd.DataFrame:
        """Group data and calculate aggregation metrics.

        Args:
            df: DataFrame with extracted data and composite name

        Returns:
            DataFrame with grouped and aggregated data
        """
        # For annual aggregation, we sum the shaves and unique_users across months
        grouped = df.groupby("name").agg({"shaves": "sum", "unique_users": "sum"}).reset_index()

        return grouped


# Factory functions for creating annual aggregators
def create_annual_razor_aggregator() -> AnnualAggregator:
    """Create annual aggregator for razors."""
    return AnnualAggregator("razors")


def create_annual_blade_aggregator() -> AnnualAggregator:
    """Create annual aggregator for blades."""
    return AnnualAggregator("blades")


def create_annual_brush_aggregator() -> AnnualAggregator:
    """Create annual aggregator for brushes."""
    return AnnualAggregator("brushes")


def create_annual_soap_aggregator() -> AnnualAggregator:
    """Create annual aggregator for soaps."""
    return AnnualAggregator("soaps")


def create_annual_razor_blade_combinations_aggregator() -> AnnualAggregator:
    """Create annual aggregator for razor-blade combinations."""
    return AnnualAggregator("razor_blade_combinations")


def create_annual_highest_use_count_per_blade_aggregator() -> AnnualAggregator:
    """Create annual aggregator for highest use count per blade."""
    return AnnualAggregator("highest_use_count_per_blade")


# Legacy function interfaces for backward compatibility
def aggregate_annual_razors(monthly_data: Dict[str, Dict]) -> List[Dict[str, Any]]:
    """Aggregate annual razor data from monthly data.

    Args:
        monthly_data: Dictionary of monthly data keyed by month

    Returns:
        List of aggregated razor data sorted by shaves desc, unique_users desc
    """
    aggregator = create_annual_razor_aggregator()
    return aggregator.aggregate_from_monthly_data(monthly_data)


def aggregate_annual_blades(monthly_data: Dict[str, Dict]) -> List[Dict[str, Any]]:
    """Aggregate annual blade data from monthly data.

    Args:
        monthly_data: Dictionary of monthly data keyed by month

    Returns:
        List of aggregated blade data sorted by shaves desc, unique_users desc
    """
    aggregator = create_annual_blade_aggregator()
    return aggregator.aggregate_from_monthly_data(monthly_data)


def aggregate_annual_brushes(monthly_data: Dict[str, Dict]) -> List[Dict[str, Any]]:
    """Aggregate annual brush data from monthly data.

    Args:
        monthly_data: Dictionary of monthly data keyed by month

    Returns:
        List of aggregated brush data sorted by shaves desc, unique_users desc
    """
    aggregator = create_annual_brush_aggregator()
    return aggregator.aggregate_from_monthly_data(monthly_data)


def aggregate_annual_soaps(monthly_data: Dict[str, Dict]) -> List[Dict[str, Any]]:
    """Aggregate annual soaps from monthly data."""
    aggregator = create_annual_soap_aggregator()
    return aggregator.aggregate_from_monthly_data(monthly_data)


def aggregate_annual_razor_blade_combinations(
    monthly_data: Dict[str, Dict],
) -> List[Dict[str, Any]]:
    """Aggregate annual razor-blade combinations from monthly data."""
    aggregator = create_annual_razor_blade_combinations_aggregator()
    return aggregator.aggregate_from_monthly_data(monthly_data)


def aggregate_annual_highest_use_count_per_blade(
    monthly_data: Dict[str, Dict],
) -> List[Dict[str, Any]]:
    """Aggregate annual highest use count per blade from monthly data."""
    aggregator = create_annual_highest_use_count_per_blade_aggregator()
    return aggregator.aggregate_from_monthly_data(monthly_data)
