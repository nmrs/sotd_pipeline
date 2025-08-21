#!/usr/bin/env python3
"""Parameter validator for enhanced report templates."""

from dataclasses import dataclass
from typing import Any, Dict, List


@dataclass
class ValidationResult:
    """Result of parameter validation."""

    is_valid: bool
    errors: List[str]


class ParameterValidator:
    """Validator for table parameters."""

    # Mapping of table names to their available sorting columns
    TABLE_SORTING_COLUMNS = {
        "razors": ["shaves", "unique_users"],
        "blades": ["shaves", "unique_users"],
        "brushes": ["shaves", "unique_users"],
        "soaps": ["shaves", "unique_users"],
        "razor-manufacturers": ["shaves", "unique_users"],
        "blade-manufacturers": ["shaves", "unique_users"],
        "brush-handle-makers": ["shaves", "unique_users"],
        "brush-knot-makers": ["shaves", "unique_users"],
        "soap-makers": ["shaves", "unique_users"],
        "top-shavers": ["shaves", "missed_days"],
        "brush-diversity": ["unique_brushes", "total_shaves"],
        "blade-diversity": ["unique_blades", "total_shaves"],
        "soap-diversity": ["unique_soaps", "total_shaves"],
        "razor-diversity": ["unique_razors", "total_shaves"],
        "highest-use-count-per-blade": ["uses"],
        "razor-format-users": ["format", "shaves"],
        "brush-fiber-users": ["fiber", "shaves"],
        "test_table": ["shaves", "unique_users"],  # For testing purposes
    }

    # Universal parameters that are always valid
    UNIVERSAL_PARAMETERS = ["rows", "ranks"]

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

    def _is_valid_parameter(self, table_name: str, param_name: str) -> bool:
        """Check if a parameter is valid for a table.

        Args:
            table_name: Name of the table
            param_name: Name of the parameter

        Returns:
            True if the parameter is valid, False otherwise
        """
        # Universal parameters are always valid
        if param_name in self.UNIVERSAL_PARAMETERS:
            return True

        # Check if it's a sorting column for this table
        return self.is_sorting_column(table_name, param_name)
