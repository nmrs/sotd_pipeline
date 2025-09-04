#!/usr/bin/env python3
"""Delta calculation functionality for trend analysis in reports."""

from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

from sotd.report.utils.tier_identifier import TierIdentifier


class DeltaCalculator:
    """Calculate position-based deltas between current and historical data."""

    def __init__(self, debug: bool = False):
        """Initialize the delta calculator.

        Args:
            debug: Enable debug logging
        """
        self.debug = debug
        self.tier_identifier = TierIdentifier()

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

        # OPTIMIZED: Use pandas operations for vectorized historical rank lookup
        # Convert historical data to DataFrame for vectorized operations
        historical_df = pd.DataFrame(historical_data)

        if historical_df.empty:
            if self.debug:
                print("[DEBUG] No historical data available")
            # Return current data with delta fields set to indicate no comparison possible
            current_df = pd.DataFrame(current_data[:max_items])
            if current_df.empty:
                return []

            # Add delta fields with no comparison values
            current_df["delta"] = None
            current_df["delta_symbol"] = "n/a"
            current_df["delta_text"] = "n/a"

            # Convert back to list of dictionaries
            results = [
                {str(k): v for k, v in item.items()} for item in current_df.to_dict("records")
            ]

            if self.debug:
                print(
                    "[DEBUG] No historical data, returning "
                    f"{len(results)} current items without deltas"
                )

            return results

        # Filter valid items and create rank mapping using pandas operations
        valid_historical = historical_df[
            (historical_df[name_key].notna()) & (historical_df["rank"].notna())
        ]

        if valid_historical.empty:
            if self.debug:
                print("[DEBUG] No valid historical items found")
            return []

        # Create lookup for historical ranks using pandas operations
        historical_ranks = valid_historical.set_index(name_key)["rank"].to_dict()

        if self.debug:
            print(f"[DEBUG] Created historical rank lookup with {len(historical_ranks)} items")

        # OPTIMIZED: Use pandas operations for vectorized current data processing
        # Convert current data to DataFrame for vectorized operations
        current_df = pd.DataFrame(current_data[:max_items])

        if current_df.empty:
            if self.debug:
                print("[DEBUG] No current data to process")
            return []

        # Filter valid items using pandas operations
        # Check if rank column exists before filtering
        if "rank" not in current_df.columns:
            if self.debug:
                print("[DEBUG] No rank column found in current data, skipping delta calculations")
            return []

        # Filter to only include items that have both name and rank values
        # Create a copy to avoid SettingWithCopyWarning
        valid_current = current_df[
            (current_df[name_key].notna()) & (current_df["rank"].notna())
        ].copy()

        if valid_current.empty:
            if self.debug:
                print("[DEBUG] No valid current items found")
            return []

        # Create vectorized delta calculation using pandas operations
        # Map historical ranks to current data
        valid_current.loc[:, "historical_rank"] = valid_current[name_key].map(historical_ranks)

        # Calculate deltas using vectorized operations
        def calculate_delta_vectorized(row):
            historical_rank = row["historical_rank"]
            current_rank = row["rank"]

            if pd.isna(historical_rank):
                return None, "n/a", "n/a"

            try:
                # Convert ranks to integers for calculation (handle string ranks like "2=")
                # Handle float ranks by converting to string and removing decimal part
                hist_rank_str = str(historical_rank).split("=")[0]
                curr_rank_str = str(current_rank).split("=")[0]

                # Remove decimal part if present (e.g., "2.0" -> "2")
                hist_rank_int = int(float(hist_rank_str))
                curr_rank_int = int(float(curr_rank_str))

                delta = hist_rank_int - curr_rank_int
                delta_symbol = self._get_delta_symbol(delta)
                delta_text = delta_symbol  # Use symbol only, not +/- format
                return delta, delta_symbol, delta_text
            except (ValueError, AttributeError):
                # If conversion fails, skip delta calculation
                return None, "n/a", "n/a"

        # Apply vectorized delta calculation
        delta_results = valid_current.apply(calculate_delta_vectorized, axis=1)

        # Add delta fields to DataFrame using .loc to avoid SettingWithCopyWarning
        # Set dtype to object from the start to allow None values
        valid_current.loc[:, "delta"] = delta_results.apply(lambda x: x[0]).astype(object)
        valid_current.loc[:, "delta_symbol"] = delta_results.apply(lambda x: x[1]).astype(object)
        valid_current.loc[:, "delta_text"] = delta_results.apply(lambda x: x[2]).astype(object)

        # Convert NaN values back to None for consistency
        valid_current.loc[:, "delta"] = valid_current["delta"].replace({np.nan: None})
        valid_current.loc[:, "delta_symbol"] = valid_current["delta_symbol"].replace({np.nan: None})
        valid_current.loc[:, "delta_text"] = valid_current["delta_text"].replace({np.nan: None})

        # Convert back to list of dictionaries with string keys for type compatibility
        results = [
            {str(k): v for k, v in item.items()}
            for item in valid_current.drop(columns=["historical_rank"]).to_dict("records")
        ]

        if self.debug:
            print(f"[DEBUG] Processed {len(results)} items with delta calculations")

        return results

    def calculate_tier_based_deltas(
        self,
        current_data: List[Dict[str, Any]],
        historical_data: List[Dict[str, Any]],
        name_key: str = "name",
        max_items: int = 20,
    ) -> List[Dict[str, Any]]:
        """Calculate tier-based deltas with comprehensive tier analysis.

        Args:
            current_data: Current period data (with rank field)
            historical_data: Historical period data (with rank field)
            name_key: Key to use for matching items between datasets
            max_items: Maximum number of items to process from current data

        Returns:
            List of current data items with enhanced tier-based delta information
        """
        if not isinstance(current_data, list):
            raise ValueError(f"Expected list for current_data, got {type(current_data)}")

        if not isinstance(historical_data, list):
            raise ValueError(f"Expected list for historical_data, got {type(historical_data)}")

        if not current_data:
            return []

        # Get comprehensive tier movement information
        tier_analysis = self.tier_identifier.get_complex_tier_movement(
            current_data, historical_data
        )

        if self.debug:
            print(f"[DEBUG] Tier analysis: {tier_analysis}")

        # Calculate basic deltas
        basic_results = self.calculate_deltas(current_data, historical_data, name_key, max_items)

        # Enhance results with tier information
        enhanced_results = []
        for item in basic_results:
            enhanced_item = item.copy()

            # Add tier analysis information
            name = item.get(name_key)
            if name in tier_analysis["tier_changes"]:
                hist_rank, curr_rank = tier_analysis["tier_changes"][name]
                enhanced_item["tier_change"] = (hist_rank, curr_rank)
                # Convert ranks to integers for calculation (handle string ranks like "2=")
                try:
                    hist_rank_int = int(str(hist_rank).split("=")[0])
                    curr_rank_int = int(str(curr_rank).split("=")[0])
                    enhanced_item["tier_movement"] = hist_rank_int - curr_rank_int
                except (ValueError, AttributeError):
                    # If conversion fails, skip tier movement calculation
                    enhanced_item["tier_movement"] = None

            # Add tier structure information
            enhanced_item["tier_structure_changed"] = tier_analysis["structure_changed"]
            enhanced_item["tier_restructured"] = tier_analysis["restructured"]

            enhanced_results.append(enhanced_item)

        return enhanced_results

    def get_tier_analysis(
        self,
        current_data: List[Dict[str, Any]],
        historical_data: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Get comprehensive tier analysis for current vs historical data.

        Args:
            current_data: Current period data (with rank field)
            historical_data: Historical period data (with rank field)

        Returns:
            Dictionary with comprehensive tier analysis information
        """
        if not isinstance(current_data, list) or not isinstance(historical_data, list):
            return {}

        return self.tier_identifier.get_complex_tier_movement(current_data, historical_data)

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
