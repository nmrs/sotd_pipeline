from abc import ABC, abstractmethod
from typing import Any, Dict, List

import pandas as pd


class BaseAggregator(ABC):
    """Base class for all aggregators in the SOTD pipeline.

    Provides common functionality for extracting data from records, processing with pandas,
    and generating standardized aggregation results with tier-based rankings.
    """

    # Default tie detection columns - can be overridden by subclasses
    tie_columns = ["shaves", "unique_users"]

    def __init__(self, debug: bool = False):
        """Initialize the aggregator.

        Args:
            debug: Enable debug output
        """
        self.debug = debug

    def aggregate(self, records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Aggregate data from enriched records.

        Returns a list of aggregations sorted by shaves desc, unique_users desc.
        Each item includes rank field for delta calculations.

        Args:
            records: List of enriched comment records

        Returns:
            List of aggregations with rank, name, shaves, and unique_users fields
        """
        if not records:
            return []

        # Extract data from records
        extracted_data = self._extract_data(records)

        if not extracted_data:
            return []

        # Convert to DataFrame for efficient aggregation
        df = pd.DataFrame(extracted_data)

        # Create composite name
        df["name"] = self._create_composite_name(df)

        # Group and aggregate
        grouped = self._group_and_aggregate(df)

        # Sort and add tier-based ranking
        result = self._sort_and_rank(grouped)

        return result

    @abstractmethod
    def _extract_data(self, records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Extract relevant data from records for aggregation.

        Args:
            records: List of enriched comment records

        Returns:
            List of dictionaries with extracted data fields
        """
        pass

    @abstractmethod
    def _create_composite_name(self, df: pd.DataFrame) -> pd.Series:
        """Create composite name from extracted data fields.

        Args:
            df: DataFrame with extracted data

        Returns:
            Series with composite names
        """
        pass

    @property
    @abstractmethod
    def IDENTIFIER_FIELDS(self) -> List[str]:
        """Fields used for matching/grouping (e.g., user, brand, name, model).

        These fields are used by the table generator to determine
        which columns should be used for delta calculation matching.

        Returns:
            List of field names that serve as identifiers
        """
        pass

    @property
    @abstractmethod
    def METRIC_FIELDS(self) -> List[str]:
        """Calculated/metric fields (e.g., counts, averages, totals).

        These fields are excluded from delta calculation matching
        as they are derived values, not identifiers.

        Returns:
            List of field names that are calculated metrics
        """
        pass

    @property
    @abstractmethod
    def RANKING_FIELDS(self) -> List[str]:
        """Fields used for sorting/ranking the results.

        These fields determine the order of results in the
        aggregated output.

        Returns:
            List of field names used for sorting
        """
        pass

    def _group_and_aggregate(self, df: pd.DataFrame) -> pd.DataFrame:
        """Group data and calculate aggregation metrics.

        Args:
            df: DataFrame with extracted data and composite name

        Returns:
            DataFrame with grouped and aggregated data
        """
        # Get grouping columns (name + any additional grouping fields)
        group_columns = self._get_group_columns(df)

        # Group by columns and calculate metrics
        grouped = df.groupby(group_columns).agg({"author": ["count", "nunique"]}).reset_index()

        # Flatten column names - preserve original column names
        if len(group_columns) == 1:
            # Single grouping column - preserve original name
            grouped.columns = list(group_columns) + ["shaves", "unique_users"]
        else:
            # Multiple grouping columns
            grouped.columns = list(group_columns) + ["shaves", "unique_users"]

        return grouped

    def _get_group_columns(self, df: pd.DataFrame) -> List[str]:
        """Get columns to use for grouping.

        Args:
            df: DataFrame with extracted data

        Returns:
            List of column names for grouping
        """
        # Default: group by name only
        return ["name"]

    def _sort_and_rank(self, grouped: pd.DataFrame) -> List[Dict[str, Any]]:
        """Sort grouped data and add tier-based rankings.

        Args:
            grouped: DataFrame with grouped and aggregated data

        Returns:
            List of dictionaries with rank field and all original columns preserved
        """
        # Get the first grouping column for sorting (could be "name", "handle_maker", etc.)
        first_group_column = self._get_group_columns(grouped)[0]

        # Assign competition ranks to the entire dataset by tie_columns (all descending)
        # This gives us 1, 2, 2, 4, 5... style ranking where ties get same rank
        # Sort by tie_columns first (desc), then assign ranks
        ascending_list = [False] * len(self.tie_columns)
        grouped = grouped.sort_values(self.tie_columns, ascending=ascending_list)
        grouped = grouped.reset_index(drop=True)

        # Use original ranking logic to maintain exact same ranking behavior
        # Create a composite key for ranking that preserves the order
        # Use sequential ranks, then group by tie_columns to get same rank for ties
        grouped["temp_rank"] = range(1, len(grouped) + 1)
        grouped["rank"] = grouped.groupby(self.tie_columns, sort=False)["temp_rank"].transform(
            "min"
        )
        grouped = grouped.drop("temp_rank", axis=1)

        # Sort by ranking first, then by name for consistent ordering of tied entries
        grouped = grouped.sort_values(["rank", first_group_column], ascending=[True, True])
        grouped = grouped.reset_index(drop=True)

        # FULLY OPTIMIZED: Use pandas operations to eliminate ALL Python loops
        # 1. Reorder columns to put rank first using pandas column operations
        cols = ["rank"] + [col for col in grouped.columns if col != "rank"]
        grouped = grouped[cols]
        
        # 2. Convert to list using pandas to_dict - no manual field ordering needed
        # Convert Hashable keys to strings for type compatibility
        result = [{str(k): v for k, v in item.items()} for item in grouped.to_dict("records")]

        return result

    def _extract_field(
        self, record: Dict[str, Any], field_path: List[str], default: str = ""
    ) -> str:
        """Extract a field from a nested record structure.

        Args:
            record: Record dictionary
            field_path: List of keys to traverse (e.g., ["razor", "matched", "brand"])
            default: Default value if field not found

        Returns:
            Extracted field value as string, stripped of whitespace, or default if empty
        """
        value = record
        for key in field_path:
            if isinstance(value, dict):
                value = value.get(key, default)
            else:
                return default

        if value is None:
            return default

        # Convert to string and strip whitespace, return default if empty
        try:
            stripped_value = str(value).strip()
            return stripped_value if stripped_value else default
        except (AttributeError, TypeError):
            return default

    def _validate_required_fields(self, data: Dict[str, Any], required_fields: List[str]) -> bool:
        """Validate that all required fields are present and non-empty.

        Args:
            data: Dictionary with extracted data
            required_fields: List of required field names

        Returns:
            True if all required fields are present and non-empty
        """
        return all(data.get(field) for field in required_fields)
