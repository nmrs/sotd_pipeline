"""
Enhanced Brush Scoring Matcher Implementation.

This module provides the full implementation of the brush scoring matcher
that uses all brush scoring components for improved architecture and performance.
"""

from pathlib import Path
from typing import List, Optional

import yaml

from sotd.match.brush_scoring_components import (
    CorrectMatchesMatcher,
    PerformanceMonitor,
    ResultProcessor,
    ScoringEngine,
    StrategyOrchestrator,
)
from sotd.match.brush_scoring_config import BrushScoringConfig
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

    def __init__(
        self, config_path: Path | None = None, correct_matches_path: Path | None = None, **kwargs
    ):
        """
        Initialize the enhanced brush scoring matcher.

        Args:
            config_path: Path to configuration file
            correct_matches_path: Path to correct_matches.yaml file
            **kwargs: Additional arguments (ignored for now)
        """
        # Initialize configuration
        self.config = BrushScoringConfig(config_path=config_path)

        # Store correct_matches_path for wrapper strategies
        self.correct_matches_path = correct_matches_path

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
            s
            for s in self._create_strategies()
            if any(keyword in s.__class__.__name__ for keyword in ["Knot", "Fiber", "Size"])
        ]
        self.knot_matcher = KnotMatcher(knot_strategies)

    def _create_strategies(self) -> List:
        """
        Create list of strategies for Phase 3.2 with individual brush strategies.

        Returns:
            List of strategy objects
        """
        # Create legacy matcher instance for wrapper strategies
        from sotd.match.brush_matcher import BrushMatcher
        from sotd.match.config import BrushMatcherConfig

        config = BrushMatcherConfig.create_default()
        legacy_matcher = BrushMatcher(config=config, correct_matches_path=self.correct_matches_path)

        # Import wrapper strategies
        from sotd.match.brush_matching_strategies.automated_split_wrapper_strategies import (
            HighPriorityAutomatedSplitWrapperStrategy,
            MediumPriorityAutomatedSplitWrapperStrategy,
        )
        from sotd.match.brush_matching_strategies.component_coordination_strategy import (
            ComponentCoordinationStrategy,
        )
        from sotd.match.brush_matching_strategies.correct_matches_wrapper_strategies import (
            CorrectCompleteBrushWrapperStrategy,
            CorrectSplitBrushWrapperStrategy,
        )

        # Import component strategies for Phase 3.3
        from sotd.match.brush_matching_strategies.handle_component_strategy import (
            HandleComponentStrategy,
        )
        from sotd.match.brush_matching_strategies.knot_component_strategy import (
            KnotComponentStrategy,
        )

        # Import individual brush strategies for Phase 3.2
        from sotd.match.brush_matching_strategies.known_brush_strategy import (
            KnownBrushMatchingStrategy,
        )
        from sotd.match.brush_matching_strategies.known_split_wrapper_strategy import (
            KnownSplitWrapperStrategy,
        )
        from sotd.match.brush_matching_strategies.legacy_composite_wrapper_strategies import (
            LegacySingleComponentFallbackWrapperStrategy,
        )
        from sotd.match.brush_matching_strategies.omega_semogue_strategy import (
            OmegaSemogueBrushMatchingStrategy,
        )
        from sotd.match.brush_matching_strategies.other_brushes_strategy import (
            OtherBrushMatchingStrategy,
        )
        from sotd.match.brush_matching_strategies.zenith_strategy import (
            ZenithBrushMatchingStrategy,
        )

        # Get catalog data for individual strategies
        catalog_data = legacy_matcher.catalog_data

        # Create strategies in legacy system priority order
        strategies = [
            # Priority 0: correct_complete_brush
            CorrectCompleteBrushWrapperStrategy(legacy_matcher),
            # Priority 1: correct_split_brush
            CorrectSplitBrushWrapperStrategy(legacy_matcher),
            # Priority 2: known_split
            KnownSplitWrapperStrategy(legacy_matcher),
            # Priority 3: high_priority_automated_split
            HighPriorityAutomatedSplitWrapperStrategy(legacy_matcher),
            # Priority 4: individual brush strategies (replacing complete_brush wrapper)
            KnownBrushMatchingStrategy(catalog_data.get("known_brushes", {})),
            OmegaSemogueBrushMatchingStrategy(),
            ZenithBrushMatchingStrategy(),
            OtherBrushMatchingStrategy(catalog_data.get("other_brushes", {})),
            # Priority 5: individual component strategies (replacing dual_component wrapper)
            HandleComponentStrategy(legacy_matcher.handle_matcher),
            KnotComponentStrategy(legacy_matcher.knot_matcher),
            ComponentCoordinationStrategy(
                legacy_matcher.handle_matcher, legacy_matcher.knot_matcher
            ),
            # Priority 6: medium_priority_automated_split
            MediumPriorityAutomatedSplitWrapperStrategy(legacy_matcher),
            # Priority 7: single_component_fallback
            LegacySingleComponentFallbackWrapperStrategy(legacy_matcher),
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
            # For Phase 3.1 (Black Box Alignment), use wrapper strategies for all matches
            # This ensures we get the exact same results as the legacy system
            strategy_results = self.strategy_orchestrator.run_all_strategies(value)

            # If no strategy results, return None
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
