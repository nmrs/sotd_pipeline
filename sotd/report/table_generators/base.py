# pyright: reportAttributeAccessIssue=false
#!/usr/bin/env python3
"""Base table generator for the report phase."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

import pandas as pd

from ..delta_calculator import DeltaCalculator


class BaseTableGenerator(ABC):
    """Base class for table generators."""

    def __init__(self, data: Dict[str, Any], debug: bool = False):
        """Initialize the table generator.

        Args:
            data: Data from aggregated data
            debug: Enable debug logging
        """
        self.data = data
        self.debug = debug
        self.delta_calculator = DeltaCalculator(debug=debug)

    @abstractmethod
    def get_table_data(self) -> List[Dict[str, Any]]:
        """Get the data for the table."""
        pass

    @abstractmethod
    def get_table_title(self) -> str:
        """Get the table title."""
        pass

    @abstractmethod
    def get_column_config(self) -> Dict[str, Dict[str, Any]]:
        """Get the column configuration for the table."""
        pass

    def get_category_name(self) -> str:
        """Get the category name for this table generator.

        This is used to match data between current and historical datasets.
        Override in subclasses if the category name differs from the table title.

        Returns:
            Category name for data matching
        """
        # Default implementation - subclasses can override
        return self.get_table_title().lower().replace(" ", "_")

    def generate_table(
        self,
        max_rows: int = 20,
        include_delta: bool = False,
        comparison_data: Optional[Dict[str, Any]] = None,
        comparison_period: str = "previous month",
    ) -> str:
        """Generate a markdown table.

        Args:
            max_rows: Maximum number of rows to include
            include_delta: Whether to include delta columns
            comparison_data: Historical data for delta calculations
            comparison_period: Which comparison period to use

        Returns:
            Markdown table as a string
        """
        if self.debug:
            print(f"[DEBUG] Generating table: {self.get_table_title()}")

        # Get the data
        table_data = self.get_table_data()

        if not table_data:
            if self.debug:
                print(f"[DEBUG] No data available for table: {self.get_table_title()}")
            return ""

        # Add position information for delta calculations
        if include_delta:
            table_data = self._add_positions(table_data)

        # Calculate deltas if requested
        if include_delta and comparison_data:
            table_data = self._calculate_deltas(table_data, comparison_data, comparison_period)

        # Convert to DataFrame
        df = pd.DataFrame(table_data)

        if df.empty:
            if self.debug:
                print(f"[DEBUG] Empty DataFrame for table: {self.get_table_title()}")
            return ""

        # Get column configuration
        column_config = self.get_column_config()

        # Add delta column configuration if deltas are included
        if include_delta and comparison_data:
            column_config = self._add_delta_column_config(column_config, comparison_period)

        # Select and rename columns
        columns = list(column_config.keys())
        available_columns = [col for col in columns if col in df.columns]

        if not available_columns:
            if self.debug:
                print(
                    f"[DEBUG] No configured columns available in data for table: "
                    f"{self.get_table_title()}"
                )
            return ""

        df = df[available_columns]

        # Rename columns for display
        column_renames: dict[str, str] = {
            col: config["display_name"]
            for col, config in column_config.items()
            if col in df.columns
        }
        df = df.rename(columns=column_renames)  # pyright: ignore[reportCallIssue]

        # Sort by the first numeric column (usually count/usage)
        numeric_columns = list(df.select_dtypes(include=["number"]).columns)
        if len(numeric_columns) > 0:
            sort_column = numeric_columns[0]
            df = df.sort_values(by=[sort_column], ascending=False)

        # Handle tie-breaking for max_rows
        if len(df) > max_rows:
            # Get the value at the cutoff point
            if len(numeric_columns) > 0:
                sort_column = numeric_columns[0]
                cutoff_value = df.iloc[max_rows - 1][sort_column]

                # Include all rows with the same value as the cutoff
                df = df[df[sort_column] >= cutoff_value]

                if self.debug:
                    print(f"[DEBUG] Tie-breaking: included {len(df)} rows (cutoff: {cutoff_value})")
            else:
                # If no numeric columns, just take the first max_rows
                df = df.head(max_rows)

        # Limit to max_rows if still over
        if len(df) > max_rows:
            df = df.head(max_rows)

        # Format numeric columns
        for col in df.columns:
            orig_col = None
            for k, v in column_renames.items():
                if v == col:
                    orig_col = k
                    break
            if orig_col and orig_col in column_config:
                config = column_config[orig_col]
                if config.get("format") == "number":
                    if col in df:
                        df[col] = (
                            df[col].astype(object).apply(lambda x: f"{x:,}" if pd.notna(x) else "0")
                        )  # pyright: ignore[reportAttributeAccessIssue]
                elif config.get("format") == "decimal":
                    decimals = config.get("decimals", 2)
                    if col in df:
                        df[col] = (
                            df[col].astype(object).apply(lambda x: _format_decimal(x, decimals))
                        )  # pyright: ignore[reportAttributeAccessIssue]
                elif config.get("format") == "delta":
                    # Delta columns are already formatted by the delta calculator
                    # Just ensure they're properly converted to strings
                    if col in df:
                        df[col] = (
                            df[col].astype(object).apply(lambda x: str(x) if pd.notna(x) else "n/a")
                        )

        # Generate markdown table
        markdown_lines = []

        # Title
        markdown_lines.append(f"### {self.get_table_title()}")
        markdown_lines.append("")

        # Table header
        header = "| " + " | ".join(df.columns) + " |"
        markdown_lines.append(header)

        # Table separator
        separator = "| " + " | ".join(["---"] * len(df.columns)) + " |"
        markdown_lines.append(separator)

        # Table rows
        for _, row in df.iterrows():
            row_str = "| " + " | ".join(str(cell) for cell in row.values) + " |"
            markdown_lines.append(row_str)

        markdown_lines.append("")

        return "\n".join(markdown_lines)

    def _add_positions(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Add position information to data for delta calculations.

        Args:
            data: List of data items

        Returns:
            Data with position information added
        """
        if not data:
            return data

        # Sort by the first numeric field (usually count/usage)
        numeric_fields = []
        for key in data[0].keys():
            if isinstance(data[0][key], (int, float)):
                numeric_fields.append(key)

        if not numeric_fields:
            if self.debug:
                print("[DEBUG] No numeric fields found for positioning")
            return data

        # Sort by the first numeric field in descending order
        sort_field = numeric_fields[0]
        sorted_data = sorted(data, key=lambda x: x.get(sort_field, 0), reverse=True)

        # Add position information
        for i, item in enumerate(sorted_data):
            item["position"] = i + 1

        if self.debug:
            print(f"[DEBUG] Added positions to {len(sorted_data)} items using {sort_field}")

        return sorted_data

    def _calculate_deltas(
        self,
        current_data: List[Dict[str, Any]],
        comparison_data: Dict[str, Any],
        comparison_period: str,
    ) -> List[Dict[str, Any]]:
        """Calculate deltas for the current data.

        Args:
            current_data: Current period data with positions
            comparison_data: Historical data for comparison
            comparison_period: Which comparison period to use

        Returns:
            Current data with delta information added
        """
        if not comparison_data:
            if self.debug:
                print("[DEBUG] No comparison data provided for delta calculation")
            return current_data

        # Get the historical data for this category
        category_name = self.get_category_name()
        historical_data = comparison_data.get(category_name, [])

        if not historical_data:
            if self.debug:
                print(f"[DEBUG] No historical data found for category: {category_name}")
            return current_data

        # Add positions to historical data if not present
        if not any("position" in item for item in historical_data):
            historical_data = self._add_positions(historical_data)

        # Calculate deltas
        try:
            result = self.delta_calculator.calculate_deltas(
                current_data, historical_data, max_items=len(current_data)
            )

            if self.debug:
                print(f"[DEBUG] Calculated deltas for {len(result)} items")

            return result
        except Exception as e:
            if self.debug:
                print(f"[DEBUG] Error calculating deltas: {e}")
            return current_data

    def _add_delta_column_config(
        self, column_config: Dict[str, Dict[str, Any]], comparison_period: str
    ) -> Dict[str, Dict[str, Any]]:
        """Add delta column configuration to the existing config.

        Args:
            column_config: Existing column configuration
            comparison_period: Which comparison period to use

        Returns:
            Updated column configuration with delta column
        """
        # Create a copy to avoid modifying the original
        updated_config = column_config.copy()

        # Add delta column configuration
        updated_config["delta_text"] = {
            "display_name": f"vs {comparison_period.title()}",
            "format": "delta",
        }

        return updated_config


class SimpleTableGenerator(BaseTableGenerator):
    """Simple table generator for basic data."""

    def __init__(
        self,
        data: Dict[str, Any],
        category: str,
        title: str,
        column_config: Dict[str, Dict[str, Any]],
        debug: bool = False,
    ):
        """Initialize the simple table generator.

        Args:
            data: Data from aggregated data
            category: Data category to use
            title: Table title
            column_config: Column configuration
            debug: Enable debug logging
        """
        super().__init__(data, debug)
        self.category = category
        self._title = title
        self._column_config = column_config

    def get_table_data(self) -> List[Dict[str, Any]]:
        """Get the data for the table."""
        return self.data.get(self.category, [])

    def get_table_title(self) -> str:
        """Get the table title."""
        return self._title

    def get_column_config(self) -> Dict[str, Dict[str, Any]]:
        """Get the column configuration."""
        return self._column_config

    def get_category_name(self) -> str:
        """Get the category name for data matching."""
        return self.category


def _format_decimal(x: Any, decimals: int) -> str:
    """Format a decimal value with the specified number of decimal places."""
    if pd.isna(x):
        return "0.0"
    try:
        return f"{float(x):.{decimals}f}"
    except (ValueError, TypeError):
        return "0.0"
