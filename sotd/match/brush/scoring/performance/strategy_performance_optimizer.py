"""
Strategy Performance Optimizer Component.

This component tracks strategy performance metrics and optimizes execution order
based on historical performance data.
"""

import statistics
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class StrategyPerformance:
    """Performance data for a single strategy."""

    execution_times: List[float] = field(default_factory=list)
    successes: List[bool] = field(default_factory=list)
    scores: List[float] = field(default_factory=list)


@dataclass
class PerformanceMetrics:
    """Calculated performance metrics for a strategy."""

    avg_execution_time: float
    success_rate: float
    avg_score: float
    total_executions: int


class StrategyPerformanceOptimizer:
    """
    Optimizer for strategy execution order based on performance metrics.

    This component tracks execution time, success rate, and scores for each
    strategy and provides optimized execution order recommendations.
    """

    def __init__(self, min_samples: int = 10, performance_window: int = 100):
        """
        Initialize the strategy performance optimizer.

        Args:
            min_samples: Minimum number of samples required before providing metrics
            performance_window: Maximum number of samples to keep per strategy
        """
        self.min_samples = min_samples
        self.performance_window = performance_window
        self.strategy_performances: Dict[str, StrategyPerformance] = {}

    def record_strategy_execution(
        self, strategy_name: str, execution_time: float, success: bool, score: float
    ) -> None:
        """
        Record execution metrics for a strategy.

        Args:
            strategy_name: Name of the strategy
            execution_time: Execution time in seconds
            success: Whether the strategy succeeded
            score: Score achieved by the strategy
        """
        if strategy_name not in self.strategy_performances:
            self.strategy_performances[strategy_name] = StrategyPerformance()

        performance = self.strategy_performances[strategy_name]

        # Add new metrics
        performance.execution_times.append(execution_time)
        performance.successes.append(success)
        performance.scores.append(score)

        # Maintain performance window
        if len(performance.execution_times) > self.performance_window:
            performance.execution_times.pop(0)
            performance.successes.pop(0)
            performance.scores.pop(0)

    def get_strategy_performance(self, strategy_name: str) -> Optional[PerformanceMetrics]:
        """
        Get performance metrics for a strategy.

        Args:
            strategy_name: Name of the strategy

        Returns:
            PerformanceMetrics if sufficient data available, None otherwise
        """
        if strategy_name not in self.strategy_performances:
            return None

        performance = self.strategy_performances[strategy_name]

        if len(performance.execution_times) < self.min_samples:
            return None

        # Calculate metrics
        avg_execution_time = statistics.mean(performance.execution_times)
        success_rate = sum(performance.successes) / len(performance.successes)
        avg_score = statistics.mean(performance.scores)
        total_executions = len(performance.execution_times)

        return PerformanceMetrics(
            avg_execution_time=avg_execution_time,
            success_rate=success_rate,
            avg_score=avg_score,
            total_executions=total_executions,
        )

    def get_optimized_execution_order(self, strategies: List[str]) -> List[str]:
        """
        Get optimized execution order for strategies based on performance.

        Args:
            strategies: List of strategy names to optimize

        Returns:
            Optimized list of strategy names
        """
        if not strategies:
            return []

        # Get performance metrics for all strategies
        strategy_metrics = {}
        for strategy in strategies:
            metrics = self.get_strategy_performance(strategy)
            if metrics is not None:
                strategy_metrics[strategy] = metrics

        # If insufficient data for any strategy, return original order
        if len(strategy_metrics) != len(strategies):
            return strategies.copy()

        # Sort by performance score (accuracy-only ranking)
        def performance_score(metrics: PerformanceMetrics) -> float:
            # Focus purely on accuracy: success rate and average score
            # Execution time is tracked for monitoring but not used in ranking
            return (metrics.success_rate * 0.6) + (metrics.avg_score * 0.4)

        sorted_strategies = sorted(
            strategies,
            key=lambda s: performance_score(strategy_metrics[s]),
            reverse=True,
        )

        return sorted_strategies

    def get_performance_summary(self) -> Dict[str, Dict[str, float]]:
        """
        Get performance summary for all strategies.

        Returns:
            Dictionary mapping strategy names to their performance metrics
        """
        summary = {}
        for strategy_name in self.strategy_performances:
            metrics = self.get_strategy_performance(strategy_name)
            if metrics is not None:
                summary[strategy_name] = {
                    "avg_execution_time": metrics.avg_execution_time,
                    "success_rate": metrics.success_rate,
                    "avg_score": metrics.avg_score,
                    "total_executions": metrics.total_executions,
                }
        return summary

    def clear_strategy_performance(self, strategy_name: str) -> None:
        """
        Clear performance data for a specific strategy.

        Args:
            strategy_name: Name of the strategy to clear
        """
        if strategy_name in self.strategy_performances:
            del self.strategy_performances[strategy_name]

    def clear_all_performance_data(self) -> None:
        """Clear all performance data."""
        self.strategy_performances.clear()

    def get_strategy_rankings(self) -> List[Dict[str, Any]]:
        """
        Get ranked list of strategies by performance.

        Returns:
            List of dictionaries with strategy rankings
        """
        rankings = []
        for strategy_name, performance in self.strategy_performances.items():
            metrics = self.get_strategy_performance(strategy_name)
            if metrics is not None:
                rankings.append(
                    {
                        "strategy_name": strategy_name,
                        "avg_execution_time": metrics.avg_execution_time,
                        "success_rate": metrics.success_rate,
                        "avg_score": metrics.avg_score,
                        "total_executions": metrics.total_executions,
                    }
                )

        # Sort by performance score (accuracy-only ranking)
        def performance_score(ranking: Dict[str, Any]) -> float:
            # Focus purely on accuracy: success rate and average score
            # Execution time is tracked for monitoring but not used in ranking
            return (ranking["success_rate"] * 0.6) + (ranking["avg_score"] * 0.4)

        return sorted(rankings, key=performance_score, reverse=True)

    def get_slow_strategies(self, threshold_seconds: float = 0.1) -> List[Dict[str, Any]]:
        """
        Get strategies that are slow and may need optimization.

        Args:
            threshold_seconds: Execution time threshold in seconds (default: 0.1s)

        Returns:
            List of slow strategies with their performance metrics
        """
        slow_strategies = []

        for strategy_name, performance in self.strategy_performances.items():
            metrics = self.get_strategy_performance(strategy_name)
            if metrics is not None and metrics.avg_execution_time > threshold_seconds:
                slow_strategies.append(
                    {
                        "strategy_name": strategy_name,
                        "avg_execution_time": metrics.avg_execution_time,
                        "success_rate": metrics.success_rate,
                        "avg_score": metrics.avg_score,
                        "total_executions": metrics.total_executions,
                        "optimization_priority": (
                            "high" if metrics.success_rate > 0.8 else "medium"
                        ),
                    }
                )

        # Sort by execution time (slowest first)
        return sorted(slow_strategies, key=lambda x: x["avg_execution_time"], reverse=True)

    def get_performance_report(self) -> Dict[str, Any]:
        """
        Get comprehensive performance report for all strategies.

        Returns:
            Dictionary containing performance summary, rankings, and optimization recommendations
        """
        summary = self.get_performance_summary()
        rankings = self.get_strategy_rankings()
        slow_strategies = self.get_slow_strategies()

        return {
            "summary": summary,
            "rankings": rankings,
            "slow_strategies": slow_strategies,
            "optimization_recommendations": {
                "high_priority": [
                    s for s in slow_strategies if s["optimization_priority"] == "high"
                ],
                "medium_priority": [
                    s for s in slow_strategies if s["optimization_priority"] == "medium"
                ],
                "low_priority": [s for s in slow_strategies if s["optimization_priority"] == "low"],
            },
        }
