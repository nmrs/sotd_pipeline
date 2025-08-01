"""
Performance monitoring for the match phase.

This module provides match-specific performance monitoring functionality
by extending the base performance monitoring classes.
"""

from dataclasses import dataclass, field
from typing import Dict

from sotd.utils.performance_base import BasePerformanceMetrics, BasePerformanceMonitor, TimingStats


@dataclass
class MatchPerformanceMetrics(BasePerformanceMetrics):
    """Performance metrics specific to the match phase."""

    # Override phase_times to be more specific for match phase
    matcher_times: Dict[str, TimingStats] = field(default_factory=dict)
    # Brush strategy performance tracking
    brush_strategy_times: Dict[str, TimingStats] = field(default_factory=dict)
    # Cache statistics
    cache_stats: Dict[str, Dict[str, int]] = field(default_factory=dict)

    def to_dict(self) -> Dict:
        """Convert metrics to dictionary for JSON serialization."""
        base_dict = super().to_dict()
        # Replace generic phase_times with match-specific matcher_times
        base_dict["matcher_times"] = {
            matcher: {
                "total_time_seconds": stats.total_time,
                "avg_time_seconds": stats.avg_time,
                "min_time_seconds": stats.min_time if stats.min_time != float("inf") else 0.0,
                "max_time_seconds": stats.max_time,
                "count": stats.count,
            }
            for matcher, stats in self.matcher_times.items()
        }
        # Add brush strategy timing
        base_dict["brush_strategy_times"] = {
            strategy: {
                "total_time_seconds": stats.total_time,
                "avg_time_seconds": stats.avg_time,
                "min_time_seconds": stats.min_time if stats.min_time != float("inf") else 0.0,
                "max_time_seconds": stats.max_time,
                "count": stats.count,
            }
            for strategy, stats in self.brush_strategy_times.items()
        }
        # Add cache statistics
        base_dict["cache_stats"] = self.cache_stats
        # Remove the generic phase_times since we're using matcher_times
        base_dict.pop("phase_times", None)
        return base_dict


class PerformanceMonitor(BasePerformanceMonitor):
    """Performance monitoring utility for the match phase."""

    def __init__(self, phase_name: str = "match", parallel_workers: int = 1):
        super().__init__(phase_name, parallel_workers)
        # Type annotation to help type checker
        self.metrics: MatchPerformanceMetrics = self.metrics

    def _create_metrics(self, phase_name: str, parallel_workers: int) -> MatchPerformanceMetrics:
        """Create match-specific metrics instance."""
        return MatchPerformanceMetrics(phase_name=phase_name, parallel_workers=parallel_workers)

    def record_matcher_timing(self, matcher_type: str, duration: float) -> None:
        """Record timing for a specific matcher."""
        if matcher_type not in self.metrics.matcher_times:
            self.metrics.matcher_times[matcher_type] = TimingStats()
        self.metrics.matcher_times[matcher_type].add_timing(duration)

    def record_cache_stats(self, cache_name: str, stats: Dict[str, int]) -> None:
        """Record cache statistics for a specific cache."""
        self.metrics.cache_stats[cache_name] = stats

    def record_brush_strategy_timing(self, strategy_name: str, duration: float) -> None:
        """Record timing for a specific brush strategy."""
        if strategy_name not in self.metrics.brush_strategy_times:
            self.metrics.brush_strategy_times[strategy_name] = TimingStats()
        self.metrics.brush_strategy_times[strategy_name].add_timing(duration)

    def print_summary(self) -> None:
        """Print a human-readable performance summary."""
        print("\n" + "=" * 60)
        print(f"{self.metrics.phase_name.upper()} PHASE PERFORMANCE SUMMARY")
        print("=" * 60)

        print(f"Total Processing Time: {self.metrics.total_processing_time:.2f}s")
        print(f"Records Processed: {self.metrics.record_count:,}")
        print(f"Processing Rate: {self.metrics.records_per_second:.1f} records/second")
        print(f"Average Time per Record: {self.metrics.avg_time_per_record * 1000:.1f}ms")

        if self.metrics.parallel_workers > 1:
            print(f"Parallel Workers: {self.metrics.parallel_workers}")

        print("\nTiming Breakdown:")
        io_percent = (
            self.metrics.file_io_time / self.metrics.total_processing_time * 100
            if self.metrics.total_processing_time > 0
            else 0
        )
        processing_percent = (
            self.metrics.processing_time / self.metrics.total_processing_time * 100
            if self.metrics.total_processing_time > 0
            else 0
        )
        print(f"  File I/O: {self.metrics.file_io_time:.2f}s ({io_percent:.1f}%)")
        print(f"  Processing: {self.metrics.processing_time:.2f}s ({processing_percent:.1f}%)")

        if self.metrics.matcher_times:
            print("\nMatcher Performance:")
            for matcher, stats in self.metrics.matcher_times.items():
                print(f"  {matcher}: {stats.avg_time * 1000:.1f}ms avg ({stats.count} calls)")

        if self.metrics.brush_strategy_times:
            print("\nBrush Strategy Performance:")
            # Calculate success rates based on strategy progression
            strategy_names = list(self.metrics.brush_strategy_times.keys())
            for i, (strategy, stats) in enumerate(self.metrics.brush_strategy_times.items()):
                attempts = stats.count
                # Calculate matches by looking at the next strategy's attempts
                if i < len(strategy_names) - 1:
                    next_strategy = strategy_names[i + 1]
                    next_attempts = self.metrics.brush_strategy_times[next_strategy].count
                    matches = attempts - next_attempts
                else:
                    # Last strategy - all attempts were matches
                    matches = attempts
                
                success_rate = (matches / attempts * 100) if attempts > 0 else 0
                print(
                    f"  {strategy}: {stats.avg_time * 1000:.1f}ms avg "
                    f"({attempts} calls, {matches} matches, {success_rate:.1f}% success)"
                )

        if self.metrics.cache_stats:
            print("\nCache Performance:")
            for cache_name, stats in self.metrics.cache_stats.items():
                hits = stats.get("hits", 0)
                misses = stats.get("misses", 0)
                total = hits + misses
                hit_rate = (hits / total * 100) if total > 0 else 0
                print(f"  {cache_name}: {hit_rate:.1f}% hit rate ({hits} hits, {misses} misses)")

        print("\nMemory Usage:")
        print(f"  Peak: {self.metrics.peak_memory_mb:.1f}MB")
        print(f"  Final: {self.metrics.final_memory_mb:.1f}MB")

        print("\nFile Sizes:")
        print(f"  Input: {self.metrics.input_file_size_mb:.1f}MB")
        if self.metrics.output_file_size_mb > 0:
            print(f"  Output: {self.metrics.output_file_size_mb:.1f}MB")

        print("=" * 60)
