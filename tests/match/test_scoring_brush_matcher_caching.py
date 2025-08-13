"""
Test extended caching functionality in ScoringBrushMatcher.

This tests that the _precompute_handle_knot_results method now includes
unified_result from FullInputComponentMatchingStrategy in the cached_results.
"""

from unittest.mock import Mock, patch

from sotd.match.scoring_brush_matcher import BrushScoringMatcher
from sotd.match.types import MatchResult


class TestScoringBrushMatcherCaching:
    """Test extended caching functionality in ScoringBrushMatcher."""

    def test_precompute_handle_knot_results_includes_unified_result(self):
        """Test that _precompute_handle_knot_results includes unified_result."""
        # Arrange
        matcher = BrushScoringMatcher()
        test_value = "Chisel and Hound Padauk Wood handle"

        # Mock the handle and knot matchers to return known results
        mock_handle_result = {"handle_maker": "Chisel and Hound", "material": "Padauk Wood"}
        mock_knot_result = Mock(spec=MatchResult)
        mock_knot_result.matched = {"model": "B2", "fiber": "boar"}

        # Mock the FullInputComponentMatchingStrategy instance
        mock_unified_strategy = Mock()
        mock_unified_strategy.match.return_value = mock_knot_result

        with (
            patch.object(
                matcher.handle_matcher, "match_handle_maker", return_value=mock_handle_result
            ),
            patch.object(matcher.knot_matcher, "match", return_value=mock_knot_result),
            patch(
                "sotd.match.brush_matching_strategies.full_input_component_matching_strategy.FullInputComponentMatchingStrategy",
                return_value=mock_unified_strategy,
            ),
        ):

            # Act
            cached_results = matcher._precompute_handle_knot_results(test_value)

            # Assert
            assert "handle_result" in cached_results
            assert "knot_result" in cached_results
            assert "unified_result" in cached_results
            assert cached_results["handle_result"] == mock_handle_result
            assert cached_results["knot_result"] == mock_knot_result
            assert cached_results["unified_result"] == mock_knot_result

    def test_precompute_handle_knot_results_handles_unified_strategy_failure(self):
        """Test that _precompute_handle_knot_results handles unified strategy failure gracefully."""
        # Arrange
        matcher = BrushScoringMatcher()
        test_value = "Test brush string"

        # Mock handle and knot matchers to succeed, but unified strategy to fail
        mock_handle_result = {"handle_maker": "Test"}
        mock_knot_result = Mock(spec=MatchResult)
        mock_knot_result.matched = {"model": "Test"}

        with (
            patch.object(
                matcher.handle_matcher, "match_handle_maker", return_value=mock_handle_result
            ),
            patch.object(matcher.knot_matcher, "match", return_value=mock_knot_result),
            patch(
                "sotd.match.brush_matching_strategies.full_input_component_matching_strategy.FullInputComponentMatchingStrategy",
                side_effect=Exception("Unified strategy failed"),
            ),
        ):

            # Act
            cached_results = matcher._precompute_handle_knot_results(test_value)

            # Assert
            assert "handle_result" in cached_results
            assert "knot_result" in cached_results
            # Should not be present on failure
            assert "unified_result" not in cached_results

    def test_precompute_handle_knot_results_handles_all_failures(self):
        """Test that _precompute_handle_knot_results handles all failures gracefully."""
        # Arrange
        matcher = BrushScoringMatcher()
        test_value = "Test brush string"

        # Mock all matchers to fail
        with (
            patch.object(
                matcher.handle_matcher, "match_handle_maker", side_effect=Exception("Handle failed")
            ),
            patch.object(matcher.knot_matcher, "match", side_effect=Exception("Knot failed")),
            patch(
                "sotd.match.brush_matching_strategies.full_input_component_matching_strategy.FullInputComponentMatchingStrategy",
                side_effect=Exception("Unified failed"),
            ),
        ):

            # Act
            cached_results = matcher._precompute_handle_knot_results(test_value)

            # Assert
            assert cached_results == {}  # Should return empty dict when all fail

    def test_precompute_handle_knot_results_preserves_existing_behavior(self):
        """Test that existing handle and knot caching behavior is preserved."""
        # Arrange
        matcher = BrushScoringMatcher()
        test_value = "Test brush string"

        # Mock only handle matcher to succeed, others to fail
        mock_handle_result = {"handle_maker": "Test"}

        with (
            patch.object(
                matcher.handle_matcher, "match_handle_maker", return_value=mock_handle_result
            ),
            patch.object(matcher.knot_matcher, "match", side_effect=Exception("Knot failed")),
            patch(
                "sotd.match.brush_matching_strategies.full_input_component_matching_strategy.FullInputComponentMatchingStrategy",
                side_effect=Exception("Unified failed"),
            ),
        ):

            # Act
            cached_results = matcher._precompute_handle_knot_results(test_value)

            # Assert
            assert "handle_result" in cached_results
            assert "knot_result" not in cached_results
            assert "unified_result" not in cached_results
            assert cached_results["handle_result"] == mock_handle_result
