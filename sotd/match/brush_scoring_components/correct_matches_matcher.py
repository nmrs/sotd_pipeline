"""
Correct Matches Matcher Component.

This component provides fast lookup against validated matches from correct_matches.yaml.
"""

from typing import Any, Dict, Optional

from sotd.match.types import MatchResult


class CorrectMatchesMatcher:
    """
    Fast lookup matcher for validated correct matches.

    This component provides the fastest path for matching by checking
    against pre-validated matches in correct_matches.yaml.
    """

    def __init__(self, correct_matches_data: Dict[str, Any]):
        """
        Initialize the correct matches matcher.

        Args:
            correct_matches_data: Data from correct_matches.yaml
        """
        self.correct_matches = correct_matches_data

    def match(self, value: str) -> Optional[MatchResult]:
        """
        Match against correct matches data.

        Args:
            value: The brush string to match

        Returns:
            MatchResult if found, None otherwise
        """
        if not value:
            return None

        # Normalize for case-insensitive matching
        normalized_value = value.lower().strip()

        # Check brush section
        brush_matches = self.correct_matches.get("brush", {})
        for brand, brand_data in brush_matches.items():
            for model, patterns in brand_data.items():
                if isinstance(patterns, list):
                    # Handle list of patterns
                    for pattern in patterns:
                        if isinstance(pattern, str) and pattern.lower() == normalized_value:
                            return self._create_match_result(value, brand, model, "exact", pattern)
                        elif isinstance(pattern, dict):
                            # Handle pattern with metadata
                            pattern_text = list(pattern.keys())[0]
                            if pattern_text.lower() == normalized_value:
                                return self._create_match_result(
                                    value, brand, model, "exact", pattern_text
                                )

        # Check split_brush section
        split_brush_matches = self.correct_matches.get("split_brush", {})
        for brand, brand_data in split_brush_matches.items():
            for model, patterns in brand_data.items():
                if isinstance(patterns, list):
                    for pattern in patterns:
                        if isinstance(pattern, str) and pattern.lower() == normalized_value:
                            return self._create_match_result(value, brand, model, "exact", pattern)
                        elif isinstance(pattern, dict):
                            pattern_text = list(pattern.keys())[0]
                            if pattern_text.lower() == normalized_value:
                                return self._create_match_result(
                                    value, brand, model, "exact", pattern_text
                                )

        return None

    def _create_match_result(
        self, original: str, brand: str, model: str, match_type: str, pattern: str
    ) -> MatchResult:
        """
        Create a MatchResult from correct match data.

        Args:
            original: Original input string
            brand: Brand name
            model: Model name
            match_type: Type of match
            pattern: Pattern that matched

        Returns:
            MatchResult object
        """
        return MatchResult(
            original=original,
            matched={
                "brand": brand,
                "model": model,
                "source_text": original,
                "source_type": "exact",
            },
            match_type=match_type,
            pattern=pattern,
        )
