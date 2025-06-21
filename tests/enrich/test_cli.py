"""
Tests for the enrich phase CLI module.
"""

import pytest
from pathlib import Path

from sotd.enrich.cli import get_parser


class TestEnrichCLI:
    """Test cases for the enrich phase CLI."""

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

    def test_year_argument(self):
        """Test that year argument works correctly."""
        parser = get_parser()
        args = parser.parse_args(["--year", "2025"])

        assert args.year == "2025"
        assert args.month is None
        assert args.range is None
        assert args.start is None
        assert args.end is None

    def test_range_argument(self):
        """Test that range argument works correctly."""
        parser = get_parser()
        args = parser.parse_args(["--range", "2025-01:2025-12"])

        assert args.range == "2025-01:2025-12"
        assert args.month is None
        assert args.year is None
        assert args.start is None
        assert args.end is None

    def test_start_end_arguments(self):
        """Test that start/end arguments work correctly."""
        parser = get_parser()
        args = parser.parse_args(["--start", "2025-01", "--end", "2025-12"])

        assert args.start == "2025-01"
        assert args.end == "2025-12"
        assert args.month is None
        assert args.year is None
        assert args.range is None

    def test_debug_and_force_flags(self):
        """Test that debug and force flags work correctly."""
        parser = get_parser()
        args = parser.parse_args(["--month", "2025-01", "--debug", "--force"])

        assert args.debug
        assert args.force

    def test_custom_output_directory(self):
        """Test that custom output directory works correctly."""
        parser = get_parser()
        args = parser.parse_args(["--month", "2025-01", "--out-dir", "/custom/path"])

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
        """Test that start/end must be provided together."""
        parser = get_parser()

        # Both provided - should work
        args = parser.parse_args(["--start", "2025-01", "--end", "2025-12"])
        assert args.start == "2025-01"
        assert args.end == "2025-12"

        # Only start provided - should raise error
        with pytest.raises(SystemExit):
            parser.parse_args(["--start", "2025-01"])

        # Only end provided - should raise error
        with pytest.raises(SystemExit):
            parser.parse_args(["--end", "2025-12"])

    def test_help_text_includes_enrich_description(self):
        """Test that help text includes enrich-specific description."""
        parser = get_parser()
        help_text = parser.format_help()

        assert "Enrich SOTD data with detailed specifications" in help_text
        assert "--month" in help_text
        assert "--year" in help_text
        assert "--range" in help_text
        assert "--start" in help_text
        assert "--end" in help_text
        assert "--out-dir" in help_text
        assert "--debug" in help_text
        assert "--force" in help_text

    def test_no_additional_arguments(self):
        """Test that enrich CLI doesn't add any additional arguments beyond base ones."""
        parser = get_parser()
        help_text = parser.format_help()

        # Should only have the standard arguments from BaseCLIParser
        # No enrich-specific arguments should be present
        assert "mode" not in help_text.lower()
        assert "parallel" not in help_text.lower()
        assert "max-workers" not in help_text.lower()

    def test_no_date_arguments_raises_error(self):
        """Test that no date arguments raises error (date required by main run.py)."""
        parser = get_parser()
        with pytest.raises(SystemExit):
            parser.parse_args([])
