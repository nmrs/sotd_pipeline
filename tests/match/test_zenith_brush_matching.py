#!/usr/bin/env python3
"""Test file for Zenith brush matching cases."""

from sotd.match.brush_matcher import BrushMatcher
from sotd.match.scoring_brush_matcher import BrushScoringMatcher


class TestZenithBrushMatching:
    """Test the specific Zenith brush matching cases."""

    def setup_method(self):
        """Set up test fixtures."""
        self.legacy_matcher = BrushMatcher()
        self.scoring_matcher = BrushScoringMatcher()
        self.test_cases = [
            "Zenith Big Scrubby Chrome (B21 28x50mm Boar)",
            "Zenith B07",
            "Zenith Big Scrubby Chrome (B21 28x50mm Boar) $DOORKNOB",
        ]

    def test_legacy_system_zenith_matching(self):
        """Test that legacy system correctly matches Zenith brushes."""
        for test_input in self.test_cases:
            result = self.legacy_matcher.match(test_input)

            assert result is not None, f"Should return result for {test_input}"
            assert result.matched is not None, f"Should produce match for {test_input}"

            # Top level should be correct
            assert result.matched["brand"] == "Zenith"
            assert result.matched["model"] in ["B21", "B07"]  # Should extract model correctly

            # Knot section should be correct
            knot = result.matched["knot"]
            assert knot["brand"] == "Zenith"
            assert knot["model"] in ["B21", "B07"]
            assert knot["fiber"] == "Boar"  # Should use brand-level default
            assert knot["_matched_by"] == "ZenithBrushMatchingStrategy"

    def test_scoring_system_zenith_matching(self):
        """Test that scoring system correctly matches Zenith brushes."""
        for test_input in self.test_cases:
            result = self.scoring_matcher.match(test_input)

            assert result is not None, f"Should return result for {test_input}"
            assert result.matched is not None, f"Should produce match for {test_input}"

            # Top level should be correct
            assert result.matched["brand"] == "Zenith"
            assert result.matched["model"] in ["B21", "B07"]  # Should extract model correctly

            # Knot section should be correct
            knot = result.matched["knot"]
            assert knot["brand"] == "Zenith"
            assert knot["model"] in ["B21", "B07"]
            assert knot["fiber"] == "Boar"  # Should use strategy default
            assert knot["_matched_by"] == "zenith"

    def test_systems_align_for_zenith(self):
        """Test that both systems produce identical results for Zenith brushes."""
        for test_input in self.test_cases:
            legacy_result = self.legacy_matcher.match(test_input)
            scoring_result = self.scoring_matcher.match(test_input)

            assert legacy_result is not None, f"Legacy should return result for {test_input}"
            assert scoring_result is not None, f"Scoring should return result for {test_input}"

            # Compare top level
            assert legacy_result.matched["brand"] == scoring_result.matched["brand"]
            assert legacy_result.matched["model"] == scoring_result.matched["model"]
            assert legacy_result.matched.get("fiber") == scoring_result.matched.get("fiber")

            # Compare handle sections
            legacy_handle = legacy_result.matched["handle"]
            scoring_handle = scoring_result.matched["handle"]
            assert legacy_handle["brand"] == scoring_handle["brand"]
            assert legacy_handle["model"] == scoring_handle["model"]

            # Compare knot sections
            legacy_knot = legacy_result.matched["knot"]
            scoring_knot = scoring_result.matched["knot"]
            assert legacy_knot["brand"] == scoring_knot["brand"]
            assert legacy_knot["model"] == scoring_knot["model"]
            assert legacy_knot["fiber"] == scoring_knot["fiber"]
            assert legacy_knot["knot_size_mm"] == scoring_knot["knot_size_mm"]

    def test_zenith_strategy_returns_correct_fields(self):
        """Test that ZenithBrushMatchingStrategy returns correct fiber."""
        # Get the ZenithBrushMatchingStrategy from the scoring system
        strategy = self.scoring_matcher.strategy_orchestrator.strategies[7]  # zenith strategy
        result = strategy.match("Zenith Big Scrubby Chrome (B21 28x50mm Boar)")

        assert result is not None
        assert result.matched is not None

        # Strategy should return correct fields
        assert result.matched["brand"] == "Zenith"
        assert result.matched["model"] == "B21"
        assert result.matched.get("fiber") == "Boar"  # Should default to Boar
        assert result.matched.get("knot_size_mm") is None  # Not specified in strategy
