"""Tests for scoring engine handle/knot score modifiers using actual matcher scores."""

from unittest.mock import Mock
import pytest

from sotd.match.brush.scoring.engine import ScoringEngine
from sotd.match.brush.config import BrushScoringConfig
from sotd.match.types import MatchResult


class TestScoringEngineHandleKnotScores:
    """Test that scoring engine uses actual matcher scores, not hardcoded base scores."""

    def setup_method(self):
        """Set up test fixtures."""
        self.config = BrushScoringConfig()
        self.engine = ScoringEngine(self.config)

    def test_handle_weight_modifier_uses_actual_handle_score(self):
        """Test that handle_weight modifier returns raw handle score."""
        # Create a mock result with handle data that has an actual score
        mock_result = Mock(spec=MatchResult)
        mock_result.matched = {
            "handle": {
                "brand": "Test Brand",
                "model": "Test Model",
                "score": 15.0,  # Actual score from handle matcher
                "priority": 1,
                "_matched_by": "HandleMatcher",
                "_pattern_used": "test_pattern",
            }
        }

        # Calculate the handle weight modifier
        result = self.engine._modifier_handle_weight("test input", mock_result, "automated_split")

        # Should return raw score (15.0), not weighted score
        # Scoring engine will apply weight: 15.0 * 0.5 = 7.5
        expected_score = 15.0
        assert result == expected_score, f"Expected {expected_score}, got {result}"

    def test_knot_weight_modifier_uses_actual_knot_score(self):
        """Test that knot_weight modifier returns raw knot score."""
        # Create a mock result with knot data that has an actual score
        mock_result = Mock(spec=MatchResult)
        mock_result.matched = {
            "knot": {
                "brand": "Test Brand",
                "model": "Test Model",
                "fiber": "Badger",
                "score": 25.0,  # Actual score from knot matcher
                "priority": 2,
                "_matched_by": "KnotMatcher",
                "_pattern_used": "test_pattern",
            }
        }

        # Calculate the knot weight modifier
        result = self.engine._modifier_knot_weight("test input", mock_result, "automated_split")

        # Should return raw score (25.0), not weighted score
        # Scoring engine will apply weight: 25.0 * 0.5 = 12.5
        expected_score = 25.0
        assert result == expected_score, f"Expected {expected_score}, got {result}"

    def test_handle_weight_modifier_with_zero_score(self):
        """Test that handle_weight modifier correctly handles zero score from matcher."""
        mock_result = Mock(spec=MatchResult)
        mock_result.matched = {
            "handle": {
                "brand": None,
                "model": None,
                "score": 0.0,  # Zero score from handle matcher
                "priority": None,
                "_matched_by": "HandleMatcher",
                "_pattern_used": "no_match",
            }
        }

        result = self.engine._modifier_handle_weight("test input", mock_result, "automated_split")

        # Should return raw score (0.0)
        # Scoring engine will apply weight: 0.0 * 0.5 = 0.0
        expected_score = 0.0
        assert result == expected_score, f"Expected {expected_score}, got {result}"

    def test_knot_weight_modifier_with_zero_score(self):
        """Test that knot_weight modifier correctly handles zero score from matcher."""
        mock_result = Mock(spec=MatchResult)
        mock_result.matched = {
            "knot": {
                "brand": None,
                "model": None,
                "fiber": None,
                "score": 0.0,  # Zero score from knot matcher
                "priority": None,
                "_matched_by": "KnotMatcher",
                "_pattern_used": "no_match",
            }
        }

        result = self.engine._modifier_knot_weight("test input", mock_result, "automated_split")

        # Should return raw score (0.0)
        # Scoring engine will apply weight: 0.0 * 0.5 = 0.0
        expected_score = 0.0
        assert result == expected_score, f"Expected {expected_score}, got {result}"

    def test_handle_weight_modifier_fails_fast_without_score_field(self):
        """Test that handle_weight modifier fails fast when score field is missing."""
        mock_result = Mock(spec=MatchResult)
        mock_result.matched = {
            "handle": {
                "brand": "Test Brand",
                "model": "Test Model",
                # No score field - should fail fast
                "priority": 1,
                "_matched_by": "HandleMatcher",
                "_pattern_used": "test_pattern",
            }
        }

        # Should raise ValueError when score field is missing
        with pytest.raises(
            ValueError, match="Handle matcher missing score for strategy automated_split"
        ):
            self.engine._modifier_handle_weight("test input", mock_result, "automated_split")

    def test_knot_weight_modifier_fails_fast_without_score_field(self):
        """Test that knot_weight modifier fails fast when score field is missing."""
        mock_result = Mock(spec=MatchResult)
        mock_result.matched = {
            "knot": {
                "brand": "Test Brand",
                "model": "Test Model",
                "fiber": "Badger",
                # No score field - should fail fast
                "priority": 2,
                "_matched_by": "KnotMatcher",
                "_pattern_used": "test_pattern",
            }
        }

        # Should raise ValueError when score field is missing
        with pytest.raises(
            ValueError, match="Knot matcher missing score for strategy automated_split"
        ):
            self.engine._modifier_knot_weight("test input", mock_result, "automated_split")
