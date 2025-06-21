"""
Tests for the match phase CLI module.
"""

import pytest
from pathlib import Path

from sotd.match.cli import get_parser


class TestMatchCLI:
    """Test cases for the match phase CLI."""

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

    def test_match_specific_arguments(self):
        """Test that match-specific arguments are properly configured."""
        parser = get_parser()
        args = parser.parse_args(
            [
                "--month",
                "2025-01",
                "--mode",
                "analyze_unmatched_razors",
                "--parallel",
                "--max-workers",
                "8",
            ]
        )

        assert args.mode == "analyze_unmatched_razors"
        assert args.parallel
        assert args.max_workers == 8

    def test_parallel_sequential_mutually_exclusive(self):
        """Test that parallel and sequential are mutually exclusive."""
        parser = get_parser()

        # Should not raise an error when only one is specified
        args = parser.parse_args(["--month", "2025-01", "--parallel"])
        assert args.parallel
        assert not args.sequential

        args = parser.parse_args(["--month", "2025-01", "--sequential"])
        assert args.sequential
        assert not args.parallel

        # Should raise an error when both are specified
        with pytest.raises(SystemExit):
            parser.parse_args(["--month", "2025-01", "--parallel", "--sequential"])

    def test_default_values(self):
        """Test that default values are set correctly."""
        parser = get_parser()
        args = parser.parse_args(["--month", "2025-01"])

        assert args.mode == "match"
        assert args.max_workers == 4
        assert not args.parallel
        assert not args.sequential

    def test_help_text_includes_match_description(self):
        """Test that help text includes match-specific description."""
        parser = get_parser()
        help_text = parser.format_help()

        assert "Match razors, blades, soaps, and brushes" in help_text
        assert "--mode" in help_text
        assert "--parallel" in help_text
        assert "--sequential" in help_text
        assert "--max-workers" in help_text
