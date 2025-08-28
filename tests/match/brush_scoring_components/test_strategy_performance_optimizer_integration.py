"""Integration tests for StrategyPerformanceOptimizer in scoring engine."""

from sotd.match.brush_scoring_components.strategy_performance_optimizer import (
    StrategyPerformanceOptimizer,
)
from sotd.match.brush_matcher import BrushScoringMatcher


class TestStrategyPerformanceOptimizerIntegration:
    """Test StrategyPerformanceOptimizer integration with scoring engine."""

    def setup_method(self):
        """Set up test fixtures."""
        self.matcher = BrushScoringMatcher()
        self.performance_optimizer = StrategyPerformanceOptimizer()

    def test_integration_with_strategy_execution_tracking(self):
        """Test that performance optimizer can track strategy execution metrics."""
        # Use a smaller performance window for testing
        optimizer = StrategyPerformanceOptimizer(min_samples=5, performance_window=20)
        strategy_name = "TestStrategy"

        # Record multiple executions with varying performance
        for i in range(10):
            optimizer.record_strategy_execution(strategy_name, 0.05, True, 0.85)

        # Add a few more with different characteristics
        optimizer.record_strategy_execution(strategy_name, 0.03, True, 0.90)
        optimizer.record_strategy_execution(strategy_name, 0.07, False, 0.60)
        optimizer.record_strategy_execution(strategy_name, 0.04, True, 0.88)
        optimizer.record_strategy_execution(strategy_name, 0.06, True, 0.82)

        # Get performance metrics
        metrics = optimizer.get_strategy_performance(strategy_name)

        assert metrics is not None
        assert metrics.avg_execution_time > 0
        assert metrics.success_rate > 0.8  # Should be high success rate
        assert metrics.avg_score > 0.8  # Average of successful scores

    def test_integration_optimized_execution_order(self):
        """Test that performance optimizer provides optimized execution order."""
        strategies = ["FastAccurate", "SlowAccurate", "FastInaccurate"]

        # Record performance data for each strategy
        for i in range(15):
            # FastAccurate: fast, high success, high score
            self.performance_optimizer.record_strategy_execution("FastAccurate", 0.01, True, 0.9)
            # SlowAccurate: slow, high success, high score
            self.performance_optimizer.record_strategy_execution("SlowAccurate", 0.15, True, 0.95)
            # FastInaccurate: fast, low success, low score
            self.performance_optimizer.record_strategy_execution("FastInaccurate", 0.01, False, 0.3)

        # Get optimized execution order
        optimized_order = self.performance_optimizer.get_optimized_execution_order(strategies)

        # Should prioritize accuracy over speed
        assert len(optimized_order) == 3
        assert "SlowAccurate" in optimized_order  # Highest success rate and score
        assert "FastAccurate" in optimized_order  # Good accuracy, fast
        assert "FastInaccurate" in optimized_order  # Fast but wrong

    def test_integration_performance_monitoring(self):
        """Test performance monitoring and slow strategy identification."""
        # Record performance for strategies with different speeds
        for i in range(15):
            self.performance_optimizer.record_strategy_execution("FastStrategy", 0.01, True, 0.8)
            self.performance_optimizer.record_strategy_execution("SlowStrategy", 0.12, True, 0.9)
            self.performance_optimizer.record_strategy_execution("MediumStrategy", 0.05, True, 0.85)

        # Identify slow strategies
        slow_strategies = self.performance_optimizer.get_slow_strategies(threshold_seconds=0.1)

        assert len(slow_strategies) == 1
        assert slow_strategies[0]["strategy_name"] == "SlowStrategy"
        assert slow_strategies[0]["avg_execution_time"] > 0.1
        assert slow_strategies[0]["optimization_priority"] == "high"  # High success rate

    def test_integration_performance_report(self):
        """Test comprehensive performance report generation."""
        # Record performance for multiple strategies
        for i in range(15):
            self.performance_optimizer.record_strategy_execution("Strategy1", 0.05, True, 0.8)
            self.performance_optimizer.record_strategy_execution("Strategy2", 0.03, True, 0.9)
            self.performance_optimizer.record_strategy_execution("SlowStrategy", 0.15, True, 0.95)

        # Generate performance report
        report = self.performance_optimizer.get_performance_report()

        assert "summary" in report
        assert "rankings" in report
        assert "slow_strategies" in report
        assert "optimization_recommendations" in report

        # Check that slow strategies are identified
        assert len(report["slow_strategies"]) == 1
        assert report["slow_strategies"][0]["strategy_name"] == "SlowStrategy"

        # Check optimization recommendations
        recommendations = report["optimization_recommendations"]
        assert len(recommendations["high_priority"]) == 1
        assert recommendations["high_priority"][0]["strategy_name"] == "SlowStrategy"

    def test_integration_accuracy_prioritization(self):
        """Test that accuracy is prioritized over speed in ranking."""
        strategies = ["AccurateSlow", "FastWrong", "AccurateFast"]

        # Record performance data
        for i in range(15):
            # AccurateSlow: slow but very accurate
            self.performance_optimizer.record_strategy_execution("AccurateSlow", 0.20, True, 0.95)
            # FastWrong: fast but inaccurate
            self.performance_optimizer.record_strategy_execution("FastWrong", 0.01, False, 0.3)
            # AccurateFast: fast and accurate
            self.performance_optimizer.record_strategy_execution("AccurateFast", 0.02, True, 0.9)

        # Get optimized order
        optimized_order = self.performance_optimizer.get_optimized_execution_order(strategies)

        # Should prioritize accuracy over speed
        assert optimized_order[0] == "AccurateSlow"  # Highest success rate and score
        assert optimized_order[1] == "AccurateFast"  # Good accuracy, fast
        assert optimized_order[2] == "FastWrong"  # Fast but wrong

    def test_integration_insufficient_data_handling(self):
        """Test handling of insufficient performance data."""
        strategies = ["Strategy1", "Strategy2"]

        # Record insufficient samples
        for i in range(5):
            self.performance_optimizer.record_strategy_execution("Strategy1", 0.05, True, 0.8)

        # Should return original order when insufficient data
        optimized_order = self.performance_optimizer.get_optimized_execution_order(strategies)
        assert optimized_order == strategies

    def test_integration_performance_window_management(self):
        """Test that performance window limits data storage."""
        strategy_name = "TestStrategy"
        optimizer = StrategyPerformanceOptimizer(min_samples=5, performance_window=10)

        # Record more than performance_window samples
        for i in range(15):
            optimizer.record_strategy_execution(strategy_name, 0.05, True, 0.8)

        # Check that only performance_window samples are kept
        performance = optimizer.strategy_performances[strategy_name]
        assert len(performance.execution_times) == 10
        assert len(performance.successes) == 10
        assert len(performance.scores) == 10

    def test_integration_strategy_rankings(self):
        """Test strategy rankings by performance."""
        # Record performance for multiple strategies
        for i in range(15):
            self.performance_optimizer.record_strategy_execution("FastStrategy", 0.01, True, 0.9)
            self.performance_optimizer.record_strategy_execution("SlowStrategy", 0.10, False, 0.5)
            self.performance_optimizer.record_strategy_execution("MediumStrategy", 0.05, True, 0.7)

        # Get rankings
        rankings = self.performance_optimizer.get_strategy_rankings()

        assert len(rankings) == 3
        # Should be sorted by performance (accuracy-first)
        assert rankings[0]["strategy_name"] == "FastStrategy"  # Highest success rate and score
        assert rankings[2]["strategy_name"] == "SlowStrategy"  # Lowest success rate
