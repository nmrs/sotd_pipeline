"""
Shared catalog loader utility.

This module provides shared functionality for loading brush-related catalog data
that was previously part of the legacy brush matching system.
"""

import yaml
from pathlib import Path
from typing import Dict, Any


class CatalogLoader:
    """
    Shared catalog loader for brush-related data.

    This class extracts the catalog loading functionality that was previously
    embedded in the legacy BrushMatcher class.
    """

    def __init__(self, base_path: Path | None = None):
        """
        Initialize the catalog loader.

        Args:
            base_path: Base path for data directories (default: data/)
        """
        self.base_path = base_path or Path("data")

    def load_brushes(self) -> Dict[str, Any]:
        """Load brushes catalog data."""
        brushes_path = self.base_path / "brushes.yaml"
        if not brushes_path.exists():
            return {}

        with open(brushes_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}

    def load_handles(self) -> Dict[str, Any]:
        """Load handles catalog data."""
        handles_path = self.base_path / "handles.yaml"
        if not handles_path.exists():
            return {}

        with open(handles_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}

    def load_knots(self) -> Dict[str, Any]:
        """Load knots catalog data."""
        knots_path = self.base_path / "knots.yaml"
        if not knots_path.exists():
            return {}

        with open(knots_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}

    def load_fibers(self) -> Dict[str, Any]:
        """Load fibers catalog data."""
        fibers_path = self.base_path / "fibers.yaml"
        if not fibers_path.exists():
            return {}

        with open(fibers_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}

    def get_knots_data(self) -> Dict[str, Any]:
        """
        Get knots data in the format expected by knot strategies.

        Returns:
            Dictionary with 'known_knots' and 'other_knots' keys
        """
        knots_data = self.load_knots()

        # Extract known_knots and other_knots sections
        known_knots = knots_data.get("known_knots", {})
        other_knots = knots_data.get("other_knots", {})

        return {
            "known_knots": known_knots,
            "other_knots": other_knots,
        }

    def get_brushes_data(self) -> Dict[str, Any]:
        """Get brushes catalog data."""
        return self.load_brushes()

    def get_handles_data(self) -> Dict[str, Any]:
        """Get handles catalog data."""
        return self.load_handles()

    def get_fibers_data(self) -> Dict[str, Any]:
        """Get fibers catalog data."""
        return self.load_fibers()
