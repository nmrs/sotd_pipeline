# pyright: reportAttributeAccessIssue=false
# !/usr/bin/env python3
"""Base table generator for the report phase."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

import pandas as pd

from ..delta_calculator import DeltaCalculator


class DataValidationMixin:
    """Mixin providing common data validation functionality for table generators."""

    def _validate_data_records(
        self, data: list, data_key: str, required_fields: list[str]
    ) -> list[dict]:
        """Generic data validation for table generators.

        Args:
            data: Raw data list to validate
            data_key: Key name for debug messages
            required_fields: List of required field names

        Returns:
            List of validated data records
        """
        if not isinstance(data, list):
            if self.debug:
                print(f"[DEBUG] {data_key} data is not a list")
            return []

        valid_data = []
        for i, record in enumerate(data):
            if not isinstance(record, dict):
                if self.debug:
                    print(f"[DEBUG] {data_key} record {i} is not a dict")
                continue

            # Check for required fields
            missing_fields = [field for field in required_fields if field not in record]
            if missing_fields:
                if self.debug:
                    print(f"[DEBUG] {data_key} record {i} missing fields: {missing_fields}")
                continue

            # Ensure shaves is numeric and positive (if present)
            if "shaves" in required_fields:
                if not isinstance(record["shaves"], (int, float)) or record["shaves"] <= 0:
                    if self.debug:
                        print(
                            f"[DEBUG] {data_key} record {i} has invalid shaves: {record['shaves']}"
                        )
                    continue

            valid_data.append(record)

        return valid_data


class NoDeltaMixin:
    """Mixin to disable delta calculations for cross-product tables."""

    def generate_table(
        self,
        max_rows: int = 20,
        include_delta: bool = False,
        comparison_data: Optional[Dict[str, Any]] = None,
        include_header: bool = True,
    ) -> str:
        """Generate a markdown table without delta columns.

        Args:
            max_rows: Maximum number of rows to include
            include_delta: Whether to include delta columns (ignored for this table)
            comparison_data: Historical data for delta calculations (ignored for this table)
            include_header: Whether to include the table header (default: True)

        Returns:
            Markdown table as a string
        """
        # Override to never include deltas for cross-product tables
        return super().generate_table(
            max_rows=max_rows, include_delta=False, include_header=include_header
        )


# Standard column configurations
STANDARD_PRODUCT_COLUMNS = {
    "name": {"display_name": "name"},
    "shaves": {"display_name": "shaves", "format": "number"},
    "unique_users": {"display_name": "unique users", "format": "number"},
    "avg_shaves_per_user": {
        "display_name": "avg shaves per user",
        "format": "decimal",
        "decimals": 2,
    },
}

STANDARD_MANUFACTURER_COLUMNS = {
    "brand": {"display_name": "name"},
    "shaves": {"display_name": "shaves", "format": "number"},
    "unique_users": {"display_name": "unique users", "format": "number"},
    "avg_shaves_per_user": {
        "display_name": "avg shaves per user",
        "format": "decimal",
        "decimals": 2,
    },
}

STANDARD_SPECIALIZED_COLUMNS = {
    "plate": {"display_name": "name", "format": "text"},
    "shaves": {"display_name": "shaves", "format": "number"},
    "unique_users": {"display_name": "unique users", "format": "number"},
    "avg_shaves_per_user": {
        "display_name": "avg shaves per user",
        "format": "decimal",
        "decimals": 2,
    },
}

STANDARD_USER_COLUMNS = {
    "user_display": {"display_name": "user", "format": "text"},
    "shaves": {"display_name": "shaves", "format": "number"},
    "missed_days": {"display_name": "missed days", "format": "number"},
}

STANDARD_DIVERSITY_COLUMNS = {
    "maker": {"display_name": "name"},
    "unique_soaps": {"display_name": "unique soaps", "format": "number"},
}

STANDARD_USE_COUNT_COLUMNS = {
    "user": {"display_name": "user"},
    "blade": {"display_name": "blade"},
    "format": {"display_name": "format"},
    "uses": {"display_name": "uses", "format": "number"},
}


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

    def get_name_key(self) -> str:
        """Get the key to use for matching items in delta calculations.

        This is used to determine which field contains the item name for matching
        between current and historical datasets.

        Returns:
            Name key for delta calculations
        """
        # Default to "name" - subclasses can override
        return "name"

    @classmethod
    def create_standard_product_table(
        cls,
        data: Dict[str, Any],
        category: str,
        title: str,
        name_key: str = "name",
        debug: bool = False,
    ) -> "BaseTableGenerator":
        """Factory method to create a standard product table generator.

        Args:
            data: Data from aggregated data
            category: Data category to use
            title: Table title
            name_key: Key to use for matching items in delta calculations
            debug: Enable debug logging

        Returns:
            Configured table generator instance
        """
        return StandardProductTableFactory(
            data=data, category=category, title=title, name_key=name_key, debug=debug
        )

    @classmethod
    def create_manufacturer_table(
        cls,
        data: Dict[str, Any],
        category: str,
        title: str,
        name_key: str = "brand",
        debug: bool = False,
    ) -> "BaseTableGenerator":
        """Factory method to create a manufacturer table generator.

        Args:
            data: Data from aggregated data
            category: Data category to use
            title: Table title
            name_key: Key to use for matching items in delta calculations
            debug: Enable debug logging

        Returns:
            Configured table generator instance
        """
        return ManufacturerTableFactory(
            data=data, category=category, title=title, name_key=name_key, debug=debug
        )

    @classmethod
    def create_specialized_table(
        cls,
        data: Dict[str, Any],
        category: str,
        title: str,
        name_key: str = "plate",
        debug: bool = False,
    ) -> "BaseTableGenerator":
        """Factory method to create a specialized table generator.

        Args:
            data: Data from aggregated data
            category: Data category to use
            title: Table title
            name_key: Key to use for matching items in delta calculations
            debug: Enable debug logging

        Returns:
            Configured table generator instance
        """
        return SpecializedTableFactory(
            data=data, category=category, title=title, name_key=name_key, debug=debug
        )

    @classmethod
    def create_diversity_table(
        cls,
        data: Dict[str, Any],
        category: str,
        title: str,
        name_key: str = "maker",
        debug: bool = False,
    ) -> "BaseTableGenerator":
        """Factory method to create a diversity table generator.

        Args:
            data: Data from aggregated data
            category: Data category to use
            title: Table title
            name_key: Key to use for matching items in delta calculations
            debug: Enable debug logging

        Returns:
            Configured table generator instance
        """
        return DiversityTableFactory(
            data=data, category=category, title=title, name_key=name_key, debug=debug
        )

    @classmethod
    def create_use_count_table(
        cls,
        data: Dict[str, Any],
        category: str,
        title: str,
        debug: bool = False,
    ) -> "BaseTableGenerator":
        """Factory method to create a use count table generator.

        Args:
            data: Data from aggregated data
            category: Data category to use
            title: Table title
            debug: Enable debug logging

        Returns:
            Configured table generator instance
        """
        return UseCountTableFactory(data=data, category=category, title=title, debug=debug)

    def generate_table(
        self,
        max_rows: int = 20,
        include_delta: bool = False,
        comparison_data: Optional[Dict[str, Any]] = None,
        include_header: bool = True,
    ) -> str:
        """Generate a markdown table.

        Args:
            max_rows: Maximum number of rows to include
            include_delta: Whether to include delta columns
            comparison_data: Historical data for delta calculations
                           (dict mapping period to (metadata, data))
            include_header: Whether to include the table header (default: True)

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

        # Add avg shaves per user calculation
        table_data = self._add_avg_shaves_per_user(table_data)

        # Add position information for delta calculations
        if include_delta:
            table_data = self._add_positions(table_data)

        # Calculate deltas if requested
        if include_delta and comparison_data:
            table_data = self._calculate_multi_period_deltas(table_data, comparison_data)

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
            column_config = self._add_multi_period_delta_column_config(
                column_config, comparison_data
            )

        # Select and rename columns
        columns = list(column_config.keys())
        # Ensure all columns from config are present in the DataFrame, fill missing with 'n/a'
        for col in columns:
            if col not in df.columns:
                df[col] = "n/a"
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
                            df[col]
                            .astype(object)
                            .apply(
                                lambda x: (
                                    f"{x:,}"
                                    if isinstance(x, (int, float))
                                    else ("n/a" if x == "n/a" else str(x))
                                )
                            )
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

        # Title (only if include_header is True)
        if include_header:
            markdown_lines.append(f"### {self.get_table_title()}")
            markdown_lines.append("")

        # Table header with proper alignment
        header = "| " + " | ".join(df.columns) + " |"
        markdown_lines.append(header)

        # Table separator with proper alignment (right-aligned for numbers, center for deltas)
        separator_parts = []
        for col in df.columns:
            orig_col = None
            for k, v in column_renames.items():
                if v == col:
                    orig_col = k
                    break

            if orig_col and orig_col in column_config:
                config = column_config[orig_col]
                if config.get("format") == "delta":
                    separator_parts.append(":---:")  # Center-aligned for deltas
                else:
                    separator_parts.append("---:")  # Right-aligned for numbers
            else:
                separator_parts.append("---")  # Left-aligned for text

        separator = "| " + " | ".join(separator_parts) + " |"
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

        # Check if positions already exist
        if any("position" in item for item in data):
            if self.debug:
                print("[DEBUG] Positions already exist in data, skipping position addition")
            return data

        # Add positions based on shaves (descending order)
        sorted_data = sorted(data, key=lambda x: x.get("shaves", 0), reverse=True)
        for i, item in enumerate(sorted_data):
            item["position"] = i + 1

        if self.debug:
            print(f"[DEBUG] Added positions to {len(data)} items")

        return data

    def _calculate_deltas(
        self,
        current_data: List[Dict[str, Any]],
        comparison_data: Dict[str, Any],
        comparison_period: str,
    ) -> List[Dict[str, Any]]:
        """Calculate deltas for the current data against historical data.

        Args:
            current_data: Current period data with positions
            comparison_data: Historical data for comparison
            comparison_period: Period name for the comparison

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
            name_key = self.get_name_key()
            deltas = self.delta_calculator.calculate_deltas(
                current_data, historical_data, name_key=name_key, max_items=len(current_data)
            )

            # Update the current data with delta information
            for i, item in enumerate(current_data):
                if i < len(deltas):
                    delta_item = deltas[i]
                    item["delta_text"] = delta_item.get("delta_text", "n/a")
                    item["delta_position"] = delta_item.get("delta_position", "n/a")

            if self.debug:
                print(f"[DEBUG] Calculated deltas for {len(current_data)} items")

        except Exception as e:
            if self.debug:
                print(f"[DEBUG] Error calculating deltas: {e}")
            # Add n/a for deltas if calculation fails
            for item in current_data:
                item["delta_text"] = "n/a"
                item["delta_position"] = "n/a"

        return current_data

    def _add_delta_column_config(
        self, column_config: Dict[str, Dict[str, Any]], comparison_period: str
    ) -> Dict[str, Dict[str, Any]]:
        """Add delta column configuration to the existing config.

        Args:
            column_config: Existing column configuration
            comparison_period: Period name for the comparison

        Returns:
            Updated column configuration with delta columns
        """
        # Create a copy to avoid modifying the original
        updated_config = column_config.copy()

        # Add delta column configuration
        updated_config["delta_text"] = {
            "display_name": f"Δ vs {comparison_period}",
            "format": "delta",
        }

        return updated_config

    def _add_avg_shaves_per_user(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Add average shaves per user calculation to data.

        Args:
            data: List of data items

        Returns:
            Data with avg shaves per user added
        """
        if not data:
            return data

        for item in data:
            if "shaves" in item and "unique_users" in item:
                shaves = item.get("shaves", 0)
                unique_users = item.get("unique_users", 0)

                if unique_users > 0:
                    avg_shaves = shaves / unique_users
                    item["avg_shaves_per_user"] = round(avg_shaves, 2)
                else:
                    item["avg_shaves_per_user"] = 0.0

        return data

    def _calculate_multi_period_deltas(
        self,
        current_data: List[Dict[str, Any]],
        comparison_data: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """Calculate deltas for the current data across multiple periods.

        Args:
            current_data: Current period data with positions
            comparison_data: Historical data for comparison
                           (dict mapping period to (metadata, data))

        Returns:
            Current data with delta information added for each period
        """
        if not comparison_data:
            if self.debug:
                print("[DEBUG] No comparison data provided for delta calculation")
            return current_data

        # Start with the current data
        result = current_data.copy()

        # Calculate deltas for each period and add to the result
        for period, (metadata, historical_data) in comparison_data.items():
            # Get the historical data for this category
            category_name = self.get_category_name()
            historical_category_data = historical_data.get(category_name, [])

            if not historical_category_data:
                if self.debug:
                    print(f"[DEBUG] No historical data found for category: {category_name}")
                continue

            # Add positions to historical data if not present
            if not any("position" in item for item in historical_category_data):
                historical_category_data = self._add_positions(historical_category_data)

            # Calculate deltas for this period
            try:
                name_key = self.get_name_key()
                period_deltas = self.delta_calculator.calculate_deltas(
                    result, historical_category_data, name_key=name_key, max_items=len(result)
                )

                # Update the result with delta information for this period
                for i, item in enumerate(result):
                    if i < len(period_deltas):
                        period_item = period_deltas[i]
                        # Add delta information for this period
                        period_key = period.lower().replace(" ", "_").replace("-", "_")
                        delta_key = f"delta_{period_key}"
                        result[i][delta_key] = period_item.get("delta_text", "n/a")

                if self.debug:
                    print(f"[DEBUG] Added deltas for period {period}")

            except Exception as e:
                if self.debug:
                    print(f"[DEBUG] Error calculating deltas for period {period}: {e}")
                # Add n/a for this period if calculation fails
                for item in result:
                    period_key = period.lower().replace(" ", "_").replace("-", "_")
                    delta_key = f"delta_{period_key}"
                    item[delta_key] = "n/a"

        if self.debug:
            print(f"[DEBUG] Calculated multi-period deltas for {len(result)} items")

        return result

    def _add_multi_period_delta_column_config(
        self, column_config: Dict[str, Dict[str, Any]], comparison_data: Dict[str, Any]
    ) -> Dict[str, Dict[str, Any]]:
        """Add delta column configuration for multiple periods to the existing config.

        Args:
            column_config: Existing column configuration
            comparison_data: Historical data for comparison
                           (dict mapping period to (metadata, data))

        Returns:
            Updated column configuration with delta columns for multiple periods
        """
        # Create a copy to avoid modifying the original
        updated_config = column_config.copy()

        # Always add delta column configuration for each period, even if historical data is empty
        for period in comparison_data.keys():
            # Create a safe column key
            period_key = period.lower().replace(" ", "_").replace("-", "_")
            updated_config[f"delta_{period_key}"] = {
                "display_name": f"Δ vs {period}",
                "format": "delta",
            }

        return updated_config


# Factory classes for common table types
class StandardProductTableFactory(BaseTableGenerator, DataValidationMixin):
    """Factory class for standard product tables."""

    def __init__(
        self,
        data: Dict[str, Any],
        category: str,
        title: str,
        name_key: str = "name",
        debug: bool = False,
    ):
        """Initialize the factory.

        Args:
            data: Data from aggregated data
            category: Data category to use
            title: Table title
            name_key: Key to use for matching items in delta calculations
            debug: Enable debug logging
        """
        super().__init__(data, debug)
        self.category = category
        self._title = title
        self._name_key = name_key

    def get_table_data(self) -> List[Dict[str, Any]]:
        """Get the data for the table."""
        data = self.data.get(self.category, [])
        return self._validate_data_records(data, self.category, ["name", "shaves"])

    def get_table_title(self) -> str:
        """Get the table title."""
        return self._title

    def get_column_config(self) -> Dict[str, Dict[str, Any]]:
        """Get the column configuration."""
        return STANDARD_PRODUCT_COLUMNS

    def get_category_name(self) -> str:
        """Get the category name for data matching."""
        return self.category

    def get_name_key(self) -> str:
        """Get the key to use for matching items in delta calculations."""
        return self._name_key


class ManufacturerTableFactory(BaseTableGenerator, DataValidationMixin):
    """Factory class for manufacturer tables."""

    def __init__(
        self,
        data: Dict[str, Any],
        category: str,
        title: str,
        name_key: str = "brand",
        debug: bool = False,
    ):
        """Initialize the factory.

        Args:
            data: Data from aggregated data
            category: Data category to use
            title: Table title
            name_key: Key to use for matching items in delta calculations
            debug: Enable debug logging
        """
        super().__init__(data, debug)
        self.category = category
        self._title = title
        self._name_key = name_key

    def get_table_data(self) -> List[Dict[str, Any]]:
        """Get the data for the table."""
        data = self.data.get(self.category, [])
        return self._validate_data_records(data, self.category, ["brand", "shaves"])

    def get_table_title(self) -> str:
        """Get the table title."""
        return self._title

    def get_column_config(self) -> Dict[str, Dict[str, Any]]:
        """Get the column configuration."""
        return STANDARD_MANUFACTURER_COLUMNS

    def get_category_name(self) -> str:
        """Get the category name for data matching."""
        return self.category

    def get_name_key(self) -> str:
        """Get the key to use for matching items in delta calculations."""
        return self._name_key


class SpecializedTableFactory(BaseTableGenerator, DataValidationMixin):
    """Factory class for specialized tables."""

    def __init__(
        self,
        data: Dict[str, Any],
        category: str,
        title: str,
        name_key: str = "plate",
        debug: bool = False,
    ):
        """Initialize the factory.

        Args:
            data: Data from aggregated data
            category: Data category to use
            title: Table title
            name_key: Key to use for matching items in delta calculations
            debug: Enable debug logging
        """
        super().__init__(data, debug)
        self.category = category
        self._title = title
        self._name_key = name_key

    def get_table_data(self) -> List[Dict[str, Any]]:
        """Get the data for the table."""
        data = self.data.get(self.category, [])
        return self._validate_data_records(data, self.category, ["plate", "shaves"])

    def get_table_title(self) -> str:
        """Get the table title."""
        return self._title

    def get_column_config(self) -> Dict[str, Dict[str, Any]]:
        """Get the column configuration."""
        return STANDARD_SPECIALIZED_COLUMNS

    def get_category_name(self) -> str:
        """Get the category name for data matching."""
        return self.category

    def get_name_key(self) -> str:
        """Get the key to use for matching items in delta calculations."""
        return self._name_key


class DiversityTableFactory(BaseTableGenerator, DataValidationMixin):
    """Factory class for diversity tables."""

    def __init__(
        self,
        data: Dict[str, Any],
        category: str,
        title: str,
        name_key: str = "maker",
        debug: bool = False,
    ):
        """Initialize the factory.

        Args:
            data: Data from aggregated data
            category: Data category to use
            title: Table title
            name_key: Key to use for matching items in delta calculations
            debug: Enable debug logging
        """
        super().__init__(data, debug)
        self.category = category
        self._title = title
        self._name_key = name_key

    def get_table_data(self) -> List[Dict[str, Any]]:
        """Get the data for the table."""
        data = self.data.get(self.category, [])
        return self._validate_data_records(data, self.category, ["maker", "unique_soaps"])

    def get_table_title(self) -> str:
        """Get the table title."""
        return self._title

    def get_column_config(self) -> Dict[str, Dict[str, Any]]:
        """Get the column configuration."""
        return STANDARD_DIVERSITY_COLUMNS

    def get_category_name(self) -> str:
        """Get the category name for data matching."""
        return self.category

    def get_name_key(self) -> str:
        """Get the key to use for matching items in delta calculations."""
        return self._name_key


class UseCountTableFactory(BaseTableGenerator, DataValidationMixin):
    """Factory class for use count tables."""

    def __init__(
        self,
        data: Dict[str, Any],
        category: str,
        title: str,
        debug: bool = False,
    ):
        """Initialize the factory.

        Args:
            data: Data from aggregated data
            category: Data category to use
            title: Table title
            debug: Enable debug logging
        """
        super().__init__(data, debug)
        self.category = category
        self._title = title

    def get_table_data(self) -> List[Dict[str, Any]]:
        """Get the data for the table."""
        data = self.data.get(self.category, [])
        return self._validate_data_records(data, self.category, ["user", "blade", "uses"])

    def get_table_title(self) -> str:
        """Get the table title."""
        return self._title

    def get_column_config(self) -> Dict[str, Dict[str, Any]]:
        """Get the column configuration."""
        return STANDARD_USE_COUNT_COLUMNS

    def get_category_name(self) -> str:
        """Get the category name for data matching."""
        return self.category


# Legacy classes for backward compatibility
class StandardProductTableGenerator(BaseTableGenerator, DataValidationMixin):
    """Base class for standard product tables (name, shaves, unique_users, avg_shaves_per_user)."""

    def get_column_config(self) -> Dict[str, Dict[str, Any]]:
        """Return standard product column configuration."""
        return STANDARD_PRODUCT_COLUMNS


class ManufacturerTableGenerator(BaseTableGenerator, DataValidationMixin):
    """Base class for manufacturer tables (brand, shaves, unique_users, avg_shaves_per_user)."""

    def get_name_key(self) -> str:
        """Return the key to use for matching items in delta calculations."""
        return "brand"

    def get_column_config(self) -> Dict[str, Dict[str, Any]]:
        """Return standard manufacturer column configuration."""
        return STANDARD_MANUFACTURER_COLUMNS


class SpecializedTableGenerator(BaseTableGenerator, DataValidationMixin):
    """Base class for specialized tables (plate, shaves, unique_users, avg_shaves_per_user)."""

    def get_name_key(self) -> str:
        """Return the key to use for matching items in delta calculations."""
        return "plate"

    def get_column_config(self) -> Dict[str, Dict[str, Any]]:
        """Return standard specialized column configuration."""
        return STANDARD_SPECIALIZED_COLUMNS


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
