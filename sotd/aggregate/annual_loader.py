"""
Annual data loader for the SOTD Pipeline.

This module provides functionality for loading 12 months of aggregated data
for a given year, including handling missing months and data validation.
"""

import json
from pathlib import Path
from typing import Dict, List, Optional


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

    def get_monthly_file_paths(self) -> List[Path]:
        """
        Get the file paths for all 12 months of the year.

        Returns:
            List of file paths for monthly aggregated data
        """
        return [self.data_dir / f"{self.year}-{month:02d}.json" for month in range(1, 13)]

    def load_monthly_file(self, file_path: Path) -> Optional[Dict]:
        """
        Load a single monthly file.

        Args:
            file_path: Path to the monthly file to load

        Returns:
            Loaded data or None if file doesn't exist or is corrupted
        """
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except FileNotFoundError:
            return None
        except json.JSONDecodeError:
            # Treat corrupted files as missing files
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
        Load all available months for the year.

        Returns:
            Dictionary with monthly data, included months, and missing months
        """
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
            else:
                missing_months.append(month)

        return {
            "monthly_data": monthly_data,
            "included_months": included_months,
            "missing_months": missing_months,
        }

    def load(self) -> Dict:
        """
        Load and validate all monthly data for the year.

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
                # Remove from included months and add to missing
                if month in included_months:
                    included_months.remove(month)
                missing_months.append(month)

        return {
            "year": self.year,
            "monthly_data": validated_data,
            "included_months": included_months,
            "missing_months": missing_months,
            "validation_errors": validation_errors,
        }


def load_annual_data(year: str, data_dir: Path) -> Dict:
    """
    Load annual data for a given year.

    Args:
        year: Year to load data for (YYYY format)
        data_dir: Directory containing monthly aggregated files

    Returns:
        Dictionary with annual data and metadata
    """
    loader = AnnualDataLoader(year, data_dir)
    return loader.load()
