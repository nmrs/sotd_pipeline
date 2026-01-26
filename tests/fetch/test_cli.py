"""
Tests for the fetch phase CLI module.
"""

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
        assert args.data_dir == Path("data")
        assert not args.debug
        assert not args.force

    # Note: Basic argument validation (month, year, range, start/end) is tested in
    # tests/cli_utils/test_base_parser.py. Only phase-specific tests are included here.

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
        assert "--data-dir" in help_text
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
