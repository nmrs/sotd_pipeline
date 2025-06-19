# pyright: reportAttributeAccessIssue=false
#!/usr/bin/env python3
"""Base table generator for the report phase."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

import pandas as pd


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

    def generate_table(
        self,
        max_rows: int = 20,
        include_delta: bool = False,
        comparison_data: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Generate a markdown table.

        Args:
            max_rows: Maximum number of rows to include
            include_delta: Whether to include delta columns
            comparison_data: Historical data for delta calculations

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

        # Convert to DataFrame
        df = pd.DataFrame(table_data)

        if df.empty:
            if self.debug:
                print(f"[DEBUG] Empty DataFrame for table: {self.get_table_title()}")
            return ""

        # Get column configuration
        column_config = self.get_column_config()

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
        """Get the column configuration for the table."""
        return self._column_config


def _format_decimal(x: Any, decimals: int) -> str:
    return f"{x:.{decimals}f}" if pd.notna(x) else "0.00"
