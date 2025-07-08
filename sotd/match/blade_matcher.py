import re
from pathlib import Path
from typing import Any, Dict, Optional

from .base_matcher import BaseMatcher, MatchType


class BladeMatcher(BaseMatcher):
    def __init__(
        self,
        catalog_path: Path = Path("data/blades.yaml"),
        correct_matches_path: Optional[Path] = None,
    ):
        super().__init__(catalog_path, "blade", correct_matches_path=correct_matches_path)
        self.patterns = self._compile_patterns()

    def _compile_patterns(self):
        compiled = []
        for format_name, brands in self.catalog.items():
            for brand, models in brands.items():
                for model, entry in models.items():
                    patterns = entry.get("patterns", [])
                    # Use the format from the catalog structure, not from the entry
                    fmt = format_name
                    for pattern in patterns:
                        compiled.append(
                            (brand, model, fmt, pattern, re.compile(pattern, re.IGNORECASE), entry)
                        )

        # Sort by pattern specificity: longer patterns first, then by pattern complexity
        def pattern_sort_key(item):
            pattern = item[3]
            # Primary sort: pattern length (longer = more specific)
            length_score = len(pattern)
            # Secondary sort: pattern complexity (more special chars = more specific)
            complexity_score = sum(1 for c in pattern if c in r"[].*+?{}()|^$\\")
            # Tertiary sort: prefer patterns with word boundaries
            boundary_score = pattern.count(r"\b") + pattern.count(r"\s")
            return (-length_score, -complexity_score, -boundary_score)

        return sorted(compiled, key=pattern_sort_key)

    def _match_with_regex(self, value: str) -> Dict[str, Any]:
        """Match using regex patterns with REGEX match type."""
        from sotd.utils.match_filter_utils import normalize_for_matching

        original = value
        # All correct match lookups must use normalize_for_matching
        # (see docs/product_matching_validation.md)
        normalized = normalize_for_matching(value, field="blade")
        if not normalized:
            return {
                "original": original,
                "matched": None,
                "pattern": None,
                "match_type": None,  # Keep None for backward compatibility
            }

        blade_text = normalized

        for brand, model, fmt, raw_pattern, compiled, entry in self.patterns:
            if compiled.search(blade_text):
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

                return {
                    "original": original,
                    "matched": matched_data,
                    "pattern": raw_pattern,
                    "match_type": MatchType.REGEX,
                }

        return {
            "original": original,
            "matched": None,
            "pattern": None,
            "match_type": None,  # Keep None for backward compatibility
        }

    def match_with_context(self, value: str, razor_format: str) -> Dict[str, Any]:
        """Match blade with context-aware format prioritization."""
        from sotd.utils.match_filter_utils import normalize_for_matching

        original = value
        # Step 1: Check correct matches first (highest priority)
        correct_match = self.match(value)
        if correct_match and correct_match.get("match_type") == "exact":
            return correct_match

        # All correct match lookups must use normalize_for_matching
        # (see docs/product_matching_validation.md)
        normalized = normalize_for_matching(value, field="blade")
        if not normalized:
            return {
                "original": original,
                "matched": None,
                "pattern": None,
                "match_type": None,
            }

        blade_text = normalized

        # Map razor formats to blade formats
        format_mapping = {
            "SHAVETTE (HAIR SHAPER)": "HAIR SHAPER",
            "SHAVETTE (AC)": "AC",
            "SHAVETTE (DE)": "DE",
            "SHAVETTE (HALF DE)": "HALF DE",
            "SHAVETTE (A77)": "A77",
            "SHAVETTE (DISPOSABLE)": "DISPOSABLE",
            "CARTRIDGE": "CARTRIDGE",
            "STRAIGHT": "STRAIGHT",
            "DE": "DE",
            "AC": "AC",
            "GEM": "GEM",
            "INJECTOR": "INJECTOR",
            "FHS": "FHS",
        }

        target_blade_format = format_mapping.get(razor_format, razor_format)

        # Collect all matches first
        all_matches = []

        for brand, model, fmt, raw_pattern, compiled, entry in self.patterns:
            if compiled.search(blade_text):
                match_data = {
                    "brand": brand,
                    "model": str(model),
                    "format": fmt,
                }

                # Preserve all additional specifications from the catalog entry
                for key, value in entry.items():
                    if key not in ["patterns", "format"]:
                        match_data[key] = value

                match_result = {
                    "original": original,
                    "matched": match_data,
                    "pattern": raw_pattern,
                    "match_type": MatchType.REGEX,
                }

                all_matches.append(match_result)

        # If we have matches, prioritize by format compatibility
        if all_matches:
            # First, try to find exact format matches
            format_matches = [
                m for m in all_matches if m["matched"]["format"].upper() == target_blade_format
            ]
            if format_matches:
                return format_matches[0]  # Return first format match

            # Special fallback case: Half DE razors can use DE blades
            if target_blade_format == "HALF DE":
                de_matches = [m for m in all_matches if m["matched"]["format"].upper() == "DE"]
                if de_matches:
                    return de_matches[0]  # Return first DE match as fallback

            # If no exact format match and no fallback, return the first match (original behavior)
            return all_matches[0]

        return {
            "original": original,
            "matched": None,
            "pattern": None,
            "match_type": None,
        }
