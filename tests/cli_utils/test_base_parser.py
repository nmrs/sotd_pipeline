"""
Unit tests for BaseCLIParser.

Tests the standardized CLI argument parsing functionality used across
all SOTD Pipeline phases.
"""

import argparse
import pytest
from pathlib import Path

from sotd.cli_utils.base_parser import BaseCLIParser


class TestBaseCLIParser:
    """Test cases for BaseCLIParser functionality."""

    def test_basic_initialization(self):
        """Test basic parser initialization with all default arguments."""
        parser = BaseCLIParser(description="Test parser")

        # Should have all common arguments
        assert parser.description == "Test parser"

        # Test that help works
        help_text = parser.format_help()
        assert "Test parser" in help_text
        assert "--month" in help_text
        assert "--year" in help_text
        assert "--range" in help_text
        assert "--start" in help_text
        assert "--end" in help_text
        assert "--out-dir" in help_text
        assert "--debug" in help_text
        assert "--force" in help_text

    def test_custom_initialization(self):
        """Test parser initialization with custom argument selection."""
        parser = BaseCLIParser(
            description="Custom parser",
            add_date_args=False,
            add_output_args=True,
            add_debug_args=False,
            add_force_args=True,
        )

        help_text = parser.format_help()
        assert "Custom parser" in help_text
        assert "--month" not in help_text
        assert "--year" not in help_text
        assert "--range" not in help_text
        assert "--start" not in help_text
        assert "--end" not in help_text
        assert "--out-dir" in help_text
        assert "--debug" not in help_text
        assert "--force" in help_text

    def test_month_validation_valid(self):
        """Test valid month format validation."""
        parser = BaseCLIParser(description="Test")

        # Valid formats
        assert parser._validate_month("2023-01") == "2023-01"
        assert parser._validate_month("2023-12") == "2023-12"
        assert parser._validate_month("1999-06") == "1999-06"

    def test_month_validation_invalid(self):
        """Test invalid month format validation."""
        parser = BaseCLIParser(description="Test")

        # Invalid formats
        invalid_formats = [
            ("2023-1", "Invalid month format"),  # Missing leading zero
            ("2023-13", "Invalid month value"),  # Invalid month
            ("2023-00", "Invalid month value"),  # Invalid month
            ("2023", "Invalid month format"),  # Missing month
            ("2023-1-1", "Invalid month format"),  # Too many parts
            ("abc-def", "Invalid month format"),  # Non-numeric
            ("2023-1a", "Invalid month format"),  # Mixed format
        ]

        for invalid_format, expected_error in invalid_formats:
            with pytest.raises(argparse.ArgumentTypeError) as exc_info:
                parser._validate_month(invalid_format)
            assert expected_error in str(exc_info.value)

    def test_year_validation_valid(self):
        """Test valid year format validation."""
        parser = BaseCLIParser(description="Test")

        # Valid formats
        assert parser._validate_year("2023") == "2023"
        assert parser._validate_year("1999") == "1999"
        assert parser._validate_year("2100") == "2100"

    def test_year_validation_invalid(self):
        """Test invalid year format validation."""
        parser = BaseCLIParser(description="Test")

        # Invalid formats
        invalid_formats = [
            "202",  # Too short
            "20234",  # Too long
            "abc",  # Non-numeric
            "20a3",  # Mixed format
            "2023-01",  # Contains separator
        ]

        for invalid_format in invalid_formats:
            with pytest.raises(argparse.ArgumentTypeError) as exc_info:
                parser._validate_year(invalid_format)
            assert "Invalid year format" in str(exc_info.value)

    def test_range_validation_valid(self):
        """Test valid range format validation."""
        parser = BaseCLIParser(description="Test")

        # Valid formats
        assert parser._validate_range("2023-01:2023-12") == "2023-01:2023-12"
        assert parser._validate_range("2022-06:2023-05") == "2022-06:2023-05"
        assert parser._validate_range("1999-01:2000-12") == "1999-01:2000-12"

    def test_range_validation_invalid(self):
        """Test invalid range format validation."""
        parser = BaseCLIParser(description="Test")

        # Invalid formats
        invalid_formats = [
            ("2023-01", "Invalid range format"),  # Missing separator and end
            ("2023-01:2023", "Invalid range format"),  # Invalid end format
            ("2023:2023-12", "Invalid range format"),  # Invalid start format
            ("2023-01-2023-12", "Invalid range format"),  # Wrong separator
            ("abc-def:ghi-jkl", "Invalid range format"),  # Non-numeric
            ("2023-01:2023-13", "Invalid month value in range"),  # Invalid end month
        ]

        for invalid_format, expected_error in invalid_formats:
            with pytest.raises(argparse.ArgumentTypeError) as exc_info:
                parser._validate_range(invalid_format)
            assert expected_error in str(exc_info.value)

    def test_parse_valid_month(self):
        """Test parsing valid month argument."""
        parser = BaseCLIParser(description="Test")
        args = parser.parse_args(["--month", "2023-06"])

        assert args.month == "2023-06"
        assert args.year is None
        assert args.range is None
        assert args.start is None
        assert args.end is None
        assert args.out_dir == Path("data")
        assert not args.debug
        assert not args.force

    def test_parse_valid_year(self):
        """Test parsing valid year argument."""
        parser = BaseCLIParser(description="Test")
        args = parser.parse_args(["--year", "2023"])

        assert args.month is None
        assert args.year == "2023"
        assert args.range is None
        assert args.start is None
        assert args.end is None

    def test_parse_valid_range(self):
        """Test parsing valid range argument."""
        parser = BaseCLIParser(description="Test")
        args = parser.parse_args(["--range", "2023-01:2023-12"])

        assert args.month is None
        assert args.year is None
        assert args.range == "2023-01:2023-12"
        assert args.start is None
        assert args.end is None

    def test_parse_start_end_range(self):
        """Test parsing start/end range arguments."""
        parser = BaseCLIParser(description="Test")
        args = parser.parse_args(["--start", "2023-01", "--end", "2023-12"])

        assert args.month is None
        assert args.year is None
        assert args.range is None
        assert args.start == "2023-01"
        assert args.end == "2023-12"

    def test_parse_with_options(self):
        """Test parsing with debug and force options."""
        parser = BaseCLIParser(description="Test")
        args = parser.parse_args(
            ["--month", "2023-06", "--out-dir", "/custom/path", "--debug", "--force"]
        )

        assert args.month == "2023-06"
        assert args.out_dir == Path("/custom/path")
        assert args.debug
        assert args.force

    def test_mutually_exclusive_date_args(self):
        """Test that date arguments are mutually exclusive."""
        parser = BaseCLIParser(description="Test")

        # Should fail with multiple date arguments
        with pytest.raises(SystemExit):
            parser.parse_args(["--month", "2023-06", "--year", "2023"])

        with pytest.raises(SystemExit):
            parser.parse_args(["--month", "2023-06", "--range", "2023-01:2023-12"])

        with pytest.raises(SystemExit):
            parser.parse_args(["--year", "2023", "--range", "2023-01:2023-12"])

    def test_required_date_argument(self):
        """Test that at least one date argument is required."""
        parser = BaseCLIParser(description="Test", require_date_args=True)

        # Should fail without any date argument
        with pytest.raises(SystemExit):
            parser.parse_args(["--debug", "--force"])

    def test_parallel_processing_arguments(self):
        """Test adding parallel processing arguments."""
        parser = BaseCLIParser(description="Test")
        parser.add_parallel_processing_arguments(default_max_workers=8)

        help_text = parser.format_help()
        assert "--parallel" in help_text
        assert "--sequential" in help_text
        assert "--max-workers" in help_text

        # Test parsing
        args = parser.parse_args(["--month", "2023-06", "--parallel", "--max-workers", "6"])
        assert args.parallel
        assert not args.sequential
        assert args.max_workers == 6

    def test_parallel_processing_mutually_exclusive(self):
        """Test that parallel and sequential are mutually exclusive."""
        parser = BaseCLIParser(description="Test")
        parser.add_parallel_processing_arguments()

        with pytest.raises(SystemExit):
            parser.parse_args(["--month", "2023-06", "--parallel", "--sequential"])

    def test_parallel_processing_group_manual(self):
        """Test manually adding parallel processing group."""
        parser = BaseCLIParser(description="Test")
        parallel_group = parser.add_parallel_processing_group()

        parallel_group.add_argument("--custom-parallel", action="store_true")
        parallel_group.add_argument("--custom-sequential", action="store_true")

        # Test that the group works
        args = parser.parse_args(["--month", "2023-06", "--custom-parallel"])
        assert args.custom_parallel
        assert not args.custom_sequential

    def test_custom_arguments(self):
        """Test adding custom arguments to the parser."""
        parser = BaseCLIParser(description="Test")
        parser.add_argument("--custom-arg", type=str, help="Custom argument")

        args = parser.parse_args(["--month", "2023-06", "--custom-arg", "test-value"])
        assert args.custom_arg == "test-value"

    def test_mutually_exclusive_groups(self):
        """Test adding custom mutually exclusive groups."""
        parser = BaseCLIParser(description="Test")
        custom_group = parser.add_mutually_exclusive_group()
        custom_group.add_argument("--option-a", action="store_true")
        custom_group.add_argument("--option-b", action="store_true")

        # Test that they work
        args = parser.parse_args(["--month", "2023-06", "--option-a"])
        assert args.option_a
        assert not args.option_b

        # Test that they're mutually exclusive
        with pytest.raises(SystemExit):
            parser.parse_args(["--month", "2023-06", "--option-a", "--option-b"])

    def test_help_integration(self):
        """Test that help text includes all arguments."""
        parser = BaseCLIParser(description="Test parser")
        parser.add_argument("--custom", help="Custom argument")

        help_text = parser.format_help()

        # Check that all arguments are present
        assert "Test parser" in help_text
        assert "--month" in help_text
        assert "--year" in help_text
        assert "--range" in help_text
        assert "--start" in help_text
        assert "--end" in help_text
        assert "--out-dir" in help_text
        assert "--debug" in help_text
        assert "--force" in help_text
        assert "--custom" in help_text
        assert "Custom argument" in help_text


class TestBaseCLIParserIntegration:
    """Integration tests for BaseCLIParser with real usage patterns."""

    def test_typical_pipeline_usage(self):
        """Test typical pipeline usage patterns."""
        parser = BaseCLIParser(description="Test pipeline")
        parser.add_parallel_processing_arguments()

        # Test typical match phase usage
        args = parser.parse_args(
            ["--month", "2023-06", "--parallel", "--max-workers", "4", "--debug"]
        )

        assert args.month == "2023-06"
        assert args.parallel
        assert args.max_workers == 4
        assert args.debug
        assert not args.force

    def test_error_messages(self):
        """Test that error messages are helpful."""
        parser = BaseCLIParser(description="Test")

        # Test invalid month format
        with pytest.raises(SystemExit):
            parser.parse_args(["--month", "invalid"])

        # Test invalid year format
        with pytest.raises(SystemExit):
            parser.parse_args(["--year", "invalid"])

        # Test invalid range format
        with pytest.raises(SystemExit):
            parser.parse_args(["--range", "invalid"])
