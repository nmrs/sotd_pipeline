"""
Scoring brush matcher for multi-strategy brush matching system.

This module provides the main scoring brush matcher that integrates with the
existing pipeline, using the scoring system to select the best match from
multiple strategies.
"""

from pathlib import Path
from typing import Dict, Optional

from sotd.match.brush_scoring_config import BrushScoringConfig
from sotd.match.brush_scoring_engine import BrushScoringEngine, BrushScoringResult
from sotd.match.brush_matcher import BrushMatcher
from sotd.match.cache import MatchCache
from sotd.match.config import BrushMatcherConfig
from sotd.match.correct_matches import CorrectMatchesChecker
from sotd.match.loaders import CatalogLoader
from sotd.match.types import MatchResult


class ScoringBrushMatcher:
    """
    Main scoring brush matcher that integrates with existing pipeline.

    This matcher extends the current BrushMatcher functionality by using
    a scoring system to select the best match from multiple strategies,
    while maintaining compatibility with the existing interface.
    """

    def __init__(
        self,
        config: Optional[BrushMatcherConfig] = None,
        catalog_path: Optional[Path] = None,
        handles_path: Optional[Path] = None,
        knots_path: Optional[Path] = None,
        correct_matches_path: Optional[Path] = None,
        scoring_config_path: Optional[Path] = None,
        debug: Optional[bool] = None,
    ):
        """Initialize scoring brush matcher.

        Args:
            config: Brush matcher configuration.
            catalog_path: Path to brush catalog file.
            handles_path: Path to handles catalog file.
            knots_path: Path to knots catalog file.
            correct_matches_path: Path to correct matches file.
            scoring_config_path: Path to scoring configuration file.
            debug: Enable debug mode.
        """
        # Handle backward compatibility: if config is None, create from individual parameters
        if config is None:
            config = BrushMatcherConfig.create_custom(
                catalog_path=catalog_path,
                handles_path=handles_path,
                knots_path=knots_path,
                correct_matches_path=correct_matches_path,
                debug=debug if debug is not None else False,
            )

        self.config = config
        self.catalog_path = config.catalog_path
        self.handles_path = config.handles_path
        self.knots_path = config.knots_path
        self.correct_matches_path = config.correct_matches_path
        self.debug = config.debug

        # Load scoring configuration
        self.scoring_config = BrushScoringConfig(scoring_config_path)
        validation_result = self.scoring_config.load_config()
        if not validation_result.is_valid:
            raise ValueError(f"Invalid scoring configuration: {validation_result.errors}")

        # Use CatalogLoader to load all catalog data
        self.catalog_loader = CatalogLoader(config)
        catalogs = self.catalog_loader.load_all_catalogs()
        self.catalog_data = catalogs["brushes"]
        self.knots_data = catalogs["knots"]
        self.correct_matches = catalogs["correct_matches"]

        # Initialize specialized components
        self.correct_matches_checker = CorrectMatchesChecker(config, self.correct_matches)

        # Initialize scoring engine
        self.scoring_engine = BrushScoringEngine(self.scoring_config)

        # Initialize the regular brush matcher for strategy execution
        self.brush_matcher = BrushMatcher(config)

        # Initialize cache
        self.cache = MatchCache()

    def match(self, value: str) -> Optional[MatchResult]:
        """Match a brush input using the scoring system.

        Args:
            value: Brush input string to match.

        Returns:
            Best scoring match result, or None if no match found.
        """
        # Check cache first
        cache_key = f"scoring_{value}"
        cached_result = self.cache.get(cache_key)
        if cached_result is not None:
            return cached_result

        # Check for exact matches from correct_matches.yaml first
        if self.scoring_config.get_brush_routing_rule("exact_match_bypass"):
            exact_match = self.correct_matches_checker.check(value)
            if exact_match:
                # Convert to MatchResult format and cache
                match_result = MatchResult(
                    original=value,
                    matched=exact_match.__dict__,
                    match_type="exact",
                    pattern="correct_matches.yaml"
                )
                self.cache.set(cache_key, match_result)
                return match_result

        # Use the regular brush matcher to get all strategy results
        # This ensures we use the same strategy execution logic as the current system
        all_results = self._get_all_strategy_results(value)

        if not all_results:
            # No matches found
            self.cache.set(cache_key, None)
            return None

        # Score all results using the scoring engine
        scoring_results = []
        for strategy_name, match_result in all_results:
            if match_result is not None:
                scoring_result = self.scoring_engine._calculate_score(
                    match_result, strategy_name, value
                )
                scoring_results.append(scoring_result)

        if not scoring_results:
            # No valid scoring results
            self.cache.set(cache_key, None)
            return None

        # Sort by total score (highest first)
        scoring_results.sort()

        # Get the best scoring result
        best_result = scoring_results[0]

        # Convert to MatchResult format
        match_result = self._convert_to_match_result(best_result, value, scoring_results)

        # Cache the result
        self.cache.set(cache_key, match_result)

        return match_result

    def _get_all_strategy_results(self, value: str) -> list[tuple[str, Optional[MatchResult]]]:
        """Get results from all brush matcher strategies.

        Args:
            value: Brush input string to match.

        Returns:
            List of (strategy_name, match_result) tuples.
        """
        # Define strategies in the same order as the brush matcher
        strategies = [
            ("correct_complete_brush", self.brush_matcher._match_correct_complete_brush),
            ("correct_split_brush", self.brush_matcher._match_correct_split_brush),
            ("known_split", self.brush_matcher._match_known_split),
            ("high_priority_automated_split", 
             self.brush_matcher._match_high_priority_automated_split),
            ("complete_brush", self.brush_matcher._match_complete_brush),
            ("dual_component", self.brush_matcher._match_dual_component),
            ("medium_priority_automated_split", 
             self.brush_matcher._match_medium_priority_automated_split),
            ("single_component_fallback", 
             self.brush_matcher._match_single_component_fallback),
        ]

        results = []
        for strategy_name, strategy_func in strategies:
            try:
                match_result = strategy_func(value)
                results.append((strategy_name, match_result))
            except Exception as e:
                # Log strategy failure but continue with other strategies
                if self.debug:
                    print(f"Strategy {strategy_name} failed: {str(e)}")
                results.append((strategy_name, None))

        return results

    def _convert_to_match_result(
        self, scoring_result: BrushScoringResult, original_value: str, all_scoring_results: list[BrushScoringResult]
    ) -> MatchResult:
        """Convert scoring result to MatchResult format.

        Args:
            scoring_result: Scoring result from engine.
            original_value: Original input value.
            all_scoring_results: All scoring results for metadata.

        Returns:
            MatchResult in standard format.
        """
        # Start with the original match result
        match_result = scoring_result.match_result

        # Add scoring metadata
        if match_result.matched:
            match_result.matched["_scoring_metadata"] = {
                "strategy_name": scoring_result.strategy_name,
                "base_score": scoring_result.base_score,
                "modifier_score": scoring_result.modifier_score,
                "total_score": scoring_result.total_score,
                "all_scores": [
                    {
                        "strategy": result.strategy_name,
                        "score": result.total_score,
                        "base": result.base_score,
                        "modifier": result.modifier_score,
                    }
                    for result in all_scoring_results
                ],
            }

        return match_result

    def get_all_matches(self, value: str) -> list[BrushScoringResult]:
        """Get all scoring matches for a brush input.

        Args:
            value: Brush input string to match.

        Returns:
            List of all scoring results sorted by score.
        """
        # Get all strategy results
        all_results = self._get_all_strategy_results(value)

        # Score all results
        scoring_results = []
        for strategy_name, match_result in all_results:
            if match_result is not None:
                scoring_result = self.scoring_engine._calculate_score(
                    match_result, strategy_name, value
                )
                scoring_results.append(scoring_result)

        # Sort by total score (highest first)
        scoring_results.sort()
        return scoring_results

    def get_best_match(self, value: str) -> Optional[BrushScoringResult]:
        """Get the best scoring match for a brush input.

        Args:
            value: Brush input string to match.

        Returns:
            Best scoring result, or None if no match found.
        """
        all_matches = self.get_all_matches(value)
        return all_matches[0] if all_matches else None

    def get_cache_stats(self) -> Dict[str, int]:
        """Get cache statistics.

        Returns:
            Dictionary with cache statistics.
        """
        return self.cache.stats()

    def clear_cache(self) -> None:
        """Clear the match cache."""
        self.cache.clear()

    @property
    def strategy_count(self) -> int:
        """Get the number of registered strategies.

        Returns:
            Number of strategies.
        """
        return 8  # Fixed number of strategies in brush matcher

    @property
    def strategy_names(self) -> list[str]:
        """Get the names of registered strategies.

        Returns:
            List of strategy names.
        """
        return [
            "correct_complete_brush",
            "correct_split_brush",
            "known_split",
            "high_priority_automated_split",
            "complete_brush",
            "dual_component",
            "medium_priority_automated_split",
            "single_component_fallback",
        ]

    def reload_scoring_config(self) -> None:
        """Reload the scoring configuration from file."""
        validation_result = self.scoring_config.reload_config()
        if not validation_result.is_valid:
            raise ValueError(f"Invalid scoring configuration: {validation_result.errors}")

        # Clear cache when configuration changes
        self.clear_cache()
