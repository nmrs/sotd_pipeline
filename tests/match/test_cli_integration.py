"""
Unit tests for CLI integration of brush scoring system.

Tests the integration of the new brush scoring system into the CLI.
"""

import pytest
from unittest.mock import Mock, patch
from pathlib import Path

from sotd.match.cli import get_parser
from sotd.match.run import run_match


class TestCLIIntegration:
    """Test CLI integration of brush scoring system."""

    def test_cli_parser_has_brush_system_flag(self):
        """Test that CLI parser has brush-system flag."""
        parser = get_parser()
        args = parser.parse_args(["--brush-system", "new", "--month", "2025-01"])

        assert args.brush_system == "new"

    def test_cli_parser_brush_system_default(self):
        """Test that CLI parser defaults to current brush system."""
        parser = get_parser()
        args = parser.parse_args(["--month", "2025-01"])

        assert args.brush_system == "current"

    def test_cli_parser_brush_system_choices(self):
        """Test that CLI parser accepts both current and new choices."""
        parser = get_parser()

        # Test current
        args_current = parser.parse_args(["--brush-system", "current", "--month", "2025-01"])
        assert args_current.brush_system == "current"

        # Test new
        args_new = parser.parse_args(["--brush-system", "new", "--month", "2025-01"])
        assert args_new.brush_system == "new"

    def test_cli_parser_brush_system_invalid_choice(self):
        """Test that CLI parser rejects invalid brush system choices."""
        parser = get_parser()

        with pytest.raises(SystemExit):
            parser.parse_args(["--brush-system", "invalid", "--month", "2025-01"])

    def test_run_match_phase_with_current_system(self):
        """Test running match phase with current brush system."""
        with patch("sotd.match.run.BrushMatcher") as mock_brush_matcher:
            mock_matcher = Mock()
            mock_brush_matcher.return_value = mock_matcher

            # Mock arguments with all required attributes
            args = Mock()
            args.brush_system = "current"
            args.month = "2025-01"
            args.force = True
            args.out_dir = "data"
            args.debug = False
            args.max_workers = 1
            args.correct_matches_path = None

            run_match(args)

            # Should use BrushMatcher
            mock_brush_matcher.assert_called_once()

    def test_run_match_phase_with_new_system(self):
        """Test running match phase with new brush system."""
        with patch("sotd.match.run.BrushScoringMatcher") as mock_scoring_matcher:
            mock_matcher = Mock()
            mock_scoring_matcher.return_value = mock_matcher

            # Mock arguments with all required attributes
            args = Mock()
            args.brush_system = "new"
            args.month = "2025-01"
            args.force = False
            args.out_dir = "data"
            args.debug = False
            args.max_workers = 1
            args.correct_matches_path = None

            run_match(args)

            # Should use BrushScoringMatcher
            mock_scoring_matcher.assert_called_once()

    def test_run_match_phase_passes_arguments(self):
        """Test that run_match_phase passes arguments to matcher."""
        with patch("sotd.match.run.BrushScoringMatcher") as mock_scoring_matcher:
            mock_matcher = Mock()
            mock_scoring_matcher.return_value = mock_matcher

            # Mock arguments with additional parameters
            args = Mock()
            args.brush_system = "new"
            args.month = "2025-01"
            args.force = False
            args.out_dir = "data"
            args.debug = False
            args.max_workers = 1
            args.correct_matches_path = None
            args.config_path = Path("/test/config.yaml")

            run_match(args)

            # Should pass config_path to BrushScoringMatcher
            mock_scoring_matcher.assert_called_once_with(config_path=Path("/test/config.yaml"))

    def test_run_match_phase_error_handling(self):
        """Test error handling in run_match_phase."""
        with patch("sotd.match.run.BrushScoringMatcher") as mock_scoring_matcher:
            mock_scoring_matcher.side_effect = Exception("Test error")

            # Mock arguments with all required attributes
            args = Mock()
            args.brush_system = "new"
            args.month = "2025-01"
            args.force = False
            args.out_dir = "data"
            args.debug = False
            args.max_workers = 1
            args.correct_matches_path = None

            # Should handle errors gracefully
            with pytest.raises(Exception, match="Test error"):
                run_match(args)

    def test_cli_help_includes_brush_system(self):
        """Test that CLI help includes brush-system option."""
        parser = get_parser()
        help_text = parser.format_help()

        assert "brush-system" in help_text
        assert "current" in help_text
        assert "new" in help_text

    def test_cli_brush_system_with_other_options(self):
        """Test that brush-system works with other CLI options."""
        parser = get_parser()
        args = parser.parse_args(["--brush-system", "new", "--month", "2025-01", "--force"])

        assert args.brush_system == "new"
        assert args.month == "2025-01"
        assert args.force is True

    def test_cli_brush_system_required_argument(self):
        """Test that brush-system is a required argument."""
        parser = get_parser()

        # Should not require brush-system to be specified
        args = parser.parse_args(["--month", "2025-01"])
        assert args.brush_system == "current"  # Default value

    def test_cli_brush_system_conflicts(self):
        """Test that brush-system doesn't conflict with other options."""
        parser = get_parser()

        # Should work with all other options
        args = parser.parse_args(
            ["--brush-system", "new", "--month", "2025-01", "--force", "--max-workers", "4"]
        )

        assert args.brush_system == "new"
        assert args.month == "2025-01"
        assert args.force is True
        assert args.max_workers == 4
