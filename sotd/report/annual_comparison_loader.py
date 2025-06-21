#!/usr/bin/env python3
"""Annual comparison data loader for year-over-year delta calculations."""

import logging
from pathlib import Path
from typing import Dict, List

from sotd.utils.file_io import load_json_data
from sotd.utils.performance import PerformanceMonitor

logger = logging.getLogger(__name__)


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
        results = {}
        total_file_size_mb = 0.0
        monitor = PerformanceMonitor("annual_comparison_loader")
        monitor.start_total_timing()

        try:
            monitor.metrics.record_count = 0

            for year in years:
                file_path = data_dir / f"{year}.json"

                if not file_path.exists():
                    if self.debug:
                        logger.warning(f"Missing annual file for year {year}")
                        print(f"[DEBUG] Missing annual file for year {year}")
                    continue

                try:
                    monitor.start_file_io_timing()
                    data = load_json_data(file_path)
                    monitor.end_file_io_timing()

                    if not isinstance(data, dict):
                        if self.debug:
                            logger.warning(f"Invalid structure for year {year} (not a dict)")
                            print(f"[DEBUG] Invalid structure for year {year} (not a dict)")
                        continue

                    results[year] = data
                    monitor.metrics.record_count += 1

                    # Update file size metrics
                    try:
                        file_size_mb = file_path.stat().st_size / (1024 * 1024)
                        total_file_size_mb += file_size_mb
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

            if self.debug:
                print(f"[DEBUG] Total years requested: {len(years)}")
                print(f"[DEBUG] Successfully loaded: {len(results)}")
                print(f"[DEBUG] Total file size: {total_file_size_mb:.1f}MB")

            return results

        finally:
            monitor.end_total_timing()
            if self.debug:
                print("\n=== Annual Comparison Loader Performance Summary ===")
                print(f"Total Processing Time: {monitor.metrics.total_processing_time:.2f}s")
                print(f"File I/O Time: {monitor.metrics.file_io_time:.2f}s")
                print(f"Requested Years: {len(years)}")
                print(f"Successfully Loaded: {len(results)}")
                print(f"Total File Size: {total_file_size_mb:.1f}MB")
                print(f"Peak Memory Usage: {monitor.metrics.peak_memory_mb:.1f}MB")
