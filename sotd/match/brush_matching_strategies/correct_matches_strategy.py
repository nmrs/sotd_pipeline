"""
Strategy for matching brushes against correct_matches.yaml.

This strategy uses CorrectMatchesChecker internally to avoid duplication
of search logic while maintaining the strategy pattern interface.
"""

from typing import Optional
from sotd.match.brush_matching_strategies.base_brush_matching_strategy import (
    BaseBrushMatchingStrategy,
)
from sotd.match.types import MatchResult
from sotd.match.correct_matches import CorrectMatchesChecker


class CorrectMatchesStrategy(BaseBrushMatchingStrategy):
    """
    Strategy for matching against correct_matches.yaml.

    Uses CorrectMatchesChecker internally to avoid duplication of search logic.
    """

    def __init__(self, correct_matches_data: dict, catalogs: dict | None = None):
        """
        Initialize with correct matches data and catalogs.

        Args:
            correct_matches_data: The loaded correct_matches.yaml data
            catalogs: Dictionary containing brushes, knots, and handles catalogs
        """
        self.checker = CorrectMatchesChecker(correct_matches_data)
        self.catalogs = catalogs or {}

    def match(self, value: str) -> Optional[MatchResult]:
        """
        Match the input value against correct_matches.yaml.

        Args:
            value: The brush string to match

        Returns:
            MatchResult if found, None otherwise
        """
        if not value or not isinstance(value, str):
            return None

        # Use the utility class to check for matches
        match_data = self.checker.check(value)
        if match_data:
            # Convert CorrectMatchData to MatchResult format
            return self._convert_to_match_result(value, match_data)

        return None

    def _convert_to_match_result(self, value: str, match_data) -> MatchResult:
        """
        Convert CorrectMatchData to MatchResult format.

        Args:
            value: Original input string
            match_data: Result from CorrectMatchesChecker

        Returns:
            MatchResult in the expected format
        """
        if match_data.match_type == "brush_section":
            # Look up complete data from brushes catalog
            matched_data = self._get_complete_brush_data(match_data.brand, match_data.model)
            matched_data.update(
                {
                    "source_text": value,
                    "_matched_by": "CorrectMatchesStrategy",
                    "_pattern": "exact_match",
                    "strategy": "correct_matches",
                }
            )
        elif match_data.match_type == "handle_knot_section":
            # Handle/knot match - use catalog data if available
            matched_data = {
                "brand": match_data.knot_info.get("brand") if match_data.knot_info else None,
                "model": match_data.knot_info.get("model") if match_data.knot_info else None,
                "fiber": match_data.knot_info.get("fiber") if match_data.knot_info else None,
                "knot_size_mm": (
                    match_data.knot_info.get("knot_size_mm") if match_data.knot_info else None
                ),
                "handle_maker": match_data.handle_maker,
                "source_text": value,
                "_matched_by": "CorrectMatchesStrategy",
                "_pattern": "exact_match",
                "strategy": "correct_matches",
            }

            # Try to enhance with catalog data if available
            if matched_data["brand"] and matched_data["model"]:
                catalog_data = self._get_complete_knot_data(
                    matched_data["brand"], matched_data["model"]
                )
                if catalog_data:
                    matched_data.update(catalog_data)
        else:
            # Fallback for unknown match types
            matched_data = {
                "brand": None,
                "model": None,
                "fiber": None,
                "knot_size_mm": None,
                "handle_maker": None,
                "source_text": value,
                "_matched_by": "CorrectMatchesStrategy",
                "_pattern": "exact_match",
                "strategy": "correct_matches",
            }

        return MatchResult(
            original=value,
            matched=matched_data,
            match_type="exact",
            pattern="exact_match",
        )

    def _get_complete_brush_data(self, brand: str, model: str) -> dict:
        """
        Get complete brush data from catalogs including nested sections.

        Args:
            brand: Brush brand
            model: Brush model

        Returns:
            Dictionary with complete brush specifications
        """
        if not self.catalogs:
            return {"brand": brand, "model": model}

        # Look up in brushes catalog
        brushes_catalog = self.catalogs.get("brushes", {})
        # Check both known_brushes and other_brushes sections
        brush_data = None
        if "known_brushes" in brushes_catalog:
            brush_data = brushes_catalog["known_brushes"].get(brand, {}).get(model, {})
        if not brush_data and "other_brushes" in brushes_catalog:
            brush_data = brushes_catalog["other_brushes"].get(brand, {}).get(model, {})

        if not brush_data:
            return {"brand": brand, "model": model}

        # Build complete data structure
        matched_data = {
            "brand": brand,
            "model": model,
            "fiber": brush_data.get("fiber"),
            "knot_size_mm": brush_data.get("knot_size_mm"),
            "handle_maker": brush_data.get("handle_maker"),
        }

        # Add nested sections if they exist
        if "handle" in brush_data:
            matched_data["handle"] = brush_data["handle"]

        if "knot" in brush_data:
            matched_data["knot"] = brush_data["knot"]

        return matched_data

    def _get_complete_knot_data(self, brand: str, model: str) -> dict:
        """
        Get complete knot data from catalogs.

        Args:
            brand: Knot brand
            model: Knot model

        Returns:
            Dictionary with complete knot specifications
        """
        if not self.catalogs:
            return {}

        # Look up in knots catalog
        knots_catalog = self.catalogs.get("knots", {})
        knot_data = knots_catalog.get(brand, {}).get(model, {})

        if not knot_data:
            return {}

        # Return relevant knot data
        return {
            "fiber": knot_data.get("fiber"),
            "knot_size_mm": knot_data.get("knot_size_mm"),
        }
