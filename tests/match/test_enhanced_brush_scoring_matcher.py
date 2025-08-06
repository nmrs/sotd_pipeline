"""
Unit tests for enhanced BrushScoringMatcher.

Tests the full implementation that uses all brush scoring components.
"""

import pytest
from unittest.mock import Mock, patch
from pathlib import Path

from sotd.match.scoring_brush_matcher import BrushScoringMatcher
from sotd.match.types import MatchResult


class TestEnhancedBrushScoringMatcher:
    """Test the enhanced BrushScoringMatcher class."""

    def test_init_with_default_config(self):
        """Test initialization with default configuration."""
        matcher = BrushScoringMatcher()
        assert matcher.config is not None
        assert matcher.correct_matches_matcher is not None
        assert matcher.strategy_orchestrator is not None
        assert matcher.scoring_engine is not None
        assert matcher.result_processor is not None
        assert matcher.performance_monitor is not None

    def test_init_with_custom_config_path(self):
        """Test initialization with custom config path."""
        custom_path = Path("/test/config.yaml")
        matcher = BrushScoringMatcher(config_path=custom_path)
        assert matcher.config.config_path == custom_path

    def test_match_with_correct_matches_hit(self):
        """Test matching when correct matches matcher finds a match."""
        # Mock correct matches data
        correct_matches_data = {"brush": {"Simpson": {"Chubby 2": ["simpson chubby 2"]}}}

        with patch(
            "sotd.match.scoring_brush_matcher.load_correct_matches",
            return_value=correct_matches_data,
        ):
            matcher = BrushScoringMatcher()
            result = matcher.match("simpson chubby 2")

            assert result is not None
            assert result.matched["brand"] == "Simpson"
            assert result.matched["model"] == "Chubby 2"
            assert result.match_type == "exact"

    def test_match_with_strategy_fallback(self):
        """Test matching when correct matches fails but strategies succeed."""
        # Mock empty correct matches
        correct_matches_data = {"brush": {}}

        # Mock strategy that returns a result
        mock_strategy = Mock()
        mock_strategy.match.return_value = MatchResult(
            original="test brush",
            matched={"brand": "Test", "model": "Brush"},
            match_type="strategy",
            pattern="test",
        )

        with patch(
            "sotd.match.scoring_brush_matcher.load_correct_matches",
            return_value=correct_matches_data,
        ):
            with patch(
                "sotd.match.scoring_brush_matcher.BrushScoringMatcher._create_strategies",
                return_value=[mock_strategy],
            ):
                matcher = BrushScoringMatcher()
                result = matcher.match("test brush")

                assert result is not None
                assert result.matched["brand"] == "Test"
                assert result.matched["model"] == "Brush"

    def test_match_with_no_results(self):
        """Test matching when no strategies return results."""
        # Mock empty correct matches
        correct_matches_data = {"brush": {}}

        # Mock strategy that returns None
        mock_strategy = Mock()
        mock_strategy.match.return_value = None

        with patch(
            "sotd.match.scoring_brush_matcher.load_correct_matches",
            return_value=correct_matches_data,
        ):
            with patch(
                "sotd.match.scoring_brush_matcher.BrushScoringMatcher._create_strategies",
                return_value=[mock_strategy],
            ):
                matcher = BrushScoringMatcher()
                result = matcher.match("unknown brush")

                assert result is None

    def test_match_performance_monitoring(self):
        """Test that performance monitoring is active during matching."""
        correct_matches_data = {"brush": {}}

        with patch(
            "sotd.match.scoring_brush_matcher.load_correct_matches",
            return_value=correct_matches_data,
        ):
            matcher = BrushScoringMatcher()

            # Mock performance monitor to track calls
            mock_monitor = Mock()
            matcher.performance_monitor = mock_monitor

            result = matcher.match("test brush")

            # Verify performance monitoring was used
            assert mock_monitor.start_timing.called
            assert mock_monitor.end_timing.called

    def test_get_cache_stats(self):
        """Test getting cache statistics."""
        matcher = BrushScoringMatcher()
        stats = matcher.get_cache_stats()

        # Should return a dictionary with performance stats
        assert isinstance(stats, dict)
        assert "performance" in stats

    def test_get_cache_stats_includes_performance(self):
        """Test that cache stats include performance data."""
        matcher = BrushScoringMatcher()

        # Mock performance monitor
        mock_monitor = Mock()
        mock_monitor.get_performance_stats.return_value = {"test": "data"}
        matcher.performance_monitor = mock_monitor

        stats = matcher.get_cache_stats()

        assert "performance" in stats
        assert stats["performance"] == {"test": "data"}

    def test_match_with_multiple_strategies(self):
        """Test matching with multiple strategies returning different results."""
        correct_matches_data = {"brush": {}}

        # Create multiple mock strategies
        mock_strategy1 = Mock()
        mock_strategy1.match.return_value = MatchResult(
            original="test brush",
            matched={"brand": "Test1", "model": "Brush1"},
            match_type="strategy1",
            pattern="test1",
        )

        mock_strategy2 = Mock()
        mock_strategy2.match.return_value = MatchResult(
            original="test brush",
            matched={"brand": "Test2", "model": "Brush2"},
            match_type="strategy2",
            pattern="test2",
        )

        with patch(
            "sotd.match.scoring_brush_matcher.load_correct_matches",
            return_value=correct_matches_data,
        ):
            with patch(
                "sotd.match.scoring_brush_matcher.BrushScoringMatcher._create_strategies",
                return_value=[mock_strategy1, mock_strategy2],
            ):
                matcher = BrushScoringMatcher()
                result = matcher.match("test brush")

                # Should get a result (the highest scoring one)
                assert result is not None
                assert result.matched["brand"] in ["Test1", "Test2"]

    def test_match_error_handling(self):
        """Test error handling during matching."""
        correct_matches_data = {"brush": {}}

        # Mock strategy that raises an exception
        mock_strategy = Mock()
        mock_strategy.match.side_effect = Exception("Test error")

        with patch(
            "sotd.match.scoring_brush_matcher.load_correct_matches",
            return_value=correct_matches_data,
        ):
            with patch(
                "sotd.match.scoring_brush_matcher.BrushScoringMatcher._create_strategies",
                return_value=[mock_strategy],
            ):
                matcher = BrushScoringMatcher()

                # Should handle errors gracefully and return None
                result = matcher.match("test brush")
                assert result is None

    def test_match_with_scoring(self):
        """Test that scoring is applied to strategy results."""
        correct_matches_data = {"brush": {}}

        # Mock strategy that returns a result
        mock_strategy = Mock()
        mock_strategy.match.return_value = MatchResult(
            original="test brush",
            matched={"brand": "Test", "model": "Brush"},
            match_type="test_strategy",
            pattern="test",
        )

        with patch(
            "sotd.match.scoring_brush_matcher.load_correct_matches",
            return_value=correct_matches_data,
        ):
            with patch(
                "sotd.match.scoring_brush_matcher.BrushScoringMatcher._create_strategies",
                return_value=[mock_strategy],
            ):
                matcher = BrushScoringMatcher()

                # Mock scoring engine
                mock_engine = Mock()
                mock_engine.score_results.return_value = [mock_strategy.match.return_value]
                mock_engine.get_best_result.return_value = mock_strategy.match.return_value
                matcher.scoring_engine = mock_engine

                result = matcher.match("test brush")

                # Verify scoring was applied
                assert mock_engine.score_results.called
                assert mock_engine.get_best_result.called
                assert result is not None

    def test_match_result_processing(self):
        """Test that results are processed before returning."""
        correct_matches_data = {"brush": {}}

        # Mock strategy that returns a result
        mock_strategy = Mock()
        mock_strategy.match.return_value = MatchResult(
            original="test brush",
            matched={"brand": "Test", "model": "Brush"},
            match_type="test_strategy",
            pattern="test",
        )

        with patch(
            "sotd.match.scoring_brush_matcher.load_correct_matches",
            return_value=correct_matches_data,
        ):
            with patch(
                "sotd.match.scoring_brush_matcher.BrushScoringMatcher._create_strategies",
                return_value=[mock_strategy],
            ):
                matcher = BrushScoringMatcher()

                # Mock result processor
                mock_processor = Mock()
                mock_processor.process_result.return_value = mock_strategy.match.return_value
                matcher.result_processor = mock_processor

                result = matcher.match("test brush")

                # Verify result processing was applied
                assert mock_processor.process_result.called
                assert result is not None

    def test_match_empty_input(self):
        """Test matching with empty input."""
        matcher = BrushScoringMatcher()
        result = matcher.match("")

        assert result is None

    def test_match_none_input(self):
        """Test matching with None input."""
        matcher = BrushScoringMatcher()
        result = matcher.match(None)

        assert result is None
