"""Performance benchmarking utilities for the aggregate phase."""

import json
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

import psutil


class BenchmarkSuite:
    """Comprehensive performance benchmarking suite for aggregate operations."""

    def __init__(self, debug: bool = False):
        self.debug = debug
        self.benchmarks = {}
        self.start_time = None
        self.start_memory = None

    def start_benchmark(self, name: str) -> None:
        """Start a benchmark operation."""
        if self.debug:
            print(f"[BENCHMARK] Starting {name}")

        self.start_time = time.time()
        self.start_memory = self._get_memory_usage()

    def end_benchmark(self, name: str, record_count: Optional[int] = None) -> Dict[str, Any]:
        """End a benchmark operation and return metrics."""
        if not self.start_time:
            return {}

        elapsed = time.time() - self.start_time
        end_memory = self._get_memory_usage()
        memory_delta = end_memory - self.start_memory if self.start_memory else 0

        metrics = {
            "elapsed_seconds": elapsed,
            "record_count": record_count,
            "records_per_second": (record_count / elapsed if record_count and elapsed > 0 else 0),
            "memory_start_mb": self.start_memory,
            "memory_end_mb": end_memory,
            "memory_delta_mb": memory_delta,
            "memory_peak_mb": self._get_peak_memory(),
        }

        self.benchmarks[name] = metrics

        if self.debug:
            print(f"[BENCHMARK] {name} completed in {elapsed:.3f}s")
            if record_count:
                rate = record_count / elapsed
                print(
                    f"[BENCHMARK] {name} processed {record_count} records at {rate:.1f} records/sec"
                )
            print(f"[BENCHMARK] {name} memory: {end_memory:.1f}MB (delta: {memory_delta:+.1f}MB)")

        return metrics

    def _get_memory_usage(self) -> float:
        """Get current memory usage in MB."""
        try:
            process = psutil.Process()
            return process.memory_info().rss / 1024 / 1024
        except (ImportError, AttributeError):
            return 0.0

    def _get_peak_memory(self) -> float:
        """Get peak memory usage in MB."""
        try:
            process = psutil.Process()
            # Use rss as fallback since peak_wset may not be available on all platforms
            return process.memory_info().rss / 1024 / 1024
        except (ImportError, AttributeError):
            return 0.0

    def get_summary(self) -> Dict[str, Any]:
        """Get comprehensive benchmark summary."""
        if not self.benchmarks:
            return {}

        total_time = sum(b.get("elapsed_seconds", 0) for b in self.benchmarks.values())
        total_records = sum(b.get("record_count", 0) for b in self.benchmarks.values())
        total_memory_delta = sum(b.get("memory_delta_mb", 0) for b in self.benchmarks.values())
        peak_memory = max(b.get("memory_peak_mb", 0) for b in self.benchmarks.values())

        summary = {
            "total_elapsed_seconds": total_time,
            "total_records_processed": total_records,
            "overall_throughput": total_records / total_time if total_time > 0 else 0,
            "total_memory_delta_mb": total_memory_delta,
            "peak_memory_mb": peak_memory,
            "operations": self.benchmarks,
        }

        return summary

    def save_benchmark_results(self, file_path: Path) -> None:
        """Save benchmark results to JSON file."""
        summary = self.get_summary()
        if not summary:
            return

        # Add metadata
        summary["metadata"] = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "system_info": self._get_system_info(),
        }

        try:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(summary, f, indent=2, ensure_ascii=False)

            if self.debug:
                print(f"[BENCHMARK] Results saved to {file_path}")
        except Exception as e:
            if self.debug:
                print(f"[BENCHMARK] Failed to save results: {e}")

    def _get_system_info(self) -> Dict[str, Any]:
        """Get system information for benchmarking context."""
        try:
            return {
                "cpu_count": psutil.cpu_count(),
                "memory_total_gb": round(psutil.virtual_memory().total / (1024**3), 2),
                "python_version": (
                    f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
                ),
            }
        except (ImportError, AttributeError):
            return {"error": "System info not available"}

    def compare_with_baseline(self, baseline_path: Path) -> Dict[str, Any]:
        """Compare current benchmark results with a baseline."""
        if not baseline_path.exists():
            return {"error": "Baseline file not found"}

        try:
            with open(baseline_path, "r", encoding="utf-8") as f:
                baseline = json.load(f)
        except Exception as e:
            return {"error": f"Failed to load baseline: {e}"}

        current = self.get_summary()
        if not current:
            return {"error": "No current benchmark data"}

        baseline_time = baseline.get("total_elapsed_seconds", 0)
        baseline_throughput = baseline.get("overall_throughput", 0)
        baseline_memory = baseline.get("total_memory_delta_mb", 0)

        comparison = {
            "total_time_change": current["total_elapsed_seconds"] - baseline_time,
            "total_time_change_percent": (
                (current["total_elapsed_seconds"] - baseline_time) / baseline_time * 100
                if baseline_time > 0
                else 0
            ),
            "throughput_change": current["overall_throughput"] - baseline_throughput,
            "throughput_change_percent": (
                (current["overall_throughput"] - baseline_throughput) / baseline_throughput * 100
                if baseline_throughput > 0
                else 0
            ),
            "memory_change_mb": current["total_memory_delta_mb"] - baseline_memory,
        }

        if self.debug:
            print("\n[BENCHMARK] Performance Comparison:")
            print(
                f"  Time change: {comparison['total_time_change']:+.3f}s "
                f"({comparison['total_time_change_percent']:+.1f}%)"
            )
            print(
                f"  Throughput change: {comparison['throughput_change']:+.1f} records/sec "
                f"({comparison['throughput_change_percent']:+.1f}%)"
            )
            print(f"  Memory change: {comparison['memory_change_mb']:+.1f}MB")

        return comparison


