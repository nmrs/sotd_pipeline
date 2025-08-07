#!/usr/bin/env python3
"""Tests for HandleMatcher integration with BrushScoringMatcher."""

import pytest
from unittest.mock import Mock, patch
from pathlib import Path

from sotd.match.scoring_brush_matcher import BrushScoringMatcher
from sotd.match.types import MatchResult


class TestHandleMatcherIntegration:
    """Test that scoring system integrates HandleMatcher correctly."""

    def test_handle_matcher_initialized(self):
        """Test that HandleMatcher is initialized in BrushScoringMatcher."""
        matcher = BrushScoringMatcher()

        # Should have HandleMatcher instance
        assert hasattr(
            matcher, "handle_matcher"
        ), "BrushScoringMatcher should have handle_matcher attribute"
        assert matcher.handle_matcher is not None, "HandleMatcher should be initialized"

    def test_handle_matcher_receives_config(self):
        """Test that HandleMatcher receives proper configuration."""
        with patch("sotd.match.handle_matcher.HandleMatcher") as mock_handle_matcher:
            matcher = BrushScoringMatcher()

            # Verify HandleMatcher was called with proper config
            mock_handle_matcher.assert_called_once()
            call_args = mock_handle_matcher.call_args
            # HandleMatcher takes handles_path as first positional argument
            assert len(call_args[0]) > 0, "HandleMatcher should receive handles_path as argument"
            handles_path = call_args[0][0]
            assert str(handles_path).endswith("handles.yaml"), "Should pass handles.yaml path"

    def test_composite_brush_matching_with_handle_matcher(self):
        """Test that composite brushes are matched using HandleMatcher."""
        # Test with a composite brush that requires HandleMatcher
        test_input = "Summer Break Soaps Maize 26mm Timberwolf"

        matcher = BrushScoringMatcher()
        result = matcher.match(test_input)

        # Should match successfully (HandleMatcher should handle this)
        assert result is not None, "Should return a MatchResult"
        assert result.matched is not None, "Should have matched data"

        # Should have handle section in matched data
        assert "handle" in result.matched, "Should have handle section for composite brush"
        handle_data = result.matched["handle"]
        assert handle_data.get("lanbrand") == "Summer Break", "Should match Summer Break brand"

    def test_handle_matcher_integration_with_scoring(self):
        """Test that HandleMatcher results are properly scored and ranked."""
        # Test with multiple possible matches to verify scoring
        test_input = "Mountain Hare Shaving - Maple Burl and Resin Badger"

        matcher = BrushScoringMatcher()
        result = matcher.match(test_input)

        # Should match successfully
        assert result is not None, "Should return a MatchResult"
        assert result.matched is not None, "Should have matched data"

        # Should have proper scoring applied
        assert hasattr(result, "score"), "Result should have score attribute"
        assert result.score > 0, "Should have positive score"

    def test_handle_matcher_fallback_behavior(self):
        """Test that HandleMatcher works as fallback when brush strategies fail."""
        # Test with input that brush strategies can't handle but HandleMatcher can
        test_input = "Maggard 22mm synth"

        matcher = BrushScoringMatcher()
        result = matcher.match(test_input)

        # Should match successfully via HandleMatcher
        assert result is not None, "Should return a MatchResult"
        assert result.matched is not None, "Should have matched data"

        # Should have handle section
        assert "handle" in result.matched, "Should have handle section"
        handle_data = result.matched["handle"]
        assert handle_data.get("brand") == "Maggard", "Should match Maggard brand"

    def test_handle_matcher_coordination_with_brush_strategies(self):
        """Test that HandleMatcher coordinates properly with brush strategies."""
        # Test with input that could match both brush strategies and HandleMatcher
        test_input = "Zenith - r/Wetshaving exclusive MOAR BOAR (31 mm × 57 mm bleached boar)"

        matcher = BrushScoringMatcher()
        result = matcher.match(test_input)

        # Should match successfully (brush strategies should take priority)
        assert result is not None, "Should return a MatchResult"
        assert result.matched is not None, "Should have matched data"

        # Should have proper structure
        assert "handle" in result.matched, "Should have handle section"
        assert "knot" in result.matched, "Should have knot section"

    def test_handle_matcher_error_handling(self):
        """Test that HandleMatcher errors are handled gracefully."""
        # Test with invalid input that might cause HandleMatcher errors
        test_input = ""

        matcher = BrushScoringMatcher()
        result = matcher.match(test_input)

        # Should handle gracefully (return None for empty input)
        # Empty input should return None, not crash
        assert result is None, "Should return None for empty input"


if __name__ == "__main__":
    pytest.main([__file__])
