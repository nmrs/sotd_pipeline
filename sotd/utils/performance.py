"""
General performance monitoring for the SOTD Pipeline.

This module provides general performance monitoring functionality by extending
the base performance monitoring classes.
"""

from typing import Dict

from sotd.utils.performance_base import (
    BasePerformanceMetrics,
    BasePerformanceMonitor,
    PipelinePerformanceTracker,
    TimingContext,
)


class GeneralPerformanceMetrics(BasePerformanceMetrics):
    """Performance metrics for general pipeline phases."""

    # Use the base phase_times field for general phase operations
    # No additional fields needed for general performance monitoring

    def to_dict(self) -> Dict:
        """Convert metrics to dictionary for JSON serialization."""
        return super().to_dict()


class PerformanceMonitor(BasePerformanceMonitor):
    """Performance monitoring utility for general pipeline phases."""

    def __init__(self, phase_name: str = "unknown", parallel_workers: int = 1):
        super().__init__(phase_name, parallel_workers)
        # Type annotation to help type checker
        self.metrics: GeneralPerformanceMetrics = self.metrics

    def _create_metrics(self, phase_name: str, parallel_workers: int) -> GeneralPerformanceMetrics:
        """Create general performance metrics instance."""
        return GeneralPerformanceMetrics(phase_name=phase_name, parallel_workers=parallel_workers)

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

        if self.metrics.phase_times:
            print("\nPhase Performance:")
            for phase, stats in self.metrics.phase_times.items():
                print(f"  {phase}: {stats.avg_time * 1000:.1f}ms avg ({stats.count} calls)")

        print("\nMemory Usage:")
        print(f"  Peak: {self.metrics.peak_memory_mb:.1f}MB")
        print(f"  Final: {self.metrics.final_memory_mb:.1f}MB")

        print("\nFile Sizes:")
        print(f"  Input: {self.metrics.input_file_size_mb:.1f}MB")
        if self.metrics.output_file_size_mb > 0:
            print(f"  Output: {self.metrics.output_file_size_mb:.1f}MB")

        print("=" * 60)


__all__ = [
    "PerformanceMonitor",
    "GeneralPerformanceMetrics",
    "TimingContext",
    "PipelinePerformanceTracker",
]
