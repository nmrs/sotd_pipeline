#!/usr/bin/env python3
"""Unified component matching strategy that handles both dual and single component matches."""

from typing import Optional

from sotd.match.brush_matching_strategies.base_brush_matching_strategy import (
    BaseBrushMatchingStrategy,
)
from sotd.match.types import MatchResult


class FullInputComponentMatchingStrategy(BaseBrushMatchingStrategy):
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

    def match(self, value: str) -> Optional[MatchResult]:
        """
        Match a brush string using unified component matching logic.

        Args:
            value: The brush string to match

        Returns:
            MatchResult or None
        """
        if not value or not isinstance(value, str):
            return None

        # Run both matchers once
        handle_result = None
        knot_result = None

        try:
            handle_result = self.handle_matcher.match_handle_maker(value)
        except Exception:
            # Handle matcher failed, continue with None
            pass

        try:
            knot_result = self.knot_matcher.match(value)
        except Exception:
            # Knot matcher failed, continue with None
            pass

        # Determine match type and create result
        if handle_result and knot_result:
            # Both matched - dual component
            result = self._create_dual_component_result(handle_result, knot_result, value)
            if result:
                result.strategy = "unified"  # Will get base score 50 + modifier 15 = 65
                result.match_type = "composite"
            return result
        elif handle_result or knot_result:
            # Only one matched - single component
            if handle_result:
                result = self._convert_handle_result_to_brush_result(handle_result)
            elif knot_result:
                result = self._convert_knot_result_to_brush_result(knot_result)
            else:
                return None
            
            if result:
                result.strategy = "unified"  # Will get base score 50 (no modifier)
                result.match_type = "single_component"
            return result
        else:
            # Neither matched
            return None

    def _create_dual_component_result(
        self, handle_result: MatchResult, knot_result: MatchResult, value: str
    ) -> MatchResult:
        """Create a dual component result combining handle and knot."""
        # Extract handle data
        handle_data = handle_result.matched or {}
        knot_data = knot_result.matched or {}
        
        # Create combined brush data
        brush_data = {
            "brand": handle_data.get("handle_maker") or knot_data.get("brand"),
            "model": handle_data.get("handle_model") or knot_data.get("model"),
            "fiber": knot_data.get("fiber"),
            "knot_size_mm": knot_data.get("knot_size_mm"),
            "handle_maker": handle_data.get("handle_maker"),
            "source_text": value,
            "_matched_by": "FullInputComponentMatchingStrategy",
            "_pattern": "dual_component",
            "_original_handle_text": handle_data.get("source_text"),
            "_original_knot_text": knot_data.get("source_text")
        }
        
        return MatchResult(
            original=value,
            matched=brush_data,
            match_type="composite",
            pattern="dual_component"
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

    def _convert_handle_result_to_brush_result(self, handle_result: MatchResult) -> MatchResult:
        """Convert HandleMatcher result to brush format."""
        handle_data = handle_result.matched or {}
        
        brush_data = {
            "brand": handle_data.get("handle_maker"),
            "model": handle_data.get("handle_model"),
            "source_text": handle_data.get("source_text", handle_result.original),
            "_matched_by": "HandleMatcher",
            "_pattern": handle_data.get("_pattern_used"),
        }
        
        return MatchResult(
            original=handle_result.original,
            matched=brush_data,
            match_type="handle",
            pattern=handle_data.get("_pattern_used"),
        )

    def _convert_knot_result_to_brush_result(self, knot_result: MatchResult) -> MatchResult:
        """Convert KnotMatcher result to brush format."""
        knot_data = knot_result.matched or {}
        
        brush_data = {
            "brand": knot_data.get("brand"),
            "model": knot_data.get("model"),
            "fiber": knot_data.get("fiber"),
            "knot_size_mm": knot_data.get("knot_size_mm"),
            "source_text": knot_data.get("source_text", knot_result.original),
            "_matched_by": "KnotMatcher",
            "_pattern": knot_data.get("_pattern_used"),
        }
        
        return MatchResult(
            original=knot_result.original,
            matched=brush_data,
            match_type="knot",
            pattern=knot_data.get("_pattern_used"),
        )
