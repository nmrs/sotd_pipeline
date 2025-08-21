#!/usr/bin/env python3
"""Table parameter parser for enhanced report templates."""

import re
from typing import Any, Dict, Tuple


class TableParameterParser:
    """Parser for enhanced table placeholders with parameters."""

    def parse_placeholder(self, placeholder: str) -> Tuple[str, Dict[str, Any]]:
        """Parse a table placeholder into table name and parameters.

        Args:
            placeholder: Table placeholder string (e.g., "{{tables.razors|shaves:5}}")

        Returns:
            Tuple of (table_name, parameters_dict)

        Raises:
            ValueError: If placeholder format is invalid
        """
        # Extract content between braces
        match = re.match(r"\{\{tables\.([^|}]+)(?:\|(.+))?\}\}", placeholder)
        if not match:
            raise ValueError("Invalid placeholder format")

        table_name = match.group(1)
        param_string = match.group(2) or ""

        parameters = self.parse_parameters(param_string)
        return table_name, parameters

    def parse_parameters(self, param_string: str) -> Dict[str, Any]:
        """Parse parameter string into dictionary.

        Args:
            param_string: Parameter string (e.g., "shaves:5|rows:20")

        Returns:
            Dictionary of parameter names and values

        Raises:
            ValueError: If parameter format is invalid
        """
        if not param_string.strip():
            return {}

        parameters = {}
        param_parts = [p.strip() for p in param_string.split("|")]

        for part in param_parts:
            if not part:
                continue

            if ":" not in part:
                raise ValueError("Invalid parameter format")

            name, value = part.split(":", 1)
            if not name or not value:
                raise ValueError("Invalid parameter format")

            # Try to convert to int if possible, otherwise keep as string
            try:
                parameters[name] = int(value)
            except ValueError:
                parameters[name] = value

        return parameters

    def validate_syntax(self, param_string: str) -> bool:
        """Validate parameter string syntax.

        Args:
            param_string: Parameter string to validate

        Returns:
            True if syntax is valid, False otherwise
        """
        try:
            self.parse_parameters(param_string)
            return True
        except ValueError:
            return False
