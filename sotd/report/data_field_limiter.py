#!/usr/bin/env python3
"""Data field limiter for enhanced report templates."""

from typing import Any, Dict, List


class DataFieldLimiter:
    """Applies data field limits to table data."""

    def apply_limits(
        self, data: List[Dict[str, Any]], parameters: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Apply data field limits to the data.

        Args:
            data: List of data records
            parameters: Dictionary of column:threshold parameters

        Returns:
            Filtered data with limits applied
        """
        if not parameters:
            return data

        result = data

        for column, threshold in parameters.items():
            # Skip universal parameters like rows/ranks
            if column in ["rows", "ranks"]:
                continue

            result = self.apply_column_limit(result, column, threshold)

        return result

    def apply_column_limit(
        self, data: List[Dict[str, Any]], column: str, threshold: Any
    ) -> List[Dict[str, Any]]:
        """Apply limit to a specific column.

        Args:
            data: List of data records
            column: Column name to limit
            threshold: Threshold value for the limit

        Returns:
            Filtered data with column limit applied
        """
        if not data:
            return data

        # Check if column exists in data
        if column not in data[0]:
            return data

        # Apply the limit based on data type
        if isinstance(threshold, (int, float)):
            # Numeric comparison
            return [item for item in data if self._compare_numeric(item.get(column), threshold)]
        else:
            # String comparison
            return [item for item in data if self._compare_string(item.get(column), threshold)]

    def _compare_numeric(self, value: Any, threshold: Any) -> bool:
        """Compare numeric values for limit application.

        Args:
            value: Value to compare
            threshold: Threshold to compare against

        Returns:
            True if value meets or exceeds threshold, False otherwise
        """
        if value is None:
            return False

        try:
            return float(value) >= float(threshold)
        except (ValueError, TypeError):
            return False

    def _compare_string(self, value: Any, threshold: Any) -> bool:
        """Compare string values for limit application.

        Args:
            value: Value to compare
            threshold: Threshold to compare against

        Returns:
            True if value meets or exceeds threshold, False otherwise
        """
        if value is None:
            return False

        try:
            return str(value) >= str(threshold)
        except (ValueError, TypeError):
            return False
