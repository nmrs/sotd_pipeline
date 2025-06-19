"""Performance monitoring utilities for aggregation operations."""

import os
import time
from typing import Any, Dict, Optional

import psutil


class PerformanceMonitor:
    """Monitor performance metrics during aggregation."""

    def __init__(self, debug: bool = False):
        self.debug = debug
        self.start_time = None
        self.start_memory = None
        self.metrics = {}

    def start(self, operation: str):
        """Start timing an operation."""
        if self.debug:
            self.start_time = time.time()
            self.start_memory = self._get_memory_usage()
            print(f"[DEBUG] Starting {operation}")

    def end(self, operation: str, record_count: Optional[int] = None):
        """End timing an operation and record metrics."""
        if self.debug and self.start_time:
            elapsed = time.time() - self.start_time
            end_memory = self._get_memory_usage()
            memory_delta = end_memory - self.start_memory if self.start_memory else 0

            self.metrics[operation] = {
                "elapsed_seconds": elapsed,
                "record_count": record_count,
                "records_per_second": (
                    record_count / elapsed if record_count and elapsed > 0 else 0
                ),
                "memory_start_mb": self.start_memory,
                "memory_end_mb": end_memory,
                "memory_delta_mb": memory_delta,
            }
            print(f"[DEBUG] {operation} completed in {elapsed:.3f}s")
            if record_count:
                rate = record_count / elapsed
                print(
                    f"[DEBUG] {operation} processed {record_count} records "
                    f"at {rate:.1f} records/sec"
                )
            print(f"[DEBUG] {operation} memory: {end_memory:.1f}MB (delta: {memory_delta:+.1f}MB)")

    def _get_memory_usage(self) -> float:
        """Get current memory usage in MB."""
        try:
            process = psutil.Process(os.getpid())
            return process.memory_info().rss / 1024 / 1024  # Convert to MB
        except (ImportError, AttributeError):
            # Fallback if psutil is not available
            return 0.0

    def get_summary(self) -> Dict[str, Any]:
        """Get performance summary."""
        return self.metrics
