#!/usr/bin/env python3
"""Tests for KnotMatcher integration with BrushScoringMatcher."""

import pytest
from unittest.mock import Mock, patch
from pathlib import Path

from sotd.match.scoring_brush_matcher import BrushScoringMatcher
from sotd.match.types import MatchResult


class TestKnotMatcherIntegration:
    """Test that scoring system integrates KnotMatcher correctly."""

    def test_knot_matcher_initialized(self):
        """Test that KnotMatcher is initialized in BrushScoringMatcher."""
        matcher = BrushScoringMatcher()

        # Should have KnotMatcher instance
        assert hasattr(
            matcher, "knot_matcher"
        ), "BrushScoringMatcher should have knot_matcher attribute"
        assert matcher.knot_matcher is not None, "KnotMatcher should be initialized"

    def test_knot_matcher_receives_config(self):
        """Test that KnotMatcher receives proper configuration."""
        with patch("sotd.match.knot_matcher.KnotMatcher") as mock_knot_matcher:
            matcher = BrushScoringMatcher()

            # Verify KnotMatcher was called with proper config
            mock_knot_matcher.assert_called_once()
            call_args = mock_knot_matcher.call_args
            # KnotMatcher takes knot strategies as first positional argument
            assert len(call_args[0]) > 0, "KnotMatcher should receive knot strategies as argument"

    def test_composite_brush_matching_with_knot_matcher(self):
        """Test that composite brushes are matched using KnotMatcher."""
        # Test with a composite brush that requires KnotMatcher
        test_input = "Summer Break Soaps Maize 26mm Timberwolf"

        matcher = BrushScoringMatcher()
        result = matcher.match(test_input)

        # Should match successfully (KnotMatcher should handle this)
        assert result is not None, "Should return a MatchResult"
        assert result.matched is not None, "Should have matched data"

        # Should have knot section in matched data
        assert "knot" in result.matched, "Should have knot section for composite brush"
        knot_data = result.matched["knot"]
        # Should have fiber information from KnotMatcher
        assert knot_data.get("fiber") is not None, "Should have fiber information"

    def test_knot_matcher_integration_with_scoring(self):
        """Test that KnotMatcher results are properly scored and ranked."""
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

    def test_knot_matcher_coordination_with_handle_matcher(self):
        """Test that KnotMatcher coordinates properly with HandleMatcher."""
        # Test with input that requires both HandleMatcher and KnotMatcher
        test_input = "Declaration Grooming Washington 26mm Badger"

        matcher = BrushScoringMatcher()
        result = matcher.match(test_input)

        # Should match successfully
        assert result is not None, "Should return a MatchResult"
        assert result.matched is not None, "Should have matched data"

        # Should have both handle and knot sections
        assert "handle" in result.matched, "Should have handle section"
        assert "knot" in result.matched, "Should have knot section"

        # Handle section should have brand/model
        handle_data = result.matched["handle"]
        assert handle_data.get("brand") is not None, "Handle should have brand"

        # Knot section should have fiber information
        knot_data = result.matched["knot"]
        assert knot_data.get("fiber") is not None, "Knot should have fiber"

    def test_knot_matcher_fallback_behavior(self):
        """Test that KnotMatcher works as fallback when brush strategies fail."""
        # Test with input that brush strategies can't handle but KnotMatcher can
        test_input = "Custom Handle with 24mm Synthetic Knot"

        matcher = BrushScoringMatcher()
        result = matcher.match(test_input)

        # Should match successfully via KnotMatcher
        assert result is not None, "Should return a MatchResult"
        assert result.matched is not None, "Should have matched data"

        # Should have knot section
        assert "knot" in result.matched, "Should have knot section"
        knot_data = result.matched["knot"]
        assert knot_data.get("fiber") == "Synthetic", "Should match Synthetic fiber"

    def test_knot_matcher_error_handling(self):
        """Test that KnotMatcher errors are handled gracefully."""
        # Test with invalid input that might cause KnotMatcher errors
        test_input = ""

        matcher = BrushScoringMatcher()
        result = matcher.match(test_input)

        # Should handle gracefully (return None for empty input)
        # Empty input should return None, not crash
        assert result is None, "Should return None for empty input"

    def test_knot_matcher_with_fiber_detection(self):
        """Test that KnotMatcher properly detects fiber types."""
        # Test with different fiber types
        test_cases = [
            ("24mm Badger", "Badger"),
            ("26mm Boar", "Boar"),
            ("22mm Synthetic", "Synthetic"),
        ]

        matcher = BrushScoringMatcher()

        for test_input, expected_fiber in test_cases:
            result = matcher.match(test_input)

            # Should match successfully
            assert result is not None, f"Should match: {test_input}"
            assert result.matched is not None, f"Should have matched data: {test_input}"

            # Should have correct fiber in knot section
            knot_data = result.matched.get("knot", {})
            actual_fiber = knot_data.get("fiber")
            assert actual_fiber == expected_fiber, f"Expected {expected_fiber}, got {actual_fiber} for {test_input}"


if __name__ == "__main__":
    pytest.main([__file__]) 