"""
Enhanced Brush Scoring Matcher Implementation.

This module provides the full implementation of the brush scoring matcher
that uses all brush scoring components for improved architecture and performance.
"""

import yaml
from pathlib import Path
from typing import Optional, List

from sotd.match.brush_scoring_config import BrushScoringConfig
from sotd.match.brush_scoring_components import (
    CorrectMatchesMatcher,
    StrategyOrchestrator,
    ScoringEngine,
    ResultProcessor,
    PerformanceMonitor,
)
from sotd.match.types import MatchResult


def load_correct_matches() -> dict:
    """
    Load correct matches data from YAML file.

    Returns:
        Dictionary containing correct matches data
    """
    correct_matches_path = Path("data/correct_matches.yaml")
    if not correct_matches_path.exists():
        return {"brush": {}, "split_brush": {}}

    with open(correct_matches_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


class BrushScoringMatcher:
    """
    Enhanced brush scoring matcher using all components.

    This implementation uses the brush scoring components for improved
    architecture, performance monitoring, and scoring capabilities.
    """

    def __init__(self, config_path: Path | None = None, **kwargs):
        """
        Initialize the enhanced brush scoring matcher.

        Args:
            config_path: Path to configuration file
            **kwargs: Additional arguments (ignored for now)
        """
        # Initialize configuration
        self.config = BrushScoringConfig(config_path=config_path)

        # Load correct matches data
        correct_matches_data = load_correct_matches()

        # Initialize components
        self.correct_matches_matcher = CorrectMatchesMatcher(correct_matches_data)
        self.strategy_orchestrator = StrategyOrchestrator(self._create_strategies())
        self.scoring_engine = ScoringEngine(self.config)
        self.result_processor = ResultProcessor()
        self.performance_monitor = PerformanceMonitor()

    def _create_strategies(self) -> List:
        """
        Create list of brush matching strategies.

        Returns:
            List of strategy objects
        """
        # For Phase 1, we'll use a simplified approach
        # In future phases, this will create actual strategy instances
        return []

    def match(self, value: str) -> Optional[MatchResult]:
        """
        Match a brush string using the enhanced scoring system.

        Args:
            value: The brush string to match

        Returns:
            MatchResult if found, None otherwise
        """
        if not value:
            return None

        # Start performance monitoring
        self.performance_monitor.start_timing()

        try:
            # First, try correct matches matcher (fastest path)
            result = self.correct_matches_matcher.match(value)
            if result is not None:
                return self.result_processor.process_result(result, value)

            # If no correct match, try strategies
            strategy_results = self.strategy_orchestrator.run_all_strategies(value)

            if not strategy_results:
                return None

            # Score the results
            scored_results = self.scoring_engine.score_results(strategy_results, value)

            # Get the best result
            best_result = self.scoring_engine.get_best_result(scored_results)

            # Process and return the result
            return self.result_processor.process_result(best_result, value)

        except Exception as e:
            # Log error but don't fail completely
            print(f"Error during brush matching: {e}")
            return None
        finally:
            # End performance monitoring
            self.performance_monitor.end_timing()

    def get_cache_stats(self) -> dict:
        """
        Get cache and performance statistics.

        Returns:
            Dictionary containing cache and performance statistics
        """
        return {
            "performance": self.performance_monitor.get_performance_stats(),
            "total_time": self.performance_monitor.get_total_time(),
        }
