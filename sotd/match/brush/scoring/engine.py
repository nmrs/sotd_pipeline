"""
Scoring Engine Component.

This component scores strategy results based on configuration weights and criteria.
"""

import re
from pathlib import Path
from typing import Any, List, Optional

import yaml

from sotd.match.types import MatchResult


class ScoringEngine:
    """
    Engine for scoring brush matching strategy results.

    This component applies scoring weights and modifiers to strategy results
    to determine the best match.
    """

    # Class-level cache for knots.yaml data
    _knots_cache = None
    _knots_cache_timestamp = 0

    @classmethod
    def clear_knots_cache(cls):
        """Clear the knots cache."""
        cls._knots_cache = None
        cls._knots_cache_timestamp = 0

    def __init__(self, config, debug: bool = False):
        """
        Initialize the scoring engine.

        Args:
            config: BrushScoringConfig instance
            debug: Enable debug output
        """
        self.config = config
        self.debug = debug

    def score_results(
        self, results: List[MatchResult], value: str, cached_results: Optional[dict] = None
    ) -> List[MatchResult]:
        """
        Score all strategy results.

        Args:
            results: List of MatchResult objects to score
            value: Original input string for context

        Returns:
            List of MatchResult objects with scores added
        """
        # Store cached_results for use in manufacturer detection
        self.cached_results = cached_results

        if self.debug:
            print("🔍 Scoring {len(results)} strategy results...")

        scored_results = []

        for result in results:
            if self.debug:
                print(f"   📊 Scoring result from strategy: {getattr(result, 'strategy', 'None')}")
            score = self._calculate_score(result, value)
            if self.debug:
                print(f"      Calculated score: {score}")
            result.score = score
            scored_results.append(result)

        if self.debug:
            print("✅ Scoring complete. All results now have scores.")
        return scored_results

    def get_best_result(self, scored_results: List[MatchResult]) -> Optional[MatchResult]:
        """
        Get the highest-scoring result.

        Args:
            scored_results: List of scored MatchResult objects

        Returns:
            Highest-scoring MatchResult, or None if list is empty or no valid matches
        """
        if not scored_results:
            return None

        # Filter out results with no valid matches (matched=None or empty matched)
        valid_results = [r for r in scored_results if r.matched is not None and r.matched]

        if not valid_results:
            return None

        return max(valid_results, key=lambda r: r.score or 0.0)

    def _calculate_score(self, result: MatchResult, value: str) -> float:
        """
        Calculate score for a single result.

        Args:
            result: MatchResult to score
            value: Original input string

        Returns:
            Calculated score
        """
        # Check if this strategy actually produced valid results
        has_valid_data = result.matched and (
            result.matched.get("brand")
            or result.matched.get("handle")
            or result.matched.get("knot")
        )

        # If no valid data, return 0.0 regardless of base score
        if not has_valid_data:
            if self.debug:
                print("      Strategy failed to produce valid results - score: 0.0")
            return 0.0

        # Get base strategy score
        strategy_name = self._get_strategy_name_from_result(result)
        if self.debug:
            print(f"      Strategy name extracted: '{strategy_name}'")

        base_score = self.config.get_base_strategy_score(strategy_name)
        if self.debug:
            print(f"      Base score from config: {base_score}")

        # Apply modifiers
        modifier_score = self._calculate_modifiers(result, value, strategy_name)
        if self.debug:
            print(f"      Modifier score: {modifier_score}")

        final_score = base_score + modifier_score
        if self.debug:
            print(f"      Final score: {final_score}")

        return final_score

    def _get_strategy_name_from_result(self, result: MatchResult) -> str:
        """
        Extract strategy name from result.

        Args:
            result: MatchResult object

        Returns:
            Strategy name
        """
        # Validate that strategy name is not None
        if result.strategy is None:
            raise ValueError(
                f"MatchResult has None strategy name. "
                f"This is a bug - all MatchResult objects must have a valid strategy name. "
                f"Result: {result}"
            )

        # If the result has a strategy field, use it directly
        if result.strategy:
            return result.strategy

        # Fallback to mapping match_type values to strategy names
        match_type = result.match_type or "unknown_strategy"
        matched = result.matched or {}

        # Check if this is a dual component result (has handle and knot sections)
        if match_type == "regex" and "handle" in matched and "knot" in matched:
            return "dual_component"

        # Map match_type values to strategy names
        match_type_to_strategy = {
            "regex": "complete_brush",  # Known brush strategies use regex
            "fiber_fallback": "single_component_fallback",  # Fiber fallback strategy
            "size_fallback": "single_component_fallback",  # Size fallback strategy
            "handle": "complete_brush",  # Handle matcher results
            "knot": "single_component_fallback",  # Knot matcher results
            "composite": "dual_component",  # Composite brush results
            "single_component": "single_component_fallback",  # Single component fallback results
        }

        return match_type_to_strategy.get(match_type, "single_component_fallback")

    def _calculate_modifiers(self, result: MatchResult, value: str, strategy_name: str) -> float:
        """
        Calculate modifier score for a result.

        Args:
            result: MatchResult to score
            value: Original input string
            strategy_name: Name of the strategy

        Returns:
            Modifier score
        """
        modifier_score = 0.0

        # Get all available modifiers for this strategy
        modifier_names = self.config.get_all_modifier_names(strategy_name)

        for modifier_name in modifier_names:
            # Get the modifier weight from configuration
            modifier_weight = self.config.get_strategy_modifier(strategy_name, modifier_name)

            # Apply the modifier function if it exists
            modifier_function = getattr(self, f"_modifier_{modifier_name}", None)
            if modifier_function is not None and hasattr(modifier_function, "__call__"):
                modifier_value = modifier_function(value, result, strategy_name)
                modifier_score += modifier_value * modifier_weight
            else:
                # If no modifier function exists, just add the weight directly
                modifier_score += modifier_weight

        return modifier_score

    def _modifier_multiple_brands(self, input_text: str, result, strategy_name: str) -> float:
        """
        Return score modifier for multiple brand mentions.

        Args:
            input_text: Original input string
            result: MatchResult object or dict
            strategy_name: Name of the strategy

        Returns:
            Modifier value (1.0 if multiple brands detected, 0.0 otherwise)
        """
        # Handle both MatchResult objects and dicts
        if hasattr(result, "matched"):
            matched = result.matched
        else:
            matched = result.get("matched", {}) if isinstance(result, dict) else {}

        # For full_input_component_matching strategy, check handle and knot sections
        if strategy_name == "full_input_component_matching":
            handle = matched.get("handle", {})
            knot = matched.get("knot", {})

            handle_brand = handle.get("brand") if handle else None
            knot_brand = knot.get("brand") if knot else None

            # Count actual brands found in the result
            brands_found = set()
            if handle_brand:
                brands_found.add(handle_brand)
            if knot_brand:
                brands_found.add(knot_brand)

            # Return 1.0 if we have 2+ different brands, 0.0 otherwise
            return 1.0 if len(brands_found) > 1 else 0.0

        # For all strategies, check nested handle and knot brand fields
        brands_found = set()

        # Handle case where matched is None
        if matched is None:
            return 0.0

        # Check nested handle and knot brand fields
        if "handle" in matched and isinstance(matched["handle"], dict):
            handle_brand = matched["handle"].get("brand")
            if handle_brand:
                brands_found.add(handle_brand)

        if "knot" in matched and isinstance(matched["knot"], dict):
            knot_brand = matched["knot"].get("brand")
            if knot_brand:
                brands_found.add(knot_brand)

        # Also check direct brand field if it exists
        if "brand" in matched and matched["brand"]:
            brands_found.add(matched["brand"])

        return 1.0 if len(brands_found) > 1 else 0.0

    def _modifier_same_brand(self, input_text: str, result, strategy_name: str) -> float:
        """
        Return score modifier for same brand detection (penalty).

        Args:
            input_text: Original input string
            result: MatchResult object or dict
            strategy_name: Name of the strategy

        Returns:
            Modifier value (1.0 if same brand detected for handle and knot, 0.0 otherwise)
        """
        # Apply only to composite brush strategies
        allowed_strategies = [
            "automated_split",
            "full_input_component_matching",
            "known_split",
        ]
        if strategy_name not in allowed_strategies:
            return 0.0

        # Handle both MatchResult objects and dicts
        if hasattr(result, "matched"):
            matched = result.matched
        else:
            matched = result.get("matched", {}) if isinstance(result, dict) else {}

        # Handle case where matched is None
        if matched is None:
            return 0.0

        # For full_input_component_matching strategy, check handle and knot sections
        if strategy_name == "full_input_component_matching":
            handle = matched.get("handle", {})
            knot = matched.get("knot", {})

            # Extract brands from nested structure
            # Handle uses "brand" field (set from handle_maker in strategy)
            # Knot uses "brand" field
            handle_brand = handle.get("brand") if handle and isinstance(handle, dict) else None
            knot_brand = knot.get("brand") if knot and isinstance(knot, dict) else None

            # Fail fast: If either brand is missing, return 0.0 (not same brand)
            if not handle_brand or not knot_brand:
                return 0.0

            # Compare brands (case-insensitive, stripped)
            handle_clean = str(handle_brand).strip().lower()
            knot_clean = str(knot_brand).strip().lower()
            
            # Only return 1.0 if brands are non-empty and match
            if handle_clean and knot_clean:
                return 1.0 if handle_clean == knot_clean else 0.0
            return 0.0

        # For all other strategies, check nested handle and knot brand fields
        handle_brand = None
        knot_brand = None

        if "handle" in matched and isinstance(matched["handle"], dict):
            handle_brand = matched["handle"].get("brand")

        if "knot" in matched and isinstance(matched["knot"], dict):
            knot_brand = matched["knot"].get("brand")

        # Return 1.0 if both brands exist and are the same (case-insensitive)
        # Only apply penalty if both brands are non-empty strings
        if handle_brand and knot_brand:
            # Strip whitespace and compare case-insensitively
            handle_clean = str(handle_brand).strip().lower()
            knot_clean = str(knot_brand).strip().lower()
            
            # Only return 1.0 if brands are non-empty and match
            if handle_clean and knot_clean:
                return 1.0 if handle_clean == knot_clean else 0.0
        return 0.0

    def _detect_fiber_conflict(
        self, input_text: str, result: Any
    ) -> tuple[bool, str | None, str | None]:
        """
        Shared helper to detect fiber conflicts between user input and catalog data.

        Args:
            input_text: Original input string
            result: MatchResult object

        Returns:
            Tuple of (has_conflict, user_fiber, catalog_fiber)
        """
        # Use existing fiber_utils to detect user fiber
        from ..strategies.utils.fiber_utils import match_fiber

        user_fiber = match_fiber(input_text)

        # If no user fiber specified, no conflict possible
        if not user_fiber:
            return False, None, None

        # Extract catalog fiber from result
        catalog_fiber = None

        # Try different possible locations for fiber info
        if hasattr(result, "matched") and result.matched:
            # Check matched data
            matched = result.matched
            if isinstance(matched, dict):
                catalog_fiber = matched.get("fiber")

            # Check knot data if no direct fiber
            if not catalog_fiber and "knot" in matched:
                knot = matched["knot"]
                if isinstance(knot, dict):
                    catalog_fiber = knot.get("fiber")

        # If no catalog fiber, no conflict possible
        if not catalog_fiber:
            return False, None, None

        # Check for actual conflict (case-insensitive)
        has_conflict = user_fiber.lower() != catalog_fiber.lower()

        return has_conflict, user_fiber, catalog_fiber

    def _modifier_fiber_match(self, input_text: str, result: dict, strategy_name: str) -> float:
        """
        Return score modifier for fiber type detection.

        Args:
            input_text: Original input string
            result: MatchResult object
            strategy_name: Name of the strategy

        Returns:
            Modifier value (1.0 if fiber detected, 0.0 otherwise)
        """
        # Only apply to individual component strategies
        if strategy_name not in ["handle_matching", "knot_matching", "handle_only", "knot_only"]:
            return 0.0

        # Use fiber_utils to detect fiber in input text
        try:
            from ..strategies.utils.fiber_utils import match_fiber

            fiber_type = match_fiber(input_text)
            return 1.0 if fiber_type else 0.0
        except ImportError:
            # Fallback to simple pattern matching if fiber_utils not available
            fiber_patterns = [
                r"\bbadger\b",
                r"\bboar\b",
                r"\bsynthetic\b",
                r"\bsilvertip\b",
                r"\btwo_band\b",
                r"\bthree_band\b",
            ]
            for pattern in fiber_patterns:
                if re.search(pattern, input_text.lower()):
                    return 1.0
            return 0.0

    def _modifier_size_match(self, input_text: str, result: dict, strategy_name: str) -> float:
        """
        Return score modifier for size specification detection.

        Args:
            input_text: Original input string
            result: MatchResult object
            strategy_name: Name of the strategy

        Returns:
            Modifier value (1.0 if size detected, 0.0 otherwise)
        """
        # Only apply to individual component strategies
        if strategy_name not in ["handle_matching", "knot_matching", "handle_only", "knot_only"]:
            return 0.0

        # Use knot_size_utils to detect size in input text
        try:
            from ..strategies.utils.knot_size_utils import parse_knot_size

            size_match = parse_knot_size(input_text)
            return 1.0 if size_match else 0.0
        except ImportError:
            # Fallback to simple pattern matching if knot_size_utils not available
            size_patterns = [
                r"\b\d+mm\b",
                r"\b\d+\.\d+mm\b",
                r"\b\d+/\d+\b",
                r"\b\d+\.\d+\b",
            ]
            for pattern in size_patterns:
                if re.search(pattern, input_text.lower()):
                    return 1.0
            return 0.0

    def _modifier_fiber_mismatch(self, input_text: str, result: dict, strategy_name: str) -> float:
        """
        Return score modifier for fiber mismatches between user input and catalog data.

        Args:
            input_text: Original input string
            result: MatchResult object
            strategy_name: Name of the strategy

        Returns:
            Modifier value (1.0 if fiber mismatch detected, 0.0 otherwise)
        """
        has_conflict, _, _ = self._detect_fiber_conflict(input_text, result)
        return 1.0 if has_conflict else 0.0

    def _modifier_dual_component(self, input_text: str, result: dict, strategy_name: str) -> float:
        """
        Return score modifier for dual component matches
        (full_input_component_matching strategy only).

        Args:
            input_text: Original input string
            result: MatchResult object
            strategy_name: Name of the strategy

        Returns:
            Modifier value (1.0 if both handle and knot matched, 0.0 otherwise)
        """
        # Only apply to full_input_component_matching strategy
        if strategy_name != "full_input_component_matching":
            return 0.0

        # Check if both handle and knot sections exist and have valid matches
        handle = result.get("handle")
        knot = result.get("knot")

        if handle and knot:
            # Both handle and knot have data
            handle_brand = handle.get("brand")
            knot_brand = knot.get("brand")

            # Return 1.0 if both have brands (indicating successful matches)
            return 1.0 if handle_brand and knot_brand else 0.0

        return 0.0

    def _modifier_high_confidence(self, input_text: str, result: dict, strategy_name: str) -> float:
        """
        Return score modifier for high-confidence delimiter usage.

        Args:
            input_text: Original input string
            result: MatchResult object
            strategy_name: Name of the strategy

        Returns:
            Modifier value (1.0 if high-confidence delimiters used, 0.0 otherwise)
        """
        # Only apply to automated_split strategy
        if strategy_name != "automated_split":
            return 0.0

        # Check if this specific result used a high-priority delimiter
        if result.get("high_priority_delimiter", False):
            return 1.0

        return 0.0

    def _modifier_priority_score(
        self, input_text: str, result: MatchResult, strategy_name: str
    ) -> float:
        """
        Return score modifier for handle/knot priority levels.

        Args:
            input_text: Original input string
            result: MatchResult object
            strategy_name: Name of the strategy

        Returns:
            Modifier value based on priority levels (higher quality = more points)
        """
        # Apply to individual handle/knot matching strategies
        if strategy_name not in ["handle_matching", "knot_matching"]:
            return 0.0

        # Check if we have handle or knot component with priority info
        if not result.matched:
            return 0.0

        if strategy_name == "handle_matching":
            handle = result.matched.get("handle", {})
            handle_priority = handle.get("priority") if handle else None

            if handle_priority is not None:
                # Lower priority number = higher quality = more points
                # 1->3, 2->2, 3->1, 4->0, etc.
                return max(0, 3 - handle_priority + 1)

        elif strategy_name == "knot_matching":
            knot = result.matched.get("knot", {})
            knot_priority = knot.get("priority") if knot else None

            if knot_priority is not None:
                # Same dynamic scaling for knots
                return max(0, 3 - knot_priority + 1)

        return 0.0

    def _modifier_handle_weight(
        self, input_text: str, result: MatchResult, strategy_name: str
    ) -> float:
        """
        Calculate and return raw handle score for component strategies.

        The scoring engine will apply the weight multiplier to this raw score.
        This function calculates the component score externally instead of
        expecting it to be pre-calculated.

        Args:
            input_text: Original input string
            result: MatchResult object
            strategy_name: Name of the strategy

        Returns:
            Raw handle matching score (weight will be applied by scoring engine)
        """
        # Apply to component strategies that do handle/knot matching
        if strategy_name not in ["automated_split", "full_input_component_matching"]:
            return 0.0

        # Get handle data from result
        handle_data = result.matched.get("handle", {}) if result.matched else {}
        if not handle_data:
            return 0.0

        # Calculate handle score externally using the same logic as ComponentScoreCalculator
        score = 0.0

        # Brand match (5 points)
        if handle_data.get("brand"):
            score += 5.0

        # Model match (5 points)
        if handle_data.get("model"):
            score += 5.0

        # Priority bonus (2 points for priority 1, 1 point for priority 2)
        priority = handle_data.get("priority")
        if priority == 1:
            score += 2.0
        elif priority == 2:
            score += 1.0

        return score

    def _modifier_knot_weight(
        self, input_text: str, result: MatchResult, strategy_name: str
    ) -> float:
        """
        Calculate and return raw knot score for component strategies.

        The scoring engine will apply the weight multiplier to this raw score.
        This function calculates the component score externally instead of
        expecting it to be pre-calculated.

        Args:
            input_text: Original input string
            result: MatchResult object
            strategy_name: Name of the strategy

        Returns:
            Raw knot matching score (weight will be applied by scoring engine)
        """
        # Apply to component strategies that do handle/knot matching
        if strategy_name not in ["automated_split", "full_input_component_matching"]:
            return 0.0

        # Get knot data from result
        knot_data = result.matched.get("knot", {}) if result.matched else {}
        if not knot_data:
            return 0.0

        # Calculate knot score externally using the same logic as ComponentScoreCalculator
        score = 0.0

        # Brand match (5 points)
        if knot_data.get("brand"):
            score += 5.0

        # Model match (5 points)
        if knot_data.get("model"):
            score += 5.0

        # Fiber match (5 points)
        if knot_data.get("fiber"):
            score += 5.0

        # Size match (2 points)
        if knot_data.get("knot_size_mm"):
            score += 2.0

        # Priority bonus (2 points for priority 1, 1 point for priority 2)
        priority = knot_data.get("priority")
        if priority == 1:
            score += 2.0
        elif priority == 2:
            score += 1.0

        return score

    def _modifier_handle_brand_without_knot_brand(
        self, input_text: str, result: MatchResult, strategy_name: str
    ) -> float:
        """
        Return score modifier for handle brand without knot brand detection.

        Args:
            input_text: Original input string
            result: MatchResult object
            strategy_name: Name of the strategy

        Returns:
            Modifier value (1.0 if handle brand detected but no knot brand, 0.0 otherwise)
        """
        # Apply to composite brush strategies and individual component strategies
        allowed_strategies = [
            "automated_split",
            "full_input_component_matching",
            "known_split",
            "handle_only",
            "knot_only",
        ]
        if strategy_name not in allowed_strategies:
            return 0.0

        # Check the current result's handle and knot data
        if not result or not result.matched:
            return 0.0

        handle_data = result.matched.get("handle", {})
        knot_data = result.matched.get("knot", {})

        handle_brand = handle_data.get("brand") if handle_data else None
        knot_brand = knot_data.get("brand") if knot_data else None

        # Return 1.0 if handle brand is populated but knot brand is not
        return 1.0 if handle_brand and not knot_brand else 0.0

    def _modifier_knot_indicators(self, input_text: str, result: dict, strategy_name: str) -> float:
        """
        Return score modifier for knot-specific indicators.

        Detects:
        - Known knot model names from knots.yaml known_knots section
        - NOT fiber/size (handled by fiber_match/size_match)

        Args:
            input_text: Original input string
            result: MatchResult object
            strategy_name: Name of the strategy

        Returns:
            Modifier value (1.0 if knot indicators detected, 0.0 otherwise)
        """
        try:
            # Use cached knots data
            knots_data = self._load_knots_data()

            if not knots_data or "known_knots" not in knots_data:
                return 0.0

            input_lower = input_text.lower()

            # Extract all knot model names from known_knots section
            for brand, brand_data in knots_data["known_knots"].items():
                for model_name, model_data in brand_data.items():
                    # Skip non-model keys like 'fiber' and 'knot_size_mm'
                    if isinstance(model_data, dict) and "patterns" in model_data:
                        # Check if model name appears in input (e.g., "Timberwolf", "v8", "G5")
                        if model_name.lower() in input_lower:
                            return 1.0

                        # Also check the patterns for this model
                        for pattern in model_data["patterns"]:
                            if re.search(pattern, input_lower, re.IGNORECASE):
                                return 1.0

            return 0.0

        except Exception as e:
            # Fail fast - log error and return 0
            print(f"Error in knot_indicators modifier: {e}")
            return 0.0

    def _modifier_handle_indicators(
        self, input_text: str, result: dict, strategy_name: str
    ) -> float:
        """
        Return score modifier for handle-specific indicators.

        Args:
            input_text: Original input string
            result: MatchResult object
            strategy_name: Name of the strategy

        Returns:
            Modifier value (1.0 if handle indicators detected, 0.0 otherwise)
        """
        # Only apply to individual component strategies
        if strategy_name not in ["handle_matching", "knot_matching", "handle_only", "knot_only"]:
            return 0.0

        handle_indicators = [
            r"\bhandle\b",
            r"\bwood\b",
            r"\bresin\b",
            r"\bacrylic\b",
            r"\bmetal\b",
            r"\bbrass\b",
            r"\baluminum\b",
            r"\bsteel\b",
            r"\btitanium\b",
            r"\bebonite\b",
            r"\bivory\b",
            r"\bhorn\b",
            r"\bbone\b",
            r"\bstone\b",
            r"\bmarble\b",
            r"\bgranite\b",
        ]
        for pattern in handle_indicators:
            if re.search(pattern, input_text.lower()):
                return 1.0
        return 0.0

    def _modifier_knot_brand_without_handle_brand(
        self, input_text: str, result, strategy_name: str
    ) -> float:
        """
        Return score modifier for knot brand without handle brand detection.

        Args:
            input_text: Original input string
            result: MatchResult object or dict
            strategy_name: Name of the strategy

        Returns:
            Modifier value (1.0 if knot brand detected but no handle brand, 0.0 otherwise)
        """
        # Apply to composite brush strategies and individual component strategies
        allowed_strategies = [
            "automated_split",
            "full_input_component_matching",
            "known_split",
            "handle_only",
            "knot_only",
        ]
        if strategy_name not in allowed_strategies:
            return 0.0

        # Check the current result's handle and knot data
        if not result or (hasattr(result, "matched") and not result.matched):
            return 0.0

        # Handle both MatchResult objects and dicts
        if hasattr(result, "matched"):
            matched = result.matched
        else:
            matched = result.get("matched", {}) if isinstance(result, dict) else {}
            if not matched:
                return 0.0

        handle_data = matched.get("handle", {})
        knot_data = matched.get("knot", {})

        handle_brand = handle_data.get("brand") if handle_data else None
        knot_brand = knot_data.get("brand") if knot_data else None

        # Return 1.0 if knot brand is populated but handle brand is not
        return 1.0 if knot_brand and not handle_brand else 0.0

    def _modifier_neither_brand(self, input_text: str, result, strategy_name: str) -> float:
        """
        Return score modifier for neither brand detection.

        Args:
            input_text: Original input string
            result: MatchResult object or dict
            strategy_name: Name of the strategy

        Returns:
            Modifier value (1.0 if neither handle brand nor knot brand detected, 0.0 otherwise)
        """
        # Apply to composite brush strategies and individual component strategies
        allowed_strategies = [
            "automated_split",
            "full_input_component_matching",
            "known_split",
            "handle_only",
            "knot_only",
        ]
        if strategy_name not in allowed_strategies:
            return 0.0

        # Check the current result's handle and knot data
        if not result or (hasattr(result, "matched") and not result.matched):
            return 0.0

        # Handle both MatchResult objects and dicts
        if hasattr(result, "matched"):
            matched = result.matched
        else:
            matched = result.get("matched", {}) if isinstance(result, dict) else {}
            if not matched:
                return 0.0

        handle_data = matched.get("handle", {})
        knot_data = matched.get("knot", {})

        handle_brand = handle_data.get("brand") if handle_data else None
        knot_brand = knot_data.get("brand") if knot_data else None

        # Return 1.0 if neither handle brand nor knot brand is populated
        return 1.0 if not handle_brand and not knot_brand else 0.0

    def _modifier_brand_match(self, input_text: str, result, strategy_name: str) -> float:
        """
        Return score modifier for brand matching (knot_matching strategy only).

        Args:
            input_text: Original input string
            result: MatchResult object or dict
            strategy_name: Name of the strategy

        Returns:
            Modifier value (1.0 if knot brand is populated, 0.0 otherwise)
        """
        # Only apply to knot_matching strategy
        if strategy_name != "knot_matching":
            return 0.0

        # Handle both MatchResult objects and dicts
        if hasattr(result, "matched"):
            matched = result.matched
        else:
            matched = result.get("matched", {}) if isinstance(result, dict) else {}

        # Check if knot brand is populated
        if matched and "knot" in matched:
            knot = matched["knot"]
            if isinstance(knot, dict) and knot.get("brand"):
                return 1.0

        return 0.0

    def _load_knots_data(self) -> dict:
        """
        Load knots.yaml data with caching.

        Returns:
            Cached knots data or loads from file if not cached
        """
        # Check if we have valid cached data
        if self._knots_cache is not None:
            return self._knots_cache

        try:
            # Load knots.yaml to extract model names
            knots_path = Path("data/knots.yaml")
            if not knots_path.exists():
                self._knots_cache = {}
                return self._knots_cache

            with knots_path.open("r", encoding="utf-8") as f:
                knots_data = yaml.safe_load(f)

            # Cache the data
            self._knots_cache = knots_data if knots_data else {}
            return self._knots_cache

        except Exception as e:
            # Fail fast - log error and cache empty dict
            print(f"Error loading knots.yaml: {e}")
            self._knots_cache = {}
            return self._knots_cache
