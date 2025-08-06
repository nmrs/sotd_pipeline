"""
Scoring Engine Component.

This component scores strategy results based on configuration weights and criteria.
"""

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
            Highest-scoring MatchResult, or None if list is empty
        """
        if not scored_results:
            return None
        
        return max(scored_results, key=lambda r: r.score)

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
        # This is a simplified implementation
        # In practice, the strategy name would be stored in the result
        # For now, we'll use the match_type as a proxy
        return result.match_type or "unknown_strategy"

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
            modifier_value = self.config.get_strategy_modifier(strategy_name, modifier_name)
            modifier_score += modifier_value
        
        return modifier_score 