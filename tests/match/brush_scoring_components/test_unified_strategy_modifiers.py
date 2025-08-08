#!/usr/bin/env python3
"""Tests for unified strategy modifiers."""

from pathlib import Path

from sotd.match.brush_scoring_components.scoring_engine import ScoringEngine
from sotd.match.brush_scoring_config import BrushScoringConfig
from sotd.match.types import MatchResult


class TestUnifiedStrategyModifiers:
    """Test that unified strategy modifiers work correctly."""

    def setup_method(self):
        """Set up test fixtures."""
        self.config = BrushScoringConfig(Path("data/brush_scoring_config.yaml"))
        self.scoring_engine = ScoringEngine(self.config)

    def test_dual_component_modifier_returns_1_0_when_both_handle_and_knot_match(self):
        """Test that dual_component modifier returns 1.0 when both handle and knot match."""
        # Create a result with both handle and knot sections
        result = MatchResult(
            original="Declaration Grooming Washington B2",
            matched={
                "brand": None,
                "model": None,
                "handle": {"brand": "Declaration Grooming", "model": "Washington"},
                "knot": {"brand": "Declaration Grooming", "model": "B2", "fiber": "Badger"},
            },
            match_type="composite",
            pattern="dual_component",
            strategy="unified",
        )

        # Test the modifier directly
        modifier_value = self.scoring_engine._modifier_dual_component(
            "Declaration Grooming Washington B2", result.matched or {}, "unified"
        )

        assert modifier_value == 1.0

    def test_dual_component_modifier_returns_0_0_when_only_handle_matches(self):
        """Test that dual_component modifier returns 0.0 when only handle matches."""
        # Create a result with only handle section
        result = MatchResult(
            original="Declaration Grooming Washington",
            matched={
                "brand": None,
                "model": None,
                "handle": {"brand": "Declaration Grooming", "model": "Washington"},
                "knot": {"brand": None, "model": None},
            },
            match_type="single_component",
            pattern="handle_only",
            strategy="unified",
        )

        # Test the modifier directly
        modifier_value = self.scoring_engine._modifier_dual_component(
            "Declaration Grooming Washington", result.matched or {}, "unified"
        )

        assert modifier_value == 0.0

    def test_dual_component_modifier_returns_0_0_for_non_unified_strategy(self):
        """Test that dual_component modifier returns 0.0 for non-unified strategies."""
        result = MatchResult(
            original="Declaration Grooming Washington B2",
            matched={
                "brand": None,
                "model": None,
                "handle": {"brand": "Declaration Grooming", "model": "Washington"},
                "knot": {"brand": "Declaration Grooming", "model": "B2", "fiber": "Badger"},
            },
            match_type="composite",
            pattern="dual_component",
            strategy="dual_component",  # Not unified
        )

        # Test the modifier directly
        modifier_value = self.scoring_engine._modifier_dual_component(
            "Declaration Grooming Washington B2", result.matched or {}, "dual_component"
        )

        assert modifier_value == 0.0

    def test_unified_strategy_scoring_with_dual_component_modifier(self):
        """Test that unified strategy gets correct score with dual component modifier."""
        # Create a result with both handle and knot sections
        result = MatchResult(
            original="Declaration Grooming Washington B2",
            matched={
                "brand": None,
                "model": None,
                "handle": {"brand": "Declaration Grooming", "model": "Washington"},
                "knot": {"brand": "Declaration Grooming", "model": "B2", "fiber": "Badger"},
            },
            match_type="composite",
            pattern="dual_component",
            strategy="unified",
        )

        # Score the result
        input_text = "Declaration Grooming Washington B2"
        scored_results = self.scoring_engine.score_results([result], input_text)
        scored_result = scored_results[0]

        # Base score 50 + dual_component modifier 15 = 65
        assert scored_result.score == 65.0

    def test_unified_strategy_scoring_without_dual_component_modifier(self):
        """Test that unified strategy gets correct score without dual component modifier."""
        # Create a result with only handle section
        result = MatchResult(
            original="Declaration Grooming Washington",
            matched={
                "brand": None,
                "model": None,
                "handle": {"brand": "Declaration Grooming", "model": "Washington"},
                "knot": {"brand": None, "model": None},
            },
            match_type="single_component",
            pattern="handle_only",
            strategy="unified",
        )

        # Score the result
        input_text = "Declaration Grooming Washington"
        scored_results = self.scoring_engine.score_results([result], input_text)
        scored_result = scored_results[0]

        # Base score 50 (no modifier)
        assert scored_result.score == 50.0
