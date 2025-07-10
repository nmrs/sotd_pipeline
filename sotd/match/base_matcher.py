import re
from pathlib import Path
from typing import Any, Dict, List, Optional

from sotd.utils.match_filter_utils import load_competition_tags, normalize_for_matching
from sotd.utils.yaml_loader import UniqueKeyLoader, load_yaml_with_nfc


class MatchType:
    """Constants for match types to improve semantic clarity."""

    EXACT = "exact"  # From correct_matches.yaml (manually verified)
    REGEX = "regex"  # From regex patterns in YAML catalogs
    ALIAS = "alias"  # Brand/model aliases
    BRAND = "brand"  # Brand-only fallback
    UNMATCHED = "unmatched"  # No match found


class BaseMatcher:
    def __init__(
        self, catalog_path: Path, field_type: str, correct_matches_path: Optional[Path] = None
    ):
        self.catalog_path = catalog_path
        self.field_type = field_type  # "razor", "blade", "brush", "soap"
        self.correct_matches_path = correct_matches_path or Path("data/correct_matches.yaml")
        self.catalog = self._load_catalog()
        self.correct_matches = self._load_correct_matches()
        self.competition_tags = self._load_competition_tags()

        # Lazy-loaded caches for performance optimization
        self._correct_matches_lookup: Optional[Dict[str, Dict[str, Any]]] = None
        self._catalog_patterns: Optional[List[Dict[str, Any]]] = None
        self._compiled_patterns: Dict[str, Any] = {}  # Pattern -> compiled regex

    def _load_catalog(self) -> dict:
        return load_yaml_with_nfc(self.catalog_path, loader_cls=UniqueKeyLoader)

    def _load_correct_matches(self) -> Dict[str, Dict[str, Any]]:
        """Load correct matches for this field type from correct_matches.yaml (or injected path)."""
        if not self.correct_matches_path.exists():
            return {}

        try:
            data = load_yaml_with_nfc(self.correct_matches_path, loader_cls=UniqueKeyLoader)
            return data.get(self.field_type, {})
        except Exception:
            # If correct matches file is corrupted or can't be loaded, continue without it
            return {}

    def _load_competition_tags(self) -> Dict[str, List[str]]:
        """Load competition tags configuration."""
        return load_competition_tags()

    def _strip_competition_tags(self, value: str) -> str:
        """
        Strip competition tags from a string while preserving useful ones.

        Args:
            value: Input string that may contain competition tags

        Returns:
            String with unwanted competition tags removed
        """
        # Use canonical normalization function for consistent behavior
        return normalize_for_matching(value, self.competition_tags, self.field_type)

    def _build_correct_matches_lookup(self) -> Dict[str, Dict[str, Any]]:
        """
        Build a fast lookup dictionary from correct matches.

        Converts the nested structure to a flat dictionary for O(1) lookups.
        Uses canonical normalize_for_matching function for consistent normalization.
        """
        lookup = {}

        for brand, brand_data in self.correct_matches.items():
            if not isinstance(brand_data, dict):
                continue

            for model, strings in brand_data.items():
                if not isinstance(strings, list):
                    continue

                # Get catalog entry for this brand/model
                catalog_entry = self.catalog.get(brand, {}).get(model, {})

                # Build matched data structure
                matched = {
                    "brand": brand,
                    "model": model,
                    "format": catalog_entry.get("format", "DE"),
                }
                # Add all other catalog fields except patterns and format
                for key, val in catalog_entry.items():
                    if key not in ["patterns", "format"]:
                        matched[key] = val

                # Create lookup entries for each correct string
                for correct_string in strings:
                    # Use canonical normalization function with field-specific processing
                    normalized = normalize_for_matching(
                        correct_string, self.competition_tags, self.field_type
                    )
                    if normalized:
                        lookup[normalized] = matched

        return lookup

    def _get_correct_matches_lookup(self) -> Dict[str, Dict[str, Any]]:
        """Lazy load field-specific correct matches lookup."""
        if self._correct_matches_lookup is None:
            self._correct_matches_lookup = self._build_correct_matches_lookup()
        return self._correct_matches_lookup

    def _extract_patterns_from_catalog(self) -> List[Dict[str, Any]]:
        """
        Extract all patterns from catalog data for this field type.

        Returns a list of pattern dictionaries with metadata.
        """
        patterns = []

        if not isinstance(self.catalog, dict):
            return patterns

        # Extract patterns based on field type
        if self.field_type == "soap":
            # Soap catalog has maker -> scent -> patterns structure
            for maker, maker_data in self.catalog.items():
                if isinstance(maker_data, dict) and "scents" in maker_data:
                    for scent, scent_data in maker_data["scents"].items():
                        if isinstance(scent_data, dict) and "patterns" in scent_data:
                            for pattern in scent_data["patterns"]:
                                patterns.append(
                                    {
                                        "pattern": pattern,
                                        "maker": maker,
                                        "scent": scent,
                                    }
                                )
        else:
            # Other catalogs have brand -> model -> patterns structure
            for brand, brand_data in self.catalog.items():
                if isinstance(brand_data, dict):
                    for model, model_data in brand_data.items():
                        if isinstance(model_data, dict) and "patterns" in model_data:
                            for pattern in model_data["patterns"]:
                                patterns.append(
                                    {
                                        "pattern": pattern,
                                        "brand": brand,
                                        "model": model,
                                    }
                                )

        return patterns

    def _get_catalog_patterns(self) -> List[Dict[str, Any]]:
        """Lazy load field-specific catalog patterns."""
        if self._catalog_patterns is None:
            self._catalog_patterns = self._extract_patterns_from_catalog()
        return self._catalog_patterns

    def _get_compiled_pattern(self, pattern_text: str) -> Optional[Any]:
        """Get or create a compiled regex pattern."""
        if pattern_text not in self._compiled_patterns:
            try:
                self._compiled_patterns[pattern_text] = re.compile(pattern_text, re.IGNORECASE)
            except re.error:
                # Skip invalid patterns
                return None
        return self._compiled_patterns[pattern_text]

    def _check_correct_matches(self, value: str) -> Optional[Dict[str, Any]]:
        # --- CANONICAL NORMALIZATION ---
        # All correct match lookups must use normalize_for_matching
        # See docs/product_matching_validation.md for details.
        if not value or not self.correct_matches:
            return None

        # Use canonical normalization function with field-specific processing
        normalized_value = normalize_for_matching(value, self.competition_tags, self.field_type)
        if not normalized_value:
            return None

        # Use pre-built lookup dictionary for O(1) access
        lookup = self._get_correct_matches_lookup()

        # Try exact match first
        result = lookup.get(normalized_value)
        if result:
            return result

        # Fall back to case-insensitive lookup for backward compatibility
        normalized_lower = normalized_value.lower()
        for key, match_data in lookup.items():
            if key.lower() == normalized_lower:
                return match_data

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
        """
        Normalize a string for comparison.

        DEPRECATED: Use normalize_for_matching() directly for correct match lookups.
        This method is kept for backward compatibility but should be replaced
        with the canonical normalize_for_matching function.
        """
        if not isinstance(value, str):
            return None
        # Use canonical normalization function for consistency
        from sotd.utils.match_filter_utils import normalize_for_matching

        return normalize_for_matching(value, self.competition_tags, self.field_type)

    def clear_caches(self) -> None:
        """Clear all caches (useful for testing or when files are updated)."""
        self._correct_matches_lookup = None
        self._catalog_patterns = None
        self._compiled_patterns.clear()

    def match(self, value: str, bypass_correct_matches: bool = False) -> Dict[str, Any]:
        """
        Enhanced match method with correct matches priority.

        Priority order:
        1. Correct matches file (highest priority, fastest) - unless bypassed
        2. Regex patterns (fallback, slower)
        3. Brand/alias fallbacks (lowest priority)

        Args:
            value: Value to match
            bypass_correct_matches: If True, skip correct matches check and go directly to regex
        """
        original = value

        # Step 1: Check correct matches first (highest priority) - unless bypassed
        if not bypass_correct_matches:
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
