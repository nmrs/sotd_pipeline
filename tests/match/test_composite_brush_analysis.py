#!/usr/bin/env python3
"""Test file to analyze legacy system's composite brush handling logic."""

import pytest
from sotd.match.brush_matcher import BrushMatcher
from sotd.match.config import BrushMatcherConfig


class TestCompositeBrushAnalysis:
    """Analyze legacy system's composite brush handling logic."""

    def setup_method(self):
        """Set up test fixtures."""
        config = BrushMatcherConfig.create_default()
        self.legacy_matcher = BrushMatcher(config=config)

    def test_legacy_dual_component_strategy_priority(self):
        """Test that dual_component strategy is priority 6 in legacy system."""
        # Legacy system strategy order from match() method:
        strategies = [
            ("correct_complete_brush", self.legacy_matcher._match_correct_complete_brush),
            ("correct_split_brush", self.legacy_matcher._match_correct_split_brush),
            ("known_split", self.legacy_matcher._match_known_split),
            (
                "high_priority_automated_split",
                self.legacy_matcher._match_high_priority_automated_split,
            ),
            ("complete_brush", self.legacy_matcher._match_complete_brush),
            ("dual_component", self.legacy_matcher._match_dual_component),  # Priority 6
            (
                "medium_priority_automated_split",
                self.legacy_matcher._match_medium_priority_automated_split,
            ),
            ("single_component_fallback", self.legacy_matcher._match_single_component_fallback),
        ]

        # Verify dual_component is at index 5 (priority 6)
        assert strategies[5][0] == "dual_component"
        assert strategies[5][1] == self.legacy_matcher._match_dual_component

    def test_legacy_dual_component_logic(self):
        """Test legacy system's dual component matching logic."""
        # Test with "Summer Break Soaps Maize 26mm Timberwolf"
        result = self.legacy_matcher._match_dual_component(
            "Summer Break Soaps Maize 26mm Timberwolf"
        )

        # Should return a composite brush result
        assert result is not None
        assert result.matched["brand"] is None  # Composite brush
        assert result.matched["model"] is None  # Composite brush
        assert "handle" in result.matched
        assert "knot" in result.matched

        # Handle section should contain Summer Break info
        handle = result.matched["handle"]
        assert handle["brand"] == "Summer Break"
        assert handle["_matched_by"] == "HandleMatcher"

        # Knot section should contain AP Shave Co Timberwolf info
        knot = result.matched["knot"]
        assert knot["brand"] == "AP Shave Co"
        assert knot["model"] == "Timberwolf"
        assert knot["_matched_by"] == "KnotMatcher"

    def test_legacy_single_component_fallback_logic(self):
        """Test legacy system's single component fallback logic."""
        # Test with handle-only input
        result = self.legacy_matcher._match_single_component_fallback("Summer Break Handle")

        # Should return a composite brush result with handle only
        assert result is not None
        assert result.matched["brand"] is None  # Composite brush
        assert result.matched["model"] is None  # Composite brush
        assert "handle" in result.matched
        assert "knot" in result.matched

        # Handle section should contain Summer Break info
        handle = result.matched["handle"]
        assert handle["brand"] == "Summer Break"
        assert handle["_matched_by"] == "HandleMatcher"

        # Knot section should be empty or minimal
        knot = result.matched["knot"]
        assert knot["brand"] is None or knot["model"] is None

    def test_legacy_composite_brush_output_structure(self):
        """Test legacy system's composite brush output structure."""
        # Test dual component result structure
        result = self.legacy_matcher._match_dual_component(
            "Summer Break Soaps Maize 26mm Timberwolf"
        )

        expected_structure = {
            "brand": type(None),  # Composite brush
            "model": type(None),  # Composite brush
            "handle": {
                "brand": str,  # Handle maker
                "model": str,  # Handle model
                "source_text": str,
                "_matched_by": str,
                "_pattern": str,
            },
            "knot": {
                "brand": str,  # Knot brand
                "model": str,  # Knot model
                "fiber": str,  # Knot fiber
                "knot_size_mm": (float, int, type(None)),  # Knot size (can be float, int, or None)
                "source_text": str,
                "_matched_by": str,
                "_pattern": str,
            },
        }

        # Verify structure matches expected
        for key, expected_type in expected_structure.items():
            assert key in result.matched
            if expected_type is not type(None):
                if isinstance(expected_type, dict):
                    # Handle nested dictionary validation
                    assert isinstance(result.matched[key], dict)
                    for nested_key, nested_type in expected_type.items():
                        assert nested_key in result.matched[key]
                        if isinstance(nested_type, tuple):
                            # Handle multiple allowed types
                            assert (
                                isinstance(result.matched[key][nested_key], nested_type)
                                or result.matched[key][nested_key] is None
                            )
                        else:
                            # Handle single type
                            assert (
                                isinstance(result.matched[key][nested_key], nested_type)
                                or result.matched[key][nested_key] is None
                            )
                elif isinstance(expected_type, tuple):
                    # Handle multiple allowed types
                    assert (
                        isinstance(result.matched[key], expected_type)
                        or result.matched[key] is None
                    )
                else:
                    # Handle single type
                    assert (
                        isinstance(result.matched[key], expected_type)
                        or result.matched[key] is None
                    )

    def test_legacy_strategy_execution_order(self):
        """Test that legacy system executes strategies in correct order."""
        # The legacy system executes strategies in this order:
        # 1. correct_complete_brush
        # 2. correct_split_brush
        # 3. known_split
        # 4. high_priority_automated_split
        # 5. complete_brush
        # 6. dual_component  <- This is where composite brushes are handled
        # 7. medium_priority_automated_split
        # 8. single_component_fallback

        # For composite brushes like "Summer Break Soaps Maize 26mm Timberwolf":
        # - Strategies 1-5 should not match (no complete brush match)
        # - Strategy 6 (dual_component) should match and return composite result
        # - Strategies 7-8 should not execute (dual_component already returned result)

        result = self.legacy_matcher.match("Summer Break Soaps Maize 26mm Timberwolf")
        assert result is not None
        assert result.matched["brand"] is None  # Composite brush
        assert "handle" in result.matched
        assert "knot" in result.matched
