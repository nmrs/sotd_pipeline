"""
Brush scoring functions for multi-strategy brush matching system.

This module provides individual scoring functions for different brush strategy
types and criteria, supporting configurable weights from brush_scoring_config.yaml.
"""

import re
from typing import Any, Dict

from sotd.match.types import MatchResult


class BrushScoringFunctions:
    """
    Collection of brush scoring functions for different criteria.
    
    This class provides methods to calculate bonus and penalty scores
    based on various brush characteristics and matching patterns.
    """
    
    def __init__(self, config):
        """Initialize scoring functions with configuration.
        
        Args:
            config: Brush scoring configuration instance.
        """
        self.config = config
        
        # Compile regex patterns for efficiency
        self._fiber_patterns = re.compile(
            r'\b(badger|boar|synthetic|horse|mixed)\b', 
            re.IGNORECASE
        )
        self._size_patterns = re.compile(r'\b(\d+(?:\.\d+)?)\s*(?:mm|millimeter)\b', re.IGNORECASE)
        self._generic_terms = re.compile(r'\b(brush|knot|handle)\b', re.IGNORECASE)
        self._delimiter_patterns = re.compile(r'\b(?:in|with)\b', re.IGNORECASE)
    
    def calculate_bonus_score(self, match_result: MatchResult, original_value: str) -> float:
        """Calculate total bonus score for a match result.
        
        Args:
            match_result: Match result to analyze.
            original_value: Original input value.
            
        Returns:
            Total bonus score.
        """
        if not match_result.matched:
            return 0.0
        
        bonus_score = 0.0
        
        # Add individual bonus factors
        bonus_score += self._bonus_delimiters_present(original_value)
        bonus_score += self._bonus_brand_match(match_result.matched)
        bonus_score += self._bonus_fiber_words(original_value)
        bonus_score += self._bonus_size_specification(match_result.matched, original_value)
        bonus_score += self._bonus_handle_maker_match(match_result.matched)
        bonus_score += self._bonus_knot_maker_match(match_result.matched)
        bonus_score += self._bonus_exact_pattern_match(match_result, original_value)
        
        return bonus_score
    
    def calculate_penalty_score(self, match_result: MatchResult, original_value: str) -> float:
        """Calculate total penalty score for a match result.
        
        Args:
            match_result: Match result to analyze.
            original_value: Original input value.
            
        Returns:
            Total penalty score (negative value).
        """
        if not match_result.matched:
            return 0.0
        
        penalty_score = 0.0
        
        # Add individual penalty factors
        penalty_score += self._penalty_single_brand_only(match_result.matched)
        penalty_score += self._penalty_no_fiber_detected(match_result.matched)
        penalty_score += self._penalty_no_size_detected(match_result.matched)
        penalty_score += self._penalty_fuzzy_match(match_result, original_value)
        penalty_score += self._penalty_generic_terms(original_value)
        penalty_score += self._penalty_incomplete_specs(match_result.matched)
        
        return penalty_score
    
    def _bonus_delimiters_present(self, original_value: str) -> float:
        """Calculate bonus for presence of delimiters.
        
        Args:
            original_value: Original input value.
            
        Returns:
            Bonus score for delimiters.
        """
        if self._delimiter_patterns.search(original_value):
            return self.config.get_bonus_factor("delimiters_present")
        return 0.0
    
    def _bonus_brand_match(self, matched_data: Dict[str, Any]) -> float:
        """Calculate bonus for brand match.
        
        Args:
            matched_data: Matched data dictionary.
            
        Returns:
            Bonus score for brand match.
        """
        if matched_data.get("brand"):
            return self.config.get_bonus_factor("brand_match")
        return 0.0
    
    def _bonus_fiber_words(self, original_value: str) -> float:
        """Calculate bonus for fiber-related words.
        
        Args:
            original_value: Original input value.
            
        Returns:
            Bonus score for fiber words.
        """
        if self._fiber_patterns.search(original_value):
            return self.config.get_bonus_factor("fiber_words")
        return 0.0
    
    def _bonus_size_specification(self, matched_data: Dict[str, Any], original_value: str) -> float:
        """Calculate bonus for size specification.
        
        Args:
            matched_data: Matched data dictionary.
            original_value: Original input value.
            
        Returns:
            Bonus score for size specification.
        """
        # Check if knot size is in matched data
        if matched_data.get("knot_size_mm"):
            return self.config.get_bonus_factor("size_specification")
        
        # Check if size pattern is in original value
        if self._size_patterns.search(original_value):
            return self.config.get_bonus_factor("size_specification")
        
        return 0.0
    
    def _bonus_handle_maker_match(self, matched_data: Dict[str, Any]) -> float:
        """Calculate bonus for handle maker match.
        
        Args:
            matched_data: Matched data dictionary.
            
        Returns:
            Bonus score for handle maker match.
        """
        if matched_data.get("handle_maker"):
            return self.config.get_bonus_factor("handle_maker_match")
        return 0.0
    
    def _bonus_knot_maker_match(self, matched_data: Dict[str, Any]) -> float:
        """Calculate bonus for knot maker match.
        
        Args:
            matched_data: Matched data dictionary.
            
        Returns:
            Bonus score for knot maker match.
        """
        if matched_data.get("knot_maker"):
            return self.config.get_bonus_factor("knot_maker_match")
        return 0.0
    
    def _bonus_exact_pattern_match(self, match_result: MatchResult, original_value: str) -> float:
        """Calculate bonus for exact pattern match.
        
        Args:
            match_result: Match result to analyze.
            original_value: Original input value.
            
        Returns:
            Bonus score for exact pattern match.
        """
        if match_result.pattern and match_result.pattern.lower() in original_value.lower():
            return self.config.get_bonus_factor("exact_pattern_match")
        return 0.0
    
    def _penalty_single_brand_only(self, matched_data: Dict[str, Any]) -> float:
        """Calculate penalty for single brand only (no model).
        
        Args:
            matched_data: Matched data dictionary.
            
        Returns:
            Penalty score for single brand only.
        """
        if matched_data.get("brand") and not matched_data.get("model"):
            return self.config.get_penalty_factor("single_brand_only")
        return 0.0
    
    def _penalty_no_fiber_detected(self, matched_data: Dict[str, Any]) -> float:
        """Calculate penalty for no fiber detected.
        
        Args:
            matched_data: Matched data dictionary.
            
        Returns:
            Penalty score for no fiber detected.
        """
        if not matched_data.get("fiber"):
            return self.config.get_penalty_factor("no_fiber_detected")
        return 0.0
    
    def _penalty_no_size_detected(self, matched_data: Dict[str, Any]) -> float:
        """Calculate penalty for no size detected.
        
        Args:
            matched_data: Matched data dictionary.
            
        Returns:
            Penalty score for no size detected.
        """
        if not matched_data.get("knot_size_mm"):
            return self.config.get_penalty_factor("no_size_detected")
        return 0.0
    
    def _penalty_fuzzy_match(self, match_result: MatchResult, original_value: str) -> float:
        """Calculate penalty for fuzzy/partial match.
        
        Args:
            match_result: Match result to analyze.
            original_value: Original input value.
            
        Returns:
            Penalty score for fuzzy match.
        """
        if match_result.pattern and match_result.pattern.lower() not in original_value.lower():
            return self.config.get_penalty_factor("fuzzy_match")
        return 0.0
    
    def _penalty_generic_terms(self, original_value: str) -> float:
        """Calculate penalty for generic terms.
        
        Args:
            original_value: Original input value.
            
        Returns:
            Penalty score for generic terms.
        """
        if self._generic_terms.search(original_value):
            return self.config.get_penalty_factor("generic_terms")
        return 0.0
    
    def _penalty_incomplete_specs(self, matched_data: Dict[str, Any]) -> float:
        """Calculate penalty for incomplete specifications.
        
        Args:
            matched_data: Matched data dictionary.
            
        Returns:
            Penalty score for incomplete specifications.
        """
        required_fields = [
            matched_data.get("brand"),
            matched_data.get("model"), 
            matched_data.get("fiber")
        ]
        if not all(required_fields):
            return self.config.get_penalty_factor("incomplete_specs")
        return 0.0
    
    def get_strategy_base_score(self, strategy_name: str) -> float:
        """Get base score for a strategy.
        
        Args:
            strategy_name: Name of the strategy.
            
        Returns:
            Base score for the strategy.
        """
        return self.config.get_base_strategy_score(strategy_name)
    
    def calculate_total_score(
        self, 
        base_score: float, 
        bonus_score: float, 
        penalty_score: float
    ) -> float:
        """Calculate total score from components.
        
        Args:
            base_score: Base strategy score.
            bonus_score: Total bonus score.
            penalty_score: Total penalty score.
            
        Returns:
            Total score with minimum threshold applied.
        """
        total_score = base_score + bonus_score + penalty_score
        
        # Apply minimum threshold
        min_threshold = self.config.get_routing_rule("minimum_score_threshold") or 0.0
        return max(total_score, min_threshold)


