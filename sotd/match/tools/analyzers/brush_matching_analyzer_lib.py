#!/usr/bin/env python3
"""Shared library for brush matching analysis.

This module provides the core analysis logic that can be used by both the CLI tool
and the web UI API to ensure consistent results and avoid code duplication.
"""

import sys
from pathlib import Path
from typing import Any, Dict

# Add the project root to the path for imports
project_root = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(project_root))

# Import SOTD modules after path setup
from sotd.enrich.brush_enricher import BrushEnricher  # noqa: E402
from sotd.match.brush.config import BrushScoringConfig  # noqa: E402
from sotd.match.brush_matcher import BrushMatcher  # noqa: E402


class BrushMatchingAnalyzer:
    """Core analyzer for brush matching that can be used by CLI and web UI."""

    def __init__(self, debug: bool = False):
        """Initialize the analyzer.

        Args:
            debug: Enable debug mode for additional output
        """
        self.debug = debug
        self.scoring_matcher = None
        self.brush_enricher = None

    def analyze_brush_string(
        self, brush_string: str, show_all_matches: bool = True, bypass_correct_matches: bool = False
    ) -> Dict[str, Any]:
        """Analyze a brush string and return structured results.

        Args:
            brush_string: The brush string to analyze
            show_all_matches: Whether to show all strategy results
            bypass_correct_matches: Whether to bypass correct_matches.yaml

        Returns:
            Dictionary containing analysis results
        """
        results = {
            "brush_string": brush_string,
            "all_strategies": [],
            "winner": None,
            "enriched_data": {},
            "analysis_summary": {},
        }

        try:
            # Initialize components if needed
            if not self.scoring_matcher:
                self.scoring_matcher = BrushMatcher()

            if not self.brush_enricher:
                self.brush_enricher = BrushEnricher()

            # Get scoring results
            if show_all_matches:
                scoring_result = self._get_scoring_results(brush_string, bypass_correct_matches)
                results["all_strategies"] = scoring_result.get("strategies", [])
                results["winner"] = scoring_result.get("winner")
                results["analysis_summary"]["scoring"] = scoring_result.get("summary", {})

            # Get basic matching results
            basic_result = self._get_basic_matching_results(brush_string)
            results["analysis_summary"]["basic_matching"] = basic_result

            # Get enrichment results
            enriched_data = self._get_enrichment_results(brush_string)
            results["enriched_data"] = enriched_data

        except Exception as e:
            results["error"] = str(e)
            if self.debug:
                import traceback

                results["traceback"] = traceback.format_exc()

        return results

    def _get_scoring_results(
        self, brush_string: str, bypass_correct_matches: bool = False
    ) -> Dict[str, Any]:
        """Get detailed scoring results from all strategies."""
        results = {"strategies": [], "winner": None, "summary": {}}

        try:
            # Handle bypassing correct_matches if requested
            original_methods = {}
            if bypass_correct_matches:
                original_methods = self._patch_correct_matches_bypass()

            # Get the scoring result
            if self.debug:
                print(f"DEBUG: Calling scoring_matcher.match('{brush_string}')")

            scoring_result = self.scoring_matcher.match(brush_string)

            if self.debug:
                print(f"DEBUG: scoring_result: {scoring_result}")
                if scoring_result:
                    print(f"DEBUG: has all_strategies: {hasattr(scoring_result, 'all_strategies')}")
                    if hasattr(scoring_result, "all_strategies"):
                        print(f"DEBUG: all_strategies count: {len(scoring_result.all_strategies)}")

            # Restore original methods if we bypassed them
            if bypass_correct_matches:
                self._restore_correct_matches_methods(original_methods)

            if scoring_result and hasattr(scoring_result, "all_strategies"):
                # Process all strategy results
                strategies = []
                for strategy_result in scoring_result.all_strategies:
                    if self.debug:
                        print(f"DEBUG: Processing strategy: {strategy_result}")
                    strategy_data = self._process_strategy_result(strategy_result, brush_string)
                    strategies.append(strategy_data)

                # Sort by score (highest first)
                strategies.sort(key=lambda x: x.get("score", 0), reverse=True)
                results["strategies"] = strategies

                if self.debug:
                    print("DEBUG: Final strategies with scores:")
                    for s in strategies:
                        print(f"  {s.get('strategy', 'unknown')}: {s.get('score', 0)}")

                # Set winner
                if strategies:
                    results["winner"] = strategies[0]

                # Add summary
                results["summary"] = {
                    "total_strategies": len(strategies),
                    "highest_score": strategies[0]["score"] if strategies else 0,
                    "lowest_score": strategies[-1]["score"] if strategies else 0,
                }

        except Exception as e:
            results["error"] = str(e)
            if self.debug:
                import traceback

                results["traceback"] = traceback.format_exc()

        return results

    def _get_basic_matching_results(self, brush_string: str) -> Dict[str, Any]:
        """Get basic matching results from the brush matcher."""
        try:
            result = self.scoring_matcher.match(brush_string)
            if result:
                return {
                    "matched": result.matched if hasattr(result, "matched") else None,
                    "match_type": getattr(result, "match_type", None),
                    "pattern": getattr(result, "pattern", None),
                    "strategy": getattr(result, "strategy", None),
                }
            return {"matched": None, "match_type": None, "pattern": None, "strategy": None}
        except Exception as e:
            return {"error": str(e)}

    def _get_enrichment_results(self, brush_string: str) -> Dict[str, Any]:
        """Get enrichment results for the brush string."""
        try:
            # For now, just extract fiber information
            # In the future, this could call the actual enrichment phase
            from sotd.match.brush.strategies.utils.fiber_utils import match_fiber

            fiber = match_fiber(brush_string)
            return {
                "fiber": fiber,
                "_fiber_extraction_source": "user_comment" if fiber else None,
                "_enriched_by": "BrushMatchingAnalyzer",
            }
        except Exception as e:
            return {"error": str(e)}

    def _process_strategy_result(
        self, strategy_result: Dict[str, Any], brush_string: str
    ) -> Dict[str, Any]:
        """Process a single strategy result into a standardized format."""
        strategy_name = strategy_result.get("strategy", "Unknown")
        score = strategy_result.get("score", 0)
        match_type = strategy_result.get("match_type", "Unknown")
        pattern = strategy_result.get("pattern", "Unknown")
        matched_data = strategy_result.get("result", {})

        # Get base score for this strategy
        base_score = self._get_base_score_for_strategy(strategy_name)
        modifier_score = score - base_score

        # Process matched data
        processed_matched_data = self._process_matched_data(matched_data)

        return {
            "strategy": strategy_name or "unknown",
            "score": score,
            "match_type": match_type or "unknown",
            "pattern": pattern or "unknown",
            "base_score": base_score,
            "modifier_score": modifier_score,
            "matched_data": processed_matched_data,
            "score_breakdown": {
                "base_score": base_score,
                "modifiers": modifier_score,
                "total": score,
            },
        }

    def _process_matched_data(self, matched_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process matched data into a clean, consistent format."""
        if not matched_data:
            return {}

        processed = {}

        # Basic fields
        for field in ["brand", "model", "fiber", "knot_size_mm", "handle_maker"]:
            if field in matched_data and matched_data[field]:
                processed[field] = matched_data[field]

        # Handle nested handle/knot structure
        if "handle" in matched_data and matched_data["handle"]:
            handle = matched_data["handle"]
            processed.update(
                {
                    "handle_brand": handle.get("brand"),
                    "handle_model": handle.get("model"),
                    "handle_source": handle.get("source_text"),
                }
            )

        if "knot" in matched_data and matched_data["knot"]:
            knot = matched_data["knot"]
            processed.update(
                {
                    "knot_brand": knot.get("brand"),
                    "knot_model": knot.get("model"),
                    "knot_fiber": knot.get("fiber"),
                    "knot_size_mm": knot.get("knot_size_mm"),
                    "knot_source": knot.get("source_text"),
                }
            )

        return processed

    def _get_base_score_for_strategy(self, strategy_name: str) -> float:
        """Get the base score for a given strategy."""
        # Fail fast - configuration must be available
        # Use absolute path to project root's config file
        project_root = Path(__file__).parent.parent.parent.parent.parent
        config_path = project_root / "data" / "brush_scoring_config.yaml"

        if self.debug:
            print(f"DEBUG: Loading scoring config from: {config_path}")
            print(f"DEBUG: Config file exists: {config_path.exists()}")

        config = BrushScoringConfig(config_path=config_path)
        base_score = config.get_base_strategy_score(strategy_name)

        if self.debug:
            print(f"DEBUG: Strategy '{strategy_name}' base score: {base_score}")

        return base_score

    def _patch_correct_matches_bypass(self) -> Dict[str, Any]:
        """Temporarily patch methods to bypass correct_matches.yaml."""
        original_methods = {}

        try:
            # Store the original match method from correct_matches_matcher
            if hasattr(self.scoring_matcher, "correct_matches_matcher"):
                original_methods["correct_matches_matcher.match"] = (
                    self.scoring_matcher.correct_matches_matcher.match
                )

                # Create a dummy method that always returns None
                def dummy_match(value):
                    return None

                # Replace the match method temporarily
                self.scoring_matcher.correct_matches_matcher.match = dummy_match

                # Also patch legacy matcher methods if they exist
                if hasattr(self.scoring_matcher, "strategy_orchestrator"):
                    for strategy in self.scoring_matcher.strategy_orchestrator.strategies:
                        if hasattr(strategy, "legacy_matcher"):
                            legacy_matcher = strategy.legacy_matcher

                            # Store and patch methods
                            for method_name in [
                                "_match_correct_complete_brush",
                                "_match_correct_split_brush",
                            ]:
                                if hasattr(legacy_matcher, method_name):
                                    original_methods[f"legacy_matcher.{method_name}"] = getattr(
                                        legacy_matcher, method_name
                                    )
                                    setattr(legacy_matcher, method_name, dummy_match)

                            # Only need to patch the first legacy matcher we find
                            break
        except Exception as e:
            if self.debug:
                print(f"Warning: Could not patch correct_matches bypass: {e}")

        return original_methods

    def _restore_correct_matches_methods(self, original_methods: Dict[str, Any]):
        """Restore original methods after bypassing correct_matches.yaml."""
        try:
            # Restore correct_matches_matcher method
            if "correct_matches_matcher.match" in original_methods:
                self.scoring_matcher.correct_matches_matcher.match = original_methods[
                    "correct_matches_matcher.match"
                ]

            # Restore legacy matcher methods
            if hasattr(self.scoring_matcher, "strategy_orchestrator"):
                for strategy in self.scoring_matcher.strategy_orchestrator.strategies:
                    if hasattr(strategy, "legacy_matcher"):
                        legacy_matcher = strategy.legacy_matcher

                        for method_name in [
                            "_match_correct_complete_brush",
                            "_match_correct_split_brush",
                        ]:
                            key = f"legacy_matcher.{method_name}"
                            if key in original_methods:
                                setattr(legacy_matcher, method_name, original_methods[key])

                        # Only need to restore the first legacy matcher we find
                        break
        except Exception as e:
            if self.debug:
                print(f"Warning: Could not restore correct_matches methods: {e}")


# Convenience function for easy use
def analyze_brush_string(
    brush_string: str,
    debug: bool = False,
    show_all_matches: bool = True,
    bypass_correct_matches: bool = False,
) -> Dict[str, Any]:
    """Convenience function to analyze a brush string.

    Args:
        brush_string: The brush string to analyze
        debug: Enable debug mode
        show_all_matches: Whether to show all strategy results
        bypass_correct_matches: Whether to bypass correct_matches.yaml

    Returns:
        Dictionary containing analysis results
    """
    analyzer = BrushMatchingAnalyzer(debug=debug)
    return analyzer.analyze_brush_string(
        brush_string,
        show_all_matches=show_all_matches,
        bypass_correct_matches=bypass_correct_matches,
    )
