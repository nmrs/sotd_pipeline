"""Tests for the aggregate benchmarks module."""

import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

from sotd.aggregate.benchmarks import BenchmarkSuite, run_performance_benchmark


class TestBenchmarkSuite:
    """Test the BenchmarkSuite class."""

    def test_init(self):
        """Test BenchmarkSuite initialization."""
        benchmark = BenchmarkSuite(debug=True)
        assert benchmark.debug is True
        assert benchmark.benchmarks == {}
        assert benchmark.start_time is None
        assert benchmark.start_memory is None

    def test_start_benchmark(self):
        """Test starting a benchmark."""
        benchmark = BenchmarkSuite(debug=True)
        benchmark.start_benchmark("test_operation")

        assert benchmark.start_time is not None
        assert benchmark.start_memory is not None

    def test_end_benchmark_without_start(self):
        """Test ending a benchmark without starting it."""
        benchmark = BenchmarkSuite(debug=True)
        result = benchmark.end_benchmark("test_operation", 100)

        assert result == {}

    @patch("sotd.aggregate.benchmarks.psutil.Process")
    def test_end_benchmark_with_start(self, mock_process):
        """Test ending a benchmark after starting it."""
        # Mock memory usage
        mock_memory = Mock()
        mock_memory.rss = 1024 * 1024 * 100  # 100MB
        mock_process.return_value.memory_info.return_value = mock_memory

        benchmark = BenchmarkSuite(debug=True)
        benchmark.start_benchmark("test_operation")
        result = benchmark.end_benchmark("test_operation", 100)

        assert "elapsed_seconds" in result
        assert "record_count" in result
        assert "records_per_second" in result
        assert "memory_start_mb" in result
        assert "memory_end_mb" in result
        assert "memory_delta_mb" in result
        assert "memory_peak_mb" in result
        assert result["record_count"] == 100

    def test_get_summary_empty(self):
        """Test getting summary with no benchmarks."""
        benchmark = BenchmarkSuite()
        summary = benchmark.get_summary()
        assert summary == {}

    @patch("sotd.aggregate.benchmarks.psutil.Process")
    def test_get_summary_with_benchmarks(self, mock_process):
        """Test getting summary with benchmarks."""
        # Mock memory usage
        mock_memory = Mock()
        mock_memory.rss = 1024 * 1024 * 100  # 100MB
        mock_process.return_value.memory_info.return_value = mock_memory

        benchmark = BenchmarkSuite()
        benchmark.start_benchmark("test1")
        benchmark.end_benchmark("test1", 50)

        benchmark.start_benchmark("test2")
        benchmark.end_benchmark("test2", 30)

        summary = benchmark.get_summary()

        assert "total_elapsed_seconds" in summary
        assert "total_records_processed" in summary
        assert "overall_throughput" in summary
        assert "total_memory_delta_mb" in summary
        assert "peak_memory_mb" in summary
        assert "operations" in summary
        assert summary["total_records_processed"] == 80

    @patch("sotd.aggregate.benchmarks.psutil.Process")
    def test_save_benchmark_results(self, mock_process, tmp_path):
        """Test saving benchmark results to file."""
        # Mock memory usage
        mock_memory = Mock()
        mock_memory.rss = 1024 * 1024 * 100  # 100MB
        mock_process.return_value.memory_info.return_value = mock_memory

        benchmark = BenchmarkSuite(debug=True)
        benchmark.start_benchmark("test_operation")
        benchmark.end_benchmark("test_operation", 100)

        results_file = tmp_path / "benchmark_results.json"
        benchmark.save_benchmark_results(results_file)

        assert results_file.exists()

        # Verify JSON content
        with open(results_file, "r") as f:
            data = json.load(f)

        assert "metadata" in data
        assert "timestamp" in data["metadata"]
        assert "system_info" in data["metadata"]
        assert "operations" in data
        assert "test_operation" in data["operations"]

    @patch("sotd.aggregate.benchmarks.psutil.Process")
    def test_compare_with_baseline(self, mock_process, tmp_path):
        """Test comparing with baseline."""
        # Mock memory usage
        mock_memory = Mock()
        mock_memory.rss = 1024 * 1024 * 100  # 100MB
        mock_process.return_value.memory_info.return_value = mock_memory

        # Create baseline file
        baseline_data = {
            "total_elapsed_seconds": 10.0,
            "overall_throughput": 50.0,
            "total_memory_delta_mb": 50.0,
        }
        baseline_file = tmp_path / "baseline.json"
        with open(baseline_file, "w") as f:
            json.dump(baseline_data, f)

        benchmark = BenchmarkSuite(debug=True)
        benchmark.start_benchmark("test_operation")
        benchmark.end_benchmark("test_operation", 100)

        comparison = benchmark.compare_with_baseline(baseline_file)

        assert "total_time_change" in comparison
        assert "total_time_change_percent" in comparison
        assert "throughput_change" in comparison
        assert "throughput_change_percent" in comparison
        assert "memory_change_mb" in comparison

    def test_compare_with_nonexistent_baseline(self):
        """Test comparing with non-existent baseline file."""
        benchmark = BenchmarkSuite()
        comparison = benchmark.compare_with_baseline(Path("nonexistent.json"))

        assert "error" in comparison
        assert comparison["error"] == "Baseline file not found"

    def test_compare_without_benchmark_data(self):
        """Test comparing without benchmark data."""
        benchmark = BenchmarkSuite()
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump({"test": "data"}, f)
            baseline_file = Path(f.name)

        try:
            comparison = benchmark.compare_with_baseline(baseline_file)
            assert "error" in comparison
            assert comparison["error"] == "No current benchmark data"
        finally:
            baseline_file.unlink()

    @patch("sotd.aggregate.benchmarks.psutil.cpu_count")
    @patch("sotd.aggregate.benchmarks.psutil.virtual_memory")
    def test_get_system_info(self, mock_virtual_memory, mock_cpu_count):
        """Test getting system information."""
        mock_cpu_count.return_value = 8
        mock_memory = Mock()
        mock_memory.total = 16 * 1024**3  # 16GB
        mock_virtual_memory.return_value = mock_memory

        benchmark = BenchmarkSuite()
        system_info = benchmark._get_system_info()

        assert "cpu_count" in system_info
        assert "memory_total_gb" in system_info
        assert "python_version" in system_info
        assert system_info["cpu_count"] == 8
        assert system_info["memory_total_gb"] == 16.0

    def test_get_system_info_without_psutil(self):
        """Test getting system info when psutil is not available."""
        with patch("sotd.aggregate.benchmarks.psutil", None):
            benchmark = BenchmarkSuite()
            system_info = benchmark._get_system_info()

            assert "error" in system_info
            assert system_info["error"] == "System info not available"


