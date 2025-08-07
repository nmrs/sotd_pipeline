"""
Unit tests for brush scoring matcher components.

Tests individual components with single responsibilities and improved architecture.
"""

import pytest
from unittest.mock import Mock, patch
from typing import List, Optional

from sotd.match.brush_scoring_components.correct_matches_matcher import CorrectMatchesMatcher
from sotd.match.brush_scoring_components.strategy_orchestrator import StrategyOrchestrator
from sotd.match.brush_scoring_components.scoring_engine import ScoringEngine
from sotd.match.brush_scoring_components.result_processor import ResultProcessor
from sotd.match.brush_scoring_components.performance_monitor import PerformanceMonitor
from sotd.match.types import MatchResult


class TestCorrectMatchesMatcher:
    """Test the CorrectMatchesMatcher component."""

    def test_init_with_correct_matches_data(self):
        """Test initialization with correct matches data."""
        correct_matches_data = {"brush": {"test": "data"}}
        matcher = CorrectMatchesMatcher(correct_matches_data)
        assert matcher.correct_matches == correct_matches_data

    def test_match_exact_match(self):
        """Test exact match against correct matches."""
        correct_matches_data = {"brush": {"Simpson": {"Chubby 2": ["simpson chubby 2"]}}}
        matcher = CorrectMatchesMatcher(correct_matches_data)
        result = matcher.match("simpson chubby 2")

        assert result is not None
        assert result.matched["brand"] == "Simpson"
        assert result.matched["model"] == "Chubby 2"

    def test_match_no_match(self):
        """Test when no exact match is found."""
        correct_matches_data = {"brush": {}}
        matcher = CorrectMatchesMatcher(correct_matches_data)
        result = matcher.match("unknown brush")

        assert result is None

    def test_match_case_insensitive(self):
        """Test case-insensitive matching."""
        correct_matches_data = {"brush": {"Simpson": {"Chubby 2": ["simpson chubby 2"]}}}
        matcher = CorrectMatchesMatcher(correct_matches_data)
        result = matcher.match("SIMPSON CHUBBY 2")

        assert result is not None
        assert result.matched["brand"] == "Simpson"

    def test_match_empty_input(self):
        """Test matching with empty input."""
        correct_matches_data = {"brush": {}}
        matcher = CorrectMatchesMatcher(correct_matches_data)
        result = matcher.match("")

        assert result is None


class TestStrategyOrchestrator:
    """Test the StrategyOrchestrator component."""

    def test_init_with_strategies(self):
        """Test initialization with strategies."""
        strategies = [Mock(), Mock()]
        orchestrator = StrategyOrchestrator(strategies)
        assert orchestrator.strategies == strategies

    def test_run_all_strategies(self):
        """Test running all strategies."""
        mock_strategy1 = Mock()
        mock_strategy1.match.return_value = MatchResult(
            original="test", matched={"brand": "Test1"}, match_type="exact", pattern="test1"
        )

        mock_strategy2 = Mock()
        mock_strategy2.match.return_value = MatchResult(
            original="test", matched={"brand": "Test2"}, match_type="exact", pattern="test2"
        )

        strategies = [mock_strategy1, mock_strategy2]
        orchestrator = StrategyOrchestrator(strategies)

        results = orchestrator.run_all_strategies("test brush")

        assert len(results) == 2
        assert results[0].matched["brand"] == "Test1"
        assert results[1].matched["brand"] == "Test2"

        mock_strategy1.match.assert_called_once_with("test brush")
        mock_strategy2.match.assert_called_once_with("test brush")

    def test_run_all_strategies_with_none_results(self):
        """Test running strategies that return None."""
        mock_strategy1 = Mock()
        mock_strategy1.match.return_value = None

        mock_strategy2 = Mock()
        mock_strategy2.match.return_value = MatchResult(
            original="test", matched={"brand": "Test2"}, match_type="exact", pattern="test2"
        )

        strategies = [mock_strategy1, mock_strategy2]
        orchestrator = StrategyOrchestrator(strategies)

        results = orchestrator.run_all_strategies("test brush")

        assert len(results) == 1
        assert results[0].matched["brand"] == "Test2"

    def test_run_all_strategies_empty_list(self):
        """Test running with empty strategy list."""
        orchestrator = StrategyOrchestrator([])
        results = orchestrator.run_all_strategies("test brush")

        assert results == []


