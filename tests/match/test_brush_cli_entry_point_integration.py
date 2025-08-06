"""
Tests for brush CLI entry point integration.

This module tests the integration of the BrushMatcherEntryPoint with the CLI
system for Phase 2 of the multi-strategy scoring system implementation.
"""

import pytest
from unittest.mock import Mock

from sotd.match.brush_matcher_entry import BrushMatcherEntryPoint
from sotd.match.cli import get_parser


class TestBrushCLIEntryPointIntegration:
    """Test brush CLI entry point integration."""

    def test_cli_parser_has_brush_system_flag(self):
        """Test that CLI parser has brush-system flag."""
        parser = get_parser()
        args = parser.parse_args(["--month", "2025-05", "--brush-system", "new"])
        assert args.brush_system == "new"

    def test_cli_parser_brush_system_default(self):
        """Test that CLI parser defaults to current system."""
        parser = get_parser()
        args = parser.parse_args(["--month", "2025-05"])
        assert args.brush_system == "current"

    def test_cli_parser_brush_system_choices(self):
        """Test that CLI parser accepts valid brush system choices."""
        parser = get_parser()

        args_current = parser.parse_args(["--month", "2025-05", "--brush-system", "current"])
        assert args_current.brush_system == "current"

        args_new = parser.parse_args(["--month", "2025-05", "--brush-system", "new"])
        assert args_new.brush_system == "new"

    def test_cli_parser_brush_system_invalid_choice(self):
        """Test that CLI parser rejects invalid brush system choices."""
        parser = get_parser()

        with pytest.raises(SystemExit):
            parser.parse_args(["--month", "2025-05", "--brush-system", "invalid"])

    def test_brush_matcher_entry_point_creation_current(self):
        """Test creation of brush matcher entry point with current system."""
        entry_point = BrushMatcherEntryPoint(use_scoring_system=False)
        assert entry_point.get_system_name() == "legacy"
        assert not entry_point.use_scoring_system

    def test_brush_matcher_entry_point_creation_new(self):
        """Test creation of brush matcher entry point with new system."""
        entry_point = BrushMatcherEntryPoint(use_scoring_system=True)
        assert entry_point.get_system_name() == "scoring"
        assert entry_point.use_scoring_system

    def test_brush_matcher_entry_point_match_interface(self):
        """Test that brush matcher entry point provides consistent match interface."""
        entry_point = BrushMatcherEntryPoint(use_scoring_system=False)

        # Test that the entry point has the expected interface
        assert hasattr(entry_point, "match")
        assert hasattr(entry_point, "get_cache_stats")
        assert hasattr(entry_point, "get_system_name")

    def test_brush_matcher_entry_point_cache_stats(self):
        """Test that brush matcher entry point provides cache stats."""
        entry_point = BrushMatcherEntryPoint(use_scoring_system=False)

        # Mock the underlying matcher's get_cache_stats method
        entry_point.matcher.get_cache_stats = Mock(return_value={"hits": 10, "misses": 5})

        stats = entry_point.get_cache_stats()
        assert stats == {"hits": 10, "misses": 5}

    def test_brush_matcher_entry_point_system_identification(self):
        """Test that brush matcher entry point correctly identifies systems."""
        entry_point_current = BrushMatcherEntryPoint(use_scoring_system=False)
        assert entry_point_current.get_system_name() == "legacy"

        entry_point_new = BrushMatcherEntryPoint(use_scoring_system=True)
        assert entry_point_new.get_system_name() == "scoring"

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
        """Test that brush-system doesn't conflict with required arguments."""
        parser = get_parser()

        # Should not require brush-system to be specified
        args = parser.parse_args(["--month", "2025-01"])
        assert args.brush_system == "current"  # Default value

    def test_cli_brush_system_conflicts(self):
        """Test that brush-system doesn't conflict with other options."""
        parser = get_parser()

        # Test with all options to ensure no conflicts
        args = parser.parse_args(
            ["--brush-system", "new", "--month", "2025-01", "--force", "--max-workers", "4"]
        )
        assert args.brush_system == "new"
        assert args.month == "2025-01"
        assert args.force is True
        assert args.max_workers == 4
