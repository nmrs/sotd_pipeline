from pathlib import Path
from typing import Any, Dict, Optional

from .base_matcher import BaseMatcher
from .loaders import CatalogLoader
from .types import MatchResult, MatchType, create_match_result
from .utils.regex_error_utils import compile_regex_with_context, create_context_dict


class RazorMatcher(BaseMatcher):
    def __init__(
        self,
        catalog_path: Path = Path("data/razors.yaml"),
        correct_matches_path: Optional[Path] = None,
        bypass_correct_matches: bool = False,
    ):
        super().__init__(
            catalog_path=catalog_path,
            field_type="razor",
            correct_matches_path=correct_matches_path,
            bypass_correct_matches=bypass_correct_matches,
        )
        self.loader = CatalogLoader()
        catalogs = self.loader.load_matcher_catalogs(
            catalog_path, "razor", correct_matches_path=correct_matches_path
        )
        # Override catalog and correct_matches from BaseMatcher with loader results
        self.catalog = catalogs["catalog"]
        self.correct_matches = catalogs["correct_matches"] if not bypass_correct_matches else {}
        self.patterns = self._compile_patterns()
        self._match_cache = {}
        self._case_insensitive_lookup: Optional[Dict[str, Dict[str, Any]]] = None

    def clear_cache(self):
        """Clear the match cache. Useful for testing to prevent cache pollution."""
        self._match_cache.clear()
        self._case_insensitive_lookup = None

    def _build_case_insensitive_lookup(self) -> Dict[str, Dict[str, Any]]:
        """
        Build a case-insensitive lookup dictionary for O(1) correct matches lookup.

        Returns:
            Dictionary mapping lowercase keys to match data
        """
        if self._case_insensitive_lookup is not None:
            return self._case_insensitive_lookup

        lookup = {}

        for brand, models in self.correct_matches.items():
            for model, entries in models.items():
                if isinstance(entries, list):
                    # Simple string list format
                    for entry in entries:
                        key = entry.lower()
                        # Get format from catalog entry
                        fmt = "DE"  # Default format
                        if brand in self.catalog and model in self.catalog[brand]:
                            model_data = self.catalog[brand][model]
                            if isinstance(model_data, dict):
                                fmt = model_data.get("format", "DE")
                        lookup[key] = {"brand": brand, "model": model, "format": fmt}
                elif isinstance(entries, dict):
                    # Nested format with additional data
                    strings = entries.get("strings", [])
                    for entry in strings:
                        key = entry.lower()
                        # Get format from catalog entry
                        fmt = "DE"  # Default format
                        if brand in self.catalog and model in self.catalog[brand]:
                            model_data = self.catalog[brand][model]
                            if isinstance(model_data, dict):
                                fmt = model_data.get("format", "DE")
                        matched_data = {"brand": brand, "model": model, "format": fmt}
                        # Copy additional fields from the entry
                        for key_field, val in entries.items():
                            if key_field != "strings":
                                matched_data[key_field] = val
                        lookup[key] = matched_data

        self._case_insensitive_lookup = lookup
        return lookup

    def _compile_patterns(self):
        compiled = []
        for brand, models in self.catalog.items():
            for model, entry in models.items():
                # Validate that entry is a dictionary, not a string
                if not isinstance(entry, dict):
                    raise ValueError(
                        f"Invalid YAML structure in razors.yaml: "
                        f"Brand '{brand}' -> Model '{model}' has value '{entry}' "
                        f"(type: {type(entry).__name__}), but expected a dictionary with "
                        f"'patterns' and 'format' fields. This usually means 'format' is "
                        f"placed at the brand level instead of the model level. "
                        f"Fix: Move 'format: {entry}' inside the '{model}:' section."
                    )

                patterns = entry.get("patterns", [])
                fmt = entry.get("format", "DE")
                for pattern in patterns:
                    context = create_context_dict(
                        file_path=str(self.catalog_path), brand=brand, model=model, format=fmt
                    )
                    compiled_pattern = compile_regex_with_context(pattern, context)
                    compiled.append((brand, model, fmt, pattern, compiled_pattern, entry))
        return sorted(compiled, key=lambda x: len(x[3]), reverse=True)

    def _get_normalized_text(self, value: str) -> str:
        """
        Return normalized text directly.

        Args:
            value: Normalized text string

        Returns:
            Normalized text string
        """
        return value

    def _get_original_text(self, value: str) -> str:
        """
        Return original text directly.

        Args:
            value: Original text string

        Returns:
            Original text string
        """
        return value

    def _match_with_regex(self, normalized_text: str, original_text: str) -> MatchResult:
        cache_key = str(normalized_text)
        if cache_key in self._match_cache:
            return self._match_cache[cache_key]

        if not normalized_text:
            result = create_match_result(
                original=original_text,
                matched=None,
                match_type=None,
                pattern=None,
            )
            self._match_cache[cache_key] = result
            return result

        razor_text = normalized_text

        for brand, model, fmt, raw_pattern, compiled, entry in self.patterns:
            if compiled.search(razor_text):
                matched_data = {
                    "brand": brand,
                    "model": str(model),
                    "format": fmt,
                }
                for key, value in entry.items():
                    if key not in ["patterns", "format"]:
                        matched_data[key] = value
                result = create_match_result(
                    original=original_text,
                    matched=matched_data,
                    pattern=raw_pattern,
                    match_type=MatchType.REGEX,
                )
                self._match_cache[cache_key] = result
                return result

        result = create_match_result(
            original=original_text,
            matched=None,
            match_type=None,
            pattern=None,
        )
        self._match_cache[cache_key] = result
        return result

    def match(
        self, value: str, original: str | None = None, bypass_correct_matches: bool = False
    ) -> MatchResult:
        """
        Match a razor value using correct matches first, then regex patterns.

        Args:
            value: Normalized text string for matching
            original: Original text string for debugging (defaults to value if not provided)
            bypass_correct_matches: If True, skip correct_matches and use regex only

        Returns:
            MatchResult with match information
        """
        # Use provided original text or default to normalized text
        original_text = original if original is not None else value
        normalized_text = value

        if not bypass_correct_matches:
            # Check correct matches first using BaseMatcher's case-insensitive logic
            correct_match = self._check_correct_matches(normalized_text)
            if correct_match:
                return create_match_result(
                    original=original_text,
                    matched=correct_match,
                    match_type=MatchType.EXACT,
                    pattern=None,
                )
        # Fall back to regex matching
        return self._match_with_regex(normalized_text, original_text)

    def _check_correct_matches(self, value: str) -> Optional[Dict[str, Any]]:
        """
        Check correct matches with O(1) lookup for razors.

        Args:
            value: Normalized text string for matching

        Returns:
            Match data if found, None otherwise
        """
        if not value or not self.correct_matches:
            return None

        # Use O(1) case-insensitive lookup for all matches
        lookup = self._build_case_insensitive_lookup()
        return lookup.get(value.lower())
