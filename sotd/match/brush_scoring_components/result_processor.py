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
        Ensure result has consistent structure.
        
        Args:
            result: MatchResult to process
        """
        # Ensure matched field exists
        if result.matched is None:
            result.matched = {}
        
        # Ensure required fields exist
        if "source_text" not in result.matched:
            result.matched["source_text"] = result.original
        
        if "source_type" not in result.matched:
            result.matched["source_type"] = result.match_type or "unknown"

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