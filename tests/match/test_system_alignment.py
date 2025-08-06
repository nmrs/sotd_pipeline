#!/usr/bin/env python3
"""Tests for system alignment between legacy and scoring brush matchers."""

import pytest
from pathlib import Path

from sotd.match.brush_matcher import BrushMatcher
from sotd.match.scoring_brush_matcher import BrushScoringMatcher
from sotd.match.config import BrushMatcherConfig


class TestSystemAlignment:
    """Test that both systems produce identical results."""

    @pytest.fixture
    def legacy_matcher(self):
        """Create legacy BrushMatcher instance."""
        config = BrushMatcherConfig.create_default()
        return BrushMatcher(config=config)

    @pytest.fixture
    def scoring_matcher(self):
        """Create scoring BrushScoringMatcher instance."""
        return BrushScoringMatcher()

    def test_identical_output_for_simple_brushes(self, legacy_matcher, scoring_matcher):
        """Test that both systems produce identical output for simple brushes."""
        test_cases = [
            "Zenith - r/Wetshaving exclusive MOAR BOAR (31 mm × 57 mm bleached boar)",
            "Declaration Grooming B2 Washington",
            "Simpson Chubby 2 Best Badger",
        ]

        for test_input in test_cases:
            legacy_result = legacy_matcher.match(test_input)
            scoring_result = scoring_matcher.match(test_input)

            # Both should return results
            assert legacy_result is not None, f"Legacy should match: {test_input}"
            assert scoring_result is not None, f"Scoring should match: {test_input}"

            # Compare key fields
            legacy_matched = legacy_result.matched or {}
            scoring_matched = scoring_result.matched or {}

            assert legacy_matched.get("brand") == scoring_matched.get("brand"), f"Brand mismatch for: {test_input}"
            assert legacy_matched.get("model") == scoring_matched.get("model"), f"Model mismatch for: {test_input}"
            assert legacy_matched.get("fiber") == scoring_matched.get("fiber"), f"Fiber mismatch for: {test_input}"

    def test_identical_output_for_composite_brushes(self, legacy_matcher, scoring_matcher):
        """Test that both systems produce identical output for composite brushes."""
        test_cases = [
            "Summer Break Soaps Maize 26mm Timberwolf",
            "Mountain Hare Shaving - Maple Burl and Resin Badger",
            "Maggard 22mm synth",
        ]

        for test_input in test_cases:
            legacy_result = legacy_matcher.match(test_input)
            scoring_result = scoring_matcher.match(test_input)

            # Both should return results
            assert legacy_result is not None, f"Legacy should match: {test_input}"
            assert scoring_result is not None, f"Scoring should match: {test_input}"

            # Compare key fields
            legacy_matched = legacy_result.matched or {}
            scoring_matched = scoring_result.matched or {}

            # For composite brushes, check handle and knot sections
            legacy_handle = legacy_matched.get("handle", {})
            scoring_handle = scoring_matched.get("handle", {})
            legacy_knot = legacy_matched.get("knot", {})
            scoring_knot = scoring_matched.get("knot", {})

            assert legacy_handle.get("brand") == scoring_handle.get("brand"), f"Handle brand mismatch for: {test_input}"
            assert legacy_knot.get("fiber") == scoring_knot.get("fiber"), f"Knot fiber mismatch for: {test_input}"

    def test_identical_output_for_unmatched_brushes(self, legacy_matcher, scoring_matcher):
        """Test that both systems produce identical output for unmatched brushes."""
        test_cases = [
            "NonExistentBrand Brush",
            "Invalid Model Name",
            "",
        ]

        for test_input in test_cases:
            legacy_result = legacy_matcher.match(test_input)
            scoring_result = scoring_matcher.match(test_input)

            # Both should return None for unmatched brushes
            assert legacy_result is None, f"Legacy should not match: {test_input}"
            assert scoring_result is None, f"Scoring should not match: {test_input}"

    def test_identical_structure_for_matched_results(self, legacy_matcher, scoring_matcher):
        """Test that both systems produce identical structure for matched results."""
        test_input = "Declaration Grooming B2 Washington"

        legacy_result = legacy_matcher.match(test_input)
        scoring_result = scoring_matcher.match(test_input)

        # Both should return results
        assert legacy_result is not None
        assert scoring_result is not None

        legacy_matched = legacy_result.matched or {}
        scoring_matched = scoring_result.matched or {}

        # Check that both have the same structure
        assert "handle" in legacy_matched, "Legacy should have handle section"
        assert "handle" in scoring_matched, "Scoring should have handle section"
        assert "knot" in legacy_matched, "Legacy should have knot section"
        assert "knot" in scoring_matched, "Scoring should have knot section"

        # Check handle section structure
        legacy_handle = legacy_matched["handle"]
        scoring_handle = scoring_matched["handle"]
        assert "brand" in legacy_handle, "Legacy handle should have brand"
        assert "brand" in scoring_handle, "Scoring handle should have brand"
        assert "model" in legacy_handle, "Legacy handle should have model"
        assert "model" in scoring_handle, "Scoring handle should have model"

        # Check knot section structure
        legacy_knot = legacy_matched["knot"]
        scoring_knot = scoring_matched["knot"]
        assert "brand" in legacy_knot, "Legacy knot should have brand"
        assert "brand" in scoring_knot, "Scoring knot should have brand"
        assert "fiber" in legacy_knot, "Legacy knot should have fiber"
        assert "fiber" in scoring_knot, "Scoring knot should have fiber"

    def test_performance_comparison(self, legacy_matcher, scoring_matcher):
        """Test that both systems have acceptable performance."""
        test_input = "Declaration Grooming B2 Washington"

        # Test legacy system performance
        import time
        start_time = time.time()
        for _ in range(100):
            legacy_result = legacy_matcher.match(test_input)
        legacy_time = time.time() - start_time

        # Test scoring system performance
        start_time = time.time()
        for _ in range(100):
            scoring_result = scoring_matcher.match(test_input)
        scoring_time = time.time() - start_time

        # Both should complete in reasonable time
        assert legacy_time < 1.0, f"Legacy system too slow: {legacy_time:.3f}s"
        assert scoring_time < 1.0, f"Scoring system too slow: {scoring_time:.3f}s"

        # Results should be identical
        assert legacy_result is not None
        assert scoring_result is not None
        assert legacy_result.matched.get("brand") == scoring_result.matched.get("brand")

    def test_edge_cases_identical_behavior(self, legacy_matcher, scoring_matcher):
        """Test that both systems handle edge cases identically."""
        edge_cases = [
            None,  # None input
            "",    # Empty string
            "   ", # Whitespace only
            "A" * 1000,  # Very long string
        ]

        for test_input in edge_cases:
            legacy_result = legacy_matcher.match(test_input)
            scoring_result = scoring_matcher.match(test_input)

            # Both should handle edge cases the same way
            if legacy_result is None:
                assert scoring_result is None, f"Scoring should return None for: {test_input}"
            else:
                assert scoring_result is not None, f"Scoring should return result for: {test_input}"


if __name__ == "__main__":
    pytest.main([__file__]) 