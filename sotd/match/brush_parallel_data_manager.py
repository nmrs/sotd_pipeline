"""
Brush parallel data manager for managing parallel data directories.

This module provides functionality for managing parallel data directories
for brush system comparison, allowing both current and new brush systems
to store data in separate directories.
"""

import json
from pathlib import Path
from typing import Any, Dict, List


class BrushParallelDataManager:
    """
    Manager for parallel brush data directories.

    Provides functionality for managing data in parallel directories:
    - data/matched/ (current brush system)
    - data/matched_new/ (new brush system)
    """

    def __init__(self, base_path: Path | None = None):
        """
        Initialize the brush parallel data manager.

        Args:
            base_path: Base path for data directories (default: data/)
        """
        self.base_path = base_path or Path("data")
        self.legacy_dir = self.base_path / "matched"
        self.new_dir = self.base_path / "matched_new"

    def create_directories(self) -> None:
        """Create the parallel data directories if they don't exist."""
        self.legacy_dir.mkdir(parents=True, exist_ok=True)
        self.new_dir.mkdir(parents=True, exist_ok=True)

    def get_output_path(self, month: str, brush_system: str) -> Path:
        """
        Get the output path for a specific month and brush system.

        Args:
            month: Month in YYYY-MM format
            brush_system: Brush system ('legacy' or 'new')

        Returns:
            Path to the output file

        Raises:
            ValueError: If brush_system is invalid
        """
        self._validate_system_name(brush_system)

        if brush_system == "legacy":
            return self.legacy_dir / f"{month}.json"
        else:  # brush_system == "new"
            return self.new_dir / f"{month}.json"

    def save_data(self, month: str, data: Dict[str, Any], brush_system: str) -> Path:
        """
        Save data for a specific month and brush system.

        Args:
            month: Month in YYYY-MM format
            data: Data to save
            brush_system: Brush system ('legacy' or 'new')

        Returns:
            Path to the saved file

        Raises:
            ValueError: If brush_system is invalid
        """
        output_path = self.get_output_path(month, brush_system)

        # Ensure directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Save data with proper formatting
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        return output_path

    def load_data(self, month: str, brush_system: str) -> Dict[str, Any]:
        """
        Load data for a specific month and brush system.

        Args:
            month: Month in YYYY-MM format
            brush_system: Brush system ('legacy' or 'new')

        Returns:
            Loaded data

        Raises:
            FileNotFoundError: If the file doesn't exist
            ValueError: If brush_system is invalid
        """
        file_path = self.get_output_path(month, brush_system)

        if not file_path.exists():
            raise FileNotFoundError(f"Data file not found: {file_path}")

        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def file_exists(self, month: str, brush_system: str) -> bool:
        """
        Check if a data file exists for a specific month and brush system.

        Args:
            month: Month in YYYY-MM format
            brush_system: Brush system ('legacy' or 'new')

        Returns:
            True if file exists, False otherwise

        Raises:
            ValueError: If brush_system is invalid
        """
        file_path = self.get_output_path(month, brush_system)
        return file_path.exists()

    def get_metadata(self, month: str, brush_system: str) -> Dict[str, Any]:
        """
        Get metadata for a specific month and brush system.

        Args:
            month: Month in YYYY-MM format
            brush_system: Brush system ('legacy' or 'new')

        Returns:
            Metadata dictionary

        Raises:
            FileNotFoundError: If the file doesn't exist
            ValueError: If brush_system is invalid
        """
        data = self.load_data(month, brush_system)
        return data.get("metadata", {})

    def list_available_months(self, brush_system: str) -> List[str]:
        """
        List available months for a specific brush system.

        Args:
            brush_system: Brush system ('legacy' or 'new')

        Returns:
            List of available months in YYYY-MM format

        Raises:
            ValueError: If brush_system is invalid
        """
        self._validate_system_name(brush_system)

        if brush_system == "legacy":
            directory = self.legacy_dir
        else:  # brush_system == "new"
            directory = self.new_dir

        if not directory.exists():
            return []

        months = []
        for file_path in directory.glob("*.json"):
            if file_path.is_file():
                month = file_path.stem  # Remove .json extension
                months.append(month)

        return sorted(months)

    def _validate_system_name(self, brush_system: str) -> None:
        """
        Validate brush system name.

        Args:
            brush_system: Brush system name to validate

        Raises:
            ValueError: If brush_system is invalid
        """
        valid_systems = ["legacy", "new"]
        if brush_system not in valid_systems:
            raise ValueError(
                f"Invalid brush system: {brush_system}. Must be one of: {valid_systems}"
            )
