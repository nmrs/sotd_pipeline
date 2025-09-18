"""
Unified catalog loading for all matchers in the SOTD pipeline.

Provides consistent YAML loading with error handling, validation, and statistics
for all matcher types (razor, blade, brush, soap).
"""

from pathlib import Path
from typing import Any, Dict, Optional

import yaml

from sotd.match.exceptions import CatalogLoadError
from sotd.utils.yaml_loader import UniqueKeyLoader, load_yaml_with_nfc

# Global cache for YAML catalog files to avoid repeated loads
_yaml_catalog_cache: Dict[str, Dict[str, Any]] = {}


def clear_yaml_cache() -> None:
    """Clear the global YAML catalog cache. Useful when catalog files are modified."""
    global _yaml_catalog_cache
    _yaml_catalog_cache.clear()


class CatalogLoader:
    """
    Handles loading of YAML catalog files with error handling, caching,
    and loading statistics for all catalog types.
    """

    def __init__(self, config: Optional[Any] = None):
        self.config = config
        self.load_stats: Dict[str, int] = {
            "catalogs_loaded": 0,
            "errors": 0,
            "warnings": 0,
        }

    def load_catalog(
        self, path: Path, catalog_type: str, use_unique_loader: bool = False
    ) -> Dict[str, Any]:
        """
        Load a single catalog file with error handling and validation.
        Uses a global cache to avoid repeated YAML loads.
        """
        abs_path = str(path.resolve())
        if abs_path in _yaml_catalog_cache:
            return _yaml_catalog_cache[abs_path]

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
            if use_unique_loader:
                data = load_yaml_with_nfc(path, loader_cls=UniqueKeyLoader)
            else:
                data = load_yaml_with_nfc(path)
            if data is None:
                data = {}
            if not isinstance(data, dict):
                raise CatalogLoadError(
                    f"Invalid {catalog_type} catalog structure: expected dict, got {type(data)}",
                    context={
                        "path": str(path),
                        "catalog_type": catalog_type,
                        "data_type": str(type(data)),
                    },
                )
            _yaml_catalog_cache[abs_path] = data
            self.load_stats["catalogs_loaded"] += 1  # type: ignore
            return data
        except yaml.YAMLError as e:
            raise CatalogLoadError(
                f"Invalid YAML in {catalog_type} catalog {path}: {e}",
                context={"path": str(path), "catalog_type": catalog_type, "error": str(e)},
            )

    def load_correct_matches(
        self, correct_matches_path: Optional[Path] = None, field_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Load correct matches with graceful error handling.
        Uses the new directory structure: data/correct_matches/{field_type}.yaml

        Args:
            correct_matches_path: Path to correct_matches directory (or legacy single file)
            field_type: Specific field type to extract (e.g., 'razor', 'blade', 'brush', 'soap')

        Returns:
            Dictionary with correct matches data
        """
        # Handle both new directory structure and legacy single file
        if correct_matches_path and correct_matches_path.is_file():
            # Legacy single file mode - load the entire file
            return self._load_legacy_correct_matches(correct_matches_path, field_type)
        
        # New directory structure mode
        base_path = correct_matches_path or Path("data/correct_matches")
        base_path = base_path.resolve()

        if not base_path.exists():
            # Use the same fallback behavior as BaseMatcher
            return {}

        try:
            if field_type:
                # Load specific field type file
                field_file = base_path / f"{field_type}.yaml"
                if not field_file.exists():
                    return {}
                
                data = load_yaml_with_nfc(field_file, loader_cls=UniqueKeyLoader)
                self.load_stats["catalogs_loaded"] += 1  # type: ignore
                return data
            else:
                # Load all sections (for brush matcher)
                result = {}
                for field in ["brush", "handle", "knot", "split_brush"]:
                    field_file = base_path / f"{field}.yaml"
                    if field_file.exists():
                        data = load_yaml_with_nfc(field_file, loader_cls=UniqueKeyLoader)
                        result[field] = data
                        self.load_stats["catalogs_loaded"] += 1  # type: ignore
                    else:
                        result[field] = {}
                return result

        except Exception:
            # Use the same error handling as BaseMatcher - return empty dict on any error
            return {}

    def _load_legacy_correct_matches(
        self, correct_matches_path: Path, field_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Load correct matches from legacy single file format.
        Maintains backward compatibility with existing correct_matches.yaml.
        """
        try:
            data = load_yaml_with_nfc(correct_matches_path, loader_cls=UniqueKeyLoader)
            self.load_stats["catalogs_loaded"] += 1  # type: ignore

            if field_type:
                # Return field-specific section
                return data.get(field_type, {})
            else:
                # Return all sections (for brush matcher)
                return {
                    "brush": data.get("brush", {}),
                    "handle": data.get("handle", {}),
                    "knot": data.get("knot", {}),
                    "split_brush": data.get("split_brush", {}),
                }

        except Exception:
            # Use the same error handling as BaseMatcher - return empty dict on any error
            return {}

    def load_matcher_catalogs(
        self, catalog_path: Path, matcher_type: str, correct_matches_path: Optional[Path] = None
    ) -> Dict[str, Any]:
        """
        Load catalogs for a specific matcher type.
        Uses the same logic as BaseMatcher for consistency.

        Args:
            catalog_path: Path to the main catalog file
            matcher_type: Type of matcher ('razor', 'blade', 'brush', 'soap')
            correct_matches_path: Path to correct_matches.yaml file

        Returns:
            Dictionary containing loaded catalog data
        """
        catalogs = {}

        # Load main catalog
        catalogs["catalog"] = self.load_catalog(catalog_path, matcher_type, use_unique_loader=True)

        # Load correct matches for this matcher type - same logic as BaseMatcher
        try:
            correct_matches = self.load_correct_matches(
                correct_matches_path, field_type=matcher_type
            )
            catalogs["correct_matches"] = correct_matches
        except Exception:
            # Use the same error handling as BaseMatcher
            catalogs["correct_matches"] = {}

        return catalogs

    def load_brush_catalogs(self, config: Any) -> Dict[str, Any]:
        """
        Load all catalogs for brush matching (special case with multiple catalogs).

        Args:
            config: Brush matcher configuration

        Returns:
            Dictionary containing all loaded catalog data
        """
        catalogs = {}

        # Load main catalogs
        catalogs["brushes"] = self.load_catalog(config.catalog_path, "brushes")
        catalogs["handles"] = self.load_catalog(config.handles_path, "handles")
        catalogs["knots"] = self.load_catalog(config.knots_path, "knots")

        # Load correct matches (with graceful error handling)
        catalogs["correct_matches"] = self.load_correct_matches(config.correct_matches_path)

        return catalogs

    def load_all_catalogs(self) -> Dict[str, Any]:
        """
        Load all catalogs for brush matching (alias for load_brush_catalogs).

        This method is used by BrushMatcher to load all required catalogs.

        Returns:
            Dictionary containing all loaded catalog data
        """
        if not self.config:
            raise CatalogLoadError(
                "Cannot load all catalogs without configuration",
                context={"operation": "load_all_catalogs"},
            )

        return self.load_brush_catalogs(self.config)

    def get_load_stats(self) -> Dict[str, Any]:
        """Get loading statistics and debug information."""
        stats: Dict[str, Any] = dict(self.load_stats)

        if self.config:
            stats["config"] = self.config.get_debug_info()

        return stats

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
                if self.config and self.config.debug:
                    print(
                        f"Warning: {catalog_type} catalog appears to be empty or "
                        f"missing expected sections"
                    )
                self.load_stats["warnings"] += 1
