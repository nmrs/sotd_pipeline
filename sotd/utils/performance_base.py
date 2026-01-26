"""
Base performance monitoring classes for the SOTD Pipeline.

This module provides abstract base classes and common functionality for performance
monitoring across all pipeline phases, eliminating code duplication.
"""

import time
from abc import ABC, abstractmethod
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
class BasePerformanceMetrics:
    """Base performance metrics for pipeline phase processing."""

    # Overall timing
    total_processing_time: float = 0.0
    file_io_time: float = 0.0
    processing_time: float = 0.0

    # Record-level timing
    record_count: int = 0
    avg_time_per_record: float = 0.0
    records_per_second: float = 0.0

    # Phase-specific timing (to be overridden by subclasses)
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


class BasePerformanceMonitor(ABC):
    """Abstract base class for performance monitoring across pipeline phases."""

    def __init__(self, phase_name: str = "unknown", parallel_workers: int = 1):
        self.metrics = self._create_metrics(phase_name, parallel_workers)
        self.start_time: Optional[float] = None
        self.file_io_start: Optional[float] = None
        self.processing_start: Optional[float] = None
        self.initial_memory: float = psutil.Process().memory_info().rss / 1024 / 1024  # MB

    @abstractmethod
    def _create_metrics(self, phase_name: str, parallel_workers: int) -> BasePerformanceMetrics:
        """Create metrics instance for this phase."""
        pass

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

    @abstractmethod
    def print_summary(self) -> None:
        """Print a human-readable performance summary."""
        pass


class TimingContext:
    """Context manager for timing operations."""

    def __init__(self, monitor: BasePerformanceMonitor, operation: str):
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
    """Track performance across multiple pipeline phases."""

    def __init__(self):
        self.phase_results: Dict[str, Dict] = {}

    def add_phase_result(self, phase_name: str, result: Dict) -> None:
        """Add a phase result to the tracker."""
        self.phase_results[phase_name] = result

    def print_pipeline_summary(self) -> None:
        """Print a summary of all phase performances."""
        logger.info("=" * 80)
        logger.info("PIPELINE PERFORMANCE SUMMARY")
        logger.info("=" * 80)

        total_time = 0.0
        total_records = 0

        for phase_name, result in self.phase_results.items():
            phase_time = result.get("total_processing_time_seconds", 0.0)
            phase_records = result.get("record_count", 0)
            total_time += phase_time
            total_records += phase_records

            logger.info(f"\n{phase_name.upper()}:")
            logger.info(f"  Time: {phase_time:.2f}s")
            logger.info(f"  Records: {phase_records:,}")
            if phase_time > 0:
                rate = phase_records / phase_time
                logger.info(f"  Rate: {rate:.1f} records/second")

        logger.info("\nTOTAL PIPELINE:")
        logger.info(f"  Time: {total_time:.2f}s")
        logger.info(f"  Records: {total_records:,}")
        if total_time > 0:
            rate = total_records / total_time
            logger.info(f"  Rate: {rate:.1f} records/second")
        logger.info("=" * 80)
