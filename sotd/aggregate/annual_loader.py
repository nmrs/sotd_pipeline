"""
Annual data loader for the SOTD Pipeline.

This module provides functionality for loading 12 months of aggregated data
for a given year, including handling missing months and data validation.
"""

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

from ..utils.file_io import load_json_data
from ..utils.performance_base import BasePerformanceMetrics, BasePerformanceMonitor

logger = logging.getLogger(__name__)


@dataclass
class AnnualLoaderMetrics(BasePerformanceMetrics):
    """Performance metrics for annual data loading."""

    # Annual loader specific fields
    year: str = field(default="")
    files_loaded: int = field(default=0)
    files_missing: int = field(default=0)
    files_corrupted: int = field(default=0)
    validation_errors: int = field(default=0)
    total_file_size_mb: float = field(default=0.0)

    def to_dict(self) -> Dict:
        """Convert metrics to dictionary for JSON serialization."""
        base_dict = super().to_dict()
        base_dict.update(
            {
                "year": self.year,
                "files_loaded": self.files_loaded,
                "files_missing": self.files_missing,
                "files_corrupted": self.files_corrupted,
                "validation_errors": self.validation_errors,
                "total_file_size_mb": self.total_file_size_mb,
            }
        )
        return base_dict


class AnnualLoaderPerformanceMonitor(BasePerformanceMonitor):
    """Performance monitor for annual data loading."""

    def __init__(self, year: str, parallel_workers: int = 1):
        self.year = year
        super().__init__("annual_loader", parallel_workers)
        # Type annotation to help type checker
        self.metrics: AnnualLoaderMetrics = self.metrics

    def _create_metrics(self, phase_name: str, parallel_workers: int) -> AnnualLoaderMetrics:
        """Create annual loader performance metrics."""
        metrics = AnnualLoaderMetrics()
        metrics.year = self.year
        metrics.phase_name = phase_name
        metrics.parallel_workers = parallel_workers
        return metrics

    def print_summary(self) -> None:
        """Print a human-readable performance summary."""
        metrics = self.metrics
        print(f"\n=== Annual Loader Performance Summary ({metrics.year}) ===")
        print(f"Total Processing Time: {metrics.total_processing_time:.2f}s")
        print(f"File I/O Time: {metrics.file_io_time:.2f}s")
        print(f"Files Loaded: {metrics.files_loaded}")
        print(f"Files Missing: {metrics.files_missing}")
        print(f"Files Corrupted: {metrics.files_corrupted}")
        print(f"Validation Errors: {metrics.validation_errors}")
        print(f"Total File Size: {metrics.total_file_size_mb:.1f}MB")
        print(f"Peak Memory Usage: {metrics.peak_memory_mb:.1f}MB")


def validate_monthly_data_structure(data: Dict) -> bool:
    """
    Validate that monthly data has the expected structure.

    Args:
        data: Monthly aggregated data to validate

    Returns:
        True if data structure is valid, False otherwise
    """
    # Check for required top-level keys
    required_keys = {"meta", "data"}
    if not all(key in data for key in required_keys):
        return False

    # Check that data contains required product sections
    data_section = data["data"]
    required_product_sections = {"razors", "blades", "brushes", "soaps"}
    if not all(key in data_section for key in required_product_sections):
        return False

    # Check that product sections are lists of dicts
    for section in required_product_sections:
        if not isinstance(data_section[section], list):
            return False
        for item in data_section[section]:
            if not isinstance(item, dict):
                return False
    return True


class AnnualDataLoader:
    """Loader for annual aggregated data from monthly files."""

    def __init__(self, year: str, data_dir: Path):
        """
        Initialize the annual data loader.

        Args:
            year: Year to load data for (YYYY format)
            data_dir: Directory containing monthly aggregated files
        """
        if not year.isdigit():
            raise ValueError("Year must be numeric")
        if len(year) != 4:
            raise ValueError("Year must be in YYYY format")

        self.year = year
        self.data_dir = data_dir
        self.monitor = AnnualLoaderPerformanceMonitor(year)

    def get_monthly_file_paths(self) -> List[Path]:
        """
        Get the file paths for all 12 months of the year.

        Returns:
            List of file paths for monthly aggregated data
        """
        return [self.data_dir / f"{self.year}-{month:02d}.json" for month in range(1, 13)]

    def load_monthly_file(self, file_path: Path) -> Optional[Dict]:
        """
        Load a single monthly file using unified file I/O patterns.

        Args:
            file_path: Path to the monthly file to load

        Returns:
            Loaded data or None if file doesn't exist or is corrupted
        """
        try:
            data = load_json_data(file_path)
            # Update file size metrics
            if file_path.exists():
                self.monitor.metrics.total_file_size_mb += file_path.stat().st_size / 1024 / 1024
            return data
        except FileNotFoundError:
            self.monitor.metrics.files_missing += 1
            return None
        except Exception as e:
            # Treat any loading error as corrupted file
            logger.warning(f"Failed to load {file_path}: {e}")
            self.monitor.metrics.files_corrupted += 1
            return None

    def validate_data_structure(self, data: Dict) -> bool:
        """
        Validate the structure of monthly data.

        Args:
            data: Monthly data to validate

        Returns:
            True if data structure is valid, False otherwise
        """
        return validate_monthly_data_structure(data)

    def load_all_months(self) -> Dict:
        """
        Load all available months for the year with performance monitoring.

        Returns:
            Dictionary with monthly data, included months, and missing months
        """
        self.monitor.start_total_timing()
        self.monitor.start_file_io_timing()

        try:
            file_paths = self.get_monthly_file_paths()
            monthly_data = {}
            included_months = []
            missing_months = []

            for i, file_path in enumerate(file_paths, 1):
                month = f"{self.year}-{i:02d}"
                data = self.load_monthly_file(file_path)

                if data is not None:
                    monthly_data[month] = data
                    included_months.append(month)
                    self.monitor.metrics.files_loaded += 1
                else:
                    missing_months.append(month)

            return {
                "monthly_data": monthly_data,
                "included_months": included_months,
                "missing_months": missing_months,
            }
        finally:
            self.monitor.end_file_io_timing()

    def load(self) -> Dict:
        """
        Load and validate all monthly data for the year with performance monitoring.

        Returns:
            Dictionary with validated monthly data and metadata
        """
        # Load all months
        load_result = self.load_all_months()
        monthly_data = load_result["monthly_data"]
        included_months = load_result["included_months"]
        missing_months = load_result["missing_months"]

        # Validate data structure and filter out invalid data
        validated_data = {}
        validation_errors = []

        for month, data in monthly_data.items():
            if self.validate_data_structure(data):
                validated_data[month] = data
            else:
                validation_errors.append(f"{month}: Invalid data structure")
                self.monitor.metrics.validation_errors += 1
                # Remove from included months and add to missing
                if month in included_months:
                    included_months.remove(month)
                missing_months.append(month)

        # Update final metrics
        self.monitor.metrics.record_count = len(validated_data)
        self.monitor.end_total_timing()

        return {
            "year": self.year,
            "monthly_data": validated_data,
            "included_months": included_months,
            "missing_months": missing_months,
            "validation_errors": validation_errors,
        }


def load_annual_data(year: str, data_dir: Path) -> Dict:
    """
    Load annual data for a given year using unified patterns.

    Args:
        year: Year to load data for (YYYY format)
        data_dir: Directory containing monthly aggregated files

    Returns:
        Dictionary with annual data and metadata
    """
    loader = AnnualDataLoader(year, data_dir)
    return loader.load()
