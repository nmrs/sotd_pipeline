"""
Brush scoring engine for multi-strategy brush matching system.

This module provides the core scoring engine that executes brush strategies,
calculates scores based on configuration weights, and returns sorted results.
"""

from typing import Any, Dict, List, Optional

from sotd.match.brush_matching_strategies.base_brush_matching_strategy import (
    BaseBrushMatchingStrategy,
)
from sotd.match.brush_scoring_config import BrushScoringConfig
from sotd.match.types import MatchResult


class BrushScoringResult:
    """Result structure for brush scoring operations."""
    
    def __init__(
        self,
        match_result: MatchResult,
        strategy_name: str,
        base_score: float,
        bonus_score: float,
        penalty_score: float,
        total_score: float,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        self.match_result = match_result
        self.strategy_name = strategy_name
        self.base_score = base_score
        self.bonus_score = bonus_score
        self.penalty_score = penalty_score
        self.total_score = total_score
        self.metadata = metadata or {}
    
    def __lt__(self, other: "BrushScoringResult") -> bool:
        """Sort by total score (higher scores first)."""
        return self.total_score > other.total_score
    
    def __repr__(self) -> str:
        return (
            f"BrushScoringResult("
            f"strategy={self.strategy_name}, "
            f"score={self.total_score:.2f}, "
            f"matched={self.match_result.matched_bool}"
            f")"
        )


class BrushScoringEngine:
    """
    Core brush scoring engine that executes strategies and calculates scores.
    
    This engine runs all brush strategies for a given input, calculates scores
    based on configuration weights, and returns sorted results with metadata.
    """
    
    def __init__(self, config: BrushScoringConfig):
        """Initialize scoring engine with configuration.
        
        Args:
            config: Brush scoring configuration.
        """
        self.config = config
        self._strategies: List[BaseBrushMatchingStrategy] = []
        self._strategy_names: List[str] = []
    
    def add_strategy(self, strategy: BaseBrushMatchingStrategy, name: str) -> None:
        """Add a brush matching strategy to the engine.
        
        Args:
            strategy: Brush matching strategy instance.
            name: Name of the strategy for scoring lookup.
        """
        self._strategies.append(strategy)
        self._strategy_names.append(name)
    
    def score_brush(self, value: str) -> List[BrushScoringResult]:
        """Score a brush input using all registered strategies.
        
        Args:
            value: Brush input string to score.
            
        Returns:
            List of scoring results sorted by total score (highest first).
        """
        if not self.config.is_loaded:
            raise ValueError("Brush scoring configuration not loaded")
        
        results = []
        max_strategies = (
            self.config.get_routing_rule("max_strategies_to_run") or len(self._strategies)
        )
        
        for i, (strategy, strategy_name) in enumerate(zip(self._strategies, self._strategy_names)):
            if i >= max_strategies:
                break
            
            try:
                # Execute strategy
                match_result = strategy.match(value)
                
                if match_result is None:
                    # No match from this strategy
                    continue
                
                # Calculate score for this result
                scoring_result = self._calculate_score(match_result, strategy_name, value)
                results.append(scoring_result)
                
                # Check if we should stop early
                if (
                    self.config.get_routing_rule("stop_on_good_match") and 
                    scoring_result.total_score >= self.config.get_routing_rule("minimum_score_threshold")
                ):
                    break
                    
            except Exception as e:
                # Log strategy failure but continue with other strategies
                # This follows the fail-fast approach for internal errors
                raise RuntimeError(f"Strategy {strategy_name} failed: {str(e)}") from e
        
        # Sort results by total score (highest first)
        results.sort()
        return results
    
    def _calculate_score(
        self, match_result: MatchResult, strategy_name: str, original_value: str
    ) -> BrushScoringResult:
        """Calculate score for a single match result.
        
        Args:
            match_result: Match result from strategy.
            strategy_name: Name of the strategy used.
            original_value: Original input value.
            
        Returns:
            BrushScoringResult with calculated scores.
        """
        # Get base score for this strategy
        base_score = self.config.get_base_strategy_score(strategy_name)
        
        # Calculate bonus factors
        bonus_score = self._calculate_bonus_score(match_result, original_value)
        
        # Calculate penalty factors
        penalty_score = self._calculate_penalty_score(match_result, original_value)
        
        # Calculate total score
        total_score = base_score + bonus_score + penalty_score
        
        # Ensure minimum score
        min_threshold = self.config.get_routing_rule("minimum_score_threshold") or 0.0
        total_score = max(total_score, min_threshold)
        
        # Create metadata
        metadata = {
            "original_value": original_value,
            "strategy_name": strategy_name,
            "match_type": match_result.match_type,
            "pattern": match_result.pattern,
        }
        
        return BrushScoringResult(
            match_result=match_result,
            strategy_name=strategy_name,
            base_score=base_score,
            bonus_score=bonus_score,
            penalty_score=penalty_score,
            total_score=total_score,
            metadata=metadata,
        )
    
    def _calculate_bonus_score(self, match_result: MatchResult, original_value: str) -> float:
        """Calculate bonus score based on match characteristics.
        
        Args:
            match_result: Match result to analyze.
            original_value: Original input value.
            
        Returns:
            Total bonus score.
        """
        if not match_result.matched:
            return 0.0
        
        bonus_score = 0.0
        matched_data = match_result.matched
        
        # Check for delimiters in original value
        if any(delimiter in original_value.lower() for delimiter in [" in ", " with "]):
            bonus_score += self.config.get_bonus_factor("delimiters_present")
        
        # Check for brand match
        if matched_data.get("brand"):
            bonus_score += self.config.get_bonus_factor("brand_match")
        
        # Check for fiber words
        fiber_words = ["badger", "boar", "synthetic", "horse", "mixed"]
        if any(word in original_value.lower() for word in fiber_words):
            bonus_score += self.config.get_bonus_factor("fiber_words")
        
        # Check for size specification
        if matched_data.get("knot_size_mm") or any(char.isdigit() for char in original_value):
            bonus_score += self.config.get_bonus_factor("size_specification")
        
        # Check for handle maker match
        if matched_data.get("handle_maker"):
            bonus_score += self.config.get_bonus_factor("handle_maker_match")
        
        # Check for knot maker match
        if matched_data.get("knot_maker"):
            bonus_score += self.config.get_bonus_factor("knot_maker_match")
        
        # Check for exact pattern match
        if match_result.pattern and match_result.pattern in original_value:
            bonus_score += self.config.get_bonus_factor("exact_pattern_match")
        
        return bonus_score
    
    def _calculate_penalty_score(self, match_result: MatchResult, original_value: str) -> float:
        """Calculate penalty score based on match characteristics.
        
        Args:
            match_result: Match result to analyze.
            original_value: Original input value.
            
        Returns:
            Total penalty score (negative value).
        """
        if not match_result.matched:
            return 0.0
        
        penalty_score = 0.0
        matched_data = match_result.matched
        
        # Check for single brand only (no model)
        if matched_data.get("brand") and not matched_data.get("model"):
            penalty_score += self.config.get_penalty_factor("single_brand_only")
        
        # Check for no fiber detected
        if not matched_data.get("fiber"):
            penalty_score += self.config.get_penalty_factor("no_fiber_detected")
        
        # Check for no size detected
        if not matched_data.get("knot_size_mm"):
            penalty_score += self.config.get_penalty_factor("no_size_detected")
        
        # Check for fuzzy match (pattern not exact)
        if match_result.pattern and match_result.pattern not in original_value:
            penalty_score += self.config.get_penalty_factor("fuzzy_match")
        
        # Check for generic terms
        generic_terms = ["brush", "knot", "handle"]
        if any(term in original_value.lower() for term in generic_terms):
            penalty_score += self.config.get_penalty_factor("generic_terms")
        
        # Check for incomplete specifications
        required_fields = [matched_data.get("brand"), matched_data.get("model"), matched_data.get("fiber")]
        if not all(required_fields):
            penalty_score += self.config.get_penalty_factor("incomplete_specs")
        
        return penalty_score
    
    def get_best_match(self, value: str) -> Optional[BrushScoringResult]:
        """Get the best scoring match for a brush input.
        
        Args:
            value: Brush input string to score.
            
        Returns:
            Best scoring result, or None if no matches found.
        """
        results = self.score_brush(value)
        return results[0] if results else None
    
    def get_all_matches(self, value: str) -> List[BrushScoringResult]:
        """Get all scoring matches for a brush input.
        
        Args:
            value: Brush input string to score.
            
        Returns:
            List of all scoring results sorted by score.
        """
        return self.score_brush(value)
    
    @property
    def strategy_count(self) -> int:
        """Get the number of registered strategies.
        
        Returns:
            Number of strategies.
        """
        return len(self._strategies)
    
    @property
    def strategy_names(self) -> List[str]:
        """Get the names of registered strategies.
        
        Returns:
            List of strategy names.
        """
        return self._strategy_names.copy() 