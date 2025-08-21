#!/usr/bin/env python3
"""Tests for TableParameterParser."""

import pytest

from sotd.report.table_parameter_parser import TableParameterParser


class TestTableParameterParser:
    """Test cases for TableParameterParser."""

    def test_parse_placeholder_basic(self):
        """Test parsing basic table placeholder without parameters."""
        parser = TableParameterParser()
        table_name, parameters = parser.parse_placeholder("{{tables.razors}}")

        assert table_name == "razors"
        assert parameters == {}

    def test_parse_placeholder_with_single_parameter(self):
        """Test parsing table placeholder with single parameter."""
        parser = TableParameterParser()
        table_name, parameters = parser.parse_placeholder("{{tables.razors|shaves:5}}")

        assert table_name == "razors"
        assert parameters == {"shaves": 5}

    def test_parse_placeholder_with_multiple_parameters(self):
        """Test parsing table placeholder with multiple parameters."""
        parser = TableParameterParser()
        table_name, parameters = parser.parse_placeholder("{{tables.razors|shaves:5|rows:20}}")

        assert table_name == "razors"
        assert parameters == {"shaves": 5, "rows": 20}

    def test_parse_placeholder_with_mixed_parameter_types(self):
        """Test parsing table placeholder with mixed parameter types."""
        parser = TableParameterParser()
        table_name, parameters = parser.parse_placeholder(
            "{{tables.razors|shaves:5|rows:20|unique_users:3}}"
        )

        assert table_name == "razors"
        assert parameters == {"shaves": 5, "rows": 20, "unique_users": 3}

    def test_parse_placeholder_with_complex_table_name(self):
        """Test parsing table placeholder with complex table name."""
        parser = TableParameterParser()
        table_name, parameters = parser.parse_placeholder(
            "{{tables.razor-manufacturers|shaves:10}}"
        )

        assert table_name == "razor-manufacturers"
        assert parameters == {"shaves": 10}

    def test_parse_parameters_empty_string(self):
        """Test parsing empty parameter string."""
        parser = TableParameterParser()
        parameters = parser.parse_parameters("")

        assert parameters == {}

    def test_parse_parameters_single_parameter(self):
        """Test parsing single parameter."""
        parser = TableParameterParser()
        parameters = parser.parse_parameters("shaves:5")

        assert parameters == {"shaves": 5}

    def test_parse_parameters_multiple_parameters(self):
        """Test parsing multiple parameters."""
        parser = TableParameterParser()
        parameters = parser.parse_parameters("shaves:5|rows:20|unique_users:3")

        assert parameters == {"shaves": 5, "rows": 20, "unique_users": 3}

    def test_parse_parameters_with_spaces(self):
        """Test parsing parameters with spaces around separators."""
        parser = TableParameterParser()
        parameters = parser.parse_parameters("shaves:5 | rows:20 | unique_users:3")

        assert parameters == {"shaves": 5, "rows": 20, "unique_users": 3}

    def test_parse_parameters_invalid_syntax(self):
        """Test parsing parameters with invalid syntax."""
        parser = TableParameterParser()

        # Missing value
        with pytest.raises(ValueError, match="Invalid parameter format"):
            parser.parse_parameters("shaves:")

        # Missing colon
        with pytest.raises(ValueError, match="Invalid parameter format"):
            parser.parse_parameters("shaves5")

        # Empty parameter name
        with pytest.raises(ValueError, match="Invalid parameter format"):
            parser.parse_parameters(":5")

    def test_validate_syntax_valid(self):
        """Test syntax validation with valid parameters."""
        parser = TableParameterParser()

        assert parser.validate_syntax("shaves:5") is True
        assert parser.validate_syntax("shaves:5|rows:20") is True
        assert parser.validate_syntax("") is True

    def test_validate_syntax_invalid(self):
        """Test syntax validation with invalid parameters."""
        parser = TableParameterParser()

        assert parser.validate_syntax("shaves:") is False
        assert parser.validate_syntax("shaves5") is False
        assert parser.validate_syntax(":5") is False
        assert parser.validate_syntax("shaves:5|invalid") is False

    def test_parse_placeholder_edge_cases(self):
        """Test parsing edge cases."""
        parser = TableParameterParser()

        # Very long parameter names and values
        long_param = "very_long_parameter_name:very_long_parameter_value"
        table_name, parameters = parser.parse_placeholder(f"{{{{tables.razors|{long_param}}}}}")

        assert table_name == "razors"
        assert parameters == {"very_long_parameter_name": "very_long_parameter_value"}

        # Special characters in values
        table_name, parameters = parser.parse_placeholder("{{tables.razors|format:DE|width:15/16}}")

        assert table_name == "razors"
        assert parameters == {"format": "DE", "width": "15/16"}

    def test_parse_placeholder_malformed(self):
        """Test parsing malformed placeholders."""
        parser = TableParameterParser()

        # Missing closing braces
        with pytest.raises(ValueError, match="Invalid placeholder format"):
            parser.parse_placeholder("{{tables.razors")

        # Missing opening braces
        with pytest.raises(ValueError, match="Invalid placeholder format"):
            parser.parse_placeholder("tables.razors}}")

        # Missing table prefix
        with pytest.raises(ValueError, match="Invalid placeholder format"):
            parser.parse_placeholder("{{invalid.razors}}")

        # Empty table name
        with pytest.raises(ValueError, match="Invalid placeholder format"):
            parser.parse_placeholder("{{tables.}}")
