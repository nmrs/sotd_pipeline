"""
Strategy management utilities for brush matching system.

This module provides centralized strategy creation and management logic
that can be used by both legacy and new brush matching systems.
"""

from typing import Any, Dict, List

from sotd.match.brush_matching_strategies.automated_split_strategy import (
    AutomatedSplitStrategy,
)
from sotd.match.brush_matching_strategies.correct_matches_wrapper_strategies import (
    CorrectCompleteBrushWrapperStrategy,
    CorrectSplitBrushWrapperStrategy,
)
from sotd.match.brush_matching_strategies.full_input_component_matching_strategy import (
    FullInputComponentMatchingStrategy,
)
from sotd.match.brush_matching_strategies.handle_only_strategy import HandleOnlyStrategy
from sotd.match.brush_matching_strategies.knot_only_strategy import KnotOnlyStrategy
from sotd.match.brush_matching_strategies.known_brush_strategy import (
    KnownBrushMatchingStrategy,
)
from sotd.match.brush_matching_strategies.known_split_wrapper_strategy import (
    KnownSplitWrapperStrategy,
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
from sotd.match.config import BrushMatcherConfig


class StrategyManager:
    """
    Manages creation and configuration of brush matching strategies.

    This class centralizes strategy creation logic that was previously
    duplicated in BrushScoringMatcher, making it reusable for both
    legacy and new systems.
    """

    def __init__(self, config: BrushMatcherConfig):
        """
        Initialize the strategy manager.

        Args:
            config: Brush matcher configuration
        """
        self.config = config

    def create_full_strategies(
        self, handle_matcher: Any, knot_matcher: Any, catalogs: Dict[str, Any]
    ) -> List[Any]:
        """
        Create complete list of strategies for brush matching.

        Args:
            handle_matcher: HandleMatcher instance
            knot_matcher: KnotMatcher instance
            catalogs: Dictionary containing all catalog data

        Returns:
            List of strategy objects in priority order
        """
        catalog_data = catalogs["brushes"]

        strategies = [
            # Priority 0: correct_complete_brush
            CorrectCompleteBrushWrapperStrategy(catalogs["correct_matches"]),
            # Priority 1: correct_split_brush
            CorrectSplitBrushWrapperStrategy(catalogs["correct_matches"]),
            # Priority 2: known_split
            KnownSplitWrapperStrategy(catalog_data.get("known_splits", {})),
            # Priority 3: high_priority_automated_split (REMOVED - replaced by AutomatedSplitStrategy)
            # Priority 4: unified component strategy (before individual brush strategies)
            FullInputComponentMatchingStrategy(handle_matcher, knot_matcher, catalogs),
            # Priority 5: individual brush strategies (replacing complete_brush wrapper)
            KnownBrushMatchingStrategy(catalog_data.get("known_brushes", {}), handle_matcher),
            OmegaSemogueBrushMatchingStrategy(),
            ZenithBrushMatchingStrategy(),
            OtherBrushMatchingStrategy(catalog_data.get("other_brushes", {})),
            # Priority 6: medium_priority_automated_split (REMOVED - replaced by AutomatedSplitStrategy)
            # NEW: automated_split (unified high/medium priority strategy)
            AutomatedSplitStrategy(catalogs, self.config),
            # NEW: handle_only strategy
            HandleOnlyStrategy(handle_matcher),
            # NEW: knot_only strategy
            KnotOnlyStrategy(knot_matcher),
        ]

        return strategies

    def create_temp_strategies(self, handle_matcher: Any, catalogs: Dict[str, Any]) -> List[Any]:
        """
        Create temporary strategy list without unified component strategy.

        This creates strategies without the unified component strategy to avoid
        circular dependency during knot matcher initialization.

        Args:
            handle_matcher: HandleMatcher instance
            catalogs: Dictionary containing all catalog data

        Returns:
            List of strategy objects (without unified component strategy)
        """
        catalog_data = catalogs["brushes"]

        strategies = [
            # Priority 0: correct_complete_brush
            CorrectCompleteBrushWrapperStrategy(catalogs["correct_matches"]),
            # Priority 1: correct_split_brush
            CorrectSplitBrushWrapperStrategy(catalogs["correct_matches"]),
            # Priority 2: known_split
            KnownSplitWrapperStrategy(catalog_data.get("known_splits", {})),
            # Priority 3: high_priority_automated_split (REMOVED - replaced by AutomatedSplitStrategy)
            # Priority 4: individual brush strategies
            KnownBrushMatchingStrategy(catalog_data.get("known_brushes", {}), handle_matcher),
            OmegaSemogueBrushMatchingStrategy(),
            ZenithBrushMatchingStrategy(),
            OtherBrushMatchingStrategy(catalog_data.get("other_brushes", {})),
            # Priority 6: medium_priority_automated_split (REMOVED - replaced by AutomatedSplitStrategy)
        ]

        return strategies

    def create_knot_strategies(self, catalogs: Dict[str, Any]) -> List[Any]:
        """
        Create knot-specific strategies for knot matcher initialization.

        Args:
            catalogs: Dictionary containing all catalog data

        Returns:
            List of knot strategy objects
        """
        knots_data = catalogs["knots"]

        from sotd.match.brush_matching_strategies.fiber_fallback_strategy import (
            FiberFallbackStrategy,
        )
        from sotd.match.brush_matching_strategies.knot_size_fallback_strategy import (
            KnotSizeFallbackStrategy,
        )
        from sotd.match.brush_matching_strategies.known_knot_strategy import (
            KnownKnotMatchingStrategy,
        )
        from sotd.match.brush_matching_strategies.other_knot_strategy import (
            OtherKnotMatchingStrategy,
        )

        knot_strategies = [
            KnownKnotMatchingStrategy(knots_data.get("known_knots", {})),
            OtherKnotMatchingStrategy(knots_data.get("other_knots", {})),
            FiberFallbackStrategy(),
            KnotSizeFallbackStrategy(),
        ]

        return knot_strategies
