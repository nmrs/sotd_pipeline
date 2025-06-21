#!/usr/bin/env python3
"""Annual comparison data loader for year-over-year delta calculations."""

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List

from sotd.utils.file_io import load_json_data
from sotd.utils.performance_base import BasePerformanceMetrics, BasePerformanceMonitor

logger = logging.getLogger(__name__)


@dataclass
class AnnualComparisonMetrics(BasePerformanceMetrics):
    """Performance metrics for annual comparison loading."""

    # Annual comparison specific fields
    requested_years: int = field(default=0)
    loaded_years: int = field(default=0)
    failed_years: int = field(default=0)
    total_file_size_mb: float = field(default=0.0)

    def to_dict(self) -> Dict:
        """Convert metrics to dictionary for JSON serialization."""
        base_dict = super().to_dict()
        base_dict.update(
            {
                "requested_years": self.requested_years,
                "loaded_years": self.loaded_years,
                "failed_years": self.failed_years,
                "total_file_size_mb": self.total_file_size_mb,
            }
        )
        return base_dict


class AnnualComparisonPerformanceMonitor(BasePerformanceMonitor):
    """Performance monitor for annual comparison loading."""

    def __init__(self, parallel_workers: int = 1):
        super().__init__("annual_comparison_loader", parallel_workers)
        # Type annotation to help type checker
        self.metrics: AnnualComparisonMetrics = self.metrics

    def _create_metrics(self, phase_name: str, parallel_workers: int) -> AnnualComparisonMetrics:
        """Create annual comparison performance metrics."""
        metrics = AnnualComparisonMetrics()
        metrics.phase_name = phase_name
        metrics.parallel_workers = parallel_workers
        return metrics

    def print_summary(self) -> None:
        """Print a human-readable performance summary."""
        metrics = self.metrics
        print("\n=== Annual Comparison Loader Performance Summary ===")
        print(f"Total Processing Time: {metrics.total_processing_time:.2f}s")
        print(f"File I/O Time: {metrics.file_io_time:.2f}s")
        print(f"Requested Years: {metrics.requested_years}")
        print(f"Successfully Loaded: {metrics.loaded_years}")
        print(f"Failed to Load: {metrics.failed_years}")
        print(f"Total File Size: {metrics.total_file_size_mb:.1f}MB")
        print(f"Peak Memory Usage: {metrics.peak_memory_mb:.1f}MB")


class AnnualComparisonLoader:
    """Load annual comparison data with performance monitoring."""

    def __init__(self, debug: bool = False):
        """Initialize the annual comparison loader.

        Args:
            debug: Enable debug logging
        """
        self.debug = debug

    def load_comparison_years(self, years: List[str], data_dir: Path) -> Dict[str, dict]:
        """Load annual data for the given years from the specified directory with
        performance monitoring.

        Args:
            years: List of years as strings (e.g., ["2023", "2022"])
            data_dir: Path to directory containing annual data files (e.g., 2023.json)

        Returns:
            Dict mapping year to loaded annual data (only for years successfully loaded)
        """
        monitor = AnnualComparisonPerformanceMonitor()
        monitor.start_total_timing()

        try:
            monitor.metrics.requested_years = len(years)
            results = {}

            for year in years:
                file_path = data_dir / f"{year}.json"

                if not file_path.exists():
                    if self.debug:
                        logger.warning(f"Missing annual file for year {year}")
                        print(f"[DEBUG] Missing annual file for year {year}")
                    monitor.metrics.failed_years += 1
                    continue

                try:
                    monitor.start_file_io_timing()
                    data = load_json_data(file_path)
                    monitor.end_file_io_timing()

                    if not isinstance(data, dict):
                        if self.debug:
                            logger.warning(f"Invalid structure for year {year} (not a dict)")
                            print(f"[DEBUG] Invalid structure for year {year} (not a dict)")
                        monitor.metrics.failed_years += 1
                        continue

                    results[year] = data
                    monitor.metrics.loaded_years += 1
                    monitor.metrics.record_count += 1

                    # Update file size metrics
                    try:
                        file_size_mb = file_path.stat().st_size / (1024 * 1024)
                        monitor.metrics.total_file_size_mb += file_size_mb
                    except OSError:
                        # File size calculation failed, continue
                        pass

                    if self.debug:
                        logger.info(f"Loaded annual file for year {year}")
                        print(f"[DEBUG] Loaded annual file for year {year}")

                except Exception as e:
                    monitor.end_file_io_timing()
                    if self.debug:
                        logger.warning(f"Corrupted or invalid JSON for year {year}: {e}")
                        print(f"[DEBUG] Corrupted or invalid JSON for year {year}")
                    monitor.metrics.failed_years += 1

            return results

        finally:
            monitor.end_total_timing()
            if self.debug:
                monitor.print_summary()
