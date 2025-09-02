"""
Strategy Orchestrator Component.

This component runs all applicable brush matching strategies and collects results.
"""

from typing import List, Optional

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

    def run_all_strategies(
        self, value: str, cached_results: Optional[dict] = None
    ) -> List[MatchResult]:
        """
        Run all strategies and collect results.

        Args:
            value: The brush string to match
            cached_results: Optional cached results to pass to strategies

        Returns:
            List of MatchResult objects from all strategies
        """
        results = []

        for strategy in self.strategies:
            # Pass cached results to strategies that support them
            if cached_results is not None:
                # Check if the strategy's match method accepts cached_results parameter
                import inspect

                sig = inspect.signature(strategy.match)
                if len(sig.parameters) > 1:  # Has more than just 'self' and 'value'
                    result = strategy.match(value, cached_results)
                else:
                    result = strategy.match(value)
            else:
                result = strategy.match(value)

            if result is not None:
                # Convert dict results to MatchResult objects
                if isinstance(result, dict):
                    from sotd.match.types import create_match_result

                    result = create_match_result(
                        original=value,
                        matched=result.get("matched", {}),
                        match_type=result.get("match_type", "unknown"),
                        pattern=result.get("pattern", "unknown"),
                        strategy=strategy.__class__.__name__,  # Set the strategy name
                    )
                elif not isinstance(result, MatchResult):
                    # Skip results that are neither dict nor MatchResult
                    continue

                # Always include results, even if they don't have matches
                # This allows the analyzer to show what each strategy attempted
                results.append(result)

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
