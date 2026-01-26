"""
Unit tests for performance base classes.

Tests the base performance monitoring functionality that will be shared
across all pipeline phases.
"""

import time
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from sotd.utils.performance_base import (
    BasePerformanceMetrics,
    BasePerformanceMonitor,
    PipelinePerformanceTracker,
    TimingContext,
    TimingStats,
)


class TestTimingStats:
    """Test the TimingStats class."""

    def test_initial_state(self):
        """Test initial state of TimingStats."""
        stats = TimingStats()
        assert stats.total_time == 0.0
        assert stats.count == 0
        assert stats.min_time == float("inf")
        assert stats.max_time == 0.0
        assert stats.avg_time == 0.0

    def test_add_timing_single(self):
        """Test adding a single timing measurement."""
        stats = TimingStats()
        stats.add_timing(1.5)

        assert stats.total_time == 1.5
        assert stats.count == 1
        assert stats.min_time == 1.5
        assert stats.max_time == 1.5
        assert stats.avg_time == 1.5

    def test_add_timing_multiple(self):
        """Test adding multiple timing measurements."""
        stats = TimingStats()
        stats.add_timing(1.0)
        stats.add_timing(2.0)
        stats.add_timing(3.0)

        assert stats.total_time == 6.0
        assert stats.count == 3
        assert stats.min_time == 1.0
        assert stats.max_time == 3.0
        assert stats.avg_time == 2.0

    def test_avg_time_zero_count(self):
        """Test average time calculation with zero count."""
        stats = TimingStats()
        assert stats.avg_time == 0.0


class TestBasePerformanceMetrics:
    """Test the BasePerformanceMetrics class."""

    def test_initial_state(self):
        """Test initial state of BasePerformanceMetrics."""
        metrics = BasePerformanceMetrics()
        assert metrics.total_processing_time == 0.0
        assert metrics.file_io_time == 0.0
        assert metrics.processing_time == 0.0
        assert metrics.record_count == 0
        assert metrics.avg_time_per_record == 0.0
        assert metrics.records_per_second == 0.0
        assert metrics.phase_times == {}
        assert metrics.peak_memory_mb == 0.0
        assert metrics.final_memory_mb == 0.0
        assert metrics.input_file_size_mb == 0.0
        assert metrics.output_file_size_mb == 0.0
        assert metrics.phase_name == "unknown"
        assert metrics.parallel_workers == 1

    def test_custom_initialization(self):
        """Test custom initialization with parameters."""
        metrics = BasePerformanceMetrics(phase_name="test_phase", parallel_workers=4)
        assert metrics.phase_name == "test_phase"
        assert metrics.parallel_workers == 4

    def test_to_dict(self):
        """Test conversion to dictionary."""
        metrics = BasePerformanceMetrics(phase_name="test_phase", parallel_workers=2)
        metrics.total_processing_time = 10.0
        metrics.file_io_time = 2.0
        metrics.processing_time = 8.0
        metrics.record_count = 100
        metrics.avg_time_per_record = 0.1
        metrics.records_per_second = 10.0
        metrics.peak_memory_mb = 50.0
        metrics.final_memory_mb = 45.0
        metrics.input_file_size_mb = 5.0
        metrics.output_file_size_mb = 3.0

        # Add some phase timing
        metrics.phase_times["test_phase"] = TimingStats()
        metrics.phase_times["test_phase"].add_timing(1.0)

        result = metrics.to_dict()

        assert result["phase_name"] == "test_phase"
        assert result["parallel_workers"] == 2
        assert result["total_processing_time_seconds"] == 10.0
        assert result["file_io_time_seconds"] == 2.0
        assert result["processing_time_seconds"] == 8.0
        assert result["record_count"] == 100
        assert result["avg_time_per_record_seconds"] == 0.1
        assert result["records_per_second"] == 10.0
        assert result["memory_usage_mb"]["peak"] == 50.0
        assert result["memory_usage_mb"]["final"] == 45.0
        assert result["file_sizes_mb"]["input"] == 5.0
        assert result["file_sizes_mb"]["output"] == 3.0
        assert "test_phase" in result["phase_times"]


class ConcretePerformanceMonitor(BasePerformanceMonitor):
    """Concrete implementation for testing."""

    def _create_metrics(self, phase_name: str, parallel_workers: int) -> BasePerformanceMetrics:
        return BasePerformanceMetrics(phase_name=phase_name, parallel_workers=parallel_workers)

    def print_summary(self) -> None:
        """Print summary for testing."""
        pass


