"""
Strategy for matching brushes against correct_matches.yaml.

This strategy uses CorrectMatchesChecker internally to avoid duplication
of search logic while maintaining the strategy pattern interface.
"""

from typing import Optional
from .base_brush_matching_strategy import (
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
            # Handle/knot match - reconstruct the full nested structure
            if match_data.handle_maker and match_data.knot_info:
                # This is a composite brush - reconstruct the full structure
                matched_data = self._reconstruct_composite_brush_structure(value, match_data)
            else:
                # Handle-only or knot-only entry - reconstruct nested structure
                if match_data.handle_maker:
                    matched_data = self._reconstruct_handle_only_structure(value, match_data)
                elif match_data.knot_info:
                    matched_data = self._reconstruct_knot_only_structure(value, match_data)
                else:
                    # Fallback to flattened structure for single components
                    matched_data = {
                        "brand": (
                            match_data.knot_info.get("brand") if match_data.knot_info else None
                        ),
                        "model": (
                            match_data.knot_info.get("model") if match_data.knot_info else None
                        ),
                        "fiber": (
                            match_data.knot_info.get("fiber") if match_data.knot_info else None
                        ),
                        "knot_size_mm": (
                            match_data.knot_info.get("knot_size_mm")
                            if match_data.knot_info
                            else None
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
        elif match_data.match_type == "complete_brush":
            # Complete brush match - reconstruct nested structure
            matched_data = self._reconstruct_complete_brush_structure(value, match_data)
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
        # Always create nested structure for complete brushes, even without catalogs
        matched_data = {
            "brand": brand,
            "model": model,
            # Always create nested sections for complete brushes
            "handle": {
                "brand": brand,  # Handle brand same as brush brand for complete brushes
                "model": None,  # Handle model not specified in catalog
            },
            "knot": {
                "brand": brand,  # Knot brand same as brush brand for complete brushes
                "model": model,  # Knot model same as brush model for complete brushes
                "fiber": None,  # Fiber not specified without catalog
                "knot_size_mm": None,  # Knot size not specified without catalog
            },
        }

        if not self.catalogs:
            return matched_data

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

        # Build complete data structure with nested sections (NO redundant root fields)
        matched_data = {
            "brand": brand,
            "model": model,
            "handle_maker": brush_data.get("handle_maker"),
            # Always create nested sections for complete brushes
            "handle": {
                "brand": brand,  # Handle brand same as brush brand for complete brushes
                "model": None,  # Handle model not specified in catalog
            },
            "knot": {
                "brand": brand,  # Knot brand same as brush brand for complete brushes
                "model": model,  # Knot model same as brush model for complete brushes
                "fiber": brush_data.get("fiber"),
                "knot_size_mm": brush_data.get("knot_size_mm"),
            },
        }

        # Override nested sections if they exist in catalog
        if "handle" in brush_data:
            matched_data["handle"].update(brush_data["handle"])

        if "knot" in brush_data:
            matched_data["knot"].update(brush_data["knot"])

        return matched_data

    def _reconstruct_composite_brush_structure(self, value: str, match_data) -> dict:
        """
        Reconstruct the full composite brush structure to match the original regex result.

        Args:
            value: Original input string
            match_data: Result from CorrectMatchesChecker with handle and knot info

        Returns:
            Dictionary with the full nested structure matching the original regex result
        """
        # Extract handle and knot information
        handle_maker = match_data.handle_maker
        handle_model = getattr(match_data, "handle_model", "Unspecified")
        knot_info = match_data.knot_info

        # Get the actual catalog data for handle and knot
        handle_catalog_data = self._get_handle_catalog_data(handle_maker, handle_model)
        knot_catalog_data = self._get_knot_catalog_data(
            knot_info.get("brand"), knot_info.get("model")
        )

        # Reconstruct the simplified structure for composite brushes
        matched_data = {
            # Top-level fields (required for aggregation compatibility)
            "brand": None,  # Composite brushes don't have top-level brand
            "model": None,  # Composite brushes don't have top-level model
            # Handle section (nested)
            "handle": {
                "brand": self._convert_placeholder_to_none(handle_maker),
                "model": self._convert_placeholder_to_none(handle_model),
            },
            # Knot section (nested)
            "knot": {
                "brand": self._convert_placeholder_to_none(knot_info.get("brand")),
                "model": self._convert_placeholder_to_none(knot_info.get("model")),
                "fiber": knot_info.get("fiber"),
                "knot_size_mm": knot_info.get("knot_size_mm"),
            },
            # Match metadata
            "source_text": value,  # Original input string
            "_matched_by": "CorrectMatchesStrategy",
            "_pattern": "exact_match",
            "strategy": "correct_matches",
        }

        # Merge in any additional catalog data
        if handle_catalog_data:
            matched_data["handle"].update(handle_catalog_data)
        if knot_catalog_data:
            matched_data["knot"].update(knot_catalog_data)

        return matched_data

    def _reconstruct_handle_only_structure(self, value: str, match_data) -> dict:
        """
        Reconstruct the nested structure for handle-only entries to match regex result.

        Args:
            value: Original input string
            match_data: Result from CorrectMatchesChecker with handle info only

        Returns:
            Dictionary with the nested structure matching the original regex result
        """
        # Extract handle information
        handle_maker = match_data.handle_maker
        handle_model = getattr(match_data, "handle_model", "Unspecified")

        # Get the actual catalog data for handle
        handle_catalog_data = self._get_handle_catalog_data(handle_maker, handle_model)

        # Reconstruct the nested structure to match regex result
        matched_data = {
            # Top-level fields (required for aggregation compatibility)
            "brand": None,  # Handle-only entries don't have top-level brand
            "model": None,  # Handle-only entries don't have top-level model
            # Handle section (nested)
            "handle": {
                "brand": self._convert_placeholder_to_none(handle_maker),
                "model": self._convert_placeholder_to_none(handle_model),
            },
            # Knot section (nested but null values)
            "knot": {
                "brand": None,
                "model": None,
                "fiber": None,
                "knot_size_mm": None,
            },
            # Match metadata
            "source_text": value,  # Original input string
            "_matched_by": "CorrectMatchesStrategy",
            "_pattern": "exact_match",
            "strategy": "correct_matches",
        }

        # Merge in any additional catalog data
        if handle_catalog_data:
            matched_data["handle"].update(handle_catalog_data)

        return matched_data

    def _reconstruct_knot_only_structure(self, value: str, match_data) -> dict:
        """
        Reconstruct the nested structure for knot-only entries to match regex result.

        Args:
            value: Original input string
            match_data: Result from CorrectMatchesChecker with knot info only

        Returns:
            Dictionary with the nested structure matching the original regex result
        """
        # Extract knot information
        knot_info = match_data.knot_info
        knot_brand = knot_info.get("brand")
        knot_model = knot_info.get("model")

        # Get the actual catalog data for knot
        knot_catalog_data = self._get_knot_catalog_data(knot_brand, knot_model)

        # Reconstruct the nested structure to match regex result
        matched_data = {
            # Top-level fields (required for aggregation compatibility)
            "brand": None,  # Knot-only entries don't have top-level brand
            "model": None,  # Knot-only entries don't have top-level model
            # Handle section (nested but null values)
            "handle": {
                "brand": None,
                "model": None,
            },
            # Knot section (nested with actual data)
            "knot": {
                "brand": self._convert_placeholder_to_none(knot_brand),
                "model": self._convert_placeholder_to_none(knot_model),
                "fiber": knot_info.get("fiber"),
                "knot_size_mm": knot_info.get("knot_size_mm"),
            },
            # Match metadata
            "source_text": value,  # Original input string
            "_matched_by": "CorrectMatchesStrategy",
            "_pattern": "exact_match",
            "strategy": "correct_matches",
        }

        # Merge in any additional catalog data
        if knot_catalog_data:
            matched_data["knot"].update(knot_catalog_data)

        return matched_data

    def _reconstruct_complete_brush_structure(self, value: str, match_data) -> dict:
        """
        Reconstruct the nested structure for complete brush entries to match regex result.

        Args:
            value: Original input string
            match_data: CorrectMatchData from CorrectMatchesChecker with complete brush info

        Returns:
            Dictionary with the nested structure matching the original regex result
        """
        # Extract brush information from CorrectMatchData attributes
        brush_brand = match_data.brand
        brush_model = match_data.model

        # For complete brushes, we need to look up the actual brush data from catalogs
        # since correct_matches.yaml only stores the brand/model mapping
        brush_data = self._get_complete_brush_data(brush_brand, brush_model)

        # Reconstruct the nested structure to match regex result
        matched_data = {
            # Top-level fields (required for aggregation compatibility)
            "brand": brush_brand,
            "model": brush_model,
            # Handle section (nested)
            "handle": {
                "brand": brush_brand,  # Handle brand same as brush brand for complete brushes
                "model": None,  # Handle model not specified in correct_matches.yaml
            },
            # Knot section (nested)
            "knot": {
                "brand": brush_brand,  # Knot brand same as brush brand for complete brushes
                "model": brush_model,  # Knot model same as brush model for complete brushes
                "fiber": brush_data.get("fiber"),
                "knot_size_mm": brush_data.get("knot_size_mm"),
            },
            # Match metadata
            "source_text": value,  # Original input string
            "_matched_by": "CorrectMatchesStrategy",
            "_pattern": "exact_match",
            "strategy": "correct_matches",
        }

        return matched_data

    def _get_handle_catalog_data(self, handle_maker: str, handle_model: str) -> dict:
        """
        Get catalog data for a handle from handles.yaml.

        Args:
            handle_maker: Brand name of the handle
            handle_model: Model name of the handle

        Returns:
            Dictionary with catalog data for the handle
        """
        # Look in artisan_handles first
        if handle_maker in self.catalogs.get("handles", {}).get("artisan_handles", {}):
            handle_data = self.catalogs["handles"]["artisan_handles"][handle_maker]
            if handle_model in handle_data:
                return handle_data[handle_model]
            elif "Unspecified" in handle_data:
                return handle_data["Unspecified"]

        # Look in manufacturer_handles
        if handle_maker in self.catalogs.get("handles", {}).get("manufacturer_handles", {}):
            handle_data = self.catalogs["handles"]["manufacturer_handles"][handle_maker]
            if handle_model in handle_data:
                return handle_data[handle_model]
            elif "Unspecified" in handle_data:
                return handle_data["Unspecified"]

        # Look in other_handles
        if handle_maker in self.catalogs.get("handles", {}).get("other_handles", {}):
            handle_data = self.catalogs["handles"]["other_handles"][handle_maker]
            if handle_model in handle_data:
                return handle_data[handle_model]
            elif "Unspecified" in handle_data:
                return handle_data["Unspecified"]

        return {}

    def _get_knot_catalog_data(self, knot_maker: str, knot_model: str) -> dict:
        """
        Get catalog data for a knot from knots.yaml.

        Args:
            knot_maker: Brand name of the knot
            knot_model: Model name of the knot

        Returns:
            Dictionary with catalog data for the knot
        """
        # Look in known_knots first
        if knot_maker in self.catalogs.get("knots", {}).get("known_knots", {}):
            knot_data = self.catalogs["knots"]["known_knots"][knot_maker]
            if knot_model in knot_data:
                return knot_data[knot_model]
            # Some brands have default fiber/knot_size_mm at brand level
            elif "fiber" in knot_data or "knot_size_mm" in knot_data:
                return {k: v for k, v in knot_data.items() if k not in ["patterns"]}

        # Look in other_knots
        if knot_maker in self.catalogs.get("knots", {}).get("other_knots", {}):
            knot_data = self.catalogs["knots"]["other_knots"][knot_maker]
            if knot_model in knot_data:
                return knot_data[knot_model]
            # Some brands have default fiber/knot_size_mm at brand level
            elif "fiber" in knot_data or "knot_size_mm" in knot_data:
                return {k: v for k, v in knot_data.items() if k not in ["patterns"]}

        return {}

    def _convert_placeholder_to_none(self, value: str | None) -> str | None:
        """
        Convert placeholder values back to None for proper data representation.

        Args:
            value: The value to check for placeholders

        Returns:
            None if value is a placeholder, otherwise the original value
        """
        if value == "_no_brand" or value == "_no_model":
            return None
        return value

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
