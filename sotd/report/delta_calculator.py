#!/usr/bin/env python3
"""Delta calculation functionality for trend analysis in reports."""

from typing import Any, Dict, List, Optional, Tuple


class DeltaCalculator:
    """Calculate position-based deltas between current and historical data."""

    def __init__(self, debug: bool = False):
        """Initialize the delta calculator.

        Args:
            debug: Enable debug logging
        """
        self.debug = debug

    def calculate_deltas(
        self,
        current_data: List[Dict[str, Any]],
        historical_data: List[Dict[str, Any]],
        name_key: str = "name",
        max_items: int = 20,
    ) -> List[Dict[str, Any]]:
        """Calculate rank deltas between current and historical data.

        Args:
            current_data: Current period data (with rank field)
            historical_data: Historical period data (with rank field)
            name_key: Key to use for matching items between datasets
            max_items: Maximum number of items to process from current data

        Returns:
            List of current data items with delta information added
        """
        if not isinstance(current_data, list):
            raise ValueError(f"Expected list for current_data, got {type(current_data)}")

        if not isinstance(historical_data, list):
            raise ValueError(f"Expected list for historical_data, got {type(historical_data)}")

        if not current_data:
            return []

        # Create lookup for historical ranks
        historical_ranks = {}
        for item in historical_data:
            if not isinstance(item, dict):
                if self.debug:
                    print("[DEBUG] Skipping invalid historical item")
                continue

            name = item.get(name_key)
            rank = item.get("rank")
            if not name or rank is None:
                if self.debug:
                    print(f"[DEBUG] Historical item missing {name_key} or rank")
                continue

            historical_ranks[name] = rank

        if self.debug:
            print(
                f"[DEBUG] Created historical rank lookup with {len(historical_ranks)} items"
            )

        # Calculate deltas for current data
        results = []
        for item in current_data[:max_items]:
            if not isinstance(item, dict):
                if self.debug:
                    print("[DEBUG] Skipping invalid current item")
                continue

            name = item.get(name_key)
            current_rank = item.get("rank")
            if not name or current_rank is None:
                if self.debug:
                    print(f"[DEBUG] Current item missing {name_key} or rank")
                continue

            historical_rank = historical_ranks.get(name)

            # Calculate delta
            if historical_rank is not None:
                delta = historical_rank - current_rank
                delta_symbol = self._get_delta_symbol(delta)
                delta_text = delta_symbol  # Use symbol only, not +/- format
            else:
                delta = None
                delta_symbol = "n/a"
                delta_text = "n/a"

            # Create result item with delta information
            result_item = item.copy()
            result_item["delta"] = delta
            result_item["delta_symbol"] = delta_symbol
            result_item["delta_text"] = delta_text

            results.append(result_item)

            if self.debug:
                print(
                    f"[DEBUG] {name}: rank {current_rank}, "
                    f"historical {historical_rank}, delta {delta_text} {delta_symbol}"
                )

        return results

    def _get_delta_symbol(self, delta: Optional[int]) -> str:
        """Get Unicode arrow symbol for delta value.

        Args:
            delta: Rank delta (positive = moved up, negative = moved down)

        Returns:
            Unicode arrow symbol with magnitude
        """
        if delta is None:
            return "n/a"  # Not available (new item)
        elif delta > 0:
            return f"↑{delta}"  # Moved up (better position) with magnitude
        elif delta < 0:
            return f"↓{abs(delta)}"  # Moved down (worse position) with magnitude
        else:
            return "="  # No change

    def calculate_category_deltas(
        self,
        current_data: Dict[str, Any],
        historical_data: Dict[str, Any],
        categories: List[str],
        max_items: int = 20,
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Calculate deltas for multiple categories.

        Args:
            current_data: Current period data dictionary
            historical_data: Historical period data dictionary
            categories: List of category names to process
            max_items: Maximum number of items per category

        Returns:
            Dictionary mapping category names to lists with delta information
        """
        if not isinstance(current_data, dict):
            raise ValueError(f"Expected dict for current_data, got {type(current_data)}")

        if not isinstance(historical_data, dict):
            raise ValueError(f"Expected dict for historical_data, got {type(historical_data)}")

        results = {}

        for category in categories:
            current_category_data = current_data.get(category, [])
            historical_category_data = historical_data.get(category, [])

            if not isinstance(current_category_data, list):
                if self.debug:
                    print(f"[DEBUG] Skipping invalid category {category} in current data")
                continue

            if not isinstance(historical_category_data, list):
                if self.debug:
                    print(f"[DEBUG] Skipping invalid category {category} in historical data")
                continue

            try:
                category_deltas = self.calculate_deltas(
                    current_category_data, historical_category_data, max_items=max_items
                )
                results[category] = category_deltas

                if self.debug:
                    print(f"[DEBUG] Calculated deltas for {category}: {len(category_deltas)} items")

            except Exception as e:
                if self.debug:
                    print(f"[DEBUG] Error calculating deltas for {category}: {e}")
                results[category] = current_category_data[:max_items]

        return results

    def format_delta_column(
        self, items: List[Dict[str, Any]], delta_key: str = "delta_text"
    ) -> List[str]:
        """Format delta values for table display.

        Args:
            items: List of items with delta information
            delta_key: Key containing the delta text

        Returns:
            List of formatted delta strings
        """
        formatted_deltas = []

        for item in items:
            if not isinstance(item, dict):
                formatted_deltas.append("n/a")
                continue

            delta_text = item.get(delta_key, "n/a")

            # For symbol-only format, just return the symbol
            if delta_text in ["↑", "↓", "=", "n/a"]:
                formatted_deltas.append(delta_text)
            elif delta_text.startswith(("↑", "↓")) and len(delta_text) > 1:
                # Handle new format with magnitude (e.g., ↑2, ↓3)
                formatted_deltas.append(delta_text)
            elif delta_text == "=":
                formatted_deltas.append("=")
            else:
                # Fallback for any legacy format
                formatted_deltas.append("n/a")

        return formatted_deltas


def calculate_deltas_for_period(
    current_data: Dict[str, Any],
    comparison_data: Dict[str, Tuple[Dict[str, Any], Dict[str, Any]]],
    period: str,
    categories: List[str],
    max_items: int = 20,
    debug: bool = False,
) -> Optional[Dict[str, List[Dict[str, Any]]]]:
    """Calculate deltas for a specific comparison period.

    Args:
        current_data: Current period data
        comparison_data: Dictionary of comparison period data
        period: Period description (e.g., "previous month", "previous year")
        categories: List of categories to process
        max_items: Maximum items per category
        debug: Enable debug logging

    Returns:
        Dictionary of category deltas or None if period not found
    """
    if period not in comparison_data:
        if debug:
            print(f"[DEBUG] Comparison period '{period}' not found in available data")
        return None

    historical_metadata, historical_data = comparison_data[period]

    if not isinstance(historical_data, dict):
        if debug:
            print(f"[DEBUG] Invalid historical data structure for period '{period}'")
        return None

    calculator = DeltaCalculator(debug=debug)
    return calculator.calculate_category_deltas(
        current_data, historical_data, categories, max_items=max_items
    )
