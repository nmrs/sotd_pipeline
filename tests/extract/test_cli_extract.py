"""
Tests for the extract phase CLI module.
"""

import pytest
from pathlib import Path

from sotd.extract.cli import get_parser


class TestExtractCLI:
    """Test cases for the extract phase CLI."""

    def test_get_parser_returns_base_parser(self):
        """Test that get_parser returns a BaseCLIParser instance."""
        parser = get_parser()
        assert parser is not None
        assert hasattr(parser, "parse_args")
        assert hasattr(parser, "add_argument")

    def test_common_arguments_present(self):
        """Test that common arguments from BaseCLIParser are present."""
        parser = get_parser()
        args = parser.parse_args(["--month", "2025-01"])

        # Test common arguments
        assert args.month == "2025-01"
        assert args.out_dir == Path("data")
        assert not args.debug
        assert not args.force

    def test_date_argument_combinations(self):
        """Test various date argument combinations."""
        parser = get_parser()

        # Test month argument
        args = parser.parse_args(["--month", "2025-01"])
        assert args.month == "2025-01"
        assert args.year is None
        assert args.range is None
        assert args.start is None
        assert args.end is None

        # Test year argument
        args = parser.parse_args(["--year", "2025"])
        assert args.month is None
        assert args.year == "2025"
        assert args.range is None
        assert args.start is None
        assert args.end is None

        # Test range argument
        args = parser.parse_args(["--range", "2025-01:2025-12"])
        assert args.month is None
        assert args.year is None
        assert args.range == "2025-01:2025-12"
        assert args.start is None
        assert args.end is None

        # Test start/end arguments
        args = parser.parse_args(["--start", "2025-01", "--end", "2025-12"])
        assert args.month is None
        assert args.year is None
        assert args.range is None
        assert args.start == "2025-01"
        assert args.end == "2025-12"

    def test_options_arguments(self):
        """Test debug, force, and out-dir arguments."""
        parser = get_parser()
        args = parser.parse_args(
            [
                "--month",
                "2025-01",
                "--debug",
                "--force",
                "--out-dir",
                "/custom/path",
            ]
        )

        assert args.debug
        assert args.force
        assert args.out_dir == Path("/custom/path")

    def test_mutually_exclusive_date_arguments(self):
        """Test that date arguments are mutually exclusive."""
        parser = get_parser()

        # Should not raise an error when only one is specified
        args = parser.parse_args(["--month", "2025-01"])
        assert args.month == "2025-01"

        args = parser.parse_args(["--year", "2025"])
        assert args.year == "2025"

        args = parser.parse_args(["--range", "2025-01:2025-12"])
        assert args.range == "2025-01:2025-12"

        # Should raise an error when multiple are specified
        with pytest.raises(SystemExit):
            parser.parse_args(["--month", "2025-01", "--year", "2025"])

        with pytest.raises(SystemExit):
            parser.parse_args(["--month", "2025-01", "--range", "2025-01:2025-12"])

        with pytest.raises(SystemExit):
            parser.parse_args(["--year", "2025", "--range", "2025-01:2025-12"])

    def test_start_end_pair_validation(self):
        """Test that start and end must be provided together."""
        parser = get_parser()

        # Both provided - should work
        args = parser.parse_args(["--start", "2025-01", "--end", "2025-12"])
        assert args.start == "2025-01"
        assert args.end == "2025-12"

        # Neither provided - should work
        args = parser.parse_args(["--month", "2025-01"])
        assert args.start is None
        assert args.end is None

        # Only start provided - should raise error
        with pytest.raises(SystemExit):
            parser.parse_args(["--start", "2025-01"])

        # Only end provided - should raise error
        with pytest.raises(SystemExit):
            parser.parse_args(["--end", "2025-12"])

    def test_default_values(self):
        """Test that default values are set correctly."""
        parser = get_parser()
        args = parser.parse_args(["--month", "2025-01"])

        assert args.out_dir == Path("data")
        assert not args.debug
        assert not args.force

    def test_help_text_includes_extract_description(self):
        """Test that help text includes extract-specific description."""
        parser = get_parser()
        help_text = parser.format_help()

        assert "Extract razors, blades, soaps, and brushes" in help_text
        assert "--month" in help_text
        assert "--year" in help_text
        assert "--range" in help_text
        assert "--start" in help_text
        assert "--end" in help_text
        assert "--out-dir" in help_text
        assert "--debug" in help_text
        assert "--force" in help_text

    def test_argument_validation(self):
        """Test argument validation for date formats."""
        parser = get_parser()

        # Valid formats
        args = parser.parse_args(["--month", "2025-01"])
        assert args.month == "2025-01"

        args = parser.parse_args(["--year", "2025"])
        assert args.year == "2025"

        args = parser.parse_args(["--range", "2025-01:2025-12"])
        assert args.range == "2025-01:2025-12"

        # Invalid formats should raise ArgumentTypeError
        with pytest.raises(SystemExit):
            parser.parse_args(["--month", "2025-1"])  # Missing leading zero

        with pytest.raises(SystemExit):
            parser.parse_args(["--month", "2025-13"])  # Invalid month

        with pytest.raises(SystemExit):
            parser.parse_args(["--year", "202"])  # Too short

        with pytest.raises(SystemExit):
            parser.parse_args(["--range", "2025-01:2025-13"])  # Invalid end month