class TestRunPerformanceBenchmark:
    """Test the run_performance_benchmark function."""

    def test_run_performance_benchmark_with_synthetic_data(self, tmp_path):
        """Test running performance benchmark with synthetic data."""
        # Create synthetic test data
        test_data = [
            {
                "id": "test_1",
                "author": "user1",
                "razor": {
                    "matched": {
                        "brand": "Merkur",
                        "model": "34C",
                        "format": "DE",
                        "match_type": "exact",
                    }
                },
                "blade": {"matched": {"brand": "Astra", "model": "SP", "match_type": "exact"}},
                "soap": {
                    "matched": {"maker": "Barrister", "scent": "Seville", "match_type": "exact"}
                },
                "brush": {
                    "matched": {
                        "brand": "Simpson",
                        "model": "Chubby 2",
                        "fiber": "badger",
                        "knot_size_mm": 26,
                        "match_type": "exact",
                    }
                },
            }
        ] * 10  # 10 records

        results_dir = tmp_path / "benchmarks"
        summary = run_performance_benchmark(
            test_data=test_data, debug=True, save_results=True, results_dir=results_dir
        )

        assert "total_elapsed_seconds" in summary
        assert "total_records_processed" in summary
        assert "overall_throughput" in summary
        assert "operations" in summary

        # Check that results file was created
        benchmark_files = list(results_dir.glob("aggregate_benchmark_*.json"))
        assert len(benchmark_files) == 1

    def test_run_performance_benchmark_without_save(self):
        """Test running performance benchmark without saving results."""
        test_data = [{"id": "test", "author": "user"}] * 5

        summary = run_performance_benchmark(test_data=test_data, debug=False, save_results=False)

        assert "total_elapsed_seconds" in summary
        assert "total_records_processed" in summary
        assert "operations" in summary

    def test_run_performance_benchmark_empty_data(self):
        """Test running performance benchmark with empty data."""
        summary = run_performance_benchmark(test_data=[], debug=False, save_results=False)

        assert "total_elapsed_seconds" in summary
        assert "total_records_processed" in summary
        assert summary["total_records_processed"] == 0
