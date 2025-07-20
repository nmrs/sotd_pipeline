import re
from pathlib import Path
from typing import Optional

from .loaders import CatalogLoader
from .types import MatchResult, MatchType, create_match_result


class RazorMatcher:
    def __init__(
        self,
        catalog_path: Path = Path("data/razors.yaml"),
        correct_matches_path: Optional[Path] = None,
    ):
        self.loader = CatalogLoader()
        catalogs = self.loader.load_matcher_catalogs(
            catalog_path, "razor", correct_matches_path=correct_matches_path
        )
        self.catalog = catalogs["catalog"]
        self.correct_matches = catalogs["correct_matches"]
        self.patterns = self._compile_patterns()
        self._match_cache = {}

    def clear_cache(self):
        """Clear the match cache. Useful for testing to prevent cache pollution."""
        self._match_cache.clear()

    def _compile_patterns(self):
        compiled = []
        for brand, models in self.catalog.items():
            for model, entry in models.items():
                patterns = entry.get("patterns", [])
                fmt = entry.get("format", "DE")
                for pattern in patterns:
                    compiled.append(
                        (brand, model, fmt, pattern, re.compile(pattern, re.IGNORECASE), entry)
                    )
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
            # Check correct matches first
            if self.correct_matches:
                for brand, models in self.correct_matches.items():
                    for model, entries in models.items():
                        if isinstance(entries, list):
                            # Simple string list format
                            if normalized_text in entries:
                                # Get format from catalog entry
                                fmt = "DE"  # Default format
                                if brand in self.catalog and model in self.catalog[brand]:
                                    fmt = self.catalog[brand][model].get("format", "DE")
                                return create_match_result(
                                    original=original_text,
                                    matched={"brand": brand, "model": model, "format": fmt},
                                    match_type=MatchType.EXACT,
                                    pattern=None,
                                )
                        elif isinstance(entries, dict):
                            # Nested format with additional data
                            strings = entries.get("strings", [])
                            if normalized_text in strings:
                                # Get format from catalog entry
                                fmt = "DE"  # Default format
                                if brand in self.catalog and model in self.catalog[brand]:
                                    fmt = self.catalog[brand][model].get("format", "DE")
                                matched_data = {"brand": brand, "model": model, "format": fmt}
                                # Copy additional fields from the entry
                                for key, val in entries.items():
                                    if key != "strings":
                                        matched_data[key] = val
                                return create_match_result(
                                    original=original_text,
                                    matched=matched_data,
                                    match_type=MatchType.EXACT,
                                    pattern=None,
                                )
        # Fall back to regex matching
        return self._match_with_regex(normalized_text, original_text)
