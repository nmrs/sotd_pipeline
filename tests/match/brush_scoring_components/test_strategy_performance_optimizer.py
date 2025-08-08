"""Unit tests for StrategyPerformanceOptimizer component."""

from dataclasses import dataclass
from typing import Dict, List, Optional

from sotd.match.brush_scoring_components.strategy_performance_optimizer import (
    StrategyPerformanceOptimizer,
    StrategyPerformance,
    PerformanceMetrics,
)
from sotd.match.types import MatchResult


@dataclass
class MockStrategy:
    """Mock strategy for testing."""

    name: str
    execution_time: float = 0.0
    success_rate: float = 1.0
    avg_score: float = 0.8


class TestStrategyPerformanceOptimizer:
    """Test StrategyPerformanceOptimizer functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.optimizer = StrategyPerformanceOptimizer()

    def test_init_with_default_config(self):
        """Test initialization with default configuration."""
        assert self.optimizer.min_samples == 10
        assert self.optimizer.performance_window == 100
        assert self.optimizer.strategy_performances == {}

    def test_init_with_custom_config(self):
        """Test initialization with custom configuration."""
        optimizer = StrategyPerformanceOptimizer(min_samples=5, performance_window=50)
        assert optimizer.min_samples == 5
        assert optimizer.performance_window == 50

    def test_record_strategy_execution(self):
        """Test recording strategy execution metrics."""
        strategy_name = "TestStrategy"
        execution_time = 0.05
        success = True
        score = 0.85

        self.optimizer.record_strategy_execution(strategy_name, execution_time, success, score)

        assert strategy_name in self.optimizer.strategy_performances
        performance = self.optimizer.strategy_performances[strategy_name]
        assert len(performance.execution_times) == 1
        assert performance.execution_times[0] == execution_time
        assert len(performance.successes) == 1
        assert performance.successes[0] == success
        assert len(performance.scores) == 1
        assert performance.scores[0] == score

    def test_record_multiple_executions(self):
        """Test recording multiple executions for the same strategy."""
        strategy_name = "TestStrategy"

        # Record multiple executions
        self.optimizer.record_strategy_execution(strategy_name, 0.05, True, 0.85)
        self.optimizer.record_strategy_execution(strategy_name, 0.03, True, 0.90)
        self.optimizer.record_strategy_execution(strategy_name, 0.07, False, 0.60)

        performance = self.optimizer.strategy_performances[strategy_name]
        assert len(performance.execution_times) == 3
        assert len(performance.successes) == 3
        assert len(performance.scores) == 3

    def test_get_strategy_performance_insufficient_samples(self):
        """Test getting performance metrics with insufficient samples."""
        strategy_name = "TestStrategy"

        # Record fewer than min_samples
        for i in range(5):
            self.optimizer.record_strategy_execution(strategy_name, 0.05, True, 0.8)

        metrics = self.optimizer.get_strategy_performance(strategy_name)
        assert metrics is None

    def test_get_strategy_performance_sufficient_samples(self):
        """Test getting performance metrics with sufficient samples."""
        strategy_name = "TestStrategy"

        # Record sufficient samples
        for i in range(15):
            execution_time = 0.05 + (i * 0.001)
            success = i < 12  # 80% success rate
            score = 0.8 + (i * 0.01)
            self.optimizer.record_strategy_execution(strategy_name, execution_time, success, score)

        metrics = self.optimizer.get_strategy_performance(strategy_name)
        assert metrics is not None
        assert metrics.avg_execution_time > 0
        assert metrics.success_rate == 12 / 15  # 80%
        assert metrics.avg_score > 0.8

    def test_get_strategy_performance_window_limiting(self):
        """Test that performance window limits the number of samples."""
        strategy_name = "TestStrategy"
        optimizer = StrategyPerformanceOptimizer(min_samples=5, performance_window=10)

        # Record more than performance_window samples
        for i in range(15):
            optimizer.record_strategy_execution(strategy_name, 0.05, True, 0.8)

        performance = optimizer.strategy_performances[strategy_name]
        assert len(performance.execution_times) == 10  # Limited by window
        assert len(performance.successes) == 10
        assert len(performance.scores) == 10

    def test_get_optimized_execution_order(self):
        """Test getting optimized execution order based on performance."""
        # Record performance for multiple strategies
        strategies = ["FastStrategy", "SlowStrategy", "MediumStrategy"]

        # FastStrategy: fast, high success, high score
        for i in range(15):
            self.optimizer.record_strategy_execution("FastStrategy", 0.01, True, 0.9)

        # SlowStrategy: slow, low success, low score
        for i in range(15):
            self.optimizer.record_strategy_execution("SlowStrategy", 0.10, False, 0.5)

        # MediumStrategy: medium performance
        for i in range(15):
            success = i < 10  # 67% success rate
            self.optimizer.record_strategy_execution("MediumStrategy", 0.05, success, 0.7)

        optimized_order = self.optimizer.get_optimized_execution_order(strategies)

        # Should prioritize fast, high-success strategies
        assert len(optimized_order) == 3
        assert "FastStrategy" in optimized_order
        assert "MediumStrategy" in optimized_order
        assert "SlowStrategy" in optimized_order

    def test_get_optimized_execution_order_insufficient_data(self):
        """Test getting execution order with insufficient performance data."""
        strategies = ["Strategy1", "Strategy2"]

        # Record insufficient samples
        for i in range(5):
            self.optimizer.record_strategy_execution("Strategy1", 0.05, True, 0.8)

        optimized_order = self.optimizer.get_optimized_execution_order(strategies)

        # Should return original order when insufficient data
        assert optimized_order == strategies

    def test_get_optimized_execution_order_empty_list(self):
        """Test getting execution order with empty strategy list."""
        optimized_order = self.optimizer.get_optimized_execution_order([])
        assert optimized_order == []

    def test_get_performance_summary(self):
        """Test getting performance summary for all strategies."""
        # Record performance for multiple strategies
        for i in range(15):
            self.optimizer.record_strategy_execution("Strategy1", 0.05, True, 0.8)
            self.optimizer.record_strategy_execution("Strategy2", 0.03, True, 0.9)

        summary = self.optimizer.get_performance_summary()

        assert "Strategy1" in summary
        assert "Strategy2" in summary
        assert summary["Strategy1"]["avg_execution_time"] > 0
        assert summary["Strategy2"]["avg_execution_time"] > 0

    def test_get_performance_summary_no_data(self):
        """Test getting performance summary with no data."""
        summary = self.optimizer.get_performance_summary()
        assert summary == {}

    def test_clear_strategy_performance(self):
        """Test clearing performance data for a strategy."""
        strategy_name = "TestStrategy"

        # Record some data
        for i in range(15):
            self.optimizer.record_strategy_execution(strategy_name, 0.05, True, 0.8)

        assert strategy_name in self.optimizer.strategy_performances

        # Clear the data
        self.optimizer.clear_strategy_performance(strategy_name)

        assert strategy_name not in self.optimizer.strategy_performances

    def test_clear_all_performance_data(self):
        """Test clearing all performance data."""
        # Record data for multiple strategies
        for i in range(15):
            self.optimizer.record_strategy_execution("Strategy1", 0.05, True, 0.8)
            self.optimizer.record_strategy_execution("Strategy2", 0.03, True, 0.9)

        assert len(self.optimizer.strategy_performances) == 2

        # Clear all data
        self.optimizer.clear_all_performance_data()

        assert len(self.optimizer.strategy_performances) == 0

    def test_get_strategy_rankings(self):
        """Test getting strategy rankings by performance."""
        # Record performance for multiple strategies
        for i in range(15):
            self.optimizer.record_strategy_execution("FastStrategy", 0.01, True, 0.9)
            self.optimizer.record_strategy_execution("SlowStrategy", 0.10, False, 0.5)
            self.optimizer.record_strategy_execution("MediumStrategy", 0.05, True, 0.7)

        rankings = self.optimizer.get_strategy_rankings()

        assert len(rankings) == 3
        # Should be sorted by performance (fast, high-success strategies first)
        assert rankings[0]["strategy_name"] == "FastStrategy"
        assert rankings[2]["strategy_name"] == "SlowStrategy"

    def test_get_strategy_rankings_insufficient_data(self):
        """Test getting rankings with insufficient data."""
        # Record insufficient samples
        for i in range(5):
            self.optimizer.record_strategy_execution("Strategy1", 0.05, True, 0.8)

        rankings = self.optimizer.get_strategy_rankings()
        assert rankings == []


class TestStrategyPerformance:
    """Test StrategyPerformance dataclass."""

    def test_strategy_performance_creation(self):
        """Test creating StrategyPerformance instance."""
        performance = StrategyPerformance()

        assert performance.execution_times == []
        assert performance.successes == []
        assert performance.scores == []

    def test_strategy_performance_add_metrics(self):
        """Test adding metrics to StrategyPerformance."""
        performance = StrategyPerformance()

        performance.execution_times.append(0.05)
        performance.successes.append(True)
        performance.scores.append(0.8)

        assert len(performance.execution_times) == 1
        assert len(performance.successes) == 1
        assert len(performance.scores) == 1


class TestPerformanceMetrics:
    """Test PerformanceMetrics dataclass."""

    def test_performance_metrics_creation(self):
        """Test creating PerformanceMetrics instance."""
        metrics = PerformanceMetrics(
            avg_execution_time=0.05, success_rate=0.8, avg_score=0.85, total_executions=15
        )

        assert metrics.avg_execution_time == 0.05
        assert metrics.success_rate == 0.8
        assert metrics.avg_score == 0.85
        assert metrics.total_executions == 15
