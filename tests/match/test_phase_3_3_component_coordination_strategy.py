#!/usr/bin/env python3
"""Tests for Phase 3.3: ComponentCoordinationStrategy for handle/knot coordination."""

from unittest.mock import Mock
from sotd.match.brush_matching_strategies.component_coordination_strategy import (
    ComponentCoordinationStrategy,
)
from sotd.match.types import MatchResult
import pytest


class TestComponentCoordinationStrategy:
    """Test ComponentCoordinationStrategy for handle/knot coordination."""

    def setup_method(self):
        """Set up test fixtures."""
        # Create mock HandleMatcher and KnotMatcher
        self.mock_handle_matcher = Mock()
        self.mock_knot_matcher = Mock()
        self.strategy = ComponentCoordinationStrategy(
            self.mock_handle_matcher, self.mock_knot_matcher
        )

    def test_component_coordination_strategy_combines_handle_and_knot(self):
        """Test that ComponentCoordinationStrategy combines handle and knot into complete result."""
        # Setup mock handle match
        mock_handle_match = {
            "handle_maker": "Summer Break",
            "handle_model": "Maize",
            "_matched_by": "HandleMatcher",
            "_pattern_used": "summer.*break",
        }
        self.mock_handle_matcher.match_handle_maker.return_value = mock_handle_match

        # Setup mock knot match
        mock_knot_result = MatchResult(
            original="Timberwolf knot",
            matched={
                "brand": "Generic",
                "model": "Timberwolf",
                "fiber": "synthetic",
                "knot_size_mm": 26.0,
            },
            match_type="regex",
            pattern="timberwolf",
        )
        self.mock_knot_matcher.match.return_value = mock_knot_result

        # Test with composite brush input
        result = self.strategy.match("Summer Break Soaps Maize 26mm Timberwolf")

        # Should return complete composite result
        assert result is not None, "Should return a result when both handle and knot are found"
        assert result.matched is not None, "Should have matched data"

        # Should have top-level brand based on handle/knot brand matching (like legacy system)
        # For "Summer Break" handle and "Timberwolf" knot (different brands), brand should be None
        assert (
            result.matched["brand"] is None
        ), "Should have top-level brand as None when handle/knot brands differ (like legacy system)"
        assert (
            result.matched["model"] is None
        ), "Should have top-level model as None (like legacy system)"
        assert (
            result.matched["_matched_by"] == "HandleMatcher+KnotMatcher"
        ), "Should indicate combined source"
        assert result.matched["_pattern"] == "summer.*break", "Should preserve handle pattern"

        # Should have handle section
        assert "handle" in result.matched, "Should have handle section"
        assert result.matched["handle"]["brand"] == "Summer Break", "Should have handle brand"
        assert result.matched["handle"]["model"] == "Maize", "Should have handle model"

        # Should have knot section
        assert "knot" in result.matched, "Should have knot section"
        assert result.matched["knot"]["brand"] == "Generic", "Should have knot brand"
        assert result.matched["knot"]["model"] == "Timberwolf", "Should have knot model"
        assert result.matched["knot"]["fiber"] == "synthetic", "Should have knot fiber"
        assert result.matched["knot"]["knot_size_mm"] == 26.0, "Should have knot size"

    def test_component_coordination_strategy_has_correct_strategy_name(self):
        """Test that ComponentCoordinationStrategy has correct strategy name for scoring."""
        # Setup mock handle match
        mock_handle_match = {
            "handle_maker": "Chisel & Hound",
            "handle_model": "The Duke",
            "_matched_by": "HandleMatcher",
            "_pattern_used": "chisel.*hound",
        }
        self.mock_handle_matcher.match_handle_maker.return_value = mock_handle_match

        # Setup mock knot match
        mock_knot_result = MatchResult(
            original="Omega 10098 Boar",
            matched={
                "brand": "Omega",
                "model": "10098",
                "fiber": "boar",
                "knot_size_mm": 26.0,
            },
            match_type="regex",
            pattern="omega.*10098",
        )
        self.mock_knot_matcher.match.return_value = mock_knot_result

        # Test strategy name
        result = self.strategy.match("Chisel & Hound 'The Duke' / Omega 10098 Boar")
        assert result is not None, "Should return a result"
        assert (
            result.strategy == "dual_component"
        ), "Strategy name should be 'dual_component' for perfect compatibility"

    def test_component_coordination_strategy_no_handle_returns_none(self):
        """Test that ComponentCoordinationStrategy returns None when no handle found."""
        # Setup mock to return None (no handle match)
        self.mock_handle_matcher.match_handle_maker.return_value = None

        # Setup mock knot match (should not matter)
        mock_knot_result = MatchResult(
            original="Omega 10098 Boar",
            matched={
                "brand": "Omega",
                "model": "10098",
                "fiber": "boar",
                "knot_size_mm": 26.0,
            },
            match_type="regex",
            pattern="omega.*10098",
        )
        self.mock_knot_matcher.match.return_value = mock_knot_result

        # Test with input that has no handle component
        result = self.strategy.match("Omega 10098 Boar")

        # Should return None (no handle component found)
        assert result is None, "Should return None when no handle component found"

    def test_component_coordination_strategy_no_knot_returns_none(self):
        """Test that ComponentCoordinationStrategy returns None when no knot found."""
        # Setup mock handle match
        mock_handle_match = {
            "handle_maker": "Summer Break",
            "handle_model": "Maize",
            "_matched_by": "HandleMatcher",
            "_pattern_used": "summer.*break",
        }
        self.mock_handle_matcher.match_handle_maker.return_value = mock_handle_match

        # Setup mock to return None (no knot match)
        self.mock_knot_matcher.match.return_value = None

        # Test with input that has no knot component
        result = self.strategy.match("Summer Break Soaps Maize")

        # Should return None (no knot component found)
        assert result is None, "Should return None when no knot component found"

    def test_component_coordination_strategy_handles_empty_handle_maker(self):
        """Test that ComponentCoordinationStrategy handles empty handle_maker gracefully."""
        # Setup mock handle match with empty handle_maker
        mock_handle_match = {
            "handle_maker": "",  # Empty handle maker
            "handle_model": "Test",
            "_matched_by": "HandleMatcher",
            "_pattern_used": "test",
        }
        self.mock_handle_matcher.match_handle_maker.return_value = mock_handle_match

        # Setup mock knot match
        mock_knot_result = MatchResult(
            original="Test knot",
            matched={
                "brand": "Test Brand",
                "model": "Test Model",
                "fiber": "badger",
                "knot_size_mm": 26.0,
            },
            match_type="regex",
            pattern="test",
        )
        self.mock_knot_matcher.match.return_value = mock_knot_result

        # Should return None when handle_maker is empty
        result = self.strategy.match("Test input")
        assert result is None, "Should return None when handle_maker is empty"

    def test_component_coordination_strategy_preserves_metadata(self):
        """Test that ComponentCoordinationStrategy preserves all metadata."""
        # Setup mock handle match with full metadata
        mock_handle_match = {
            "handle_maker": "Declaration Grooming",
            "handle_model": "Washington",
            "_matched_by": "HandleMatcher",
            "_pattern_used": "declaration.*washington",
            "_source_text": "Declaration Grooming Washington handle",
        }
        self.mock_handle_matcher.match_handle_maker.return_value = mock_handle_match

        # Setup mock knot match with full metadata
        mock_knot_result = MatchResult(
            original="Declaration B2",
            matched={
                "brand": "Declaration Grooming",
                "model": "B2",
                "fiber": "badger",
                "knot_size_mm": 26.0,
            },
            match_type="regex",
            pattern="declaration.*b2",
        )
        self.mock_knot_matcher.match.return_value = mock_knot_result

        # Test metadata preservation
        result = self.strategy.match("Declaration Grooming Washington B2")
        assert result is not None, "Should return a result"
        assert (
            result.matched["_source_text"] == "Declaration Grooming Washington handle"
        ), "Should preserve handle source text"

    def test_component_coordination_strategy_handles_invalid_input(self):
        """Test that ComponentCoordinationStrategy handles invalid input gracefully."""
        # Test with None input
        result = self.strategy.match(None)
        assert result is None, "Should return None for None input"

        # Test with empty string
        result = self.strategy.match("")
        assert result is None, "Should return None for empty string"

        # Test with non-string input
        result = self.strategy.match(123)
        assert result is None, "Should return None for non-string input"

    def test_component_coordination_strategy_fail_fast_on_handle_matcher_error(self):
        """Test that ComponentCoordinationStrategy fails fast on HandleMatcher errors."""
        # Setup mock to raise exception
        self.mock_handle_matcher.match_handle_maker.side_effect = ValueError("Handle matcher error")

        # Should raise exception (fail fast)
        with pytest.raises(ValueError, match="Component coordination failed"):
            self.strategy.match("Test input")

    def test_component_coordination_strategy_fail_fast_on_knot_matcher_error(self):
        """Test that ComponentCoordinationStrategy fails fast on KnotMatcher errors."""
        # Setup mock handle match
        mock_handle_match = {
            "handle_maker": "Test Maker",
            "handle_model": "Test Model",
            "_matched_by": "HandleMatcher",
            "_pattern_used": "test",
        }
        self.mock_handle_matcher.match_handle_maker.return_value = mock_handle_match

        # Setup mock to raise exception
        self.mock_knot_matcher.match.side_effect = ValueError("Knot matcher error")

        # Should raise exception (fail fast)
        with pytest.raises(ValueError, match="Component coordination failed"):
            self.strategy.match("Test input")

    def test_component_coordination_strategy_match_type(self):
        """Test that ComponentCoordinationStrategy has correct match_type."""
        # Setup mock handle match
        mock_handle_match = {
            "handle_maker": "Test Maker",
            "handle_model": "Test Model",
            "_matched_by": "HandleMatcher",
            "_pattern_used": "test.*pattern",
        }
        self.mock_handle_matcher.match_handle_maker.return_value = mock_handle_match

        # Setup mock knot match
        mock_knot_result = MatchResult(
            original="Test input",
            matched={
                "brand": "Test Brand",
                "model": "Test Model",
                "fiber": "badger",
                "knot_size_mm": 26.0,
            },
            match_type="regex",
            pattern="test.*pattern",
        )
        self.mock_knot_matcher.match.return_value = mock_knot_result

        # Test match_type
        result = self.strategy.match("Test input")
        assert result is not None, "Should return a result"
        assert result.match_type == "regex", "Match type should be 'regex' (like legacy system)"

    def test_component_coordination_strategy_same_brand_sets_top_level(self):
        """Test that ComponentCoordinationStrategy sets top-level brand when handle/knot brands match."""
        # Setup mock handle match with same brand as knot
        mock_handle_match = {
            "handle_maker": "Wolf Whiskers",  # Same brand as knot
            "handle_model": "Custom Handle",
            "_matched_by": "HandleMatcher",
            "_pattern_used": "wolf.*whisker",
        }
        self.mock_handle_matcher.match_handle_maker.return_value = mock_handle_match

        # Setup mock knot match with same brand
        mock_knot_result = MatchResult(
            original="Test input",
            matched={
                "brand": "Wolf Whiskers",  # Same brand as handle
                "model": "Mixed Badger/Boar",
                "fiber": "badger",
                "knot_size_mm": 26.0,
            },
            match_type="regex",
            pattern="wolf.*whisker",
        )
        self.mock_knot_matcher.match.return_value = mock_knot_result

        # Should set top-level brand when handle/knot brands match (like legacy system)
        result = self.strategy.match("Wolf Whiskers - Mixed Badger/Boar")
        assert result is not None, "Should return a result"
        assert (
            result.matched["brand"] == "Wolf Whiskers"
        ), "Should set top-level brand when brands match"
        assert result.matched["model"] is None, "Should have top-level model as None"
        assert result.match_type == "regex", "Match type should be 'regex' (like legacy system)"

    def test_component_coordination_strategy_handles_missing_patterns(self):
        """Test that ComponentCoordinationStrategy handles missing patterns gracefully."""
        # Setup mock handle match with missing pattern
        mock_handle_match = {
            "handle_maker": "Test Maker",
            "handle_model": "Test Model",
            "_matched_by": "HandleMatcher",
            "_pattern_used": None,  # Missing pattern
        }
        self.mock_handle_matcher.match_handle_maker.return_value = mock_handle_match

        # Setup mock knot match with missing pattern
        mock_knot_result = MatchResult(
            original="Test input",
            matched={
                "brand": "Test Brand",
                "model": "Test Model",
                "fiber": "badger",
                "knot_size_mm": 26.0,
            },
            match_type="regex",
            pattern=None,  # Missing pattern
        )
        self.mock_knot_matcher.match.return_value = mock_knot_result

        # Should handle missing patterns gracefully
        result = self.strategy.match("Test input")
        assert result is not None, "Should return a result"
        assert result.matched["_pattern"] == "unknown", "Should use 'unknown' for missing pattern"
