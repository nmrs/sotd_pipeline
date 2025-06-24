from pathlib import Path
from typing import Any, Dict, Optional

from sotd.utils.yaml_loader import UniqueKeyLoader, load_yaml_with_nfc


class MatchType:
    """Constants for match types to improve semantic clarity."""

    EXACT = "exact"  # From correct_matches.yaml (manually verified)
    REGEX = "regex"  # From regex patterns in YAML catalogs
    ALIAS = "alias"  # Brand/model aliases
    BRAND = "brand"  # Brand-only fallback
    UNMATCHED = "unmatched"  # No match found


class BaseMatcher:
    def __init__(self, catalog_path: Path, field_type: str):
        self.catalog_path = catalog_path
        self.field_type = field_type  # "razor", "blade", "brush", "soap"
        self.catalog = self._load_catalog()
        self.correct_matches = self._load_correct_matches()

    def _load_catalog(self) -> dict:
        return load_yaml_with_nfc(self.catalog_path, loader_cls=UniqueKeyLoader)

    def _load_correct_matches(self) -> Dict[str, Dict[str, Any]]:
        """Load correct matches for this field type from correct_matches.yaml."""
        correct_matches_path = Path("data/correct_matches.yaml")
        if not correct_matches_path.exists():
            return {}

        try:
            data = load_yaml_with_nfc(correct_matches_path, loader_cls=UniqueKeyLoader)
            return data.get(self.field_type, {})
        except Exception:
            # If correct matches file is corrupted or can't be loaded, continue without it
            return {}

    def _check_correct_matches(self, value: str) -> Optional[Dict[str, Any]]:
        """
        Check if value matches any correct matches entry.

        Returns match data if found, None otherwise.
        """
        if not value or not self.correct_matches:
            return None

        normalized_value = self.normalize(value)
        if not normalized_value:
            return None

        # Search through correct matches structure
        for brand, brand_data in self.correct_matches.items():
            if not isinstance(brand_data, dict):
                continue

            for model, strings in brand_data.items():
                if not isinstance(strings, list):
                    continue

                # Check if normalized value matches any of the correct strings
                for correct_string in strings:
                    if self.normalize(correct_string) == normalized_value:
                        # Merge all catalog fields for this brand/model
                        catalog_entry = self.catalog.get(brand, {}).get(model, {})
                        matched = {
                            "brand": brand,
                            "model": model,
                            "format": catalog_entry.get("format", "DE"),
                        }
                        # Add all other catalog fields except patterns and format
                        for key, val in catalog_entry.items():
                            if key not in ["patterns", "format"]:
                                matched[key] = val
                        return matched

        return None

    def _get_format_from_catalog(self, brand: str, model: str) -> str:
        """Get format from catalog for a brand/model combination."""
        try:
            brand_data = self.catalog.get(brand, {})
            model_data = brand_data.get(model, {})
            return model_data.get("format", "DE")  # Default to DE for razors/blades
        except Exception:
            return "DE"

    def normalize(self, value: Optional[str]) -> Optional[str]:
        """Normalize a string for comparison."""
        if not isinstance(value, str):
            return None
        return value.strip().lower()

    def match(self, value: str) -> Dict[str, Any]:
        """
        Enhanced match method with correct matches priority.

        Priority order:
        1. Correct matches file (highest priority, fastest)
        2. Regex patterns (fallback, slower)
        3. Brand/alias fallbacks (lowest priority)
        """
        original = value

        # Step 1: Check correct matches first (highest priority)
        correct_match = self._check_correct_matches(value)
        if correct_match:
            return {
                "original": original,
                "matched": correct_match,
                "pattern": None,  # No pattern used for correct matches
                "match_type": "exact",
            }

        # Step 2: Fall back to regex patterns (implemented by subclasses)
        # This should be implemented by each specific matcher
        return self._match_with_regex(value)

    def _match_with_regex(self, value: str) -> Dict[str, Any]:
        """
        Match using regex patterns. To be implemented by subclasses.

        This method should return the same structure as match() but with
        match_type set to MatchType.REGEX for regex-based matches.
        """
        raise NotImplementedError("Subclasses must implement _match_with_regex")
