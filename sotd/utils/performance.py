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
    """Comprehensive performance metrics for pipeline phase processing."""

    # Overall timing
    total_processing_time: float = 0.0
    file_io_time: float = 0.0
    processing_time: float = 0.0

    # Record-level timing
    record_count: int = 0
    avg_time_per_record: float = 0.0
    records_per_second: float = 0.0

    # Phase-specific timing
    phase_times: Dict[str, TimingStats] = field(default_factory=dict)

    # Memory usage
    peak_memory_mb: float = 0.0
    final_memory_mb: float = 0.0

    # File information
    input_file_size_mb: float = 0.0
    output_file_size_mb: float = 0.0

    # Pipeline phase info
    phase_name: str = "unknown"
    parallel_workers: int = 1

    def to_dict(self) -> Dict:
        """Convert metrics to dictionary for JSON serialization."""
        return {
            "phase_name": self.phase_name,
            "parallel_workers": self.parallel_workers,
            "total_processing_time_seconds": self.total_processing_time,
            "file_io_time_seconds": self.file_io_time,
            "processing_time_seconds": self.processing_time,
            "record_count": self.record_count,
            "avg_time_per_record_seconds": self.avg_time_per_record,
            "records_per_second": self.records_per_second,
            "phase_times": {
                phase: {
                    "total_time_seconds": stats.total_time,
                    "avg_time_seconds": stats.avg_time,
                    "min_time_seconds": stats.min_time if stats.min_time != float("inf") else 0.0,
                    "max_time_seconds": stats.max_time,
                    "count": stats.count,
                }
                for phase, stats in self.phase_times.items()
            },
            "memory_usage_mb": {"peak": self.peak_memory_mb, "final": self.final_memory_mb},
            "file_sizes_mb": {"input": self.input_file_size_mb, "output": self.output_file_size_mb},
        }


class PerformanceMonitor:
    """Performance monitoring utility for pipeline phases."""

    def __init__(self, phase_name: str = "unknown", parallel_workers: int = 1):
        self.metrics = PerformanceMetrics()
        self.metrics.phase_name = phase_name
        self.metrics.parallel_workers = parallel_workers
        self.start_time: Optional[float] = None
        self.file_io_start: Optional[float] = None
        self.processing_start: Optional[float] = None
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

    def start_processing_timing(self) -> None:
        """Start timing for processing operations."""
        self.processing_start = time.time()

    def end_processing_timing(self) -> None:
        """End timing for processing operations."""
        if self.processing_start is not None:
            self.metrics.processing_time += time.time() - self.processing_start
            self.processing_start = None

    def record_phase_timing(self, phase_type: str, duration: float) -> None:
        """Record timing for a specific phase operation."""
        if phase_type not in self.metrics.phase_times:
            self.metrics.phase_times[phase_type] = TimingStats()
        self.metrics.phase_times[phase_type].add_timing(duration)

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
            self.monitor.record_phase_timing(self.operation, duration)


class PipelinePerformanceTracker:
    """Tracks performance across multiple pipeline phases."""

    def __init__(self):
        self.phase_results: Dict[str, Dict] = {}
        self.total_records: int = 0
        self.total_time: float = 0.0

    def add_phase_result(self, phase_name: str, result: Dict) -> None:
        """Add a phase result to the tracker."""
        self.phase_results[phase_name] = result
        if "performance" in result:
            perf = result["performance"]
            self.total_records += perf.get("record_count", 0)
            self.total_time += perf.get("total_processing_time_seconds", 0)

    def print_pipeline_summary(self) -> None:
        """Print a summary of all pipeline phases."""
        if not self.phase_results:
            print("No pipeline results to summarize.")
            return

        print("\n" + "=" * 80)
        print("PIPELINE PERFORMANCE SUMMARY")
        print("=" * 80)

        print(f"Total Records Processed: {self.total_records:,}")
        print(f"Total Pipeline Time: {self.total_time:.2f}s")
        if self.total_time > 0:
            print(f"Overall Throughput: {self.total_records / self.total_time:.1f} records/sec")

        print("\nPhase Breakdown:")
        for phase_name, result in self.phase_results.items():
            if "performance" in result:
                perf = result["performance"]
                records = perf.get("record_count", 0)
                time_taken = perf.get("total_processing_time_seconds", 0)
                throughput = perf.get("records_per_second", 0)
                workers = perf.get("parallel_workers", 1)

                print(f"  {phase_name}:")
                print(f"    Records: {records:,}")
                print(f"    Time: {time_taken:.2f}s")
                print(f"    Throughput: {throughput:.1f} records/sec")
                if workers > 1:
                    print(f"    Workers: {workers}")

        print("=" * 80)
