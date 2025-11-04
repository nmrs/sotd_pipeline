#!/usr/bin/env python3
"""Parameter validator for table template parameters."""

from dataclasses import dataclass
from typing import Any, Dict, List


@dataclass
class ValidationResult:
    """Result of parameter validation."""

    is_valid: bool
    errors: List[str]


class ParameterValidator:
    """Validator for table parameters based on known table structures."""

    # Mapping of table names to their available sorting columns
    # This is derived from the actual aggregator implementations and can be easily updated
    # when aggregators change their field names or structure
    # These are the actual field names used in templates for filtering, not display names
    TABLE_SORTING_COLUMNS = {
        # Core product tables
        "razors": ["shaves", "unique_users"],
        "blades": ["shaves", "unique_users"],
        "brushes": ["shaves", "unique_users"],
        "soaps": ["shaves", "unique_users"],
        # Manufacturer tables
        "razor-manufacturers": ["shaves", "unique_users"],
        "blade-manufacturers": ["shaves", "unique_users"],
        "brush-handle-makers": ["shaves", "unique_users"],
        "brush-knot-makers": ["shaves", "unique_users"],
        "soap-makers": ["shaves", "unique_users"],
        # Diversity tables
        "brush-diversity": ["unique_brushes", "shaves"],
        "blade-diversity": ["unique_blades", "shaves"],
        "soap-diversity": ["unique_soaps", "shaves"],
        "razor-diversity": ["unique_razors", "shaves"],
        "brand-diversity": ["unique_soaps", "shaves"],
        # Specialized tables
        "blackbird-plates": ["shaves", "unique_users"],
        "christopher-bradley-plates": ["shaves", "unique_users"],
        "game-changer-plates": ["shaves", "unique_users"],
        "super-speed-tips": ["shaves", "unique_users"],
        "straight-widths": ["shaves", "unique_users"],
        "straight-grinds": ["shaves", "unique_users"],
        "straight-points": ["shaves", "unique_users"],
        # Cross-product tables
        "razor-blade-combinations": ["shaves", "unique_users"],
        "highest-use-count-per-blade": ["uses"],
        # User tables
        "users": ["shaves", "missed_days"],
        "top-shavers": ["shaves", "missed_days"],
        # Format and fiber tables
        "razor-formats": ["shaves", "unique_users"],
        "brush-fibers": ["shaves", "unique_users"],
        "brush-knot-sizes": ["shaves", "unique_users"],
        "razor-format-users": ["format", "shaves"],
        "brush-fiber-users": ["fiber", "shaves"],
        # Software tables
        "soap-brands": ["shaves", "unique_users"],  # Alias for soap-makers
        "top-sampled-soaps": ["shaves", "unique_users"],
        # User diversity tables
        "user-soap-brand-scent-diversity": ["unique_combinations", "shaves"],
        # Testing
        "test_table": ["shaves", "unique_users"],  # For testing purposes
    }

    # Universal parameters that are always valid
    UNIVERSAL_PARAMETERS = ["rows", "ranks", "deltas", "columns"]

    def get_available_columns(self, table_name: str) -> List[str]:
        """Get available columns for a table.

        Args:
            table_name: Name of the table

        Returns:
            List of available column names
        """
        if table_name not in self.TABLE_SORTING_COLUMNS:
            return []

        return self.TABLE_SORTING_COLUMNS[table_name] + self.UNIVERSAL_PARAMETERS

    def is_sorting_column(self, table_name: str, column: str) -> bool:
        """Check if a column is a sorting column for a table.

        Args:
            table_name: Name of the table
            column: Name of the column to check

        Returns:
            True if the column is a sorting column, False otherwise
        """
        if table_name not in self.TABLE_SORTING_COLUMNS:
            return False

        return column in self.TABLE_SORTING_COLUMNS[table_name]

    def validate_parameters(
        self, table_name: str, parameters: Dict[str, Any] | None
    ) -> ValidationResult:
        """Validate parameters for a specific table.

        Args:
            table_name: Name of the table
            parameters: Dictionary of parameters to validate, or None

        Returns:
            ValidationResult with validation status and any errors
        """
        if not parameters:
            return ValidationResult(is_valid=True, errors=[])

        errors = []

        # Check if table exists
        if table_name not in self.TABLE_SORTING_COLUMNS:
            errors.append(f"Unknown table: {table_name}")
            return ValidationResult(is_valid=False, errors=errors)

        # Validate each parameter
        for param_name, param_value in parameters.items():
            if not self._is_valid_parameter(table_name, param_name):
                errors.append(
                    f"'{param_name}' is not a sorting column for table '{table_name}'. "
                    f"Available columns: {', '.join(self.get_available_columns(table_name))}"
                )

        return ValidationResult(is_valid=len(errors) == 0, errors=errors)

    def _is_valid_parameter(self, table_name: str, param_name: str) -> bool:
        """Check if a parameter is valid for a table.

        Args:
            table_name: Name of the table
            param_name: Name of the parameter to check

        Returns:
            True if the parameter is valid, False otherwise
        """
        # Universal parameters are always valid
        if param_name in self.UNIVERSAL_PARAMETERS:
            return True

        # Check if it's a valid sorting column for the table
        return self.is_sorting_column(table_name, param_name)

    def get_table_metadata(self, table_name: str) -> Dict[str, Any]:
        """Get metadata about a table.

        Args:
            table_name: Name of the table

        Returns:
            Dictionary with table metadata (ranking_fields, available_columns)
        """
        if table_name not in self.TABLE_SORTING_COLUMNS:
            return {}

        return {
            "ranking_fields": self.TABLE_SORTING_COLUMNS[table_name],
            "available_columns": self.get_available_columns(table_name),
        }