class TestBasePerformanceMonitor:
    """Test the BasePerformanceMonitor class."""

    def test_initialization(self):
        """Test monitor initialization."""
        monitor = ConcretePerformanceMonitor("test_phase", 4)
        assert monitor.metrics.phase_name == "test_phase"
        assert monitor.metrics.parallel_workers == 4
        assert monitor.start_time is None
        assert monitor.file_io_start is None
        assert monitor.processing_start is None

    def test_total_timing(self):
        """Test total timing functionality."""
        monitor = ConcretePerformanceMonitor()

        monitor.start_total_timing()
        assert monitor.start_time is not None

        time.sleep(0.01)  # Small delay to ensure measurable time

        monitor.end_total_timing()
        assert monitor.metrics.total_processing_time > 0

    def test_file_io_timing(self):
        """Test file I/O timing functionality."""
        monitor = ConcretePerformanceMonitor()

        monitor.start_file_io_timing()
        assert monitor.file_io_start is not None

        time.sleep(0.01)

        monitor.end_file_io_timing()
        assert monitor.metrics.file_io_time > 0
        assert monitor.file_io_start is None

    def test_processing_timing(self):
        """Test processing timing functionality."""
        monitor = ConcretePerformanceMonitor()

        monitor.start_processing_timing()
        assert monitor.processing_start is not None

        time.sleep(0.01)

        monitor.end_processing_timing()
        assert monitor.metrics.processing_time > 0
        assert monitor.processing_start is None

    def test_phase_timing(self):
        """Test phase timing recording."""
        monitor = ConcretePerformanceMonitor()

        monitor.record_phase_timing("test_operation", 1.5)
        assert "test_operation" in monitor.metrics.phase_times
        assert monitor.metrics.phase_times["test_operation"].total_time == 1.5
        assert monitor.metrics.phase_times["test_operation"].count == 1

    def test_record_count(self):
        """Test record count setting."""
        monitor = ConcretePerformanceMonitor()
        monitor.set_record_count(100)
        assert monitor.metrics.record_count == 100

    @patch("pathlib.Path.exists")
    @patch("pathlib.Path.stat")
    def test_file_sizes(self, mock_stat, mock_exists):
        """Test file size setting."""
        mock_exists.return_value = True
        mock_stat.return_value.st_size = 1024 * 1024  # 1MB

        monitor = ConcretePerformanceMonitor()
        input_path = Path("input.json")
        output_path = Path("output.json")

        monitor.set_file_sizes(input_path, output_path)

        assert monitor.metrics.input_file_size_mb == 1.0
        assert monitor.metrics.output_file_size_mb == 1.0

    def test_derived_metrics_calculation(self):
        """Test derived metrics calculation."""
        monitor = ConcretePerformanceMonitor()
        monitor.metrics.record_count = 100
        monitor.metrics.total_processing_time = 10.0

        monitor._calculate_derived_metrics()

        assert monitor.metrics.avg_time_per_record == 0.1
        assert monitor.metrics.records_per_second == 10.0

    @patch("psutil.Process")
    def test_memory_usage_update(self, mock_process):
        """Test memory usage update."""
        mock_memory_info = Mock()
        mock_memory_info.rss = 50 * 1024 * 1024  # 50MB
        mock_process.return_value.memory_info.return_value = mock_memory_info

        monitor = ConcretePerformanceMonitor()
        monitor._update_memory_usage()

        assert monitor.metrics.final_memory_mb == 50.0
        assert monitor.metrics.peak_memory_mb == 50.0

    def test_get_summary(self):
        """Test getting performance summary."""
        monitor = ConcretePerformanceMonitor("test_phase", 2)
        monitor.metrics.total_processing_time = 10.0
        monitor.metrics.record_count = 100

        summary = monitor.get_summary()

        assert summary["phase_name"] == "test_phase"
        assert summary["parallel_workers"] == 2
        assert summary["total_processing_time_seconds"] == 10.0
        assert summary["record_count"] == 100


class TestTimingContext:
    """Test the TimingContext class."""

    def test_context_manager(self):
        """Test TimingContext as context manager."""
        monitor = ConcretePerformanceMonitor()

        with TimingContext(monitor, "test_operation"):
            time.sleep(0.01)

        assert "test_operation" in monitor.metrics.phase_times
        assert monitor.metrics.phase_times["test_operation"].count == 1
        assert monitor.metrics.phase_times["test_operation"].total_time > 0

    def test_context_manager_exception(self):
        """Test TimingContext handles exceptions properly."""
        monitor = ConcretePerformanceMonitor()

        with pytest.raises(ValueError):
            with TimingContext(monitor, "test_operation"):
                raise ValueError("Test exception")

        # Should still record timing even with exception
        assert "test_operation" in monitor.metrics.phase_times


class TestPipelinePerformanceTracker:
    """Test the PipelinePerformanceTracker class."""

    def test_initialization(self):
        """Test tracker initialization."""
        tracker = PipelinePerformanceTracker()
        assert tracker.phase_results == {}

    def test_add_phase_result(self):
        """Test adding phase results."""
        tracker = PipelinePerformanceTracker()
        result = {"total_processing_time_seconds": 10.0, "record_count": 100}

        tracker.add_phase_result("test_phase", result)

        assert "test_phase" in tracker.phase_results
        assert tracker.phase_results["test_phase"] == result

    def test_print_pipeline_summary(self, caplog):
        """Test pipeline summary printing."""
        tracker = PipelinePerformanceTracker()
        tracker.add_phase_result(
            "phase1", {"total_processing_time_seconds": 10.0, "record_count": 100}
        )
        tracker.add_phase_result(
            "phase2", {"total_processing_time_seconds": 5.0, "record_count": 50}
        )

        with caplog.at_level("INFO"):
            tracker.print_pipeline_summary()

        # Verify logger.info was called multiple times (summary lines)
        log_output = caplog.text
        assert "PIPELINE PERFORMANCE SUMMARY" in log_output

        # Check for key summary elements in log output
        assert "PIPELINE PERFORMANCE SUMMARY" in log_output
        assert "PHASE1:" in log_output
        assert "PHASE2:" in log_output
        assert "TOTAL PIPELINE:" in log_output
