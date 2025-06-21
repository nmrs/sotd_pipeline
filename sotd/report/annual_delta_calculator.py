#!/usr/bin/env python3
"""Annual delta calculation functionality for year-over-year trend analysis."""

from typing import Any, Dict, List, Optional

from sotd.report.delta_calculator import DeltaCalculator


class AnnualDeltaCalculator:
    """Calculate year-over-year deltas for annual reports."""

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
        """Calculate year-over-year deltas for annual data.

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
                    print(
                        f"[DEBUG] Requested categories not found in current data: "
                        f"{missing_categories}"
                    )
                # Only process categories that exist
                categories = list(requested_categories & available_categories)

        if self.debug:
            print(f"[DEBUG] Processing categories: {categories}")

        # Calculate deltas for each category
        results = {}
        for category in categories:
            current_category_data = current_data.get(category, [])
            previous_category_data = previous_data.get(category, [])

            if not isinstance(current_category_data, list):
                if self.debug:
                    print(
                        f"[DEBUG] Invalid category {category} in current data; returning empty list"
                    )
                results[category] = []
                continue

            if not isinstance(previous_category_data, list):
                if self.debug:
                    print(f"[DEBUG] Skipping invalid category {category} in previous data")
                continue

            try:
                category_deltas = self.delta_calculator.calculate_deltas(
                    current_category_data, previous_category_data, max_items=max_items
                )
                results[category] = category_deltas

                if self.debug:
                    print(f"[DEBUG] Calculated deltas for {category}: {len(category_deltas)} items")

            except Exception as e:
                if self.debug:
                    print(f"[DEBUG] Error calculating deltas for {category}: {e}")
                # Return current data without deltas if calculation fails
                results[category] = current_category_data[:max_items]

        return results

    def calculate_multi_year_deltas(
        self,
        current_year_data: Dict[str, Any],
        comparison_years_data: Dict[str, Dict[str, Any]],
        categories: Optional[List[str]] = None,
        max_items: int = 20,
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Calculate deltas against multiple comparison years.

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
        if not comparison_years_data:
            if self.debug:
                print("[DEBUG] No comparison years data provided")
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
            print(f"[DEBUG] Processing multi-year deltas for categories: {categories}")

        # Initialize results with current data
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
                    print(f"[DEBUG] Skipping invalid comparison data for year {comparison_year}")
                continue

            comparison_category_data = comparison_data.get("data", {})
            if not isinstance(comparison_category_data, dict):
                if self.debug:
                    print(
                        f"[DEBUG] Skipping invalid comparison data structure for year "
                        f"{comparison_year}"
                    )
                continue

            # Calculate deltas for this comparison year
            try:
                year_deltas = self.calculate_annual_deltas(
                    current_year_data, comparison_data, categories=categories, max_items=max_items
                )

                # Add delta information to results
                for category in categories:
                    if category in year_deltas and category in results:
                        year_category_deltas = year_deltas[category]
                        result_category = results[category]

                        # Add delta information for this year
                        for i, item in enumerate(result_category):
                            if i < len(year_category_deltas):
                                year_item = year_category_deltas[i]
                                # Add delta information for this year
                                delta_symbol_key = f"delta_{comparison_year}_symbol"
                                delta_text_key = f"delta_{comparison_year}_text"

                                item[delta_symbol_key] = year_item.get("delta_symbol", "n/a")
                                item[delta_text_key] = year_item.get("delta_text", "n/a")

                if self.debug:
                    print(f"[DEBUG] Added deltas for comparison year {comparison_year}")

            except Exception as e:
                if self.debug:
                    print(
                        f"[DEBUG] Error calculating deltas for comparison year "
                        f"{comparison_year}: {e}"
                    )
                # Add n/a for this year if calculation fails
                for category in categories:
                    if category in results:
                        for item in results[category]:
                            delta_symbol_key = f"delta_{comparison_year}_symbol"
                            delta_text_key = f"delta_{comparison_year}_text"

                            item[delta_symbol_key] = "n/a"
                            item[delta_text_key] = "n/a"

        return results

    def get_delta_column_config(self, comparison_years: List[str]) -> Dict[str, Dict[str, Any]]:
        """Get column configuration for delta columns.

        Args:
            comparison_years: List of comparison years (e.g., ["2023", "2022", "2020"])

        Returns:
            Dictionary mapping column keys to column configuration
        """
        column_config = {}

        for year in comparison_years:
            delta_symbol_key = f"delta_{year}_symbol"
            delta_text_key = f"delta_{year}_text"

            column_config[delta_symbol_key] = {
                "display_name": f"Δ vs {year}",
                "format": "delta",
            }

            column_config[delta_text_key] = {
                "display_name": f"Δ vs {year}",
                "format": "delta",
            }

        return column_config
