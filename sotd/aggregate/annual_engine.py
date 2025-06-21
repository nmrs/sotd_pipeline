"""
Annual aggregation engine for the SOTD Pipeline.

This module provides annual aggregation functionality by combining 12 months
of aggregated data into yearly summaries.
"""

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

from ..utils.performance_base import BasePerformanceMetrics, BasePerformanceMonitor
from .aggregators.annual_aggregator import (
    aggregate_annual_blades,
    aggregate_annual_brushes,
    aggregate_annual_razors,
    aggregate_annual_soaps,
)
from .annual_loader import load_annual_data

logger = logging.getLogger(__name__)


@dataclass
class AnnualPerformanceMetrics(BasePerformanceMetrics):
    """Performance metrics for annual aggregation."""

    # Annual-specific fields
    year: str = field(default="")
    data_loading_time: float = field(default=0.0)
    aggregation_time: float = field(default=0.0)
    month_count: int = field(default=0)
    total_shaves: int = field(default=0)
    unique_shavers: int = field(default=0)

    def to_dict(self) -> Dict:
        """Convert metrics to dictionary for JSON serialization."""
        base_dict = super().to_dict()
        base_dict.update(
            {
                "year": self.year,
                "data_loading_time_seconds": self.data_loading_time,
                "aggregation_time_seconds": self.aggregation_time,
                "month_count": self.month_count,
                "total_shaves": self.total_shaves,
                "unique_shavers": self.unique_shavers,
            }
        )
        return base_dict


class AnnualPerformanceMonitor(BasePerformanceMonitor):
    """Performance monitor for annual aggregation."""

    def __init__(self, year: str, parallel_workers: int = 1):
        self.year = year
        super().__init__("annual_aggregation", parallel_workers)
        # Type annotation to help type checker
        self.metrics: AnnualPerformanceMetrics = self.metrics

    def _create_metrics(self, phase_name: str, parallel_workers: int) -> AnnualPerformanceMetrics:
        """Create annual performance metrics."""
        metrics = AnnualPerformanceMetrics()
        metrics.year = self.year
        metrics.phase_name = phase_name
        metrics.parallel_workers = parallel_workers
        return metrics

    def print_summary(self) -> None:
        """Print a human-readable performance summary."""
        metrics = self.metrics
        print(f"\n=== Annual Aggregation Performance Summary ({metrics.year}) ===")
        print(f"Total Processing Time: {metrics.total_processing_time:.2f}s")
        print(f"Data Loading Time: {metrics.data_loading_time:.2f}s")
        print(f"Aggregation Time: {metrics.aggregation_time:.2f}s")
        print(f"File I/O Time: {metrics.file_io_time:.2f}s")
        print(f"Months Processed: {metrics.month_count}")
        print(f"Total Shaves: {metrics.total_shaves:,}")
        print(f"Unique Shavers: {metrics.unique_shavers:,}")
        print(f"Peak Memory Usage: {metrics.peak_memory_mb:.1f}MB")
        print(f"Input File Size: {metrics.input_file_size_mb:.1f}MB")
        print(f"Output File Size: {metrics.output_file_size_mb:.1f}MB")


