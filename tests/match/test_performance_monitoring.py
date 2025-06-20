import tempfile
import time
from pathlib import Path
from unittest.mock import patch

import pytest

from sotd.match.utils.performance import (
    PerformanceMonitor,
    TimingContext,
    TimingStats,
    PerformanceMetrics,
)


class TestTimingStats:
    def test_timing_stats_initialization(self):
        """Test TimingStats initialization."""
        stats = TimingStats()
        assert stats.total_time == 0.0
        assert stats.count == 0
        assert stats.min_time == float("inf")
        assert stats.max_time == 0.0
        assert stats.avg_time == 0.0

    def test_timing_stats_add_timing(self):
        """Test adding timing measurements."""
        stats = TimingStats()

        stats.add_timing(1.0)
        assert stats.total_time == 1.0
        assert stats.count == 1
        assert stats.min_time == 1.0
        assert stats.max_time == 1.0
        assert stats.avg_time == 1.0

        stats.add_timing(2.0)
        assert stats.total_time == 3.0
        assert stats.count == 2
        assert stats.min_time == 1.0
        assert stats.max_time == 2.0
        assert stats.avg_time == 1.5


class TestPerformanceMetrics:
    def test_performance_metrics_to_dict(self):
        """Test converting PerformanceMetrics to dictionary."""
        metrics = PerformanceMetrics()
        metrics.total_processing_time = 10.0
        metrics.record_count = 100
        metrics.records_per_second = 10.0

        result = metrics.to_dict()

        assert result["total_processing_time_seconds"] == 10.0
        assert result["record_count"] == 100
        assert result["records_per_second"] == 10.0
        assert "matcher_times" in result
        assert "memory_usage_mb" in result
        assert "file_sizes_mb" in result


class TestPerformanceMonitor:
    def test_performance_monitor_initialization(self):
        """Test PerformanceMonitor initialization."""
        monitor = PerformanceMonitor()
        assert monitor.metrics.total_processing_time == 0.0
        assert monitor.metrics.record_count == 0
        assert monitor.start_time is None

    def test_total_timing(self):
        """Test total timing functionality."""
        monitor = PerformanceMonitor()

        monitor.start_total_timing()
        time.sleep(0.01)  # Small delay
        monitor.end_total_timing()

        assert monitor.metrics.total_processing_time > 0.0
        assert monitor.metrics.records_per_second == 0.0  # No records set

    def test_file_io_timing(self):
        """Test file I/O timing functionality."""
        monitor = PerformanceMonitor()

        monitor.start_file_io_timing()
        time.sleep(0.01)  # Small delay
        monitor.end_file_io_timing()

        assert monitor.metrics.file_io_time > 0.0

    def test_matching_timing(self):
        """Test matching timing functionality."""
        monitor = PerformanceMonitor()

        monitor.start_matching_timing()
        time.sleep(0.01)  # Small delay
        monitor.end_matching_timing()

        assert monitor.metrics.matching_time > 0.0

    def test_record_matcher_timing(self):
        """Test recording matcher timing."""
        monitor = PerformanceMonitor()

        monitor.record_matcher_timing("razor", 1.0)
        monitor.record_matcher_timing("razor", 2.0)
        monitor.record_matcher_timing("blade", 0.5)

        assert "razor" in monitor.metrics.matcher_times
        assert "blade" in monitor.metrics.matcher_times

        razor_stats = monitor.metrics.matcher_times["razor"]
        assert razor_stats.total_time == 3.0
        assert razor_stats.count == 2
        assert razor_stats.avg_time == 1.5

    def test_set_record_count(self):
        """Test setting record count."""
        monitor = PerformanceMonitor()
        monitor.set_record_count(100)
        assert monitor.metrics.record_count == 100

    def test_set_file_sizes(self):
        """Test setting file size information."""
        monitor = PerformanceMonitor()

        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            f.write("test data")
            temp_path = Path(f.name)

        try:
            monitor.set_file_sizes(temp_path)
            assert monitor.metrics.input_file_size_mb > 0.0
        finally:
            temp_path.unlink()

    def test_calculate_derived_metrics(self):
        """Test calculation of derived metrics."""
        monitor = PerformanceMonitor()
        monitor.metrics.record_count = 100
        monitor.metrics.total_processing_time = 10.0

        monitor._calculate_derived_metrics()

        assert monitor.metrics.avg_time_per_record == 0.1
        assert monitor.metrics.records_per_second == 10.0

    def test_get_summary(self):
        """Test getting performance summary."""
        monitor = PerformanceMonitor()
        monitor.metrics.record_count = 50
        monitor.metrics.total_processing_time = 5.0

        summary = monitor.get_summary()

        assert summary["record_count"] == 50
        assert summary["total_processing_time_seconds"] == 5.0
        assert "matcher_times" in summary
        assert "memory_usage_mb" in summary
        assert "file_sizes_mb" in summary

    @patch("builtins.print")
    def test_print_summary(self, mock_print):
        """Test printing performance summary."""
        monitor = PerformanceMonitor()
        monitor.metrics.record_count = 100
        monitor.metrics.total_processing_time = 10.0
        monitor.metrics.records_per_second = 10.0
        monitor.metrics.avg_time_per_record = 0.1

        monitor.print_summary()

        # Verify that print was called multiple times (summary lines)
        assert mock_print.call_count > 5


class TestTimingContext:
    def test_timing_context(self):
        """Test TimingContext as context manager."""
        monitor = PerformanceMonitor()

        with TimingContext(monitor, "test_operation"):
            time.sleep(0.01)  # Small delay

        assert "test_operation" in monitor.metrics.matcher_times
        stats = monitor.metrics.matcher_times["test_operation"]
        assert stats.count == 1
        assert stats.total_time > 0.0

    def test_timing_context_exception(self):
        """Test TimingContext handles exceptions properly."""
        monitor = PerformanceMonitor()

        with pytest.raises(ValueError):
            with TimingContext(monitor, "test_operation"):
                time.sleep(0.01)
                raise ValueError("Test exception")

        # Should still record timing even with exception
        assert "test_operation" in monitor.metrics.matcher_times
        stats = monitor.metrics.matcher_times["test_operation"]
        assert stats.count == 1
        assert stats.total_time > 0.0


class TestPerformanceMonitoringIntegration:
    def test_performance_monitoring_integration(self):
        """Test integration of performance monitoring components."""
        monitor = PerformanceMonitor()

        # Simulate a complete processing cycle
        monitor.start_total_timing()

        # File I/O
        monitor.start_file_io_timing()
        time.sleep(0.01)
        monitor.end_file_io_timing()

        # Set record count
        monitor.set_record_count(100)

        # Matching operations
        monitor.start_matching_timing()
        with TimingContext(monitor, "razor"):
            time.sleep(0.01)
        with TimingContext(monitor, "blade"):
            time.sleep(0.01)
        monitor.end_matching_timing()

        # More file I/O
        monitor.start_file_io_timing()
        time.sleep(0.01)
        monitor.end_file_io_timing()

        monitor.end_total_timing()

        # Verify all metrics are populated
        summary = monitor.get_summary()
        assert summary["total_processing_time_seconds"] > 0.0
        assert summary["file_io_time_seconds"] > 0.0
        assert summary["matching_time_seconds"] > 0.0
        assert summary["record_count"] == 100
        assert summary["records_per_second"] > 0.0
        assert "razor" in summary["matcher_times"]
        assert "blade" in summary["matcher_times"]
