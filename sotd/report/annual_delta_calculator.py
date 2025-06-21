#!/usr/bin/env python3
"""Annual delta calculation functionality for year-over-year trend analysis."""

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from sotd.report.delta_calculator import DeltaCalculator
from sotd.utils.performance_base import BasePerformanceMetrics, BasePerformanceMonitor

logger = logging.getLogger(__name__)


@dataclass
class AnnualDeltaMetrics(BasePerformanceMetrics):
    """Performance metrics for annual delta calculation."""

    # Annual delta specific fields
    current_year: str = field(default="")
    comparison_years: int = field(default=0)
    categories_processed: int = field(default=0)
    categories_with_deltas: int = field(default=0)
    total_delta_calculations: int = field(default=0)

    def to_dict(self) -> Dict:
        """Convert metrics to dictionary for JSON serialization."""
        base_dict = super().to_dict()
        base_dict.update(
            {
                "current_year": self.current_year,
                "comparison_years": self.comparison_years,
                "categories_processed": self.categories_processed,
                "categories_with_deltas": self.categories_with_deltas,
                "total_delta_calculations": self.total_delta_calculations,
            }
        )
        return base_dict


class AnnualDeltaPerformanceMonitor(BasePerformanceMonitor):
    """Performance monitor for annual delta calculation."""

    def __init__(self, current_year: str, parallel_workers: int = 1):
        self.current_year = current_year
        super().__init__("annual_delta", parallel_workers)
        # Type annotation to help type checker
        self.metrics: AnnualDeltaMetrics = self.metrics

    def _create_metrics(self, phase_name: str, parallel_workers: int) -> AnnualDeltaMetrics:
        """Create annual delta performance metrics."""
        metrics = AnnualDeltaMetrics()
        metrics.current_year = self.current_year
        metrics.phase_name = phase_name
        metrics.parallel_workers = parallel_workers
        return metrics

    def print_summary(self) -> None:
        """Print a human-readable performance summary."""
        metrics = self.metrics
        print(f"\n=== Annual Delta Performance Summary ({metrics.current_year}) ===")
        print(f"Total Processing Time: {metrics.total_processing_time:.2f}s")
        print(f"Processing Time: {metrics.processing_time:.2f}s")
        print(f"Comparison Years: {metrics.comparison_years}")
        print(f"Categories Processed: {metrics.categories_processed}")
        print(f"Categories with Deltas: {metrics.categories_with_deltas}")
        print(f"Total Delta Calculations: {metrics.total_delta_calculations}")
        print(f"Peak Memory Usage: {metrics.peak_memory_mb:.1f}MB")


