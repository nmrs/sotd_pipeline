"""
Scoring Engine Component.

This component scores strategy results based on configuration weights and criteria.
"""

import re
from typing import List, Optional

from sotd.match.types import MatchResult


class ScoringEngine:
    """
    Engine for scoring brush matching strategy results.

    This component applies scoring weights and modifiers to strategy results
    to determine the best match.
    """

    def __init__(self, config):
        """
        Initialize the scoring engine.

        Args:
            config: BrushScoringConfig instance
        """
        self.config = config

    def score_results(self, results: List[MatchResult], value: str) -> List[MatchResult]:
        """
        Score all strategy results.

        Args:
            results: List of MatchResult objects to score
            value: Original input string for context

        Returns:
            List of MatchResult objects with scores added
        """
        scored_results = []

        for result in results:
            score = self._calculate_score(result, value)
            result.score = score
            scored_results.append(result)

        return scored_results

    def get_best_result(self, scored_results: List[MatchResult]) -> Optional[MatchResult]:
        """
        Get the highest-scoring result.

        Args:
            scored_results: List of scored MatchResult objects

        Returns:
            Highest-scoring MatchResult, or None if list is empty or no valid matches
        """
        if not scored_results:
            return None

        # Filter out results with no valid matches (matched=None or empty matched)
        valid_results = [r for r in scored_results if r.matched is not None and r.matched]

        if not valid_results:
            return None

        return max(valid_results, key=lambda r: r.score or 0.0)

    def _calculate_score(self, result: MatchResult, value: str) -> float:
        """
        Calculate score for a single result.

        Args:
            result: MatchResult to score
            value: Original input string

        Returns:
            Calculated score
        """
        # Get base strategy score
        strategy_name = self._get_strategy_name_from_result(result)
        base_score = self.config.get_base_strategy_score(strategy_name)

        # Apply modifiers
        modifier_score = self._calculate_modifiers(result, value, strategy_name)

        return base_score + modifier_score

    def _get_strategy_name_from_result(self, result: MatchResult) -> str:
        """
        Extract strategy name from result.

        Args:
            result: MatchResult object

        Returns:
            Strategy name
        """
        # If the result has a strategy field, use it directly
        if result.strategy:
            return result.strategy

        # Fallback to mapping match_type values to strategy names
        match_type = result.match_type or "unknown_strategy"
        matched = result.matched or {}

        # Check if this is a dual component result (has handle and knot sections)
        if match_type == "regex" and "handle" in matched and "knot" in matched:
            return "dual_component"

        # Map match_type values to strategy names
        match_type_to_strategy = {
            "regex": "complete_brush",  # Known brush strategies use regex
            "fiber_fallback": "single_component_fallback",  # Fiber fallback strategy
            "size_fallback": "single_component_fallback",  # Size fallback strategy
            "handle": "complete_brush",  # Handle matcher results
            "knot": "single_component_fallback",  # Knot matcher results
            "composite": "dual_component",  # Composite brush results
            "single_component": "single_component_fallback",  # Single component fallback results
        }

        return match_type_to_strategy.get(match_type, "single_component_fallback")

    def _calculate_modifiers(self, result: MatchResult, value: str, strategy_name: str) -> float:
        """
        Calculate modifier score for a result.

        Args:
            result: MatchResult to score
            value: Original input string
            strategy_name: Name of the strategy

        Returns:
            Modifier score
        """
        modifier_score = 0.0

        # Get all available modifiers for this strategy
        modifier_names = self.config.get_all_modifier_names(strategy_name)

        for modifier_name in modifier_names:
            # Get the modifier weight from configuration
            modifier_weight = self.config.get_strategy_modifier(strategy_name, modifier_name)

            # Apply the modifier function if it exists
            modifier_function = getattr(self, f"_modifier_{modifier_name}", None)
            if callable(modifier_function):
                modifier_value = modifier_function(value, result, strategy_name)
                modifier_score += modifier_value * modifier_weight
            else:
                # If no modifier function exists, just add the weight directly
                modifier_score += modifier_weight

        return modifier_score

    def _modifier_multiple_brands(self, input_text: str, result: dict, strategy_name: str) -> float:
        """
        Return score modifier for multiple brand mentions.

        Args:
            input_text: Original input string
            result: MatchResult object
            strategy_name: Name of the strategy

        Returns:
            Modifier value (1.0 if multiple brands detected, 0.0 otherwise)
        """
        # Count brand mentions in input text
        brand_patterns = [
            r"\bsimpson\b",
            r"\bomega\b",
            r"\bsemogue\b",
            r"\bzenith\b",
            r"\bdeclaration\b",
            r"\bchisel\b",
            r"\bhound\b",
            r"\bwolf\b",
            r"\bwhiskers\b",
            r"\bsummer\b",
            r"\bbreak\b",
            r"\bsoaps\b",
            r"\bmountain\b",
            r"\bhare\b",
            r"\bshaving\b",
            r"\bmaggard\b",
            r"\belite\b",
            r"\bmojito\b",
            r"\bwashington\b",
            r"\btimberwolf\b",
        ]

        brand_count = 0
        for pattern in brand_patterns:
            if re.search(pattern, input_text.lower()):
                brand_count += 1

        return 1.0 if brand_count > 1 else 0.0

    def _modifier_fiber_words(self, input_text: str, result: dict, strategy_name: str) -> float:
        """
        Return score modifier for fiber-specific terminology.

        Args:
            input_text: Original input string
            result: MatchResult object
            strategy_name: Name of the strategy

        Returns:
            Modifier value (1.0 if fiber words detected, 0.0 otherwise)
        """
        fiber_patterns = [
            r"\bbadger\b",
            r"\bboar\b",
            r"\bsynthetic\b",
            r"\bsyn\b",
            r"\bnylon\b",
            r"\bplissoft\b",
            r"\btuxedo\b",
            r"\bcashmere\b",
            r"\bmixed\b",
            r"\btimberwolf\b",
        ]

        for pattern in fiber_patterns:
            if re.search(pattern, input_text.lower()):
                return 1.0

        return 0.0

    def _modifier_size_specification(
        self, input_text: str, result: dict, strategy_name: str
    ) -> float:
        """
        Return score modifier for size specifications.

        Args:
            input_text: Original input string
            result: MatchResult object
            strategy_name: Name of the strategy

        Returns:
            Modifier value (1.0 if size specification detected, 0.0 otherwise)
        """
        size_patterns = [r"\b\d+mm\b", r"\b\d+\s*mm\b", r"\b\d+x\d+\b", r"\b\d+\s*x\s*\d+\b"]

        for pattern in size_patterns:
            if re.search(pattern, input_text.lower()):
                return 1.0

        return 0.0

    def _modifier_delimiter_confidence(
        self, input_text: str, result: dict, strategy_name: str
    ) -> float:
        """
        Return score modifier for high-confidence delimiters.

        Args:
            input_text: Original input string
            result: MatchResult object
            strategy_name: Name of the strategy

        Returns:
            Modifier value (1.0 if high-confidence delimiter detected, 0.0 otherwise)
        """
        high_confidence_delimiters = [r"\s+w/\s+", r"\s+with\s+", r"\s+in\s+"]

        for delimiter in high_confidence_delimiters:
            if re.search(delimiter, input_text.lower()):
                return 1.0

        return 0.0

    def _modifier_handle_confidence(
        self, input_text: str, result: dict, strategy_name: str
    ) -> float:
        """
        Return score modifier for handle confidence.

        Args:
            input_text: Original input string
            result: MatchResult object
            strategy_name: Name of the strategy

        Returns:
            Modifier value (0.0 to 1.0 based on handle confidence)
        """
        # This is a placeholder for handle confidence scoring
        # In a full implementation, this would use the existing _score_as_handle logic
        return 0.0

    def _modifier_knot_confidence(self, input_text: str, result: dict, strategy_name: str) -> float:
        """
        Return score modifier for knot confidence.

        Args:
            input_text: Original input string
            result: MatchResult object
            strategy_name: Name of the strategy

        Returns:
            Modifier value (0.0 to 1.0 based on knot confidence)
        """
        # This is a placeholder for knot confidence scoring
        # In a full implementation, this would use the existing _score_as_knot logic
        return 0.0

    def _modifier_word_count_balance(
        self, input_text: str, result: dict, strategy_name: str
    ) -> float:
        """
        Return score modifier for word count balance.

        Args:
            input_text: Original input string
            result: MatchResult object
            strategy_name: Name of the strategy

        Returns:
            Modifier value (0.0 to 1.0 based on word count balance)
        """
        # This is a placeholder for word count balance scoring
        # In a full implementation, this would calculate balance between handle/knot words
        return 0.0

    def _modifier_dual_component(
        self, input_text: str, result: dict, strategy_name: str
    ) -> float:
        """
        Return score modifier for dual component matches (unified strategy only).

        Args:
            input_text: Original input string
            result: MatchResult object
            strategy_name: Name of the strategy

        Returns:
            Modifier value (1.0 if both handle and knot matched, 0.0 otherwise)
        """
        if strategy_name != "unified":
            return 0.0

        # Check if both handle and knot sections exist and have valid matches
        handle = result.get("handle")
        knot = result.get("knot")
        
        if handle and knot:
            # Both handle and knot have data
            handle_brand = handle.get("brand")
            knot_brand = knot.get("brand")
            
            # Return 1.0 if both have brands (indicating successful matches)
            return 1.0 if handle_brand and knot_brand else 0.0
        
        return 0.0
