"""
Strategy Orchestrator Component.

This component runs all applicable brush matching strategies and collects results.
"""

from typing import List

from sotd.match.types import MatchResult


class StrategyOrchestrator:
    """
    Orchestrator for running all brush matching strategies.
    
    This component runs all available strategies and collects their results
    for scoring and selection.
    """

    def __init__(self, strategies: List):
        """
        Initialize the strategy orchestrator.
        
        Args:
            strategies: List of brush matching strategies to run
        """
        self.strategies = strategies

    def run_all_strategies(self, value: str) -> List[MatchResult]:
        """
        Run all strategies and collect results.
        
        Args:
            value: The brush string to match
            
        Returns:
            List of MatchResult objects from all strategies
        """
        results = []
        
        for strategy in self.strategies:
            try:
                result = strategy.match(value)
                if result is not None:
                    results.append(result)
            except Exception as e:
                # Log error but continue with other strategies
                # This allows individual strategy failures without breaking the system
                print(f"Strategy {strategy.__class__.__name__} failed: {e}")
                continue
        
        return results

    def get_strategy_count(self) -> int:
        """
        Get the number of strategies available.
        
        Returns:
            Number of strategies
        """
        return len(self.strategies)

    def get_strategy_names(self) -> List[str]:
        """
        Get names of all strategies.
        
        Returns:
            List of strategy class names
        """
        return [strategy.__class__.__name__ for strategy in self.strategies] 