"""
Known Split Wrapper Strategy.

This strategy implements known split functionality directly
to integrate with the scoring system architecture.
"""

import re
from typing import Optional

from sotd.match.brush_matching_strategies.base_brush_matching_strategy import (
    BaseBrushMatchingStrategy,
)
from sotd.match.types import MatchResult


class KnownSplitWrapperStrategy(BaseBrushMatchingStrategy):
    """Strategy for matching known split brush patterns."""

    def __init__(self, known_splits_data: dict):
        """
        Initialize the strategy with known splits data.

        Args:
            known_splits_data: Dictionary containing known split brush patterns
        """
        super().__init__()
        self.known_splits_data = known_splits_data or {}
        self.compiled_patterns = self._compile_patterns()

    def _compile_patterns(self) -> list:
        """Compile regex patterns for known splits."""
        compiled = []
        for brand, brand_data in self.known_splits_data.items():
            if isinstance(brand_data, dict):
                for model, model_data in brand_data.items():
                    if isinstance(model_data, dict) and "patterns" in model_data:
                        for pattern in model_data["patterns"]:
                            try:
                                compiled.append(
                                    {
                                        "pattern": pattern,
                                        "regex": re.compile(pattern, re.IGNORECASE),
                                        "brand": brand,
                                        "model": model,
                                        "data": model_data,
                                    }
                                )
                            except re.error:
                                # Skip invalid patterns
                                continue
        return compiled

    def match(self, value: str) -> Optional[MatchResult]:
        """
        Match using known split logic.

        Args:
            value: The brush string to match

        Returns:
            MatchResult or None
        """
        if not value or not isinstance(value, str):
            return None

        # Try to match against compiled patterns
        for pattern_info in self.compiled_patterns:
            if pattern_info["regex"].search(value):
                # Create match result
                matched_data = {
                    "brand": pattern_info["brand"],
                    "model": pattern_info["model"],
                    "fiber": pattern_info["data"].get("fiber"),
                    "knot_size_mm": pattern_info["data"].get("knot_size_mm"),
                    "handle_maker": pattern_info["data"].get("handle_maker"),
                    "source_text": value,
                    "_matched_by": "KnownSplitWrapperStrategy",
                    "_pattern": pattern_info["pattern"],
                }

                return MatchResult(
                    original=value,
                    matched=matched_data,
                    match_type="known_split",
                    pattern=pattern_info["pattern"],
                    strategy="known_split",  # Set the strategy name
                )

        return None
