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

        # Initialize HandleMatcher for composite brush matching
        from sotd.match.handle_matcher import HandleMatcher

        handles_path = Path("data/handles.yaml")
        self.handle_matcher = HandleMatcher(handles_path)

    def _create_strategies(self) -> List:
        """
        Create list of brush matching strategies.

        Returns:
            List of strategy objects
        """
        # Import existing strategy classes to reuse them
        from sotd.match.brush_matching_strategies.known_brush_strategy import (
            KnownBrushMatchingStrategy,
        )
        from sotd.match.brush_matching_strategies.omega_semogue_strategy import (
            OmegaSemogueBrushMatchingStrategy,
        )
        from sotd.match.brush_matching_strategies.zenith_strategy import ZenithBrushMatchingStrategy
        from sotd.match.brush_matching_strategies.other_brushes_strategy import (
            OtherBrushMatchingStrategy,
        )
        from sotd.match.brush_matching_strategies.known_knot_strategy import (
            KnownKnotMatchingStrategy,
        )
        from sotd.match.brush_matching_strategies.other_knot_strategy import (
            OtherKnotMatchingStrategy,
        )
        from sotd.match.brush_matching_strategies.fiber_fallback_strategy import (
            FiberFallbackStrategy,
        )
        from sotd.match.brush_matching_strategies.knot_size_fallback_strategy import (
            KnotSizeFallbackStrategy,
        )

        # Load catalog data for strategies that need it
        from sotd.match.loaders import CatalogLoader
        from sotd.match.config import BrushMatcherConfig

        # Create config and load catalogs
        config = BrushMatcherConfig.create_default()
        catalog_loader = CatalogLoader(config)
        catalogs = catalog_loader.load_all_catalogs()

        brush_catalog = catalogs["brushes"]
        knots_catalog = catalogs["knots"]

        # Create strategies in same order as legacy system
        strategies = [
            # Brush strategies (same as legacy)
            KnownBrushMatchingStrategy(brush_catalog.get("known_brushes", {})),
            OmegaSemogueBrushMatchingStrategy(),
            ZenithBrushMatchingStrategy(),
            OtherBrushMatchingStrategy(brush_catalog.get("other_brushes", {})),
            # Knot strategies (same as legacy)
            KnownKnotMatchingStrategy(knots_catalog.get("known_knots", {})),
            OtherKnotMatchingStrategy(knots_catalog.get("other_knots", {})),
            FiberFallbackStrategy(),
            KnotSizeFallbackStrategy(),
        ]

        return strategies

    def _convert_handle_result_to_brush_result(self, handle_result: MatchResult) -> MatchResult:
        """
        Convert HandleMatcher result to brush format for processing.

        Args:
            handle_result: MatchResult from HandleMatcher

        Returns:
            MatchResult in brush format
        """
        # Extract handle data from HandleMatcher result
        handle_data = handle_result.matched or {}

        # Create brush format result
        brush_data = {
            "brand": handle_data.get("handle_maker"),
            "model": handle_data.get("handle_model"),
            "source_text": handle_data.get("_source_text", handle_result.original),
            "_matched_by": "HandleMatcher",
            "_pattern": handle_data.get("_pattern_used"),
        }

        # Create nested handle/knot structure to match legacy format
        brush_data["handle"] = {
            "brand": handle_data.get("handle_maker"),
            "model": handle_data.get("handle_model"),
            "source_text": handle_data.get("_source_text", handle_result.original),
            "_matched_by": "HandleMatcher",
            "_pattern": handle_data.get("_pattern_used"),
        }

        # Create empty knot section for composite brush
        brush_data["knot"] = {
            "brand": None,
            "model": None,
            "fiber": None,
            "knot_size_mm": None,
            "source_text": handle_data.get("_source_text", handle_result.original),
            "_matched_by": "HandleMatcher",
            "_pattern": handle_data.get("_pattern_used"),
        }

        return MatchResult(
            original=handle_result.original,
            matched=brush_data,
            match_type="handle",
            pattern=handle_data.get("_pattern_used"),
        )

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

            # If no strategy results, try HandleMatcher for composite brushes
            if not strategy_results:
                handle_result = self.handle_matcher.match(value)
                if handle_result is not None:
                    # Convert HandleMatcher result to brush format
                    brush_result = self._convert_handle_result_to_brush_result(handle_result)
                    return self.result_processor.process_result(brush_result, value)
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
