#!/usr/bin/env python3
"""Composite brush matching strategy for scoring system."""

from typing import Optional, Dict, Any
from pathlib import Path

from sotd.match.brush_matching_strategies.base_brush_matching_strategy import (
    BaseBrushMatchingStrategy,
)
from sotd.match.handle_matcher import HandleMatcher
from sotd.match.knot_matcher import KnotMatcher
from sotd.match.types import MatchResult, create_match_result


class CompositeBrushStrategy(BaseBrushMatchingStrategy):
    """Strategy for matching composite brushes using HandleMatcher and KnotMatcher."""

    def __init__(self, handles_path: Path, knot_strategies: list):
        """Initialize composite brush strategy."""
        super().__init__()
        self.handle_matcher = HandleMatcher(handles_path)
        self.knot_matcher = KnotMatcher(knot_strategies)

    def match(self, value: str) -> Optional[Dict[str, Any]]:
        """
        Try to match both handle and knot components in the input string.

        Returns:
            Optional[Dict]: Match result if both handle and knot found, None otherwise
        """
        if not value or not isinstance(value, str):
            return None

        try:
            # Try handle matching on the entire string
            handle_match = self.handle_matcher.match_handle_maker(value)

            # Try knot matching on the entire string
            knot_match = self.knot_matcher.match(value)

            # Both must be found for a valid composite brush
            if handle_match and handle_match.get("handle_maker") and knot_match:
                return self._create_composite_result(handle_match, knot_match, value)

            return None

        except Exception as e:
            # Fail fast for debugging
            raise ValueError(f"Composite brush matching failed for '{value}': {e}")

    def _create_composite_result(
        self, handle_match: Dict[str, Any], knot_match: MatchResult, value: str
    ) -> Dict[str, Any]:
        """Create composite brush result matching legacy system structure."""
        # Get the actual patterns used for matching
        handle_pattern = handle_match.get("_pattern_used", "unknown")
        knot_pattern = knot_match.pattern if knot_match.pattern else "unknown"

        # Create composite brush structure matching legacy system
        matched = {
            "brand": None,  # Composite brush
            "model": None,  # Composite brush
            "handle": {
                "brand": handle_match.get("handle_maker"),
                "model": handle_match.get("handle_model"),
                "source_text": value,
                "_matched_by": "HandleMatcher",
                "_pattern": handle_pattern,
            },
            "knot": {
                "brand": knot_match.matched.get("brand"),
                "model": knot_match.matched.get("model"),
                "fiber": knot_match.matched.get("fiber"),
                "knot_size_mm": knot_match.matched.get("knot_size_mm"),
                "source_text": value,
                "_matched_by": "KnotMatcher",
                "_pattern": knot_pattern,
            },
        }

        return {
            "matched": matched,
            "match_type": "composite",
            "pattern": handle_pattern if handle_pattern != "unknown" else knot_pattern,
        }


class SingleComponentFallbackStrategy(BaseBrushMatchingStrategy):
    """Strategy for single component fallback (handle-only or knot-only)."""

    def __init__(self, handles_path: Path, knot_strategies: list):
        """Initialize single component fallback strategy."""
        super().__init__()
        self.handle_matcher = HandleMatcher(handles_path)
        self.knot_matcher = KnotMatcher(knot_strategies)

    def match(self, value: str) -> Optional[Dict[str, Any]]:
        """
        Try to match either handle or knot component in the input string.

        Returns:
            Optional[Dict]: Match result if handle or knot found, None otherwise
        """
        if not value or not isinstance(value, str):
            return None

        try:
            best_match = None
            best_score = -1
            best_match_type = None

            # Try knot matching first
            knot_match = self.knot_matcher.match(value)
            if knot_match and knot_match.matched:
                # Score knot match
                knot_score = self._score_knot_match(value, knot_match)
                if knot_score > best_score:
                    best_score = knot_score
                    best_match = knot_match
                    best_match_type = "knot"

            # Try handle matching
            handle_match = self.handle_matcher.match_handle_maker(value)
            if handle_match and handle_match.get("handle_maker"):
                # Score handle match
                handle_score = self._score_handle_match(value, handle_match)
                if handle_score > best_score:
                    best_score = handle_score
                    best_match = handle_match
                    best_match_type = "handle"

            if best_match:
                return self._create_single_component_result(best_match, best_match_type, value)

            return None

        except Exception as e:
            # Fail fast for debugging
            raise ValueError(f"Single component fallback failed for '{value}': {e}")

    def _score_knot_match(self, value: str, knot_match: MatchResult) -> int:
        """Score a knot match."""
        # Simple scoring based on fiber presence
        fiber = knot_match.matched.get("fiber")
        if fiber:
            return 10  # Higher score for fiber matches
        return 5  # Base score for knot matches

    def _score_handle_match(self, value: str, handle_match: Dict[str, Any]) -> int:
        """Score a handle match."""
        # Simple scoring based on handle maker presence
        handle_maker = handle_match.get("handle_maker")
        if handle_maker:
            return 8  # Base score for handle matches
        return 0

    def _create_single_component_result(
        self, match: Any, match_type: str, value: str
    ) -> Dict[str, Any]:
        """Create single component result matching legacy system structure."""
        if match_type == "handle":
            # Handle-only match
            handle_pattern = match.get("_pattern_used", "unknown")
            matched = {
                "brand": None,  # Composite brush
                "model": None,  # Composite brush
                "handle": {
                    "brand": match.get("handle_maker"),
                    "model": match.get("handle_model"),
                    "source_text": value,
                    "_matched_by": "HandleMatcher",
                    "_pattern": handle_pattern,
                },
                "knot": {
                    "brand": None,
                    "model": None,
                    "fiber": None,
                    "knot_size_mm": None,
                    "source_text": value,
                    "_matched_by": "SingleComponentFallback",
                    "_pattern": "handle_only",
                },
            }
        else:
            # Knot-only match
            knot_pattern = match.pattern if match.pattern else "unknown"
            matched = {
                "brand": None,  # Composite brush
                "model": None,  # Composite brush
                "handle": {
                    "brand": None,
                    "model": None,
                    "source_text": value,
                    "_matched_by": "SingleComponentFallback",
                    "_pattern": "knot_only",
                },
                "knot": {
                    "brand": match.matched.get("brand"),
                    "model": match.matched.get("model"),
                    "fiber": match.matched.get("fiber"),
                    "knot_size_mm": match.matched.get("knot_size_mm"),
                    "source_text": value,
                    "_matched_by": "KnotMatcher",
                    "_pattern": knot_pattern,
                },
            }

        return {
            "matched": matched,
            "match_type": "single_component",
            "pattern": (
                matched["handle"]["_pattern"]
                if match_type == "handle"
                else matched["knot"]["_pattern"]
            ),
        }
