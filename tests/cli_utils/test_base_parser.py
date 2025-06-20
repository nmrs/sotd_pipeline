"""
Unit tests for BaseCLIParser.

Tests the standardized CLI argument parsing functionality used across
all SOTD pipeline phases.
"""

import pytest
from pathlib import Path
import argparse

from sotd.cli_utils.base_parser import BaseCLIParser, validate_month, validate_year, validate_range


class TestValidationFunctions:
    """Test validation functions for CLI arguments."""

    def test_validate_month_valid(self):
        """Test valid month format."""
        assert validate_month("2025-01") == "2025-01"
        assert validate_month("2024-12") == "2024-12"
        assert validate_month("2020-06") == "2020-06"

    def test_validate_month_invalid(self):
        """Test invalid month formats."""
        with pytest.raises(argparse.ArgumentTypeError, match="Invalid month format"):
            validate_month("2025-1")  # Missing leading zero

        with pytest.raises(argparse.ArgumentTypeError, match="Invalid month value"):
            validate_month("2025-13")  # Invalid month

        with pytest.raises(argparse.ArgumentTypeError, match="Invalid month format"):
            validate_month("25-01")  # Invalid year

        with pytest.raises(argparse.ArgumentTypeError, match="Invalid month format"):
            validate_month("2025/01")  # Wrong separator

        with pytest.raises(argparse.ArgumentTypeError, match="Invalid month format"):
            validate_month("invalid")  # Completely invalid

    def test_validate_year_valid(self):
        """Test valid year format."""
        assert validate_year("2025") == "2025"
        assert validate_year("2024") == "2024"
        assert validate_year("2020") == "2020"

    def test_validate_year_invalid(self):
        """Test invalid year formats."""
        with pytest.raises(argparse.ArgumentTypeError, match="Invalid year format"):
            validate_year("25")  # Too short

        with pytest.raises(argparse.ArgumentTypeError, match="Invalid year format"):
            validate_year("20250")  # Too long

        with pytest.raises(argparse.ArgumentTypeError, match="Invalid year format"):
            validate_year("invalid")  # Non-numeric

    def test_validate_range_valid(self):
        """Test valid range format."""
        assert validate_range("2025-01:2025-12") == "2025-01:2025-12"
        assert validate_range("2024-06:2024-08") == "2024-06:2024-08"
        assert validate_range("2020-01:2020-01") == "2020-01:2020-01"

    def test_validate_range_invalid(self):
        """Test invalid range formats."""
        with pytest.raises(argparse.ArgumentTypeError, match="Invalid range format"):
            validate_range("2025-01-2025-12")  # Missing colon

        with pytest.raises(argparse.ArgumentTypeError, match="Invalid range format"):
            validate_range("2025-1:2025-12")  # Missing leading zero

        with pytest.raises(argparse.ArgumentTypeError, match="Invalid month value in range"):
            validate_range("2025-01:2025-13")  # Invalid end month

        with pytest.raises(argparse.ArgumentTypeError, match="Invalid range format"):
            validate_range("invalid")  # Completely invalid


