import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Optional

import psutil


@dataclass
class TimingStats:
    """Statistics for a specific timing category."""

    total_time: float = 0.0
    count: int = 0
    min_time: float = float("inf")
    max_time: float = 0.0

    @property
    def avg_time(self) -> float:
        """Calculate average time."""
        return self.total_time / self.count if self.count > 0 else 0.0

    def add_timing(self, duration: float) -> None:
        """Add a timing measurement."""
        self.total_time += duration
        self.count += 1
        self.min_time = min(self.min_time, duration)
        self.max_time = max(self.max_time, duration)


@dataclass
class PerformanceMetrics:
    """Comprehensive performance metrics for match phase processing."""

    # Overall timing
    total_processing_time: float = 0.0
    file_io_time: float = 0.0
    matching_time: float = 0.0

    # Record-level timing
    record_count: int = 0
    avg_time_per_record: float = 0.0
    records_per_second: float = 0.0

    # Matcher-specific timing
    matcher_times: Dict[str, TimingStats] = field(default_factory=dict)

    # Memory usage
    peak_memory_mb: float = 0.0
    final_memory_mb: float = 0.0

    # File information
    input_file_size_mb: float = 0.0
    output_file_size_mb: float = 0.0

    def to_dict(self) -> Dict:
        """Convert metrics to dictionary for JSON serialization."""
        return {
            "total_processing_time_seconds": self.total_processing_time,
            "file_io_time_seconds": self.file_io_time,
            "matching_time_seconds": self.matching_time,
            "record_count": self.record_count,
            "avg_time_per_record_seconds": self.avg_time_per_record,
            "records_per_second": self.records_per_second,
            "matcher_times": {
                matcher: {
                    "total_time_seconds": stats.total_time,
                    "avg_time_seconds": stats.avg_time,
                    "min_time_seconds": stats.min_time if stats.min_time != float("inf") else 0.0,
                    "max_time_seconds": stats.max_time,
                    "count": stats.count,
                }
                for matcher, stats in self.matcher_times.items()
            },
            "memory_usage_mb": {"peak": self.peak_memory_mb, "final": self.final_memory_mb},
            "file_sizes_mb": {"input": self.input_file_size_mb, "output": self.output_file_size_mb},
        }


class PerformanceMonitor:
    """Performance monitoring utility for the match phase."""

    def __init__(self):
        self.metrics = PerformanceMetrics()
        self.start_time: Optional[float] = None
        self.file_io_start: Optional[float] = None
        self.matching_start: Optional[float] = None
        self.initial_memory: float = psutil.Process().memory_info().rss / 1024 / 1024  # MB

    def start_total_timing(self) -> None:
        """Start timing for total processing."""
        self.start_time = time.time()

    def end_total_timing(self) -> None:
        """End timing for total processing and calculate metrics."""
        if self.start_time is not None:
            self.metrics.total_processing_time = time.time() - self.start_time
            self._calculate_derived_metrics()
            self._update_memory_usage()

    def start_file_io_timing(self) -> None:
        """Start timing for file I/O operations."""
        self.file_io_start = time.time()

    def end_file_io_timing(self) -> None:
        """End timing for file I/O operations."""
        if self.file_io_start is not None:
            self.metrics.file_io_time += time.time() - self.file_io_start
            self.file_io_start = None

    def start_matching_timing(self) -> None:
        """Start timing for matching operations."""
        self.matching_start = time.time()

    def end_matching_timing(self) -> None:
        """End timing for matching operations."""
        if self.matching_start is not None:
            self.metrics.matching_time += time.time() - self.matching_start
            self.matching_start = None

    def record_matcher_timing(self, matcher_type: str, duration: float) -> None:
        """Record timing for a specific matcher."""
        if matcher_type not in self.metrics.matcher_times:
            self.metrics.matcher_times[matcher_type] = TimingStats()
        self.metrics.matcher_times[matcher_type].add_timing(duration)

    def set_record_count(self, count: int) -> None:
        """Set the total number of records processed."""
        self.metrics.record_count = count

    def set_file_sizes(self, input_path: Path, output_path: Optional[Path] = None) -> None:
        """Set file size information."""
        if input_path.exists():
            self.metrics.input_file_size_mb = input_path.stat().st_size / 1024 / 1024
        if output_path and output_path.exists():
            self.metrics.output_file_size_mb = output_path.stat().st_size / 1024 / 1024

    def _calculate_derived_metrics(self) -> None:
        """Calculate derived metrics like averages and rates."""
        if self.metrics.record_count > 0 and self.metrics.total_processing_time > 0:
            self.metrics.avg_time_per_record = (
                self.metrics.total_processing_time / self.metrics.record_count
            )
            self.metrics.records_per_second = (
                self.metrics.record_count / self.metrics.total_processing_time
            )

    def _update_memory_usage(self) -> None:
        """Update memory usage metrics."""
        current_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
        self.metrics.final_memory_mb = current_memory
        self.metrics.peak_memory_mb = max(self.metrics.peak_memory_mb, current_memory)

    def get_summary(self) -> Dict:
        """Get performance summary as dictionary."""
        return self.metrics.to_dict()

    def print_summary(self) -> None:
        """Print a human-readable performance summary."""
        print("\n" + "=" * 60)
        print("MATCH PHASE PERFORMANCE SUMMARY")
        print("=" * 60)

        print(f"Total Processing Time: {self.metrics.total_processing_time:.2f}s")
        print(f"Records Processed: {self.metrics.record_count:,}")
        print(f"Processing Rate: {self.metrics.records_per_second:.1f} records/second")
        print(f"Average Time per Record: {self.metrics.avg_time_per_record * 1000:.1f}ms")

        print("\nTiming Breakdown:")
        io_percent = (
            self.metrics.file_io_time / self.metrics.total_processing_time * 100
            if self.metrics.total_processing_time > 0
            else 0
        )
        matching_percent = (
            self.metrics.matching_time / self.metrics.total_processing_time * 100
            if self.metrics.total_processing_time > 0
            else 0
        )
        print(f"  File I/O: {self.metrics.file_io_time:.2f}s ({io_percent:.1f}%)")
        print(f"  Matching: {self.metrics.matching_time:.2f}s ({matching_percent:.1f}%)")

        if self.metrics.matcher_times:
            print("\nMatcher Performance:")
            for matcher, stats in self.metrics.matcher_times.items():
                print(f"  {matcher}: {stats.avg_time * 1000:.1f}ms avg ({stats.count} calls)")

        print("\nMemory Usage:")
        print(f"  Peak: {self.metrics.peak_memory_mb:.1f}MB")
        print(f"  Final: {self.metrics.final_memory_mb:.1f}MB")

        print("\nFile Sizes:")
        print(f"  Input: {self.metrics.input_file_size_mb:.1f}MB")
        if self.metrics.output_file_size_mb > 0:
            print(f"  Output: {self.metrics.output_file_size_mb:.1f}MB")

        print("=" * 60)


class TimingContext:
    """Context manager for timing operations."""

    def __init__(self, monitor: PerformanceMonitor, operation: str):
        self.monitor = monitor
        self.operation = operation
        self.start_time: Optional[float] = None

    def __enter__(self):
        self.start_time = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.start_time is not None:
            duration = time.time() - self.start_time
            self.monitor.record_matcher_timing(self.operation, duration)
