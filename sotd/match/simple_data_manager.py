"""
Simple data manager for brush matching data.

This module provides simple data management functionality for the new
brush matching system, replacing the complex parallel data manager.
"""

import json
from pathlib import Path
from typing import Any, Dict


class SimpleDataManager:
    """
    Simple manager for brush data directory.

    Provides functionality for managing data in the single directory:
    - data/matched/ (new brush system)
    """

    def __init__(self, base_path: Path | None = None):
        """
        Initialize the simple data manager.

        Args:
            base_path: Base path for data directories (default: data/)
        """
        self.base_path = base_path or Path("data")
        self.matched_dir = self.base_path / "matched"

    def create_directories(self) -> None:
        """Create the matched data directory if it doesn't exist."""
        self.matched_dir.mkdir(parents=True, exist_ok=True)

    def get_output_path(self, month: str) -> Path:
        """
        Get the output path for a specific month.

        Args:
            month: Month in YYYY-MM format

        Returns:
            Path to the output file
        """
        return self.matched_dir / f"{month}.json"

    def save_data(self, month: str, data: Dict[str, Any]) -> Path:
        """
        Save data for a specific month.

        Args:
            month: Month in YYYY-MM format
            data: Data to save

        Returns:
            Path to the saved file
        """
        output_path = self.get_output_path(month)

        # Ensure directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Save data with proper formatting
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        return output_path

    def load_data(self, month: str) -> Dict[str, Any]:
        """
        Load data for a specific month.

        Args:
            month: Month in YYYY-MM format

        Returns:
            Loaded data

        Raises:
            FileNotFoundError: If the file doesn't exist
        """
        file_path = self.get_output_path(month)

        if not file_path.exists():
            raise FileNotFoundError(f"Data file not found: {file_path}")

        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def file_exists(self, month: str) -> bool:
        """
        Check if a data file exists for a specific month.

        Args:
            month: Month in YYYY-MM format

        Returns:
            True if file exists, False otherwise
        """
        file_path = self.get_output_path(month)
        return file_path.exists()

    def get_metadata(self, month: str) -> Dict[str, Any]:
        """
        Get metadata for a specific month.

        Args:
            month: Month in YYYY-MM format

        Returns:
            Metadata dictionary

        Raises:
            FileNotFoundError: If the file doesn't exist
        """
        data = self.load_data(month)
        return data.get("metadata", {})

    def list_available_months(self) -> list[str]:
        """
        List available months.

        Returns:
            List of available month strings in YYYY-MM format
        """
        months = []
        if self.matched_dir.exists():
            for file_path in self.matched_dir.glob("*.json"):
                month = file_path.stem
                if month and len(month) == 7 and month[4] == "-":  # YYYY-MM format
                    months.append(month)
        return sorted(months)
