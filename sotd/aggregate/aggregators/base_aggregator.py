from abc import ABC, abstractmethod
from typing import Any, Dict, List

import pandas as pd


class BaseAggregator(ABC):
    """Base class for all aggregators in the SOTD pipeline.

    Provides common functionality for extracting data from records, processing with pandas,
    and generating standardized aggregation results with position rankings.
    """

    def aggregate(self, records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Aggregate data from enriched records.

        Returns a list of aggregations sorted by shaves desc, unique_users desc.
        Each item includes position field for delta calculations.

        Args:
            records: List of enriched comment records

        Returns:
            List of aggregations with position, name, shaves, and unique_users fields
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

        # Sort and add position
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

        # Flatten column names
        if len(group_columns) == 1:
            # Single grouping column (name only)
            grouped.columns = ["name", "shaves", "unique_users"]
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
        """Sort grouped data and add position rankings.

        Args:
            grouped: DataFrame with grouped and aggregated data

        Returns:
            List of dictionaries with position, name, shaves, and unique_users fields
        """
        # Sort by shaves desc, unique_users desc
        grouped = grouped.sort_values(["shaves", "unique_users"], ascending=[False, False])

        # Add position field (1-based rank)
        grouped = grouped.reset_index(drop=True).assign(position=lambda df: range(1, len(df) + 1))  # type: ignore

        # Convert to list of dictionaries
        result = []
        for _, row in grouped.iterrows():
            item = {
                "position": int(row["position"]),
                "shaves": int(row["shaves"]),
                "unique_users": int(row["unique_users"]),
            }

            # Add all other columns (name, fiber, etc.)
            for col in row.index:
                if col not in ["position", "shaves", "unique_users"]:
                    item[str(col)] = row[col]  # type: ignore

            result.append(item)

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
