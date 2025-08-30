"""Tests for scoring engine handle/knot score modifiers using actual matcher scores."""

from unittest.mock import Mock

from sotd.match.brush_scoring_components.scoring_engine import ScoringEngine
from sotd.match.brush_scoring_config import BrushScoringConfig
from sotd.match.types import MatchResult


class TestScoringEngineHandleKnotScores:
    """Test that scoring engine uses actual matcher scores, not hardcoded base scores."""

    def setup_method(self):
        """Set up test fixtures."""
        self.config = BrushScoringConfig()
        self.engine = ScoringEngine(self.config)

    def test_handle_weight_modifier_uses_actual_handle_score(self):
        """Test that handle_weight modifier uses actual handle matcher score, not hardcoded 50.0."""
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

        # The result should be based on the actual score (15.0), not hardcoded 50.0
        # weight = 0.5 (from config), score = 15.0 + priority_bonus
        # priority_bonus = max(0, 3 - 1 + 1) = 3
        # total_score = 15.0 + 3 = 18.0
        # result = 0.5 * 18.0 = 9.0
        expected_score = 9.0
        assert result == expected_score, f"Expected {expected_score}, got {result}"

    def test_knot_weight_modifier_uses_actual_knot_score(self):
        """Test that knot_weight modifier uses actual knot matcher score, not hardcoded 50.0."""
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

        # The result should be based on the actual score (25.0), not hardcoded 50.0
        # weight = 0.5 (from config), score = 25.0 + priority_bonus
        # priority_bonus = max(0, 3 - 2 + 1) = 2
        # total_score = 25.0 + 2 = 27.0
        # result = 0.5 * 27.0 = 13.5
        expected_score = 13.5
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

        # With zero score, should get minimal result
        # weight = 0.5, score = 0.0 + priority_bonus (0)
        # total_score = 0.0
        # result = 0.5 * 0.0 = 0.0
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

        # With zero score, should get minimal result
        # weight = 0.5, score = 0.0 + priority_bonus (0)
        # total_score = 0.0
        # result = 0.5 * 0.0 = 0.0
        expected_score = 0.0
        assert result == expected_score, f"Expected {expected_score}, got {result}"

    def test_handle_weight_modifier_without_score_field(self):
        """Test that handle_weight modifier gracefully handles missing score field."""
        mock_result = Mock(spec=MatchResult)
        mock_result.matched = {
            "handle": {
                "brand": "Test Brand",
                "model": "Test Model",
                # No score field - should fall back to base score
                "priority": 1,
                "_matched_by": "HandleMatcher",
                "_pattern_used": "test_pattern",
            }
        }

        result = self.engine._modifier_handle_weight("test input", mock_result, "automated_split")

        # Should fall back to base score when score field is missing
        # weight = 0.5, score = base_score (50.0) + priority_bonus (3)
        # total_score = 53.0
        # result = 0.5 * 53.0 = 26.5
        expected_score = 26.5
        assert result == expected_score, f"Expected {expected_score}, got {result}"

    def test_knot_weight_modifier_without_score_field(self):
        """Test that knot_weight modifier gracefully handles missing score field."""
        mock_result = Mock(spec=MatchResult)
        mock_result.matched = {
            "knot": {
                "brand": "Test Brand",
                "model": "Test Model",
                "fiber": "Badger",
                # No score field - should fall back to base score
                "priority": 2,
                "_matched_by": "KnotMatcher",
                "_pattern_used": "test_pattern",
            }
        }

        result = self.engine._modifier_knot_weight("test input", mock_result, "automated_split")

        # Should fall back to base score when score field is missing
        # weight = 0.5, score = base_score (50.0) + priority_bonus (2)
        # total_score = 52.0
        # result = 0.5 * 52.0 = 26.0
        expected_score = 26.0
        assert result == expected_score, f"Expected {expected_score}, got {result}"
