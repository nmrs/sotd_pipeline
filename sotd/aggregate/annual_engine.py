"""
Annual aggregation engine for the SOTD Pipeline.

This module provides annual aggregation functionality by combining 12 months
of aggregated data into yearly summaries.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

import pandas as pd

from .annual_loader import load_annual_data


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

    def aggregate_razors(self, monthly_data: Dict[str, Dict]) -> List[Dict[str, Any]]:
        """
        Aggregate razor data from monthly data.

        Args:
            monthly_data: Dictionary of monthly data keyed by month

        Returns:
            List of aggregated razor data sorted by shaves desc, unique_users desc
        """
        return self._aggregate_product_category(monthly_data, "razors")

    def aggregate_blades(self, monthly_data: Dict[str, Dict]) -> List[Dict[str, Any]]:
        """
        Aggregate blade data from monthly data.

        Args:
            monthly_data: Dictionary of monthly data keyed by month

        Returns:
            List of aggregated blade data sorted by shaves desc, unique_users desc
        """
        return self._aggregate_product_category(monthly_data, "blades")

    def aggregate_brushes(self, monthly_data: Dict[str, Dict]) -> List[Dict[str, Any]]:
        """
        Aggregate brush data from monthly data.

        Args:
            monthly_data: Dictionary of monthly data keyed by month

        Returns:
            List of aggregated brush data sorted by shaves desc, unique_users desc
        """
        return self._aggregate_product_category(monthly_data, "brushes")

    def aggregate_soaps(self, monthly_data: Dict[str, Dict]) -> List[Dict[str, Any]]:
        """
        Aggregate soap data from monthly data.

        Args:
            monthly_data: Dictionary of monthly data keyed by month

        Returns:
            List of aggregated soap data sorted by shaves desc, unique_users desc
        """
        return self._aggregate_product_category(monthly_data, "soaps")

    def _aggregate_product_category(
        self, monthly_data: Dict[str, Dict], category: str
    ) -> List[Dict[str, Any]]:
        """
        Aggregate a product category from monthly data.

        Args:
            monthly_data: Dictionary of monthly data keyed by month
            category: Product category to aggregate (razors, blades, brushes, soaps)

        Returns:
            List of aggregated data sorted by shaves desc, unique_users desc
        """
        if not monthly_data:
            return []

        # Collect all items from all months
        all_items = []
        for month, data in monthly_data.items():
            if "data" in data and isinstance(data["data"], dict):
                data_section = data["data"]
                if category in data_section and isinstance(data_section[category], list):
                    for item in data_section[category]:
                        if isinstance(item, dict) and "name" in item:
                            all_items.append(item)

        if not all_items:
            return []

        # Convert to DataFrame for efficient aggregation
        df = pd.DataFrame(all_items)

        # Group by name and aggregate
        grouped = df.groupby("name").agg({"shaves": "sum", "unique_users": "sum"}).reset_index()

        # Sort by shaves desc, unique_users desc
        grouped = grouped.sort_values(["shaves", "unique_users"], ascending=[False, False])

        # Add position field (1-based rank)
        grouped = grouped.reset_index(drop=True).assign(position=lambda df: range(1, len(df) + 1))

        # Convert to list of dictionaries
        result = []
        for _, row in grouped.iterrows():
            result.append(
                {
                    "name": row["name"],
                    "shaves": int(row["shaves"]),
                    "unique_users": int(row["unique_users"]),
                    "position": int(row["position"]),
                }
            )

        return result

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
    Save annual aggregated data to file.

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
    Process annual aggregation for a single year.

    Args:
        year: Year to process (YYYY format)
        data_dir: Data directory containing monthly aggregated files
        debug: Enable debug logging
        force: Force regeneration of existing files
    """
    if debug:
        print(f"[DEBUG] Processing annual aggregation for {year}")
        print(f"[DEBUG] Data directory: {data_dir}")
        print(f"[DEBUG] Force: {force}")

    # Load monthly data
    load_result = load_annual_data(year, data_dir)
    monthly_data = load_result["monthly_data"]
    included_months = load_result["included_months"]
    missing_months = load_result["missing_months"]

    if debug:
        print(f"[DEBUG] Loaded {len(monthly_data)} months of data")
        print(f"[DEBUG] Included months: {included_months}")
        print(f"[DEBUG] Missing months: {missing_months}")

    # Aggregate monthly data
    aggregated_data = aggregate_monthly_data(year, monthly_data, included_months, missing_months)

    if debug:
        print("[DEBUG] Aggregated data generated")
        print(f"[DEBUG] Total shaves: {aggregated_data['metadata']['total_shaves']}")
        print(f"[DEBUG] Unique shavers: {aggregated_data['metadata']['unique_shavers']}")

    # Save aggregated data
    save_annual_data(aggregated_data, year, data_dir)

    if debug:
        print(f"[DEBUG] Annual aggregation for {year} completed")


def process_annual_range(
    years: Sequence[str], data_dir: Path, debug: bool = False, force: bool = False
) -> None:
    """
    Process annual aggregation for multiple years.

    Args:
        years: List of years to process (YYYY format)
        data_dir: Data directory containing monthly aggregated files
        debug: Enable debug logging
        force: Force regeneration of existing files
    """
    if debug:
        print(f"[DEBUG] Processing annual aggregation for years: {years}")
        print(f"[DEBUG] Data directory: {data_dir}")
        print(f"[DEBUG] Force: {force}")

    for year in years:
        try:
            process_annual(year, data_dir, debug=debug, force=force)
        except Exception as e:
            print(f"[ERROR] Failed to process year {year}: {e}")
            if debug:
                import traceback

                traceback.print_exc()