class TestBaseCLIParser:
    """Test BaseCLIParser class functionality."""

    def test_init(self):
        """Test parser initialization."""
        parser = BaseCLIParser("Test description")
        assert parser.parser.description == "Test description"

    def test_common_arguments_present(self):
        """Test that all common arguments are present."""
        parser = BaseCLIParser("Test")
        help_text = parser.format_help()

        # Check that all common arguments are in help text
        assert "--month" in help_text
        assert "--year" in help_text
        assert "--range" in help_text
        assert "--start" in help_text
        assert "--end" in help_text
        assert "--out-dir" in help_text
        assert "--debug" in help_text
        assert "--force" in help_text

    def test_mutually_exclusive_date_args(self):
        """Test that date arguments are mutually exclusive."""
        parser = BaseCLIParser("Test")

        # Should fail when multiple date args are provided
        with pytest.raises(SystemExit):
            parser.parse_args(["--month", "2025-01", "--year", "2025"])

        with pytest.raises(SystemExit):
            parser.parse_args(["--month", "2025-01", "--range", "2025-01:2025-12"])

        with pytest.raises(SystemExit):
            parser.parse_args(["--year", "2025", "--range", "2025-01:2025-12"])

    def test_required_date_arg(self):
        """Test that at least one date argument is required."""
        parser = BaseCLIParser("Test")

        # Should fail when no date args are provided
        with pytest.raises(SystemExit):
            parser.parse_args([])

    def test_valid_month_arg(self):
        """Test parsing valid month argument."""
        parser = BaseCLIParser("Test")
        args = parser.parse_args(["--month", "2025-01"])
        assert args.month == "2025-01"
        assert args.year is None
        assert args.range is None

    def test_valid_year_arg(self):
        """Test parsing valid year argument."""
        parser = BaseCLIParser("Test")
        args = parser.parse_args(["--year", "2025"])
        assert args.year == "2025"
        assert args.month is None
        assert args.range is None

    def test_valid_range_arg(self):
        """Test parsing valid range argument."""
        parser = BaseCLIParser("Test")
        args = parser.parse_args(["--range", "2025-01:2025-12"])
        assert args.range == "2025-01:2025-12"
        assert args.month is None
        assert args.year is None

    def test_start_end_args(self):
        """Test parsing start/end arguments."""
        parser = BaseCLIParser("Test")
        args = parser.parse_args(["--month", "2025-01", "--start", "2025-01", "--end", "2025-12"])
        assert args.start == "2025-01"
        assert args.end == "2025-12"

    def test_default_values(self):
        """Test default values for optional arguments."""
        parser = BaseCLIParser("Test")
        args = parser.parse_args(["--month", "2025-01"])
        assert args.out_dir == Path("data")
        assert args.debug is False
        assert args.force is False

    def test_custom_values(self):
        """Test custom values for optional arguments."""
        parser = BaseCLIParser("Test")
        args = parser.parse_args(
            ["--month", "2025-01", "--out-dir", "/custom/path", "--debug", "--force"]
        )
        assert args.out_dir == Path("/custom/path")
        assert args.debug is True
        assert args.force is True

    def test_add_custom_argument(self):
        """Test adding custom arguments."""
        parser = BaseCLIParser("Test")
        parser.add_argument("--custom", help="Custom argument")

        args = parser.parse_args(["--month", "2025-01", "--custom", "value"])
        assert args.custom == "value"

    def test_add_mutually_exclusive_group(self):
        """Test adding mutually exclusive groups."""
        parser = BaseCLIParser("Test")
        group = parser.add_mutually_exclusive_group()
        group.add_argument("--option1", action="store_true")
        group.add_argument("--option2", action="store_true")

        # Should work with one option
        args = parser.parse_args(["--month", "2025-01", "--option1"])
        assert args.option1 is True
        assert args.option2 is False

        # Should fail with both options
        with pytest.raises(SystemExit):
            parser.parse_args(["--month", "2025-01", "--option1", "--option2"])

    def test_parse_args_with_argv(self):
        """Test parsing with custom argv."""
        parser = BaseCLIParser("Test")
        args = parser.parse_args(["--month", "2025-01"])
        assert args.month == "2025-01"

    def test_help_methods(self):
        """Test help-related methods."""
        parser = BaseCLIParser("Test")

        # format_help should return a string
        help_text = parser.format_help()
        assert isinstance(help_text, str)
        assert "Test" in help_text

        # print_help should not raise an exception
        parser.print_help()


class TestBaseCLIParserIntegration:
    """Integration tests for BaseCLIParser with real scenarios."""

    def test_typical_pipeline_usage(self):
        """Test typical pipeline usage patterns."""
        parser = BaseCLIParser("Aggregate phase")

        # Single month processing
        args = parser.parse_args(["--month", "2025-01", "--force"])
        assert args.month == "2025-01"
        assert args.force is True

        # Year processing
        args = parser.parse_args(["--year", "2025", "--debug"])
        assert args.year == "2025"
        assert args.debug is True

        # Range processing
        args = parser.parse_args(["--range", "2025-01:2025-06", "--out-dir", "/tmp/data"])
        assert args.range == "2025-01:2025-06"
        assert args.out_dir == Path("/tmp/data")

    def test_error_messages(self):
        """Test that error messages are helpful."""
        parser = BaseCLIParser("Test")

        # Test missing required argument
        with pytest.raises(SystemExit):
            parser.parse_args([])

        # Test invalid month format
        with pytest.raises(SystemExit):
            parser.parse_args(["--month", "invalid"])

        # Test invalid year format
        with pytest.raises(SystemExit):
            parser.parse_args(["--year", "invalid"])

        # Test invalid range format
        with pytest.raises(SystemExit):
            parser.parse_args(["--range", "invalid"])
