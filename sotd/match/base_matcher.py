import re
from pathlib import Path
from typing import Any, Dict, List, Optional

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
        self.competition_tags = self._load_competition_tags()

        # Lazy-loaded caches for performance optimization
        self._correct_matches_lookup: Optional[Dict[str, Dict[str, Any]]] = None
        self._catalog_patterns: Optional[List[Dict[str, Any]]] = None
        self._compiled_patterns: Dict[str, Any] = {}  # Pattern -> compiled regex

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

    def _load_competition_tags(self) -> Dict[str, List[str]]:
        """Load competition tags configuration."""
        tags_path = Path("data/competition_tags.yaml")
        if not tags_path.exists():
            return {"strip_tags": [], "preserve_tags": []}

        try:
            data = load_yaml_with_nfc(tags_path, loader_cls=UniqueKeyLoader)
            return {
                "strip_tags": data.get("strip_tags", []),
                "preserve_tags": data.get("preserve_tags", []),
            }
        except Exception:
            # If tags file is corrupted or can't be loaded, continue without it
            return {"strip_tags": [], "preserve_tags": []}

    def _strip_competition_tags(self, value: str) -> str:
        """
        Strip competition tags from a string while preserving useful ones.

        Args:
            value: Input string that may contain competition tags

        Returns:
            String with unwanted competition tags removed
        """
        if not isinstance(value, str):
            return value

        # Get tags to strip and preserve
        strip_tags = self.competition_tags.get("strip_tags", [])
        preserve_tags = self.competition_tags.get("preserve_tags", [])

        if not strip_tags:
            return value

        # Create a list of tags to actually strip (exclude preserve_tags)
        tags_to_strip = [tag for tag in strip_tags if tag not in preserve_tags]

        if not tags_to_strip:
            return value

        # Build regex pattern to match tags with word boundaries
        # This ensures we match whole tags, not partial matches
        # Also handle tags that might be wrapped in backticks or asterisks
        strip_pattern = (
            r"[`*]*\$(" + "|".join(re.escape(tag) for tag in tags_to_strip) + r")\b[`*]*"
        )

        # Remove the tags and clean up extra whitespace
        cleaned = re.sub(strip_pattern, "", value, flags=re.IGNORECASE)
        cleaned = re.sub(r"\s+", " ", cleaned)  # Normalize whitespace
        cleaned = cleaned.strip()

        return cleaned

    def _build_correct_matches_lookup(self) -> Dict[str, Dict[str, Any]]:
        """
        Build a fast lookup dictionary from correct matches.

        Converts the nested structure to a flat dictionary for O(1) lookups.
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
                    normalized = self.normalize(correct_string)
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
        """
        Check if value matches any correct matches entry using optimized lookup.

        Returns match data if found, None otherwise.
        Performance: O(1) instead of O(n×m×p) nested loop.
        """
        if not value or not self.correct_matches:
            return None

        normalized_value = self.normalize(value)
        if not normalized_value:
            return None

        # Use pre-built lookup dictionary for O(1) access
        lookup = self._get_correct_matches_lookup()
        return lookup.get(normalized_value)

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
        value = value.strip().lower()
        value = self._strip_competition_tags(value)
        return value

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
