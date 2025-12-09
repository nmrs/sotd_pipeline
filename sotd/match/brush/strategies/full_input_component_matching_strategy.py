#!/usr/bin/env python3
"""Unified component matching strategy that handles both dual and single component matches."""

from typing import List, Optional

# ComponentScoreCalculator no longer needed - scoring is handled externally
from sotd.match.types import MatchResult

from .base_brush_matching_strategy import (
    BaseMultiResultBrushMatchingStrategy,
)


class FullInputComponentMatchingStrategy(BaseMultiResultBrushMatchingStrategy):
    """
    Unified strategy for component matching that handles both dual and single component scenarios.

    This strategy runs HandleMatcher and KnotMatcher once and combines their results:
    - If both match: Creates dual component result (score 65)
    - If only one matches: Creates single component result (score 50)
    - If neither matches: Returns None
    """

    def __init__(self, handle_matcher, knot_matcher, catalogs: dict):
        """
        Initialize the unified component matching strategy.

        Args:
            handle_matcher: HandleMatcher instance for handle matching
            knot_matcher: KnotMatcher instance for knot matching
            catalogs: Dictionary containing all catalog data
        """
        super().__init__()
        self.handle_matcher = handle_matcher
        self.knot_matcher = knot_matcher
        self.catalogs = catalogs

    def match(self, value: str | dict, full_string: Optional[str] = None) -> Optional[MatchResult]:
        """
        Match a brush string using unified component matching logic.
        Returns the best single result for backward compatibility.

        Args:
            value: The brush string or field data object to match

        Returns:
            MatchResult or None
        """
        all_results = self.match_all(value)
        return all_results[0] if all_results else None

    def match_all(self, value: str | dict) -> List[MatchResult]:
        """
        Match a brush string and return all possible brand combination results.

        Args:
            value: The brush string or field data object to match

        Returns:
            List of MatchResult objects for all possible matches
        """
        # Handle both string and field data object inputs
        if isinstance(value, dict):
            # Extract normalized text from field data object
            text = value.get("normalized", value.get("original", ""))
        else:
            # Direct string input
            text = value

        if not text or not isinstance(text, str):
            return []

        results = []
        seen_combinations = set()

        # Run both matchers once
        handle_result = None
        knot_result = None

        try:
            handle_result = self.handle_matcher.match_handle_maker(text)
        except Exception:
            # Handle matcher failed, continue with None
            pass

        try:
            knot_result = self.knot_matcher.match(text)
        except Exception:
            # Knot matcher failed, continue with None
            pass

        # Determine match type and create results
        if handle_result and knot_result:
            # Both matched - dual component
            # Extract brands for comparison
            handle_brand = self._extract_brand_from_result(handle_result)
            knot_brand = self._extract_brand_from_result(knot_result)

            # Always include the original combination
            combination_key = (handle_brand, knot_brand)
            if combination_key not in seen_combinations:
                result = self._create_dual_component_result(handle_result, knot_result, text)
                if result:
                    result.strategy = "full_input_component_matching"
                    result.match_type = "composite"
                    results.append(result)
                    seen_combinations.add(combination_key)

            # Check if both components have the same brand
            if handle_brand and knot_brand and handle_brand == knot_brand:
                # Same brand - generate alternative combinations
                self._generate_alternative_combinations(
                    text, handle_result, knot_result, results, seen_combinations
                )
        elif handle_result or knot_result:
            # Only one matched - single component
            if handle_result:
                result = self._convert_handle_result_to_brush_result(handle_result)
            elif knot_result:
                result = self._convert_knot_result_to_brush_result(knot_result)
            else:
                return []

            if result:
                result.strategy = "full_input_component_matching"
                result.match_type = "single_component"
                results.append(result)

        return results

    def _generate_alternative_combinations(
        self,
        text: str,
        original_handle_result,
        original_knot_result,
        results: List[MatchResult],
        seen_combinations: set,
    ) -> None:
        """
        Generate alternative brand combinations when both components have the same brand.

        Args:
            text: Original text to match against
            original_handle_result: Original handle match result
            original_knot_result: Original knot match result
            results: List to add new results to
            seen_combinations: Set to track seen combinations for deduplication
        """
        original_handle_brand = self._extract_brand_from_result(original_handle_result)
        original_knot_brand = self._extract_brand_from_result(original_knot_result)

        # Try to find alternative handle with different brand
        alternative_handle_result = self._match_handle_with_exclusions(
            text, {original_handle_brand}
        )

        # Try to find alternative knot with different brand
        alternative_knot_result = self._match_knot_with_exclusions(text, {original_knot_brand})

        # Generate all possible combinations
        combinations_to_try = []

        # Original + alternative knot
        if alternative_knot_result:
            combinations_to_try.append((original_handle_result, alternative_knot_result))

        # Alternative handle + original knot
        if alternative_handle_result:
            combinations_to_try.append((alternative_handle_result, original_knot_result))

        # Alternative handle + alternative knot
        if alternative_handle_result and alternative_knot_result:
            combinations_to_try.append((alternative_handle_result, alternative_knot_result))

        # Create results for valid combinations
        for handle_res, knot_res in combinations_to_try:
            handle_brand = self._extract_brand_from_result(handle_res)
            knot_brand = self._extract_brand_from_result(knot_res)
            combination_key = (handle_brand, knot_brand)

            if combination_key not in seen_combinations:
                result = self._create_dual_component_result(handle_res, knot_res, text)
                if result:
                    result.strategy = "full_input_component_matching"
                    result.match_type = "composite"
                    results.append(result)
                    seen_combinations.add(combination_key)

    def _match_handle_with_exclusions(
        self, text: str, excluded_brands: set[str]
    ) -> Optional[MatchResult]:
        """
        Match handle while excluding specific brands.

        Args:
            text: Text to match against
            excluded_brands: Set of brand names to exclude (case-insensitive)

        Returns:
            MatchResult if match found and brand not excluded, None otherwise
        """
        try:
            result = self.handle_matcher.match_handle_maker(text)
            if result is None:
                return None

            # Extract brand from result
            brand = self._extract_brand_from_result(result)
            if not brand:
                return result  # No brand to exclude

            # Check if brand is in excluded set (case-insensitive)
            if brand.lower() in {b.lower() for b in excluded_brands}:
                return None

            return result
        except Exception:
            # Handle matcher failed, return None
            return None

    def _match_knot_with_exclusions(
        self, text: str, excluded_brands: set[str]
    ) -> Optional[MatchResult]:
        """
        Match knot while excluding specific brands.

        Args:
            text: Text to match against
            excluded_brands: Set of brand names to exclude (case-insensitive)

        Returns:
            MatchResult if match found and brand not excluded, None otherwise
        """
        try:
            result = self.knot_matcher.match(text)
            if result is None:
                return None

            # Extract brand from result
            brand = self._extract_brand_from_result(result)
            if not brand:
                return result  # No brand to exclude

            # Check if brand is in excluded set (case-insensitive)
            if brand.lower() in {b.lower() for b in excluded_brands}:
                return None

            return result
        except Exception:
            # Knot matcher failed, return None
            return None

    def _extract_brand_from_result(self, result) -> str:
        """
        Extract brand name from a match result for consistent comparison.

        Args:
            result: MatchResult or dict containing match data

        Returns:
            Lowercase brand name for consistent comparison
        """
        if result is None:
            return ""

        # Handle MatchResult objects
        if hasattr(result, "matched"):
            matched_data = result.matched or {}
        else:
            # Handle dict results
            matched_data = result or {}

        # Extract brand based on result type
        # Handle results have "handle_maker" field
        if "handle_maker" in matched_data:
            brand = matched_data.get("handle_maker", "")
        # Knot results have "brand" field
        elif "brand" in matched_data:
            brand = matched_data.get("brand", "")
        else:
            brand = ""

        # Return lowercase for consistent comparison
        return brand.lower() if brand else ""

    def _create_dual_component_result(self, handle_result, knot_result, value: str) -> MatchResult:
        """Create a dual component result combining handle and knot."""
        # Extract handle data - handle_result might be a dict or MatchResult
        if hasattr(handle_result, "matched"):
            handle_data = handle_result.matched or {}
        else:
            handle_data = handle_result or {}

        # Extract knot data - knot_result should be a MatchResult
        if hasattr(knot_result, "matched"):
            knot_data = knot_result.matched or {}
        else:
            knot_data = knot_result or {}

        # Create combined brush data with nested handle/knot structure
        brush_data = {
            "brand": None,  # Multi-component brushes should not have top-level brand
            "model": None,  # Multi-component brushes should not have top-level model
            "fiber": knot_data.get("fiber"),
            "knot_size_mm": knot_data.get("knot_size_mm"),
            "handle_maker": handle_data.get("handle_maker"),
            "source_text": value,
            "_matched_by": "FullInputComponentMatchingStrategy",
            "_pattern": "dual_component",
            "_original_handle_text": handle_data.get("source_text"),
            "_original_knot_text": knot_data.get("source_text"),
            # Add nested handle and knot sections for modifier functions
            "handle": {
                "brand": handle_data.get("handle_maker"),
                "model": handle_data.get("handle_model"),
                "source_text": handle_data.get("source_text", value),
                "_matched_by": "HandleMatcher",
                "_pattern": handle_data.get("_pattern_used"),
            },
            "knot": {
                "brand": knot_data.get("brand"),
                "model": knot_data.get("model"),
                "fiber": knot_data.get("fiber"),
                "knot_size_mm": knot_data.get("knot_size_mm"),
                "source_text": knot_data.get("source_text", value),
                "_matched_by": "KnotMatcher",
                "_pattern": (
                    knot_result.pattern
                    if hasattr(knot_result, "pattern")
                    else knot_data.get("_pattern_used")
                ),
            },
        }

        # Component scores are now calculated externally by the scoring engine
        # No need to pre-calculate scores here

        return MatchResult(
            original=value, matched=brush_data, match_type="composite", pattern="dual_component"
        )

    def _create_single_component_result(
        self, component_result: MatchResult, value: str, component_type: str
    ) -> MatchResult:
        """Create a single component result."""
        if component_type == "handle":
            return self._convert_handle_result_to_brush_result(component_result)
        elif component_type == "knot":
            return self._convert_knot_result_to_brush_result(component_result)
        else:
            return component_result

    def _convert_handle_result_to_brush_result(self, handle_result) -> MatchResult:
        """Convert HandleMatcher result to brush format."""
        # Handle both dict and MatchResult types
        if hasattr(handle_result, "matched"):
            handle_data = handle_result.matched or {}
        else:
            handle_data = handle_result or {}

        brush_data = {
            "brand": handle_data.get("handle_maker"),
            "model": handle_data.get("handle_model"),
            "source_text": handle_data.get("source_text", ""),
            "_matched_by": "HandleMatcher",
            "_pattern": handle_data.get("_pattern_used"),
            # Add nested handle and knot sections for modifier functions
            "handle": {
                "brand": handle_data.get("handle_maker"),
                "model": handle_data.get("handle_model"),
                "source_text": handle_data.get("source_text", ""),
                "_matched_by": "HandleMatcher",
                "_pattern": handle_data.get("_pattern_used"),
            },
            "knot": {
                "brand": None,
                "model": None,
                "fiber": None,
                "knot_size_mm": None,
                "source_text": "",
                "_matched_by": "HandleMatcher",
                "_pattern": handle_data.get("_pattern_used"),
            },
        }

        # Component scores are now calculated externally by the scoring engine
        # No need to pre-calculate scores here

        return MatchResult(
            original="",  # Handle matcher doesn't provide original text
            matched=brush_data,
            match_type="handle",
            pattern=handle_data.get("_pattern_used"),
        )

    def _convert_knot_result_to_brush_result(self, knot_result: MatchResult) -> MatchResult:
        """Convert KnotMatcher result to brush format."""
        knot_data = knot_result.matched or {}
        # Get pattern from MatchResult.pattern, not from matched data
        knot_pattern = (
            knot_result.pattern or knot_data.get("_pattern_used") or knot_data.get("_pattern")
        )

        brush_data = {
            "brand": knot_data.get("brand"),
            "model": knot_data.get("model"),
            "source_text": knot_data.get("source_text", ""),
            "_matched_by": "KnotMatcher",
            "_pattern": knot_pattern,
            # Add nested handle and knot sections for modifier functions
            "handle": {
                "brand": None,
                "model": None,
                "source_text": "",
                "_matched_by": "KnotMatcher",
                "_pattern": knot_pattern,
            },
            "knot": {
                "brand": knot_data.get("brand"),
                "model": knot_data.get("model"),
                "fiber": knot_data.get("fiber"),
                "knot_size_mm": knot_data.get("knot_size_mm"),
                "source_text": knot_data.get("source_text", ""),
                "_matched_by": "KnotMatcher",
                "_pattern": knot_pattern,
            },
        }

        # Component scores are now calculated externally by the scoring engine
        # No need to pre-calculate scores here

        return MatchResult(
            original="",  # Knot matcher doesn't provide original text
            matched=brush_data,
            match_type="knot",
            pattern=knot_pattern,
            strategy="full_input_component_matching",
        )
