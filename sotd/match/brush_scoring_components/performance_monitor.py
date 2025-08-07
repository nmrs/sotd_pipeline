"""
Performance Monitor Component.

This component tracks performance metrics for brush matching strategies.
"""

import time
from typing import Any, Dict


class PerformanceMonitor:
    """
    Monitor for tracking brush matching performance metrics.

    This component tracks timing and statistics for individual strategies
    and overall performance.
    """

    def __init__(self):
        """Initialize the performance monitor."""
        self.strategy_timings = {}
        self.start_time = None
        self.end_time = None

    def record_strategy_timing(self, strategy_name: str, duration: float) -> None:
        """
        Record timing for a strategy.

        Args:
            strategy_name: Name of the strategy
            duration: Duration in seconds
        """
        if duration <= 0:
            return  # Ignore invalid timing data

        if strategy_name not in self.strategy_timings:
            self.strategy_timings[strategy_name] = {
                "count": 0,
                "total_time": 0.0,
                "min_time": float("inf"),
                "max_time": 0.0,
            }

        stats = self.strategy_timings[strategy_name]
        stats["count"] += 1
        stats["total_time"] += duration
        stats["min_time"] = min(stats["min_time"], duration)
        stats["max_time"] = max(stats["max_time"], duration)

    def get_performance_stats(self) -> Dict[str, Any]:
        """
        Get performance statistics.

        Returns:
            Dictionary containing performance statistics
        """
        stats = {}

        for strategy_name, timing_data in self.strategy_timings.items():
            stats[strategy_name] = {
                "count": timing_data["count"],
                "total_time": timing_data["total_time"],
                "average_time": timing_data["total_time"] / timing_data["count"],
                "min_time": timing_data["min_time"],
                "max_time": timing_data["max_time"],
            }

        return stats

    def start_timing(self) -> None:
        """Start overall timing."""
        self.start_time = time.time()

    def end_timing(self) -> None:
        """End overall timing."""
        self.end_time = time.time()

    def get_total_time(self) -> float:
        """
        Get total processing time.

        Returns:
            Total time in seconds, or 0.0 if timing not started/ended
        """
        if self.start_time is None or self.end_time is None:
            return 0.0

        return self.end_time - self.start_time

    def reset(self) -> None:
        """Reset all performance data."""
        self.strategy_timings = {}
        self.start_time = None
        self.end_time = None