class AnnualDeltaCalculator:
    """Calculate year-over-year deltas for annual reports with performance monitoring."""

    def __init__(self, debug: bool = False):
        """Initialize the annual delta calculator.

        Args:
            debug: Enable debug logging
        """
        self.debug = debug
        self.delta_calculator = DeltaCalculator(debug=debug)

    def calculate_annual_deltas(
        self,
        current_year_data: Dict[str, Any],
        previous_year_data: Dict[str, Any],
        categories: Optional[List[str]] = None,
        max_items: int = 20,
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Calculate year-over-year deltas for annual data with performance monitoring.

        Args:
            current_year_data: Current year annual data with structure:
                {
                    "year": "2024",
                    "meta": {...},
                    "data": {
                        "razors": [{"name": "...", "shaves": 100, "position": 1}, ...],
                        "blades": [...],
                        ...
                    }
                }
            previous_year_data: Previous year annual data with same structure
            categories: List of categories to process (None = all available)
            max_items: Maximum number of items per category

        Returns:
            Dictionary mapping category names to lists with delta information added
        """
        if not isinstance(current_year_data, dict):
            raise ValueError(f"Expected dict for current_year_data, got {type(current_year_data)}")
        if not isinstance(previous_year_data, dict):
            raise ValueError(
                f"Expected dict for previous_year_data, got {type(previous_year_data)}"
            )
        current_year = current_year_data.get("year", "unknown")
        monitor = AnnualDeltaPerformanceMonitor(current_year)
        monitor.start_total_timing()

        try:
            # Extract data sections
            current_data = current_year_data.get("data", None)
            previous_data = previous_year_data.get("data", {})

            if current_data is None:
                raise ValueError("Missing 'data' section in current year data")
            if not isinstance(current_data, dict):
                raise ValueError("Current year data missing or invalid 'data' section")
            if not isinstance(previous_data, dict):
                raise ValueError("Previous year data missing or invalid 'data' section")

            # Determine categories to process
            if categories is None:
                # Use all categories present in current data
                categories = list(current_data.keys())
            else:
                # Validate that requested categories exist in current data
                available_categories = set(current_data.keys())
                requested_categories = set(categories)
                missing_categories = requested_categories - available_categories
                if missing_categories:
                    if self.debug:
                        logger.warning(
                            f"Requested categories not found in current data: {missing_categories}"
                        )
                    # Only process categories that exist
                    categories = list(requested_categories & available_categories)

            if self.debug:
                logger.info(f"Processing categories: {categories}")

            # Update metrics
            monitor.metrics.comparison_years = 1
            monitor.metrics.categories_processed = len(categories)

            # Calculate deltas for each category
            monitor.start_processing_timing()
            results = {}
            for category in categories:
                current_category_data = current_data.get(category, [])
                previous_category_data = previous_data.get(category, [])

                if not isinstance(current_category_data, list):
                    if self.debug:
                        logger.warning(
                            f"Invalid category {category} in current data; returning empty list"
                        )
                    results[category] = []
                    continue

                if not isinstance(previous_category_data, list):
                    if self.debug:
                        logger.warning(f"Skipping invalid category {category} in previous data")
                    continue

                try:
                    category_deltas = self.delta_calculator.calculate_deltas(
                        current_category_data, previous_category_data, max_items=max_items
                    )
                    results[category] = category_deltas
                    monitor.metrics.categories_with_deltas += 1
                    monitor.metrics.total_delta_calculations += len(category_deltas)

                    if self.debug:
                        logger.info(
                            f"Calculated deltas for {category}: {len(category_deltas)} items"
                        )

                except Exception as e:
                    if self.debug:
                        logger.warning(f"Error calculating deltas for {category}: {e}")
                    # Return current data without deltas if calculation fails
                    results[category] = current_category_data[:max_items]

            monitor.end_processing_timing()

            return results

        finally:
            monitor.end_total_timing()
            if self.debug:
                monitor.print_summary()

    def calculate_multi_year_deltas(
        self,
        current_year_data: Dict[str, Any],
        comparison_years_data: Dict[str, Dict[str, Any]],
        categories: Optional[List[str]] = None,
        max_items: int = 20,
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Calculate deltas against multiple comparison years with performance monitoring.

        Args:
            current_year_data: Current year annual data
            comparison_years_data: Dictionary mapping year to annual data:
                {
                    "2023": {year_data},
                    "2022": {year_data},
                    "2020": {year_data}
                }
            categories: List of categories to process (None = all available)
            max_items: Maximum number of items per category

        Returns:
            Dictionary mapping category names to lists with multi-year delta information
        """
        current_year = current_year_data.get("year", "unknown")
        monitor = AnnualDeltaPerformanceMonitor(current_year)
        monitor.start_total_timing()

        try:
            if not comparison_years_data:
                if self.debug:
                    logger.info("No comparison years data provided")
                return {}

            # Start with current year data
            current_data = current_year_data.get("data", {})
            if not isinstance(current_data, dict):
                raise ValueError("Current year data missing or invalid 'data' section")

            # Determine categories to process
            if categories is None:
                categories = list(current_data.keys())
            else:
                available_categories = set(current_data.keys())
                requested_categories = set(categories)
                categories = list(requested_categories & available_categories)

            if self.debug:
                logger.info(f"Processing multi-year deltas for categories: {categories}")

            # Update metrics
            monitor.metrics.comparison_years = len(comparison_years_data)
            monitor.metrics.categories_processed = len(categories)

            # Initialize results with current data
            monitor.start_processing_timing()
            results = {}
            for category in categories:
                current_category_data = current_data.get(category, [])
                if isinstance(current_category_data, list):
                    # Start with copies of current data
                    results[category] = [item.copy() for item in current_category_data[:max_items]]

            # Calculate deltas for each comparison year
            for comparison_year, comparison_data in comparison_years_data.items():
                if not isinstance(comparison_data, dict):
                    if self.debug:
                        logger.warning(
                            f"Skipping invalid comparison data for year {comparison_year}"
                        )
                    continue

                comparison_category_data = comparison_data.get("data", {})
                if not isinstance(comparison_category_data, dict):
                    if self.debug:
                        logger.warning(
                            f"Skipping invalid comparison data structure for year {comparison_year}"
                        )
                    continue

                # Calculate deltas for this comparison year
                try:
                    year_deltas = self.calculate_annual_deltas(
                        current_year_data,
                        comparison_data,
                        categories=categories,
                        max_items=max_items,
                    )

                    # Add delta information to results
                    for category in categories:
                        if category in year_deltas and category in results:
                            # Add delta information to each item
                            for i, item in enumerate(results[category]):
                                if i < len(year_deltas[category]):
                                    delta_item = year_deltas[category][i]
                                    # Add delta information with year prefix
                                    for key, value in delta_item.items():
                                        if key.startswith("delta_"):
                                            new_key = f"{key}_{comparison_year}"
                                            item[new_key] = value

                    monitor.metrics.categories_with_deltas += len(year_deltas)
                    monitor.metrics.total_delta_calculations += sum(
                        len(deltas) for deltas in year_deltas.values()
                    )

                except Exception as e:
                    if self.debug:
                        logger.warning(
                            f"Error calculating deltas for comparison year {comparison_year}: {e}"
                        )

            monitor.end_processing_timing()

            return results

        finally:
            monitor.end_total_timing()
            if self.debug:
                monitor.print_summary()

    def get_delta_column_config(self, comparison_years: List[str]) -> Dict[str, Dict[str, Any]]:
        """Get column configuration for delta columns based on comparison years.

        Args:
            comparison_years: List of comparison years

        Returns:
            Dictionary mapping column names to column configurations
        """
        config = {}
        for year in comparison_years:
            # Position delta column
            config[f"delta_position_{year}"] = {
                "title": f"Δ Pos {year}",
                "align": "right",
                "format": "number",
                "width": 8,
            }
            # Shaves delta column
            config[f"delta_shaves_{year}"] = {
                "title": f"Δ Shaves {year}",
                "align": "right",
                "format": "number",
                "width": 10,
            }
            # Unique users delta column
            config[f"delta_unique_users_{year}"] = {
                "title": f"Δ Users {year}",
                "align": "right",
                "format": "number",
                "width": 10,
            }
        return config
