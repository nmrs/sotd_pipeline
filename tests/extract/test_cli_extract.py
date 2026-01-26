"""
Tests for the extract phase CLI module.
"""

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
        assert args.data_dir == Path("data")
        assert not args.debug
        assert not args.force

    # Note: Basic argument validation (month, year, range, start/end) is tested in
    # tests/cli_utils/test_base_parser.py. Only phase-specific tests are included here.

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
        assert "--data-dir" in help_text
        assert "--debug" in help_text
        assert "--force" in help_text
