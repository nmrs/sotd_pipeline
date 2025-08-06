#!/usr/bin/env python3
"""Tests for brush scoring strategy integration."""

import pytest
from unittest.mock import Mock, patch

from sotd.match.scoring_brush_matcher import BrushScoringMatcher
from sotd.match.brush_matcher import BrushMatcher


class TestBrushScoringStrategyIntegration:
    """Test that scoring system uses the same strategies as legacy system."""

    def test_create_strategies_returns_actual_strategies(self):
        """Test that _create_strategies returns actual strategy instances."""
        matcher = BrushScoringMatcher()
        strategies = matcher._create_strategies()

        # Should not return empty list
        assert len(strategies) > 0, "Scoring system should have actual strategies"

        # Should have brush strategies
        brush_strategies = [s for s in strategies if hasattr(s, "match")]
        assert len(brush_strategies) > 0, "Should have brush matching strategies"

    def test_strategies_match_legacy_system(self):
        """Test that scoring system has same strategies as legacy system."""
        scoring_matcher = BrushScoringMatcher()
        legacy_matcher = BrushMatcher()

        scoring_strategies = scoring_matcher._create_strategies()
        legacy_brush_strategies = legacy_matcher.brush_strategies
        legacy_knot_strategies = legacy_matcher.knot_strategies

        # Should have same number of strategies
        expected_total = len(legacy_brush_strategies) + len(legacy_knot_strategies)
        assert (
            len(scoring_strategies) == expected_total
        ), f"Expected {expected_total} strategies, got {len(scoring_strategies)}"

        # Should have same strategy types
        scoring_types = [type(s).__name__ for s in scoring_strategies]
        legacy_types = [type(s).__name__ for s in legacy_brush_strategies + legacy_knot_strategies]

        # Sort for comparison
        scoring_types.sort()
        legacy_types.sort()

        assert (
            scoring_types == legacy_types
        ), f"Strategy types don't match. Scoring: {scoring_types}, Legacy: {legacy_types}"

    def test_strategy_orchestrator_uses_strategies(self):
        """Test that strategy orchestrator uses the created strategies."""
        matcher = BrushScoringMatcher()

        # Mock a strategy to return a known result
        mock_strategy = Mock()
        mock_strategy.match.return_value = Mock(
            original="test brush",
            matched={"brand": "Test", "model": "Brush"},
            match_type="test",
            pattern="test_pattern",
        )

        # Replace strategies with our mock
        matcher.strategy_orchestrator.strategies = [mock_strategy]

        # Test that the orchestrator uses the strategy
        result = matcher.strategy_orchestrator.run_all_strategies("test brush")

        assert len(result) == 1
        assert result[0].matched["brand"] == "Test"
        assert mock_strategy.match.called

    def test_scoring_system_matches_legacy_results(self):
        """Test that scoring system produces same results as legacy system for known brushes."""
        # Test with a brush that should match using KnownBrushMatchingStrategy
        test_brush = "Simpson Chubby 2"

        # Create both matchers
        scoring_matcher = BrushScoringMatcher()
        legacy_matcher = BrushMatcher()

        # Get results
        scoring_result = scoring_matcher.match(test_brush)
        legacy_result = legacy_matcher.match(test_brush)

        # Both should return results (not None)
        assert scoring_result is not None, "Scoring system should match known brush"
        assert legacy_result is not None, "Legacy system should match known brush"

        # Results should be similar (allowing for minor differences in structure)
        if scoring_result and legacy_result:
            scoring_brand = scoring_result.matched.get("brand") if scoring_result.matched else None
            legacy_brand = legacy_result.matched.get("brand") if legacy_result.matched else None

            assert (
                scoring_brand == legacy_brand
            ), f"Brand mismatch: scoring={scoring_brand}, legacy={legacy_brand}"

    def test_strategy_priority_order(self):
        """Test that strategies are created in correct priority order."""
        matcher = BrushScoringMatcher()
        strategies = matcher._create_strategies()

        # Should have strategies in priority order
        strategy_names = [type(s).__name__ for s in strategies]

        # Check that known strategies come before fallback strategies
        known_strategies = [
            "KnownBrushMatchingStrategy",
            "OmegaSemogueBrushMatchingStrategy",
            "ZenithBrushMatchingStrategy",
        ]
        fallback_strategies = ["FiberFallbackStrategy", "KnotSizeFallbackStrategy"]

        # Find positions
        known_positions = [
            strategy_names.index(name) for name in known_strategies if name in strategy_names
        ]
        fallback_positions = [
            strategy_names.index(name) for name in fallback_strategies if name in strategy_names
        ]

        # Known strategies should come before fallback strategies
        if known_positions and fallback_positions:
            max_known_pos = max(known_positions)
            min_fallback_pos = min(fallback_positions)
            assert (
                max_known_pos < min_fallback_pos
            ), "Known strategies should come before fallback strategies"

    def test_catalog_data_passed_to_strategies(self):
        """Test that catalog data is properly passed to strategies."""
        matcher = BrushScoringMatcher()
        strategies = matcher._create_strategies()

        # Find KnownBrushMatchingStrategy
        known_strategy = None
        for strategy in strategies:
            if type(strategy).__name__ == "KnownBrushMatchingStrategy":
                known_strategy = strategy
                break

        assert known_strategy is not None, "Should have KnownBrushMatchingStrategy"

        # Should have catalog data
        assert hasattr(
            known_strategy, "catalog"
        ), "KnownBrushMatchingStrategy should have catalog data"
        assert known_strategy.catalog is not None, "Catalog data should not be None"
