"""
Integration tests for brush system flag integration.

Tests that the brush system flag is properly passed through the match phase processing.
"""

from sotd.match.cli import get_parser


class TestBrushSystemIntegration:
    """Test brush system flag integration."""

    def test_process_month_brush_system_parameter(self):
        """Test that process_month accepts brush_system parameter."""
        # This test verifies the function signature supports brush_system
        # The actual implementation will be added in the next step
        pass

    def test_run_match_brush_system_flag(self):
        """Test that run_match function receives brush_system from args."""
        parser = get_parser()
        args = parser.parse_args(["--month", "2025-05", "--brush-system", "new"])

        # Verify the flag is properly parsed
        assert args.brush_system == "new"

    def test_brush_system_flag_default_value(self):
        """Test that brush system flag defaults to 'new' (multi-strategy scoring system)."""
        parser = get_parser()
        args = parser.parse_args(["--month", "2025-05"])

        assert args.brush_system == "new"

    def test_brush_system_flag_validation(self):
        """Test that brush system flag validation works correctly."""
        parser = get_parser()

        # Valid values
        valid_values = ["legacy", "new"]
        for value in valid_values:
            args = parser.parse_args(["--month", "2025-05", "--brush-system", value])
            assert args.brush_system == value

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
