import re
from pathlib import Path
from typing import Any, Dict, Optional

from .base_matcher import BaseMatcher, MatchType


class RazorMatcher(BaseMatcher):
    def __init__(
        self,
        catalog_path: Path = Path("data/razors.yaml"),
        correct_matches_path: Optional[Path] = None,
    ):
        super().__init__(catalog_path, "razor", correct_matches_path=correct_matches_path)
        self.patterns = self._compile_patterns()
        # Add cache for expensive operations
        self._match_cache = {}

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

    def _match_with_regex(self, value: str) -> Dict[str, Any]:
        """Match using regex patterns with REGEX match type."""
        # Check cache first - ensure cache key is always a string
        cache_key = str(value) if not isinstance(value, str) else value
        if cache_key in self._match_cache:
            return self._match_cache[cache_key]

        original = value
        # All correct match lookups must use normalize_for_matching
        # (see docs/product_matching_validation.md)
        from sotd.utils.match_filter_utils import normalize_for_matching

        normalized = normalize_for_matching(value, field="razor")
        if not normalized:
            result = {
                "original": original,
                "matched": None,
                "pattern": None,
                "match_type": None,  # Keep None for backward compatibility
            }
            self._match_cache[cache_key] = result
            return result

        razor_text = normalized

        for brand, model, fmt, raw_pattern, compiled, entry in self.patterns:
            if compiled.search(razor_text):
                # Start with basic match data
                matched_data = {
                    "brand": brand,
                    "model": str(model),  # Ensure model is always a string
                    "format": fmt,
                }

                # Preserve all additional specifications from the catalog entry
                # (excluding patterns and format which are already handled)
                for key, value in entry.items():
                    if key not in ["patterns", "format"]:
                        matched_data[key] = value

                result = {
                    "original": original,
                    "matched": matched_data,
                    "pattern": raw_pattern,
                    "match_type": MatchType.REGEX,
                }
                self._match_cache[cache_key] = result
                return result

        result = {
            "original": original,
            "matched": None,
            "pattern": None,
            "match_type": None,  # Keep None for backward compatibility
        }
        self._match_cache[cache_key] = result
        return result
