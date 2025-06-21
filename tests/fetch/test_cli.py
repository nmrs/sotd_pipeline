"""
Tests for the fetch phase CLI module.
"""

import pytest
from pathlib import Path

from sotd.fetch.cli import get_parser


class TestFetchCLI:
    """Test cases for the fetch phase CLI."""

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

    def test_fetch_specific_arguments(self):
        """Test that fetch-specific arguments are properly configured."""
        parser = get_parser()
        args = parser.parse_args(
            [
                "--month",
                "2025-01",
                "--audit",
                "--list-months",
            ]
        )

        assert args.audit
        assert args.list_months

    def test_audit_argument(self):
        """Test that audit argument works correctly."""
        parser = get_parser()
        args = parser.parse_args(["--month", "2025-01", "--audit"])

        assert args.audit
        assert not args.list_months

    def test_list_months_argument(self):
        """Test that list-months argument works correctly."""
        parser = get_parser()
        args = parser.parse_args(["--month", "2025-01", "--list-months"])

        assert args.list_months
        assert not args.audit

    def test_both_fetch_arguments(self):
        """Test that both fetch-specific arguments can be used together."""
        parser = get_parser()
        args = parser.parse_args(["--month", "2025-01", "--audit", "--list-months"])

        assert args.audit
        assert args.list_months

    def test_year_argument(self):
        """Test that year argument works correctly."""
        parser = get_parser()
        args = parser.parse_args(["--year", "2025", "--audit"])

        assert args.year == "2025"
        assert args.audit
        assert args.month is None
        assert args.range is None
        assert args.start is None
        assert args.end is None

    def test_range_argument(self):
        """Test that range argument works correctly."""
        parser = get_parser()
        args = parser.parse_args(["--range", "2025-01:2025-12", "--list-months"])

        assert args.range == "2025-01:2025-12"
        assert args.list_months
        assert args.month is None
        assert args.year is None
        assert args.start is None
        assert args.end is None

    def test_start_end_arguments(self):
        """Test that start/end arguments work correctly."""
        parser = get_parser()
        args = parser.parse_args(["--start", "2025-01", "--end", "2025-12", "--audit"])

        assert args.start == "2025-01"
        assert args.end == "2025-12"
        assert args.audit
        assert args.month is None
        assert args.year is None
        assert args.range is None

    def test_debug_and_force_flags(self):
        """Test that debug and force flags work correctly."""
        parser = get_parser()
        args = parser.parse_args(["--month", "2025-01", "--debug", "--force", "--audit"])

        assert args.debug
        assert args.force
        assert args.audit

    def test_custom_output_directory(self):
        """Test that custom output directory works correctly."""
        parser = get_parser()
        args = parser.parse_args(
            ["--month", "2025-01", "--out-dir", "/custom/path", "--list-months"]
        )

        assert args.out_dir == Path("/custom/path")
        assert args.list_months

    def test_mutually_exclusive_date_arguments(self):
        """Test that date arguments are mutually exclusive."""
        parser = get_parser()

        # Should not raise an error when only one is specified
        args = parser.parse_args(["--month", "2025-01", "--audit"])
        assert args.month == "2025-01"
        assert args.audit

        args = parser.parse_args(["--year", "2025", "--list-months"])
        assert args.year == "2025"
        assert args.list_months

        args = parser.parse_args(["--range", "2025-01:2025-12"])
        assert args.range == "2025-01:2025-12"

        # Should raise an error when multiple are specified
        with pytest.raises(SystemExit):
            parser.parse_args(["--month", "2025-01", "--year", "2025", "--audit"])

        with pytest.raises(SystemExit):
            parser.parse_args(["--month", "2025-01", "--range", "2025-01:2025-12", "--list-months"])

        with pytest.raises(SystemExit):
            parser.parse_args(["--year", "2025", "--range", "2025-01:2025-12"])

    def test_start_end_pair_validation(self):
        """Test that start/end must be provided together."""
        parser = get_parser()

        # Both provided - should work
        args = parser.parse_args(["--start", "2025-01", "--end", "2025-12", "--audit"])
        assert args.start == "2025-01"
        assert args.end == "2025-12"
        assert args.audit

        # Only start provided - should raise error
        with pytest.raises(SystemExit):
            parser.parse_args(["--start", "2025-01", "--list-months"])

        # Only end provided - should raise error
        with pytest.raises(SystemExit):
            parser.parse_args(["--end", "2025-12", "--audit"])

    def test_help_text_includes_fetch_description(self):
        """Test that help text includes fetch-specific description."""
        parser = get_parser()
        help_text = parser.format_help()

        assert "Fetch & persist SOTD data" in help_text
        assert "--month" in help_text
        assert "--year" in help_text
        assert "--range" in help_text
        assert "--start" in help_text
        assert "--end" in help_text
        assert "--out-dir" in help_text
        assert "--debug" in help_text
        assert "--force" in help_text
        assert "--audit" in help_text
        assert "--list-months" in help_text

    def test_fetch_specific_help_text(self):
        """Test that fetch-specific arguments have proper help text."""
        parser = get_parser()
        help_text = parser.format_help()

        assert "Audit existing data for missing files and days" in help_text
        assert "List months with existing threads or comments files" in help_text