class AnnualAggregationEngine:
    """Engine for aggregating monthly data into annual summaries."""

    def __init__(self, year: str, data_dir: Path):
        """
        Initialize the annual aggregation engine.

        Args:
            year: Year to process (YYYY format)
            data_dir: Data directory containing monthly aggregated files
        """
        if not year.isdigit():
            raise ValueError("Year must be numeric")
        if len(year) != 4:
            raise ValueError("Year must be in YYYY format")

        self.year = year
        self.data_dir = data_dir
        self.monitor = AnnualPerformanceMonitor(year)

    def aggregate_razors(self, monthly_data: Dict[str, Dict]) -> List[Dict[str, Any]]:
        """
        Aggregate razor data from monthly data.

        Args:
            monthly_data: Dictionary of monthly data keyed by month

        Returns:
            List of aggregated razor data sorted by shaves desc, unique_users desc
        """
        return aggregate_annual_razors(monthly_data)

    def aggregate_blades(self, monthly_data: Dict[str, Dict]) -> List[Dict[str, Any]]:
        """
        Aggregate blade data from monthly data.

        Args:
            monthly_data: Dictionary of monthly data keyed by month

        Returns:
            List of aggregated blade data sorted by shaves desc, unique_users desc
        """
        return aggregate_annual_blades(monthly_data)

    def aggregate_brushes(self, monthly_data: Dict[str, Dict]) -> List[Dict[str, Any]]:
        """
        Aggregate brush data from monthly data.

        Args:
            monthly_data: Dictionary of monthly data keyed by month

        Returns:
            List of aggregated brush data sorted by shaves desc, unique_users desc
        """
        return aggregate_annual_brushes(monthly_data)

    def aggregate_soaps(self, monthly_data: Dict[str, Dict]) -> List[Dict[str, Any]]:
        """
        Aggregate soap data from monthly data.

        Args:
            monthly_data: Dictionary of monthly data keyed by month

        Returns:
            List of aggregated soap data sorted by shaves desc, unique_users desc
        """
        return aggregate_annual_soaps(monthly_data)

    def generate_metadata(
        self,
        monthly_data: Dict[str, Dict],
        included_months: Optional[List[str]] = None,
        missing_months: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Generate metadata for annual aggregation.

        Args:
            monthly_data: Dictionary of monthly data keyed by month
            included_months: List of months that were successfully loaded
            missing_months: List of months that were missing

        Returns:
            Dictionary with annual metadata
        """
        total_shaves = 0
        total_unique_shavers = 0

        # Calculate totals from included months
        for month, data in monthly_data.items():
            if "meta" in data and isinstance(data["meta"], dict):
                meta = data["meta"]
                total_shaves += meta.get("total_shaves", 0)
                total_unique_shavers += meta.get("unique_shavers", 0)

        # Use provided lists or calculate from monthly_data keys
        if included_months is None:
            included_months = sorted(monthly_data.keys())
        if missing_months is None:
            # Calculate missing months if not provided
            missing_months = []
            for month_num in range(1, 13):
                month_key = f"{self.year}-{month_num:02d}"
                if month_key not in monthly_data:
                    missing_months.append(month_key)

        # Update performance metrics
        self.monitor.metrics.total_shaves = total_shaves
        self.monitor.metrics.unique_shavers = total_unique_shavers
        self.monitor.metrics.month_count = len(included_months)

        return {
            "year": self.year,
            "total_shaves": total_shaves,
            "unique_shavers": total_unique_shavers,
            "included_months": sorted(included_months),
            "missing_months": sorted(missing_months),
        }

    def aggregate_all_categories(
        self,
        monthly_data: Dict[str, Dict],
        included_months: Optional[List[str]] = None,
        missing_months: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Aggregate all product categories from monthly data.

        Args:
            monthly_data: Dictionary of monthly data keyed by month
            included_months: List of months that were successfully loaded
            missing_months: List of months that were missing

        Returns:
            Dictionary with all aggregated data and metadata
        """
        metadata = self.generate_metadata(monthly_data, included_months, missing_months)

        return {
            "metadata": metadata,
            "razors": self.aggregate_razors(monthly_data),
            "blades": self.aggregate_blades(monthly_data),
            "brushes": self.aggregate_brushes(monthly_data),
            "soaps": self.aggregate_soaps(monthly_data),
        }


def aggregate_monthly_data(
    year: str,
    monthly_data: Dict[str, Dict],
    included_months: Optional[List[str]] = None,
    missing_months: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Aggregate monthly data into annual summaries.

    Args:
        year: Year being aggregated (YYYY format)
        monthly_data: Dictionary of monthly data keyed by month
        included_months: List of months that were successfully loaded
        missing_months: List of months that were missing

    Returns:
        Dictionary with annual aggregated data and metadata
    """
    engine = AnnualAggregationEngine(year, Path("/dummy"))  # data_dir not used for aggregation
    return engine.aggregate_all_categories(monthly_data, included_months, missing_months)


def save_annual_data(aggregated_data: Dict[str, Any], year: str, data_dir: Path) -> None:
    """
    Save annual aggregated data to file using unified file I/O patterns.

    Args:
        aggregated_data: Annual aggregated data to save
        year: Year being saved (YYYY format)
        data_dir: Data directory to save to
    """
    # Validate year format
    if not year.isdigit() or len(year) != 4:
        raise ValueError("Year must be in YYYY format")

    # Validate data structure
    if not isinstance(aggregated_data, dict):
        raise ValueError("Invalid annual data structure")

    if "metadata" not in aggregated_data:
        raise ValueError("Invalid annual data structure")

    required_categories = ["razors", "blades", "brushes", "soaps"]
    for category in required_categories:
        if category not in aggregated_data:
            raise ValueError("Invalid annual data structure")

    # Create output directory structure
    output_dir = data_dir / "aggregated" / "annual"
    output_dir.mkdir(parents=True, exist_ok=True)

    # Define output file path
    file_path = output_dir / f"{year}.json"

    # Use unified file I/O utilities for atomic write
    from sotd.utils.file_io import save_json_data

    save_json_data(aggregated_data, file_path, indent=2)


def process_annual(year: str, data_dir: Path, debug: bool = False, force: bool = False) -> None:
    """
    Process annual aggregation for a single year with performance monitoring.

    Args:
        year: Year to process (YYYY format)
        data_dir: Data directory containing monthly aggregated files
        debug: Enable debug logging
        force: Force regeneration of existing files
    """
    monitor = AnnualPerformanceMonitor(year)
    monitor.start_total_timing()

    try:
        if debug:
            logger.info(f"Processing annual aggregation for {year}")
            print(f"[DEBUG] Processing annual aggregation for {year}")
            logger.info(f"Data directory: {data_dir}")
            print(f"[DEBUG] Data directory: {data_dir}")
            logger.info(f"Force: {force}")
            print(f"[DEBUG] Force: {force}")

        # Load monthly data from the aggregated subdirectory
        monthly_data_dir = data_dir / "aggregated"

        monitor.start_file_io_timing()
        load_result = load_annual_data(year, monthly_data_dir)
        monitor.end_file_io_timing()

        monthly_data = load_result["monthly_data"]
        included_months = load_result["included_months"]
        missing_months = load_result["missing_months"]

        if debug:
            logger.info(f"Loaded {len(monthly_data)} months of data")
            print(f"[DEBUG] Loaded {len(monthly_data)} months of data")
            logger.info(f"Included months: {included_months}")
            print(f"[DEBUG] Included months: {included_months}")
            logger.info(f"Missing months: {missing_months}")
            print(f"[DEBUG] Missing months: {missing_months}")

        # Aggregate monthly data
        monitor.start_processing_timing()
        aggregated_data = aggregate_monthly_data(
            year, monthly_data, included_months, missing_months
        )
        monitor.end_processing_timing()

        if debug:
            logger.info("Aggregated data generated")
            print("[DEBUG] Aggregated data generated")
            logger.info(f"Total shaves: {aggregated_data['metadata']['total_shaves']}")
            print(f"[DEBUG] Total shaves: {aggregated_data['metadata']['total_shaves']}")
            logger.info(f"Unique shavers: {aggregated_data['metadata']['unique_shavers']}")
            print(f"[DEBUG] Unique shavers: {aggregated_data['metadata']['unique_shavers']}")

        # Save aggregated data
        monitor.start_file_io_timing()
        save_annual_data(aggregated_data, year, data_dir)
        monitor.end_file_io_timing()

        # Update performance metrics
        monitor.metrics.total_shaves = aggregated_data["metadata"]["total_shaves"]
        monitor.metrics.unique_shavers = aggregated_data["metadata"]["unique_shavers"]
        monitor.metrics.month_count = len(included_months)

        if debug:
            logger.info(f"Annual aggregation for {year} completed")
            print(f"[DEBUG] Annual aggregation for {year} completed")

    finally:
        monitor.end_total_timing()
        if debug:
            monitor.print_summary()


def process_annual_range(
    years: Sequence[str], data_dir: Path, debug: bool = False, force: bool = False
) -> None:
    """
    Process annual aggregation for multiple years with performance monitoring.

    Args:
        years: List of years to process (YYYY format)
        data_dir: Data directory containing monthly aggregated files
        debug: Enable debug logging
        force: Force regeneration of existing files
    """
    if debug:
        logger.info(f"Processing annual aggregation for years: {years}")
        logger.info(f"Data directory: {data_dir}")
        logger.info(f"Force: {force}")

    for year in years:
        try:
            process_annual(year, data_dir, debug=debug, force=force)
        except Exception as e:
            logger.error(f"Failed to process year {year}: {e}")
            if debug:
                import traceback

                logger.error(traceback.format_exc())
