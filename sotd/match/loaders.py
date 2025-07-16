"""
Unified catalog loading for brush matching system.

Provides consistent YAML loading with error handling, validation, and statistics.
"""

from pathlib import Path
from typing import Any, Dict

import yaml

from sotd.match.config import BrushMatcherConfig
from sotd.match.exceptions import CatalogLoadError
from sotd.utils.yaml_loader import load_yaml_with_nfc


class CatalogLoader:
    """
    Unified catalog loader for brush matching system.

    Provides consistent YAML loading with error handling, validation,
    and loading statistics for all catalog types.
    """

    def __init__(self, config: BrushMatcherConfig):
        self.config = config
        self.load_stats = {
            "catalogs_loaded": 0,
            "errors": 0,
            "warnings": 0,
        }

    def load_catalog(self, path: Path, catalog_type: str) -> Dict[str, Any]:
        """
        Load a single catalog file with error handling and validation.

        Args:
            path: Path to the catalog file
            catalog_type: Type of catalog (e.g., 'brushes', 'handles', 'knots')

        Returns:
            Loaded catalog data as dictionary

        Raises:
            CatalogLoadError: If file is missing or contains invalid YAML
        """
        if not path.exists():
            raise CatalogLoadError(
                f"{catalog_type} catalog file not found: {path}",
                context={
                    "path": str(path),
                    "catalog_type": catalog_type,
                    "operation": "load_catalog",
                },
            )

        try:
            with path.open("r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
                if data is None:
                    return {}

                # Validate basic structure
                if not isinstance(data, dict):
                    raise CatalogLoadError(
                        f"Invalid {catalog_type} catalog structure: expected dict, "
                        f"got {type(data)}",
                        context={
                            "path": str(path),
                            "catalog_type": catalog_type,
                            "data_type": str(type(data)),
                        },
                    )

                self.load_stats["catalogs_loaded"] += 1
                return data

        except yaml.YAMLError as e:
            raise CatalogLoadError(
                f"Invalid YAML in {catalog_type} catalog {path}: {e}",
                context={"path": str(path), "catalog_type": catalog_type, "error": str(e)},
            )

    def load_correct_matches(self) -> Dict[str, Dict[str, Any]]:
        """
        Load correct matches with graceful error handling.

        Returns:
            Dictionary with brush, handle, and knot sections
        """
        path = self.config.correct_matches_path

        if not path.exists():
            if self.config.debug:
                print(f"Warning: Correct matches file not found: {path}")
            return {"brush": {}, "handle": {}, "knot": {}}

        try:
            data = load_yaml_with_nfc(path)
            correct_matches = {
                "brush": data.get("brush", {}),
                "handle": data.get("handle", {}),
                "knot": data.get("knot", {}),
            }
            self.load_stats["catalogs_loaded"] += 1
            return correct_matches

        except (FileNotFoundError, yaml.YAMLError) as e:
            # Handle external errors gracefully
            if self.config.debug:
                print(f"Warning: Could not load correct matches from {path}: {e}")
            self.load_stats["warnings"] += 1
            return {"brush": {}, "handle": {}, "knot": {}}

    def load_all_catalogs(self) -> Dict[str, Any]:
        """
        Load all required catalogs for brush matching.

        Returns:
            Dictionary containing all loaded catalog data
        """
        catalogs = {}

        # Load main catalogs
        catalogs["brushes"] = self.load_catalog(self.config.catalog_path, "brushes")
        catalogs["handles"] = self.load_catalog(self.config.handles_path, "handles")
        catalogs["knots"] = self.load_catalog(self.config.knots_path, "knots")

        # Load correct matches (with graceful error handling)
        catalogs["correct_matches"] = self.load_correct_matches()

        return catalogs

    def get_load_stats(self) -> Dict[str, Any]:
        """Get loading statistics and debug information."""
        return {
            **self.load_stats,
            "config": self.config.get_debug_info(),
        }

    def validate_catalog_structure(self, data: Dict[str, Any], catalog_type: str) -> None:
        """
        Validate catalog data structure.

        Args:
            data: Catalog data to validate
            catalog_type: Type of catalog for validation rules

        Raises:
            CatalogLoadError: If validation fails
        """
        if not isinstance(data, dict):
            raise CatalogLoadError(
                f"Invalid {catalog_type} catalog: expected dict, got {type(data)}",
                context={"catalog_type": catalog_type, "data_type": str(type(data))},
            )

        # Add catalog-specific validation rules here if needed
        if catalog_type == "brushes":
            if not data.get("known_brushes") and not data.get("other_brushes"):
                if self.config.debug:
                    print(
                        f"Warning: {catalog_type} catalog appears to be empty or "
                        f"missing expected sections"
                    )
                self.load_stats["warnings"] += 1
