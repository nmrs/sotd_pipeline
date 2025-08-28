"""
Enhanced Brush Scoring Matcher.

This module provides an enhanced brush matching system using scoring components.
"""

from pathlib import Path
from typing import List, Optional

import yaml

from sotd.match.brush_scoring_components.correct_matches_matcher import CorrectMatchesMatcher
from sotd.match.brush_scoring_components.performance_monitor import PerformanceMonitor
from sotd.match.brush_scoring_components.result_conflict_resolver import ResultConflictResolver
from sotd.match.brush_scoring_components.result_processor import ResultProcessor
from sotd.match.brush_scoring_components.scoring_engine import ScoringEngine
from sotd.match.brush_scoring_components.strategy_dependency_manager import (
    DependencyType,
    StrategyDependency,
    StrategyDependencyManager,
)
from sotd.match.brush_scoring_components.strategy_orchestrator import StrategyOrchestrator
from sotd.match.brush_scoring_components.strategy_performance_optimizer import (
    StrategyPerformanceOptimizer,
)
from sotd.match.brush_scoring_config import BrushScoringConfig
from sotd.match.types import MatchResult


def load_correct_matches(correct_matches_path: Path | None = None) -> dict:
    """Load correct matches data from YAML file."""
    if correct_matches_path is None:
        correct_matches_path = Path("data/correct_matches.yaml")
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
        correct_matches_data = load_correct_matches(correct_matches_path)

        # Initialize HandleMatcher and KnotMatcher first (needed for strategies)
        from sotd.match.handle_matcher import HandleMatcher
        from sotd.match.knot_matcher import KnotMatcher

        handles_path = Path("data/handles.yaml")
        self.handle_matcher = HandleMatcher(handles_path)

        # Initialize KnotMatcher with knot-specific strategies using shared strategy manager
        from sotd.match.config import BrushMatcherConfig
        from sotd.match.loaders import CatalogLoader
        from sotd.match.utils.strategy_manager import StrategyManager

        # Use shared catalog loader and strategy manager
        config = BrushMatcherConfig.create_default()
        catalog_loader = CatalogLoader(config)
        catalogs = catalog_loader.load_brush_catalogs(config)

        # Use strategy manager to create knot strategies
        strategy_manager = StrategyManager(config)
        knot_strategies = strategy_manager.create_knot_strategies(catalogs)
        self.knot_matcher = KnotMatcher(knot_strategies)

        # Initialize components
        self.correct_matches_matcher = CorrectMatchesMatcher(correct_matches_data)
        self.strategy_orchestrator = StrategyOrchestrator(self._create_strategies())
        self.scoring_engine = ScoringEngine(self.config)
        self.result_processor = ResultProcessor(self.knot_matcher)
        self.performance_monitor = PerformanceMonitor()
        self.conflict_resolver = ResultConflictResolver()
        self.performance_optimizer = StrategyPerformanceOptimizer()
        self.strategy_dependency_manager = StrategyDependencyManager()

        # Configure handle/knot dependencies for automated split strategies

        # HandleMatcher and KnotMatcher depend on BrushSplitter success
        self.strategy_dependency_manager.add_dependency(
            StrategyDependency("HandleMatcher", "BrushSplitter", DependencyType.REQUIRES_SUCCESS)
        )
        self.strategy_dependency_manager.add_dependency(
            StrategyDependency("KnotMatcher", "BrushSplitter", DependencyType.REQUIRES_SUCCESS)
        )

        # Dual Component depends on both HandleMatcher and KnotMatcher success
        self.strategy_dependency_manager.add_dependency(
            StrategyDependency(
                "LegacyDualComponentWrapperStrategy",
                "HandleMatcher",
                DependencyType.REQUIRES_SUCCESS,
            )
        )
        self.strategy_dependency_manager.add_dependency(
            StrategyDependency(
                "LegacyDualComponentWrapperStrategy", "KnotMatcher", DependencyType.REQUIRES_SUCCESS
            )
        )

        # Single Component depends on any of HandleMatcher or KnotMatcher
        self.strategy_dependency_manager.add_dependency(
            StrategyDependency(
                "LegacySingleComponentFallbackWrapperStrategy",
                "HandleMatcher",
                DependencyType.REQUIRES_ANY,
            )
        )
        self.strategy_dependency_manager.add_dependency(
            StrategyDependency(
                "LegacySingleComponentFallbackWrapperStrategy",
                "KnotMatcher",
                DependencyType.REQUIRES_ANY,
            )
        )

        # HandleMatcher and KnotMatcher are now initialized above

    def _create_strategies(self) -> List:
        """
        Create list of strategies for Phase 3.2 with individual brush strategies.

        Returns:
            List of strategy objects
        """
        # Use shared strategy manager instead of duplicating logic
        from sotd.match.config import BrushMatcherConfig
        from sotd.match.loaders import CatalogLoader
        from sotd.match.utils.strategy_manager import StrategyManager

        config = BrushMatcherConfig.create_default()
        catalog_loader = CatalogLoader(config)
        catalogs = catalog_loader.load_brush_catalogs(config)

        # Use strategy manager to create strategies
        strategy_manager = StrategyManager(config)
        strategies = strategy_manager.create_full_strategies(
            self.handle_matcher, self.knot_matcher, catalogs
        )

        return strategies

    def _create_temp_strategies(self) -> List:
        """
        Create temporary strategy list for knot matcher initialization.

        This creates strategies without the unified component strategy to avoid circular dependency.

        Returns:
            List of strategy objects (without unified component strategy)
        """
        # Use shared strategy manager instead of duplicating logic
        from sotd.match.config import BrushMatcherConfig
        from sotd.match.loaders import CatalogLoader
        from sotd.match.utils.strategy_manager import StrategyManager

        config = BrushMatcherConfig.create_default()
        catalog_loader = CatalogLoader(config)
        catalogs = catalog_loader.load_brush_catalogs(config)

        # Use strategy manager to create temporary strategies
        strategy_manager = StrategyManager(config)
        strategies = strategy_manager.create_temp_strategies(self.handle_matcher, catalogs)

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

    def _track_strategy_performance(self, strategy_results: List[MatchResult], value: str):
        """
        Track performance of individual strategies and update the optimizer.

        Args:
            strategy_results: List of MatchResult objects from strategies
            value: The brush string being matched
        """
        # Track which strategies produced results
        for result in strategy_results:
            strategy_name = result.strategy or "unknown_strategy"
            success = result.matched is not None and bool(result.matched)
            score = result.score or 0.0

            # For now, use a simple execution time estimate
            # In a real implementation, this would be measured during strategy execution
            execution_time = 0.01  # Placeholder - would be actual measured time

            # Record the strategy execution
            self.performance_optimizer.record_strategy_execution(
                strategy_name, execution_time, success, score
            )

    def _get_optimized_execution_order(self, strategy_names: List[str]) -> List[str]:
        """
        Get an optimized execution order based on strategy dependencies and performance.

        Args:
            strategy_names: List of strategy names to optimize

        Returns:
            List of strategy names in optimized order
        """
        # Use the strategy dependency manager to get the optimized order
        return self.strategy_dependency_manager.get_execution_order(strategy_names)

    def _apply_dependency_constraints(
        self, strategy_results: List[MatchResult]
    ) -> List[MatchResult]:
        """
        Apply dependency constraints to filter out strategies that cannot execute.

        Args:
            strategy_results: List of strategy results

        Returns:
            Filtered list of strategy results that can execute
        """
        # Convert results to dictionary for dependency checking
        results_dict = {result.strategy: result for result in strategy_results if result.strategy}

        # Filter out strategies that cannot execute due to dependencies
        executable_results = []
        for result in strategy_results:
            if not result.strategy:
                executable_results.append(result)
                continue

            if self.strategy_dependency_manager.can_execute_strategy(result.strategy, results_dict):
                executable_results.append(result)

        return executable_results

    def _precompute_handle_knot_results(self, value: str) -> dict:
        """
        Pre-compute HandleMatcher and KnotMatcher results for optimization.

        Args:
            value: The brush string to match

        Returns:
            Dictionary with cached handle and knot results
        """
        cached_results = {}

        # Pre-compute HandleMatcher result
        try:
            handle_result = self.handle_matcher.match_handle_maker(value)
            if handle_result:
                cached_results["handle_result"] = handle_result
        except Exception:
            # Handle matcher failed, continue without handle result
            pass

        # Pre-compute KnotMatcher result
        try:
            knot_result = self.knot_matcher.match(value)
            if knot_result:
                cached_results["knot_result"] = knot_result
        except Exception:
            # Knot matcher failed, continue without knot result
            pass

        # Pre-compute FullInputComponentMatchingStrategy result for unified strategy caching
        try:
            # Create a temporary instance of the unified strategy to avoid circular dependency
            from sotd.match.brush_matching_strategies.full_input_component_matching_strategy import (
                FullInputComponentMatchingStrategy,
            )
            from sotd.match.config import BrushMatcherConfig

            # Create catalog loader for unified strategy
            from sotd.match.loaders import CatalogLoader

            config = BrushMatcherConfig.create_default()
            catalog_loader = CatalogLoader(config)
            catalogs = catalog_loader.load_brush_catalogs(config)

            unified_strategy = FullInputComponentMatchingStrategy(
                self.handle_matcher, self.knot_matcher, catalogs
            )
            unified_result = unified_strategy.match(value)
            if unified_result:
                cached_results["unified_result"] = unified_result
        except Exception:
            # Unified strategy failed, continue without unified result
            pass

        return cached_results

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
            # Pre-compute HandleMatcher and KnotMatcher results for optimization
            cached_results = self._precompute_handle_knot_results(value)

            # For Phase 3.1 (Black Box Alignment), use wrapper strategies for all matches
            # This ensures we get the exact same results as the legacy system
            strategy_results = self.strategy_orchestrator.run_all_strategies(value, cached_results)

            # If no strategy results, return None
            if not strategy_results:
                return None

            # Track strategy performance for optimization
            self._track_strategy_performance(strategy_results, value)

            # Apply dependency constraints to filter executable strategies
            executable_results = self._apply_dependency_constraints(strategy_results)

            # Get optimized execution order based on dependencies and performance
            strategy_names = [result.strategy for result in executable_results if result.strategy]
            # Note: optimized_order is calculated but not yet used for reordering
            # This will be used in future iterations when we implement actual reordering
            self.strategy_dependency_manager.get_execution_order(strategy_names)

            # Score the results
            scored_results = self.scoring_engine.score_results(
                executable_results, value, cached_results
            )

            # Get the best result based on score
            best_result = self.scoring_engine.get_best_result(scored_results)

            # Phase 4.1: Capture all strategy results for persistence
            # Store full MatchResult objects to preserve detailed data for API
            all_strategies = []
            for result in scored_results:  # Use scored_results from ScoringEngine
                # Store the full MatchResult object to preserve all data
                all_strategies.append(result)

            # Note: We no longer create separate best_result_data since strategy and score
            # are now added directly to the matched data

            # Process and return the result with strategy data
            final_result = self.result_processor.process_result(best_result, value)

            # Add strategy persistence fields
            if final_result:
                final_result.all_strategies = all_strategies

                # Add strategy and score directly to the matched data instead of
                # separate best_result
                if final_result.matched and best_result:
                    final_result.matched["strategy"] = best_result.strategy
                    final_result.matched["score"] = best_result.score

            return final_result

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

    def get_performance_stats(self) -> dict:
        """
        Get comprehensive performance statistics including strategy optimization data.

        Returns:
            Dictionary containing performance statistics and optimization data
        """
        # Get basic performance stats
        basic_stats = self.get_cache_stats()

        # Get strategy performance data
        strategy_performance = self.performance_optimizer.get_performance_report()

        return {
            **basic_stats,
            "strategy_performance": strategy_performance,
            "optimization_recommendations": strategy_performance.get(
                "optimization_recommendations", {}
            ),
            "slow_strategies": strategy_performance.get("slow_strategies", []),
        }

    def get_dependency_info(self) -> dict:
        """
        Get dependency information and status.

        Returns:
            Dictionary containing dependency information and status
        """
        return {
            "dependency_manager": self.strategy_dependency_manager,
            "dependencies": self.strategy_dependency_manager.dependencies,
            "dependency_graph": self.strategy_dependency_manager.dependency_graph,
            "topological_graph": self.strategy_dependency_manager.topological_graph,
        }
