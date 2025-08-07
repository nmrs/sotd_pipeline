#!/usr/bin/env python3
"""Tests for Phase 3.3: KnotComponentStrategy for knot-only matching."""

from unittest.mock import Mock
from sotd.match.brush_matching_strategies.knot_component_strategy import KnotComponentStrategy
from sotd.match.types import MatchResult
import pytest


class TestKnotComponentStrategy:
    """Test KnotComponentStrategy for knot-only component matching."""

    def setup_method(self):
        """Set up test fixtures."""
        # Create mock KnotMatcher
        self.mock_knot_matcher = Mock()
        self.strategy = KnotComponentStrategy(self.mock_knot_matcher)

    def test_knot_component_strategy_matches_knot_only(self):
        """Test that KnotComponentStrategy matches knot components only."""
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

        # Test with composite brush input
        result = self.strategy.match("Summer Break Soaps Maize 26mm Timberwolf")

        # Should return partial result with knot information only
        assert result is not None, "Should return a result when knot is found"
        assert result.matched is not None, "Should have matched data"
        assert result.matched["brand"] == "Omega", "Should match knot brand"
        assert result.matched["model"] == "10098", "Should match knot model"
        assert result.matched["fiber"] == "boar", "Should match knot fiber"
        assert result.matched["knot_size_mm"] == 26.0, "Should match knot size"
        assert result.matched["_matched_by"] == "KnotMatcher", "Should indicate KnotMatcher source"
        assert result.matched["_pattern"] == "omega.*10098", "Should preserve pattern"

        # Should be partial result (no top-level brand/model)
        assert "handle_maker" not in result.matched, "Should not have handle_maker (partial result)"
        assert "handle_model" not in result.matched, "Should not have handle_model (partial result)"
        assert "handle" not in result.matched, "Should not have handle section (partial result)"

    def test_knot_component_strategy_has_correct_strategy_name(self):
        """Test that KnotComponentStrategy has correct strategy name for scoring."""
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

        # Test strategy name
        result = self.strategy.match("Timberwolf knot")
        assert result is not None, "Should return a result"
        assert result.strategy == "knot_component", "Strategy name should be 'knot_component'"

    def test_knot_component_strategy_no_match_returns_none(self):
        """Test that KnotComponentStrategy returns None when no knot found."""
        # Setup mock to return None (no knot match)
        self.mock_knot_matcher.match.return_value = None

        # Test with input that has no knot component
        result = self.strategy.match("Unknown Brush XYZ")

        # Should return None (no knot component found)
        assert result is None, "Should return None when no knot component found"

    def test_knot_component_strategy_handles_empty_matched_data(self):
        """Test that KnotComponentStrategy handles empty matched data gracefully."""
        # Setup mock knot result with empty matched data
        mock_knot_result = MatchResult(
            original="Test input",
            matched={},  # Empty matched data
            match_type="regex",
            pattern="test",
        )
        self.mock_knot_matcher.match.return_value = mock_knot_result

        # Should return None when matched data is empty
        result = self.strategy.match("Test input")
        assert result is None, "Should return None when matched data is empty"

    def test_knot_component_strategy_handles_none_matched_data(self):
        """Test that KnotComponentStrategy handles None matched data gracefully."""
        # Setup mock knot result with None matched data
        mock_knot_result = MatchResult(
            original="Test input",
            matched=None,  # None matched data
            match_type="regex",
            pattern="test",
        )
        self.mock_knot_matcher.match.return_value = mock_knot_result

        # Should return None when matched data is None
        result = self.strategy.match("Test input")
        assert result is None, "Should return None when matched data is None"

    def test_knot_component_strategy_preserves_metadata(self):
        """Test that KnotComponentStrategy preserves all knot metadata."""
        # Setup mock knot result with full metadata
        mock_knot_result = MatchResult(
            original="Declaration B2 Washington",
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
        result = self.strategy.match("Declaration B2 Washington")
        assert result is not None, "Should return a result"
        assert (
            result.matched["_source_text"] == "Declaration B2 Washington"
        ), "Should preserve source text"

    def test_knot_component_strategy_handles_invalid_input(self):
        """Test that KnotComponentStrategy handles invalid input gracefully."""
        # Test with None input
        result = self.strategy.match(None)
        assert result is None, "Should return None for None input"

        # Test with empty string
        result = self.strategy.match("")
        assert result is None, "Should return None for empty string"

        # Test with non-string input
        result = self.strategy.match(123)
        assert result is None, "Should return None for non-string input"

    def test_knot_component_strategy_fail_fast_on_knot_matcher_error(self):
        """Test that KnotComponentStrategy fails fast on KnotMatcher errors."""
        # Setup mock to raise exception
        self.mock_knot_matcher.match.side_effect = ValueError("Knot matcher error")

        # Should raise exception (fail fast)
        with pytest.raises(ValueError, match="Knot component matching failed"):
            self.strategy.match("Test input")

    def test_knot_component_strategy_match_type(self):
        """Test that KnotComponentStrategy has correct match_type."""
        # Setup mock knot result
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
        assert result.match_type == "knot_component", "Match type should be 'knot_component'"

    def test_knot_component_strategy_handles_missing_pattern(self):
        """Test that KnotComponentStrategy handles missing pattern gracefully."""
        # Setup mock knot result with missing pattern
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

        # Should handle missing pattern gracefully
        result = self.strategy.match("Test input")
        assert result is not None, "Should return a result"
        assert result.matched["_pattern"] == "unknown", "Should use 'unknown' for missing pattern"