class TestScoringEngine:
    """Test the ScoringEngine component."""

    def test_init_with_config(self):
        """Test initialization with configuration."""
        mock_config = Mock()
        engine = ScoringEngine(mock_config)
        assert engine.config == mock_config

    def test_score_results(self):
        """Test scoring strategy results."""
        mock_config = Mock()
        mock_config.get_base_strategy_score.return_value = 80.0
        mock_config.get_strategy_modifier.return_value = 5.0
        mock_config.get_all_modifier_names.return_value = ["test_modifier"]

        engine = ScoringEngine(mock_config)

        results = [
            MatchResult(
                original="test", matched={"brand": "Test1"}, match_type="exact", pattern="test1"
            ),
            MatchResult(
                original="test", matched={"brand": "Test2"}, match_type="exact", pattern="test2"
            ),
        ]

        scored_results = engine.score_results(results, "test brush")

        assert len(scored_results) == 2
        assert all(hasattr(result, "score") for result in scored_results)
        assert all(result.score > 0 for result in scored_results)

    def test_get_best_result(self):
        """Test getting the best result."""
        mock_config = Mock()
        engine = ScoringEngine(mock_config)

        # Create results with different scores
        result1 = Mock()
        result1.score = 85.0

        result2 = Mock()
        result2.score = 90.0

        result3 = Mock()
        result3.score = 75.0

        scored_results = [result1, result2, result3]
        best_result = engine.get_best_result(scored_results)

        assert best_result == result2  # Highest score

    def test_get_best_result_empty_list(self):
        """Test getting best result from empty list."""
        mock_config = Mock()
        engine = ScoringEngine(mock_config)

        best_result = engine.get_best_result([])
        assert best_result is None

    def test_score_results_with_modifiers(self):
        """Test scoring with strategy modifiers."""
        mock_config = Mock()
        mock_config.get_base_strategy_score.return_value = 80.0
        mock_config.get_strategy_modifier.return_value = 10.0
        mock_config.get_all_modifier_names.return_value = ["test_modifier"]

        engine = ScoringEngine(mock_config)

        result = MatchResult(
            original="test",
            matched={"brand": "Test", "fiber": "badger"},
            match_type="exact",
            pattern="test",
        )

        scored_results = engine.score_results([result], "test brush")

        assert len(scored_results) == 1
        assert scored_results[0].score >= 80.0  # Base score plus modifiers


class TestResultProcessor:
    """Test the ResultProcessor component."""

    def test_process_result_with_valid_result(self):
        """Test processing a valid result."""
        processor = ResultProcessor()

        result = MatchResult(
            original="test brush",
            matched={"brand": "Test", "model": "Brush"},
            match_type="exact",
            pattern="test",
        )

        processed_result = processor.process_result(result, "test brush")

        assert processed_result == result
        assert processed_result.original == "test brush"

    def test_process_result_with_none(self):
        """Test processing None result."""
        processor = ResultProcessor()

        processed_result = processor.process_result(None, "test brush")

        assert processed_result is None

    def test_process_result_ensures_consistency(self):
        """Test that processing ensures output format consistency."""
        processor = ResultProcessor()

        # Create result with missing fields
        result = MatchResult(
            original="test brush", matched={"brand": "Test"}, match_type="exact", pattern="test"
        )

        processed_result = processor.process_result(result, "test brush")

        # Should have consistent structure
        assert hasattr(processed_result, "original")
        assert hasattr(processed_result, "matched")
        assert hasattr(processed_result, "match_type")
        assert hasattr(processed_result, "pattern")


class TestPerformanceMonitor:
    """Test the PerformanceMonitor component."""

    def test_record_strategy_timing(self):
        """Test recording strategy timing."""
        monitor = PerformanceMonitor()

        monitor.record_strategy_timing("test_strategy", 0.1)
        monitor.record_strategy_timing("test_strategy", 0.2)

        stats = monitor.get_performance_stats()
        assert "test_strategy" in stats
        assert stats["test_strategy"]["count"] == 2
        assert abs(stats["test_strategy"]["total_time"] - 0.3) < 0.001

    def test_get_performance_stats(self):
        """Test getting performance statistics."""
        monitor = PerformanceMonitor()

        # Record some timing data
        monitor.record_strategy_timing("strategy1", 0.1)
        monitor.record_strategy_timing("strategy2", 0.2)
        monitor.record_strategy_timing("strategy1", 0.15)

        stats = monitor.get_performance_stats()

        assert "strategy1" in stats
        assert "strategy2" in stats
        assert stats["strategy1"]["count"] == 2
        assert stats["strategy2"]["count"] == 1
        assert stats["strategy1"]["total_time"] == 0.25
        assert stats["strategy2"]["total_time"] == 0.2

    def test_get_performance_stats_empty(self):
        """Test getting performance stats when no data recorded."""
        monitor = PerformanceMonitor()
        stats = monitor.get_performance_stats()

        assert stats == {}

    def test_record_strategy_timing_negative_time(self):
        """Test recording negative timing (should be ignored)."""
        monitor = PerformanceMonitor()

        monitor.record_strategy_timing("test_strategy", -0.1)

        stats = monitor.get_performance_stats()
        assert "test_strategy" not in stats

    def test_performance_stats_structure(self):
        """Test that performance stats have correct structure."""
        monitor = PerformanceMonitor()

        monitor.record_strategy_timing("test_strategy", 0.1)
        stats = monitor.get_performance_stats()

        strategy_stats = stats["test_strategy"]
        assert "count" in strategy_stats
        assert "total_time" in strategy_stats
        assert "average_time" in strategy_stats
        assert "min_time" in strategy_stats
        assert "max_time" in strategy_stats

        assert strategy_stats["count"] == 1
        assert strategy_stats["total_time"] == 0.1
        assert strategy_stats["average_time"] == 0.1
        assert strategy_stats["min_time"] == 0.1
        assert strategy_stats["max_time"] == 0.1
