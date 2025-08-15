#!/usr/bin/env python3
"""Tests for HandleComponentStrategy for handle-only matching."""

from unittest.mock import Mock
from sotd.match.brush_matching_strategies.handle_component_strategy import HandleComponentStrategy
from sotd.match.types import MatchResult
import pytest


class TestHandleComponentStrategy:
    """Test HandleComponentStrategy for handle-only component matching."""

    def setup_method(self):
        """Set up test fixtures."""
        # Create mock HandleMatcher
        self.mock_handle_matcher = Mock()
        self.strategy = HandleComponentStrategy(self.mock_handle_matcher)

    def test_handle_component_strategy_matches_handle_only(self):
        """Test that HandleComponentStrategy matches handle components only."""
        # Setup mock handle match
        mock_handle_match = {
            "handle_maker": "Summer Break",
            "handle_model": "Maize",
            "_matched_by": "HandleMatcher",
            "_pattern_used": "summer.*break",
        }
        self.mock_handle_matcher.match_handle_maker.return_value = mock_handle_match

        # Test with composite brush input
        result = self.strategy.match("Summer Break Soaps Maize 26mm Timberwolf")

        # Should return partial result with handle information only
        assert result is not None, "Should return a result when handle is found"
        assert result.matched is not None, "Should have matched data"
        assert result.matched["handle_maker"] == "Summer Break", "Should match handle maker"
        assert result.matched["handle_model"] == "Maize", "Should match handle model"
        assert (
            result.matched["_matched_by"] == "HandleMatcher"
        ), "Should indicate HandleMatcher source"
        assert result.matched["_pattern"] == "summer.*break", "Should preserve pattern"

        # Should be partial result (no top-level brand/model)
        assert "brand" not in result.matched, "Should not have top-level brand (partial result)"
        assert "model" not in result.matched, "Should not have top-level model (partial result)"
        assert "knot" not in result.matched, "Should not have knot section (partial result)"

    def test_handle_component_strategy_has_correct_strategy_name(self):
        """Test that HandleComponentStrategy has correct strategy name for scoring."""
        # Setup mock handle match
        mock_handle_match = {
            "handle_maker": "Chisel & Hound",
            "handle_model": "The Duke",
            "_matched_by": "HandleMatcher",
            "_pattern_used": "chisel.*hound",
        }
        self.mock_handle_matcher.match_handle_maker.return_value = mock_handle_match

        # Test strategy name
        result = self.strategy.match("Chisel & Hound 'The Duke' / Omega 10098 Boar")
        assert result is not None, "Should return a result"
        assert result.strategy == "handle_component", "Strategy name should be 'handle_component'"

    def test_handle_component_strategy_no_match_returns_none(self):
        """Test that HandleComponentStrategy returns None when no handle found."""
        # Setup mock to return None (no handle match)
        self.mock_handle_matcher.match_handle_maker.return_value = None

        # Test with input that has no handle component
        result = self.strategy.match("Omega 10098 Boar")

        # Should return None (no handle component found)
        assert result is None, "Should return None when no handle component found"

    def test_handle_component_strategy_handles_empty_handle_maker(self):
        """Test that HandleComponentStrategy handles empty handle_maker gracefully."""
        # Setup mock handle match with empty handle_maker
        mock_handle_match = {
            "handle_maker": "",  # Empty handle maker
            "handle_model": "Test",
            "_matched_by": "HandleMatcher",
            "_pattern_used": "test",
        }
        self.mock_handle_matcher.match_handle_maker.return_value = mock_handle_match

        # Should return None when handle_maker is empty
        result = self.strategy.match("Test input")
        assert result is None, "Should return None when handle_maker is empty"

    def test_handle_component_strategy_handles_none_handle_maker(self):
        """Test that HandleComponentStrategy handles None handle_maker gracefully."""
        # Setup mock handle match with None handle_maker
        mock_handle_match = {
            "handle_maker": None,  # None handle maker
            "handle_model": "Test",
            "_matched_by": "HandleMatcher",
            "_pattern_used": "test",
        }
        self.mock_handle_matcher.match_handle_maker.return_value = mock_handle_match

        # Should return None when handle_maker is None
        result = self.strategy.match("Test input")
        assert result is None, "Should return None when handle_maker is None"

    def test_handle_component_strategy_preserves_metadata(self):
        """Test that HandleComponentStrategy preserves all handle metadata."""
        # Setup mock handle match with full metadata
        mock_handle_match = {
            "handle_maker": "Declaration Grooming",
            "handle_model": "Washington",
            "_matched_by": "HandleMatcher",
            "_pattern_used": "declaration.*washington",
            "_source_text": "Declaration Grooming Washington handle",
        }
        self.mock_handle_matcher.match_handle_maker.return_value = mock_handle_match

        # Test metadata preservation
        result = self.strategy.match("Declaration Grooming Washington handle")
        assert result is not None, "Should return a result"
        assert (
            result.matched["_source_text"] == "Declaration Grooming Washington handle"
        ), "Should preserve source text"

    def test_handle_component_strategy_handles_invalid_input(self):
        """Test that HandleComponentStrategy handles invalid input gracefully."""
        # Test with None input
        result = self.strategy.match(None)
        assert result is None, "Should return None for None input"

        # Test with empty string
        result = self.strategy.match("")
        assert result is None, "Should return None for empty string"

        # Test with non-string input
        result = self.strategy.match(123)
        assert result is None, "Should return None for non-string input"

    def test_handle_component_strategy_fail_fast_on_handle_matcher_error(self):
        """Test that HandleComponentStrategy fails fast on HandleMatcher errors."""
        # Setup mock to raise exception
        self.mock_handle_matcher.match_handle_maker.side_effect = ValueError("Handle matcher error")

        # Should raise exception (fail fast)
        with pytest.raises(ValueError, match="Handle component matching failed"):
            self.strategy.match("Test input")

    def test_handle_component_strategy_match_type(self):
        """Test that HandleComponentStrategy has correct match_type."""
        # Setup mock handle match
        mock_handle_match = {
            "handle_maker": "Test Maker",
            "handle_model": "Test Model",
            "_matched_by": "HandleMatcher",
            "_pattern_used": "test.*pattern",
        }
        self.mock_handle_matcher.match_handle_maker.return_value = mock_handle_match

        # Test match_type
        result = self.strategy.match("Test input")
        assert result is not None, "Should return a result"
        assert result.match_type == "handle_component", "Match type should be 'handle_component'"
