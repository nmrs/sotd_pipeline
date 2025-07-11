import re
from pathlib import Path
from typing import Any, Dict, List, Optional

from .base_matcher import BaseMatcher, MatchType


class BladeMatcher(BaseMatcher):
    def __init__(
        self,
        catalog_path: Path = Path("data/blades.yaml"),
        correct_matches_path: Optional[Path] = None,
    ):
        super().__init__(catalog_path, "blade", correct_matches_path=correct_matches_path)
        self.patterns = self._compile_patterns()
        # Pre-compute normalized correct matches for performance
        self._normalized_correct_matches = self._precompute_normalized_correct_matches()

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

    def _precompute_normalized_correct_matches(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        Pre-compute normalized correct matches for performance.

        Returns a dictionary mapping normalized strings to their match data.
        """
        from sotd.utils.match_filter_utils import normalize_for_matching

        if not self.correct_matches:
            return {}

        normalized_matches = {}

        # Iterate through all formats in correct matches (blade section is organized by format)
        for format_name, format_data in self.correct_matches.items():
            if not isinstance(format_data, dict):
                continue

            # Iterate through all brands in this format
            for brand, brand_data in format_data.items():
                if not isinstance(brand_data, dict):
                    continue

                # Iterate through all models in this brand
                for model, strings in brand_data.items():
                    if not isinstance(strings, list):
                        continue

                    # Find the catalog entry for this brand/model in this format
                    catalog_entry = None
                    if format_name in self.catalog:
                        format_brands = self.catalog[format_name]
                        if brand in format_brands and model in format_brands[brand]:
                            catalog_entry = format_brands[brand][model]

                    if catalog_entry is None:
                        # If not found in catalog, use empty dict
                        catalog_entry = {}

                    # Build matched data structure
                    matched = {
                        "brand": brand,
                        "model": model,
                        "format": format_name,  # Use the format from the structure
                    }
                    # Add all other catalog fields except patterns and format
                    for key, val in catalog_entry.items():
                        if key not in ["patterns", "format"]:
                            matched[key] = val

                    # Check if this string matches any of the correct strings
                    for correct_string in strings:
                        normalized_correct = normalize_for_matching(correct_string, field="blade")
                        if normalized_correct:
                            if normalized_correct not in normalized_matches:
                                normalized_matches[normalized_correct] = []
                            normalized_matches[normalized_correct].append(matched)

        return normalized_matches

    def _match_with_regex(self, value: str) -> Dict[str, Any]:
        """Match blade using regex patterns."""
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
                "match_type": None,
            }

        blade_text = normalized

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

                return {
                    "original": original,
                    "matched": match_data,
                    "pattern": raw_pattern,
                    "match_type": MatchType.REGEX,
                }

        return {
            "original": original,
            "matched": None,
            "pattern": None,
            "match_type": None,
        }

    def _collect_all_correct_matches(self, value: str) -> List[Dict[str, Any]]:
        """
        Collect all correct matches for a given string.

        Returns a list of all matching brand/model combinations from correct_matches.yaml.
        """
        from sotd.utils.match_filter_utils import normalize_for_matching

        if not value or not self._normalized_correct_matches:
            return []

        # Use canonical normalization function
        normalized_value = normalize_for_matching(value, field="blade")
        if not normalized_value:
            return []

        # Try exact match first
        if normalized_value in self._normalized_correct_matches:
            return self._normalized_correct_matches[normalized_value]

        # If no exact match, try case-insensitive match
        normalized_value_lower = normalized_value.lower()
        for key, matches in self._normalized_correct_matches.items():
            if key.lower() == normalized_value_lower:
                return matches

        return []

    def _filter_by_format(
        self, matches: List[Dict[str, Any]], target_format: str
    ) -> Optional[Dict[str, Any]]:
        """
        Filter matches by format compatibility.

        Args:
            matches: List of all matching brand/model combinations
            target_format: Target blade format (e.g., "DE", "GEM", "AC")

        Returns:
            Best matching format or first match if no format match found
        """
        if not matches:
            return None

        # First, try to find exact format matches
        format_matches = [m for m in matches if m["format"].upper() == target_format.upper()]
        if format_matches:
            return format_matches[0]  # Return first format match

        # Special fallback case: Half DE razors can use DE blades
        if target_format.upper() == "HALF DE":
            de_matches = [m for m in matches if m["format"].upper() == "DE"]
            if de_matches:
                return de_matches[0]  # Return first DE match as fallback

        # If no exact format match and no fallback, return the first match
        return matches[0]

    def match_with_context(self, value: str, razor_format: str) -> Dict[str, Any]:
        """Match blade with context-aware format prioritization."""
        from sotd.utils.match_filter_utils import normalize_for_matching

        original = value

        # Step 1: Check correct matches with format awareness
        all_correct_matches = self._collect_all_correct_matches(value)
        if all_correct_matches:
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

            # Filter by format and return the best match
            best_match = self._filter_by_format(all_correct_matches, target_blade_format)
            if best_match:
                return {
                    "original": original,
                    "matched": best_match,
                    "pattern": None,  # No pattern used for correct matches
                    "match_type": "exact",
                }

        # Step 2: Fall back to regex matching if no correct match found
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

    def match(self, value: str, bypass_correct_matches: bool = False) -> Dict[str, Any]:
        """
        Match blade with format-aware logic.

        When no context is provided, prioritizes more specific patterns over default DE format.
        """
        # First try correct matches without context (will find all matches)
        all_correct_matches = self._collect_all_correct_matches(value)
        if all_correct_matches:
            # If we have multiple matches, prioritize by pattern specificity
            # For now, return the first match (correct matches are already prioritized)
            return {
                "original": value,
                "matched": all_correct_matches[0],
                "pattern": None,  # No pattern used for correct matches
                "match_type": "exact",
            }

        # If no correct matches, use regex matching with format prioritization
        from sotd.utils.match_filter_utils import normalize_for_matching

        original = value
        normalized = normalize_for_matching(value, field="blade")
        if not normalized:
            return {
                "original": original,
                "matched": None,
                "pattern": None,
                "match_type": None,
            }

        blade_text = normalized

        # Collect all regex matches
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

                all_matches.append(
                    {
                        "original": original,
                        "matched": match_data,
                        "pattern": raw_pattern,
                        "match_type": MatchType.REGEX,
                    }
                )

        # If we have matches, prioritize by pattern specificity
        if all_matches:
            # The patterns are already sorted by specificity in _compile_patterns
            # So the first match should be the most specific
            return all_matches[0]

        return {
            "original": original,
            "matched": None,
            "pattern": None,
            "match_type": None,
        }
