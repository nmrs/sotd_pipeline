"""
Correct Matches Checker for brush matching.

This module provides a focused component for checking if input values match
any entries in the correct_matches.yaml file, supporting both brush section
(simple brushes) and handle/knot sections (combo brushes).
"""

from typing import Any, Dict, Optional

from sotd.match.config import BrushMatcherConfig
from sotd.match.types import CorrectMatchData
from sotd.utils.match_filter_utils import normalize_for_matching


class CorrectMatchesChecker:
    """
    Focused component for checking correct matches with efficient lookup strategies.

    This class handles checking if input values match any entries in the
    correct_matches.yaml file, supporting both brush section (simple brushes)
    and handle/knot sections (combo brushes).
    """

    def __init__(self, config: BrushMatcherConfig, correct_matches: Dict[str, Any]):
        """
        Initialize the correct matches checker.

        Args:
            config: Configuration object containing paths and settings
            correct_matches: Loaded correct matches data from YAML
        """
        self.config = config
        self.correct_matches = correct_matches or {}
        self.debug = config.debug

    def check(self, value: str) -> Optional[CorrectMatchData]:
        """
        Check if value matches any correct matches entry using canonical normalization.

        Args:
            value: Input string to check against correct matches

        Returns:
            CorrectMatchData if found, None otherwise.
            Supports both brush section (simple brushes) and handle/knot sections (combo brushes).
        """
        if not value or not self.correct_matches:
            return None

        # All correct match lookups must use normalize_for_matching
        # (see docs/product_matching_validation.md)
        normalized_value = normalize_for_matching(value, field="brush")
        if not normalized_value:
            return None

        # Step 1: Check handle/knot sections first (for combo brush/handle brushes)
        handle_knot_match = self._check_handle_knot_correct_matches(value, normalized_value)
        if handle_knot_match:
            return handle_knot_match

        # Step 2: Check brush section (for simple brushes)
        brush_match = self._check_brush_correct_matches(value, normalized_value)
        if brush_match:
            return brush_match

        return None

    def _check_brush_correct_matches(
        self, value: str, normalized_value: str
    ) -> Optional[CorrectMatchData]:
        """
        Check if value matches any brush section correct matches entry.

        Args:
            value: Original input string
            normalized_value: Normalized input string for comparison

        Returns:
            CorrectMatchData if found, None otherwise.
        """
        brush_section = self.correct_matches.get("brush", {})

        # Search through correct matches structure
        for brand, brand_data in brush_section.items():
            if not isinstance(brand_data, dict):
                continue

            for model, strings in brand_data.items():
                if not isinstance(strings, list):
                    continue

                # Check if normalized value matches any of the correct strings
                for correct_string in strings:
                    normalized_correct = normalize_for_matching(correct_string, field="brush")
                    if normalized_correct == normalized_value:
                        # Return match data in the expected format
                        return CorrectMatchData(
                            brand=brand, model=model, match_type="brush_section"
                        )

        return None

    def _check_handle_knot_correct_matches(
        self, value: str, normalized_value: str
    ) -> Optional[CorrectMatchData]:
        """
        Check if value matches any handle/knot section correct matches entry.

        Args:
            value: Original input string
            normalized_value: Normalized input string for comparison

        Returns:
            CorrectMatchData if found, None otherwise.
        """
        handle_section = self.correct_matches.get("handle", {})
        knot_section = self.correct_matches.get("knot", {})

        # Search through handle section
        for handle_maker, handle_models in handle_section.items():
            if not isinstance(handle_models, dict):
                continue

            for handle_model, strings in handle_models.items():
                if not isinstance(strings, list):
                    continue

                # Check if normalized value matches any of the correct strings
                for correct_string in strings:
                    normalized_correct = normalize_for_matching(correct_string, field="brush")
                    if normalized_correct == normalized_value:
                        # Find corresponding knot information
                        knot_info = self._find_knot_info_for_string(value, knot_section)

                        return CorrectMatchData(
                            handle_maker=handle_maker,
                            handle_model=handle_model,
                            knot_info=knot_info,
                            match_type="handle_knot_section",
                        )

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
        normalized_value = normalize_for_matching(value, field="brush")

        # Search through knot section
        for knot_maker, knot_models in knot_section.items():
            if not isinstance(knot_models, dict):
                continue

            for knot_model, knot_data in knot_models.items():
                if not isinstance(knot_data, dict):
                    continue

                strings = knot_data.get("strings", [])
                if not isinstance(strings, list):
                    continue

                # Check if normalized value matches any of the correct strings
                for correct_string in strings:
                    normalized_correct = normalize_for_matching(correct_string, field="brush")
                    if normalized_correct == normalized_value:
                        return {
                            "brand": knot_maker,
                            "model": knot_model,
                            "fiber": knot_data.get("fiber"),
                            "knot_size_mm": knot_data.get("knot_size_mm"),
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
