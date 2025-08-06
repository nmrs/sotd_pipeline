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

        # Initialize KnotMatcher for composite brush matching
        from sotd.match.knot_matcher import KnotMatcher

        # Get knot strategies from the strategy list
        knot_strategies = [
            s for s in self._create_strategies()
            if any(keyword in s.__class__.__name__ for keyword in ["Knot", "Fiber", "Size"])
        ]
        self.knot_matcher = KnotMatcher(knot_strategies)

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

    def _combine_handle_and_knot_results(
        self, handle_result: MatchResult, knot_result: MatchResult
    ) -> MatchResult:
        """
        Combine HandleMatcher and KnotMatcher results into a single brush result.
        
        Args:
            handle_result: MatchResult from HandleMatcher
            knot_result: MatchResult from KnotMatcher
            
        Returns:
            MatchResult with combined handle and knot data
        """
        handle_data = handle_result.matched or {}
        knot_data = knot_result.matched or {}
        
        # Create combined brush data
        brush_data = {
            "brand": handle_data.get("handle_maker"),
            "model": handle_data.get("handle_model"),
            "source_text": handle_data.get("_source_text", handle_result.original),
            "_matched_by": "HandleMatcher+KnotMatcher",
            "_pattern": handle_data.get("_pattern_used"),
        }
        
        # Create handle section
        brush_data["handle"] = {
            "brand": handle_data.get("handle_maker"),
            "model": handle_data.get("handle_model"),
            "source_text": handle_data.get("_source_text", handle_result.original),
            "_matched_by": "HandleMatcher",
            "_pattern": handle_data.get("_pattern_used"),
        }
        
        # Create knot section with knot data
        brush_data["knot"] = {
            "brand": knot_data.get("brand"),
            "model": knot_data.get("model"),
            "fiber": knot_data.get("fiber"),
            "knot_size_mm": knot_data.get("knot_size_mm"),
            "source_text": knot_data.get("source_text", handle_result.original),
            "_matched_by": "KnotMatcher",
            "_pattern": knot_data.get("_pattern_used"),
        }
        
        return MatchResult(
            original=handle_result.original,
            matched=brush_data,
            match_type="composite",
            pattern=handle_data.get("_pattern_used"),
        )

    def _convert_knot_result_to_brush_result(self, knot_result: MatchResult) -> MatchResult:
        """
        Convert KnotMatcher result to brush format for processing.
        
        Args:
            knot_result: MatchResult from KnotMatcher
            
        Returns:
            MatchResult in brush format
        """
        knot_data = knot_result.matched or {}
        
        # Create brush format result
        brush_data = {
            "brand": knot_data.get("brand"),
            "model": knot_data.get("model"),
            "fiber": knot_data.get("fiber"),
            "knot_size_mm": knot_data.get("knot_size_mm"),
            "source_text": knot_data.get("source_text", knot_result.original),
            "_matched_by": "KnotMatcher",
            "_pattern": knot_data.get("_pattern_used"),
        }
        
        # Create empty handle section for knot-only brush
        brush_data["handle"] = {
            "brand": None,
            "model": None,
            "source_text": knot_data.get("source_text", knot_result.original),
            "_matched_by": "KnotMatcher",
            "_pattern": knot_data.get("_pattern_used"),
        }
        
        # Create knot section
        brush_data["knot"] = {
            "brand": knot_data.get("brand"),
            "model": knot_data.get("model"),
            "fiber": knot_data.get("fiber"),
            "knot_size_mm": knot_data.get("knot_size_mm"),
            "source_text": knot_data.get("source_text", knot_result.original),
            "_matched_by": "KnotMatcher",
            "_pattern": knot_data.get("_pattern_used"),
        }
        
        return MatchResult(
            original=knot_result.original,
            matched=brush_data,
            match_type="knot",
            pattern=knot_data.get("_pattern_used"),
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

            # If no strategy results, try HandleMatcher and KnotMatcher for composite brushes
            if not strategy_results:
                # Try HandleMatcher first
                handle_result = self.handle_matcher.match(value)
                if handle_result is not None:
                    # Try KnotMatcher to enhance the result
                    knot_result = self.knot_matcher.match(value)
                    if knot_result is not None:
                        # Combine handle and knot results
                        brush_result = self._combine_handle_and_knot_results(handle_result, knot_result)
                    else:
                        # Use only handle result
                        brush_result = self._convert_handle_result_to_brush_result(handle_result)
                    return self.result_processor.process_result(brush_result, value)
                
                # If HandleMatcher fails, try KnotMatcher alone
                knot_result = self.knot_matcher.match(value)
                if knot_result is not None:
                    brush_result = self._convert_knot_result_to_brush_result(knot_result)
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
