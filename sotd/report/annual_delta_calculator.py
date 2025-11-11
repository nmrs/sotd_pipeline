#!/usr/bin/env python3
"""Annual delta calculation functionality for year-over-year trend analysis."""

import logging
from typing import Any, Dict, List, Optional

from sotd.report.delta_calculator import DeltaCalculator
from sotd.report.utils.tier_identifier import TierIdentifier
from sotd.utils.performance import PerformanceMonitor

logger = logging.getLogger(__name__)


class AnnualDeltaCalculator:
    """Calculate year-over-year deltas for annual reports with performance monitoring."""

    def __init__(self, debug: bool = False):
        """Initialize the annual delta calculator.

        Args:
            debug: Enable debug logging
        """
        self.debug = debug
        self.delta_calculator = DeltaCalculator(debug=debug)
        self.tier_identifier = TierIdentifier()

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
                        "razors": [{"name": "...", "shaves": 100, "rank": 1}, ...],
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
        monitor = PerformanceMonitor("annual_delta")
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
            monitor.metrics.record_count = len(categories)

            # Calculate deltas for each category
            monitor.start_processing_timing()
            results = {}
            categories_with_deltas = 0
            total_delta_calculations = 0

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
                    categories_with_deltas += 1
                    total_delta_calculations += len(category_deltas)

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

            # Update final metrics
            monitor.metrics.record_count = total_delta_calculations

            return results

        finally:
            monitor.end_total_timing()
            if self.debug:
                monitor.print_summary()

    def calculate_tier_based_annual_deltas(
        self,
        current_year_data: Dict[str, Any],
        previous_year_data: Dict[str, Any],
        categories: Optional[List[str]] = None,
        max_items: int = 20,
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Calculate tier-based year-over-year deltas with comprehensive tier analysis.

        Args:
            current_year_data: Current year annual data
            previous_year_data: Previous year annual data
            categories: List of categories to process (None = all available)
            max_items: Maximum number of items per category

        Returns:
            Dictionary mapping category names to lists with enhanced tier-based delta information
        """
        if not isinstance(current_year_data, dict):
            raise ValueError(f"Expected dict for current_year_data, got {type(current_year_data)}")
        if not isinstance(previous_year_data, dict):
            raise ValueError(
                f"Expected dict for previous_year_data, got {type(previous_year_data)}"
            )

        monitor = PerformanceMonitor("annual_tier_delta")
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
                categories = list(current_data.keys())
            else:
                available_categories = set(current_data.keys())
                requested_categories = set(categories)
                categories = list(requested_categories & available_categories)

            if self.debug:
                logger.info(f"Processing tier-based annual deltas for categories: {categories}")

            # Update metrics
            monitor.metrics.record_count = len(categories)

            # Calculate tier-based deltas for each category
            monitor.start_processing_timing()
            results = {}
            categories_with_deltas = 0
            total_delta_calculations = 0

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
                    # Use tier-based delta calculation
                    category_deltas = self.delta_calculator.calculate_tier_based_deltas(
                        current_category_data, previous_category_data, max_items=max_items
                    )
                    results[category] = category_deltas
                    categories_with_deltas += 1
                    total_delta_calculations += len(category_deltas)

                    if self.debug:
                        logger.info(
                            f"Calculated tier-based deltas for {category}: "
                            f"{len(category_deltas)} items"
                        )

                except Exception as e:
                    if self.debug:
                        logger.warning(f"Error calculating tier-based deltas for {category}: {e}")
                    # Return current data without deltas if calculation fails
                    results[category] = current_category_data[:max_items]

            monitor.end_processing_timing()

            # Update final metrics
            monitor.metrics.record_count = total_delta_calculations

            return results

        finally:
            monitor.end_total_timing()
            if self.debug:
                monitor.print_summary()

    def get_annual_tier_analysis(
        self,
        current_year_data: Dict[str, Any],
        previous_year_data: Dict[str, Any],
        categories: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Get comprehensive tier analysis for annual year-over-year comparison.

        Args:
            current_year_data: Current year annual data
            previous_year_data: Previous year annual data
            categories: List of categories to analyze (None = all available)

        Returns:
            Dictionary with comprehensive tier analysis for each category
        """
        if not isinstance(current_year_data, dict) or not isinstance(previous_year_data, dict):
            return {}

        current_data = current_year_data.get("data", {})
        previous_data = previous_year_data.get("data", {})

        if not isinstance(current_data, dict) or not isinstance(previous_data, dict):
            return {}

        # Determine categories to analyze
        if categories is None:
            categories = list(current_data.keys())
        else:
            available_categories = set(current_data.keys())
            requested_categories = set(categories)
            categories = list(requested_categories & available_categories)

        tier_analysis = {}

        for category in categories:
            current_category_data = current_data.get(category, [])
            previous_category_data = previous_data.get(category, [])

            if isinstance(current_category_data, list) and isinstance(previous_category_data, list):
                category_analysis = self.tier_identifier.get_complex_tier_movement(
                    current_category_data, previous_category_data
                )
                tier_analysis[category] = category_analysis

        return tier_analysis

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
        monitor = PerformanceMonitor("annual_delta")
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
            monitor.metrics.record_count = len(categories)

            # Initialize results with current data
            monitor.start_processing_timing()
            results = {}
            total_delta_calculations = 0

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

                    total_delta_calculations += sum(len(deltas) for deltas in year_deltas.values())

                except Exception as e:
                    if self.debug:
                        logger.warning(
                            f"Error calculating deltas for comparison year {comparison_year}: {e}"
                        )

            monitor.end_processing_timing()

            # Update final metrics
            monitor.metrics.record_count = total_delta_calculations

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
            # Rank delta column
            config[f"delta_rank_{year}"] = {
                "title": f"Δ Rank {year}",
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
