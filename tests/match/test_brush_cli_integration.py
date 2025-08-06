"""
Unit tests for brush CLI flag integration.

Tests the addition of brush system selection flags to the pipeline CLI.
"""

import pytest

from sotd.match.cli import get_parser


class TestBrushCLIIntegration:
    """Test brush CLI flag integration."""

    def test_brush_system_flag_default(self):
        """Test that brush system flag defaults to 'current'."""
        parser = get_parser()
        args = parser.parse_args(["--month", "2025-05"])

        assert args.brush_system == "current"

    def test_brush_system_flag_new(self):
        """Test that brush system flag accepts 'new' value."""
        parser = get_parser()
        args = parser.parse_args(["--month", "2025-05", "--brush-system", "new"])

        assert args.brush_system == "new"

    def test_brush_system_flag_invalid(self):
        """Test that invalid brush system flag raises error."""
        parser = get_parser()

        with pytest.raises(SystemExit):
            parser.parse_args(["--month", "2025-05", "--brush-system", "invalid"])

    def test_brush_system_flag_help(self):
        """Test that brush system flag has proper help text."""
        parser = get_parser()
        help_text = parser.format_help()

        assert "brush-system" in help_text
        assert "current" in help_text
        assert "new" in help_text

    def test_brush_system_flag_with_other_args(self):
        """Test that brush system flag works with other arguments."""
        parser = get_parser()
        args = parser.parse_args(
            ["--month", "2025-05", "--brush-system", "new", "--force", "--debug"]
        )

        assert args.brush_system == "new"
        assert args.force is True
        assert args.debug is True
        assert args.month == "2025-05"

    def test_brush_system_flag_validation(self):
        """Test that brush system flag validation works correctly."""
        parser = get_parser()

        # Valid values
        valid_values = ["current", "new"]
        for value in valid_values:
            args = parser.parse_args(["--month", "2025-05", "--brush-system", value])
            assert args.brush_system == value

    def test_brush_system_flag_required_args(self):
        """Test that brush system flag doesn't interfere with required arguments."""
        parser = get_parser()

        # Should still require month when no brush system specified
        with pytest.raises(SystemExit):
            parser.parse_args(["--brush-system", "new"])

        # Should work with month specified
        args = parser.parse_args(["--month", "2025-05", "--brush-system", "new"])
        assert args.month == "2025-05"
        assert args.brush_system == "new"
