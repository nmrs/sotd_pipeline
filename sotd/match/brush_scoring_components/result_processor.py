"""
Result Processor Component.

This component processes final results to ensure consistency and format.
"""

from typing import Optional

from sotd.match.types import MatchResult


class ResultProcessor:
    """
    Processor for final brush matching results.

    This component ensures output format consistency and applies
    any final processing steps.
    """

    def __init__(self):
        """Initialize the result processor."""
        pass

    def process_result(self, result: Optional[MatchResult], value: str) -> Optional[MatchResult]:
        """
        Process a final result.

        Args:
            result: MatchResult to process, or None
            value: Original input string

        Returns:
            Processed MatchResult, or None
        """
        if result is None:
            return None

        # Ensure consistent structure
        self._ensure_consistent_structure(result)

        # Apply any final processing
        self._apply_final_processing(result, value)

        return result

    def _ensure_consistent_structure(self, result: MatchResult) -> None:
        """
        Ensure result has consistent structure matching legacy system.

        Args:
            result: MatchResult to process
        """
        # For Phase 3.1 (Black Box Alignment), preserve None for unmatched cases
        # Don't convert None to empty dict - this should match legacy behavior
        if result.matched is None:
            return  # Preserve None for unmatched cases

        # For Phase 3.1 (Black Box Alignment), don't add extra fields
        # that the legacy system doesn't have
        # TODO: Re-enable these fields in Phase 3.2+ when we break down individual strategies
        # if "source_text" not in result.matched:
        #     result.matched["source_text"] = result.original
        #
        # if "source_type" not in result.matched:
        #     result.matched["source_type"] = result.match_type or "unknown"

        # Create nested handle and knot sections to match legacy system structure
        # Only if they don't already exist (preserve composite brush structure)
        if "handle" not in result.matched or "knot" not in result.matched:
            self._create_handle_knot_sections(result)

    def _apply_final_processing(self, result: MatchResult, value: str) -> None:
        """
        Apply final processing steps.

        Args:
            result: MatchResult to process
            value: Original input string
        """
        # Set original field if not already set
        if not result.original:
            result.original = value

        # Ensure pattern field exists
        if not result.pattern:
            result.pattern = "unknown"

        # Ensure match_type field exists
        if not result.match_type:
            result.match_type = "unknown"

    def _create_handle_knot_sections(self, result: MatchResult) -> None:
        """
        Create nested handle and knot sections to match legacy system structure.

        Args:
            result: MatchResult to process
        """
        if result.matched is None:
            return  # Preserve None for unmatched cases

        # Extract fields from the flat structure
        brand = result.matched.get("brand")
        model = result.matched.get("model")
        fiber = result.matched.get("fiber")
        knot_size_mm = result.matched.get("knot_size_mm")

        # Create handle section
        result.matched["handle"] = {
            "brand": brand,
            "model": model,
            "_matched_by": "BrushScoringMatcher",
            "_pattern": result.pattern or "unknown",
        }

        # Create knot section
        result.matched["knot"] = {
            "brand": brand,
            "model": model,
            "fiber": fiber,
            "knot_size_mm": knot_size_mm,
            "_matched_by": "BrushScoringMatcher",
            "_pattern": result.pattern or "unknown",
        }

        # Remove flat fields that are now in nested sections
        # Keep brand and model at top level for compatibility
        result.matched.pop("fiber", None)
        result.matched.pop("knot_size_mm", None)
        result.matched.pop("handle_maker", None)
        result.matched.pop("source_type", None)
