"""
Correct Matches Checker for brush matching.

This module provides a focused component for checking if input values match
any entries in the correct_matches.yaml file, supporting both brush section
(simple brushes) and handle/knot sections (combo brushes).
"""

from typing import Any, Dict, Optional

from sotd.match.types import CorrectMatchData
from sotd.utils.extract_normalization import normalize_for_matching


class CorrectMatchesChecker:
    """
    Focused component for checking correct matches with efficient lookup strategies.

    This class handles checking if input values match any entries in the
    correct_matches.yaml file, supporting both brush section (simple brushes)
    and handle/knot sections (combo brushes).
    """

    def __init__(self, correct_matches: Dict[str, Any], debug: bool = False):
        """
        Initialize the correct matches checker.

        Args:
            correct_matches: Loaded correct matches data from YAML
            debug: Optional debug flag for verbose logging
        """
        self.correct_matches = correct_matches or {}
        self.debug = debug
        self._case_insensitive_lookup: Optional[Dict[str, Dict[str, Any]]] = None
        # Add normalization cache for performance optimization
        self._normalization_cache: Dict[str, str] = {}

    def _normalize_with_cache(self, value: str) -> str:
        """
        Normalize value with caching for performance optimization.

        Args:
            value: Input string to normalize

        Returns:
            Normalized string
        """
        if value in self._normalization_cache:
            return self._normalization_cache[value]

        normalized = normalize_for_matching(value, field="brush")
        self._normalization_cache[value] = normalized
        return normalized

    def check(self, value: str) -> Optional[CorrectMatchData]:
        """
        Check if value matches any correct matches entry using canonical normalization.

        Args:
            value: Input string to check against correct matches

        Returns:
            CorrectMatchData if found, None otherwise.
            Supports both brush section (simple brushes), handle/knot sections (combo brushes),
            and split_brush section (split brush mappings).
        """
        if not value or not self.correct_matches:
            return None

        # Use cached normalization for performance
        normalized_value = self._normalize_with_cache(value)
        if not normalized_value:
            return None

        # Use the new priority order: brush → handle/knot → split_brush
        return self._check_with_new_priority_order(value, normalized_value)

    def _check_with_new_priority_order(
        self, value: str, normalized_value: str
    ) -> Optional[CorrectMatchData]:
        """
        Check correct matches with new priority order: brush → handle/knot → split_brush.
        This implements the data-driven brush type determination logic.
        """
        # Step 1: Check brush section first (highest priority)
        brush_match = self._check_brush_correct_matches(value, normalized_value)
        if brush_match:
            return brush_match

        # Step 2: Check handle/knot sections (medium priority)
        handle_knot_match = self._check_handle_knot_correct_matches(value, normalized_value)
        if handle_knot_match:
            return handle_knot_match

        return None

    def _check_brush_correct_matches(
        self, value: str, normalized_value: str
    ) -> Optional[CorrectMatchData]:
        """
        Check if value matches any brush section correct matches entry using O(1) lookup.

        Args:
            value: Original input string
            normalized_value: Normalized input string for comparison

        Returns:
            CorrectMatchData if found, None otherwise.
        """
        # Use O(1) case-insensitive lookup for brush section only
        lookup = self._build_case_insensitive_lookup()
        brush_lookup = lookup["brush"]
        match_data = brush_lookup.get(normalized_value.lower())

        if match_data:
            return CorrectMatchData(
                brand=match_data["brand"],
                model=match_data["model"],
                match_type=match_data["match_type"],
            )

        return None

    def _build_case_insensitive_lookup(self) -> Dict[str, Dict[str, Any]]:
        """
        Build O(1) case-insensitive lookup dictionaries for all correct matches.

        Returns separate dictionaries for each section to preserve priority order:
        - brush: Complete brushes (mutually exclusive from handle/knot)
        - handle: Handle components (mutually exclusive from brush)
        - knot: Knot components (mutually exclusive from brush)

        Returns:
            Dictionary with separate lookups for each section
        """
        if self._case_insensitive_lookup is not None:
            return self._case_insensitive_lookup

        brush_lookup = {}
        handle_lookup = {}
        knot_lookup = {}

        # Build brush section lookup (complete brushes only)
        brush_section = self.correct_matches.get("brush", {})
        for brand, brand_data in brush_section.items():
            if not isinstance(brand_data, dict):
                continue
            for model, strings in brand_data.items():
                if not isinstance(strings, list):
                    continue
                for correct_string in strings:
                    key = correct_string.lower()
                    brush_lookup[key] = {
                        "type": "brush_section",
                        "brand": brand,
                        "model": model,
                        "match_type": "brush_section",
                    }

        # Build handle section lookup (handle components only)
        handle_section = self.correct_matches.get("handle", {})
        for handle_maker, handle_models in handle_section.items():
            if not isinstance(handle_models, dict):
                continue
            for handle_model, strings in handle_models.items():
                if not isinstance(strings, list):
                    continue
                for correct_string in strings:
                    key = correct_string.lower()
                    handle_lookup[key] = {
                        "type": "handle_section",
                        "handle_maker": handle_maker,
                        "handle_model": handle_model,
                        "match_type": "handle_knot_section",
                    }

        # Build knot section lookup (knot components only)
        knot_section = self.correct_matches.get("knot", {})
        for knot_brand, knot_models in knot_section.items():
            if not isinstance(knot_models, dict):
                continue
            for knot_model, strings in knot_models.items():
                if not isinstance(strings, list):
                    continue
                for correct_string in strings:
                    key = correct_string.lower()
                    knot_lookup[key] = {
                        "type": "knot_section",
                        "knot_brand": knot_brand,
                        "knot_model": knot_model,
                        "match_type": "handle_knot_section",
                    }

        self._case_insensitive_lookup = {
            "brush": brush_lookup,
            "handle": handle_lookup,
            "knot": knot_lookup,
        }
        return self._case_insensitive_lookup

    def clear_cache(self):
        """Clear all caches (case-insensitive lookup and normalization cache)."""
        self._case_insensitive_lookup = None
        self._normalization_cache.clear()

    def _check_handle_knot_correct_matches(
        self, value: str, normalized_value: str
    ) -> Optional[CorrectMatchData]:
        """
        Check if value matches any handle/knot section correct matches entry using O(1) lookup.

        Args:
            value: Original input string
            normalized_value: Normalized input string for comparison

        Returns:
            CorrectMatchData if found, None otherwise.
        """
        # Use O(1) case-insensitive lookup for handle and knot sections
        lookup = self._build_case_insensitive_lookup()
        handle_lookup = lookup["handle"]
        knot_lookup = lookup["knot"]

        # Check handle section first (higher priority than knot)
        handle_match_data = handle_lookup.get(normalized_value.lower())
        if handle_match_data:
            # Find corresponding knot info
            knot_info = self._find_knot_info_for_string(value, self.correct_matches.get("knot", {}))
            return CorrectMatchData(
                handle_maker=handle_match_data["handle_maker"],
                handle_model=handle_match_data["handle_model"],
                knot_info=knot_info,
                match_type=handle_match_data["match_type"],
            )

        # Check knot section
        knot_match_data = knot_lookup.get(normalized_value.lower())
        if knot_match_data:
            # Create knot info structure
            knot_info = {
                "brand": knot_match_data["knot_brand"],
                "model": knot_match_data["knot_model"],
            }
            return CorrectMatchData(knot_info=knot_info, match_type=knot_match_data["match_type"])

        return None

    def _find_knot_info_for_string(
        self, value: str, knot_section: dict
    ) -> Optional[Dict[str, Any]]:
        """
        Find knot information for a given input string.

        Args:
            value: Input string to search for
            knot_section: Knot section from correct matches data

        Returns:
            Knot info if found, None otherwise.
        """
        normalized_value = self._normalize_with_cache(value)

        # Search through knot section
        for knot_maker, knot_models in knot_section.items():
            if not isinstance(knot_models, dict):
                continue

            for knot_model, knot_data in knot_models.items():
                # Handle both old structure (dict with strings key) and new structure (direct list)
                if isinstance(knot_data, dict):
                    strings = knot_data.get("strings", [])
                    if not isinstance(strings, list):
                        continue
                elif isinstance(knot_data, list):
                    strings = knot_data
                else:
                    continue

                # Check if normalized value matches any of the correct strings
                # Use case-insensitive comparison
                for correct_string in strings:
                    normalized_correct = self._normalize_with_cache(correct_string)
                    if normalized_correct.lower() == normalized_value.lower():
                        # Handle both old and new data structures
                        if isinstance(knot_data, dict):
                            return {
                                "brand": knot_maker,
                                "model": knot_model,
                                "fiber": knot_data.get("fiber"),
                                "knot_size_mm": knot_data.get("knot_size_mm"),
                                "strings": strings,
                            }
                        else:
                            # New structure - minimal knot info
                            return {
                                "brand": knot_maker,
                                "model": knot_model,
                                "fiber": None,
                                "knot_size_mm": None,
                                "strings": strings,
                            }

        return None

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about the correct matches data.

        Returns:
            Dictionary containing statistics about the loaded correct matches
        """
        brush_section = self.correct_matches.get("brush", {})
        handle_section = self.correct_matches.get("handle", {})
        knot_section = self.correct_matches.get("knot", {})

        brush_count = sum(
            len(strings) if isinstance(strings, list) else 0
            for brand_data in brush_section.values()
            if isinstance(brand_data, dict)
            for strings in brand_data.values()
        )

        handle_count = sum(
            len(strings) if isinstance(strings, list) else 0
            for handle_models in handle_section.values()
            if isinstance(handle_models, dict)
            for strings in handle_models.values()
        )

        knot_count = sum(
            len(knot_data.get("strings", [])) if isinstance(knot_data, dict) else 0
            for knot_models in knot_section.values()
            if isinstance(knot_models, dict)
            for knot_data in knot_models.values()
        )

        return {
            "total_brush_entries": brush_count,
            "total_handle_entries": handle_count,
            "total_knot_entries": knot_count,
            "total_entries": brush_count + handle_count + knot_count,
            "brands_in_brush_section": len(brush_section),
            "handle_makers": len(handle_section),
            "knot_makers": len(knot_section),
        }