def run_performance_benchmark(
    test_data: List[Dict[str, Any]],
    debug: bool = False,
    save_results: bool = True,
    results_dir: Optional[Path] = None,
) -> Dict[str, Any]:
    """
    Run comprehensive performance benchmarks on aggregate operations.

    Args:
        test_data: Sample enriched data for benchmarking
        debug: Enable debug logging
        save_results: Save benchmark results to file
        results_dir: Directory to save results (default: data/benchmarks)

    Returns:
        Benchmark summary dictionary
    """
    from sotd.aggregate.engine import (
        aggregate_blade_manufacturers,
        aggregate_blades,
        aggregate_brush_fibers,
        aggregate_brush_handle_makers,
        aggregate_brush_knot_makers,
        aggregate_brush_knot_sizes,
        aggregate_brushes,
        aggregate_razor_manufacturers,
        aggregate_razors,
        aggregate_soap_makers,
        aggregate_soaps,
        aggregate_users,
        calculate_basic_metrics,
        filter_matched_records,
    )

    benchmark = BenchmarkSuite(debug=debug)

    if debug:
        print(f"[BENCHMARK] Starting performance benchmark with {len(test_data)} records")

    # Benchmark data filtering
    benchmark.start_benchmark("filter_matched_records")
    matched_records = filter_matched_records(test_data, debug=debug)
    benchmark.end_benchmark("filter_matched_records", len(matched_records))

    # Benchmark basic metrics calculation
    benchmark.start_benchmark("calculate_basic_metrics")
    calculate_basic_metrics(matched_records, debug=debug)
    benchmark.end_benchmark("calculate_basic_metrics", len(matched_records))

    # Benchmark individual aggregations
    aggregation_functions = [
        ("aggregate_razors", aggregate_razors),
        ("aggregate_blades", aggregate_blades),
        ("aggregate_soaps", aggregate_soaps),
        ("aggregate_brushes", aggregate_brushes),
        ("aggregate_users", aggregate_users),
        ("aggregate_razor_manufacturers", aggregate_razor_manufacturers),
        ("aggregate_blade_manufacturers", aggregate_blade_manufacturers),
        ("aggregate_soap_makers", aggregate_soap_makers),
        ("aggregate_brush_knot_makers", aggregate_brush_knot_makers),
        ("aggregate_brush_handle_makers", aggregate_brush_handle_makers),
        ("aggregate_brush_fibers", aggregate_brush_fibers),
        ("aggregate_brush_knot_sizes", aggregate_brush_knot_sizes),
    ]

    for name, func in aggregation_functions:
        benchmark.start_benchmark(name)
        result = func(matched_records, debug=debug)
        benchmark.end_benchmark(name, len(result))

    # Get summary
    summary = benchmark.get_summary()

    # Save results if requested
    if save_results:
        if results_dir is None:
            results_dir = Path("data/benchmarks")

        results_dir.mkdir(parents=True, exist_ok=True)
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        results_file = results_dir / f"aggregate_benchmark_{timestamp}.json"
        benchmark.save_benchmark_results(results_file)

    if debug:
        print("\n[BENCHMARK] Benchmark completed:")
        print(f"  Total time: {summary['total_elapsed_seconds']:.3f}s")
        print(f"  Total records: {summary['total_records_processed']}")
        print(f"  Overall throughput: {summary['overall_throughput']:.1f} records/sec")
        print(f"  Peak memory: {summary['peak_memory_mb']:.1f}MB")

    return summary