# Convenience functions for direct use
def calculate_bonus_score(
    match_result: MatchResult, 
    original_value: str, 
    config
) -> float:
    """Calculate bonus score for a match result.
    
    Args:
        match_result: Match result to analyze.
        original_value: Original input value.
        config: Brush scoring configuration.
        
    Returns:
        Total bonus score.
    """
    scoring_functions = BrushScoringFunctions(config)
    return scoring_functions.calculate_bonus_score(match_result, original_value)


def calculate_penalty_score(
    match_result: MatchResult, 
    original_value: str, 
    config
) -> float:
    """Calculate penalty score for a match result.
    
    Args:
        match_result: Match result to analyze.
        original_value: Original input value.
        config: Brush scoring configuration.
        
    Returns:
        Total penalty score (negative value).
    """
    scoring_functions = BrushScoringFunctions(config)
    return scoring_functions.calculate_penalty_score(match_result, original_value)


def get_strategy_base_score(strategy_name: str, config) -> float:
    """Get base score for a strategy.
    
    Args:
        strategy_name: Name of the strategy.
        config: Brush scoring configuration.
        
    Returns:
        Base score for the strategy.
    """
    scoring_functions = BrushScoringFunctions(config)
    return scoring_functions.get_strategy_base_score(strategy_name) 