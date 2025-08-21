#!/usr/bin/env python3
"""Enhanced table generator for report templates with parameter support."""

from typing import Any, Dict, List

from .data_field_limiter import DataFieldLimiter
from .parameter_validator import ParameterValidator
from .table_parameter_parser import TableParameterParser
from .table_size_limiter import TableSizeLimiter


class EnhancedTableGenerator:
    """Enhanced table generator with parameter support."""

    def __init__(self):
        """Initialize the enhanced table generator."""
        self.parameter_parser = TableParameterParser()
        self.parameter_validator = ParameterValidator()
        self.data_field_limiter = DataFieldLimiter()
        self.table_size_limiter = TableSizeLimiter()

    def generate_table(
        self, table_name: str, data: List[Dict[str, Any]], parameters: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Generate a table with enhanced parameter support.

        Args:
            table_name: Name of the table
            data: Table data to process
            parameters: Dictionary of parameters to apply

        Returns:
            Processed table data

        Raises:
            ValueError: If data is None or parameters are invalid
        """
        if data is None:
            raise ValueError("Data cannot be None")

        if not data:
            return data

        # Trace ranks at input
        from .utils.rank_tracer import trace_ranks
        trace_ranks("EnhancedTableGenerator.input", data)

        # Validate parameters
        validation_result = self.parameter_validator.validate_parameters(table_name, parameters)
        if not validation_result.is_valid:
            raise ValueError(validation_result.errors[0])

        # Apply data field limits first
        data = self.data_field_limiter.apply_limits(data, parameters)

        # Sort data by rank before applying size limits
        if data and "rank" in data[0]:
            data = sorted(data, key=lambda x: x.get("rank", 0))

        # Apply size limits
        data = self.table_size_limiter.apply_size_limits(data, parameters)

        # Trace ranks at output
        trace_ranks("EnhancedTableGenerator.output", data)

        return data

    def generate_table_from_placeholder(
        self, placeholder: str, data: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Generate a table from a placeholder string.

        Args:
            placeholder: Table placeholder string (e.g., "{{tables.razors|shaves:5}}")
            data: Table data to process

        Returns:
            Processed table data

        Raises:
            ValueError: If placeholder format is invalid
        """
        try:
            table_name, parameters = self.parameter_parser.parse_placeholder(placeholder)
        except ValueError as e:
            raise ValueError(f"Invalid placeholder format: {e}")

        return self.generate_table(table_name, data, parameters)
