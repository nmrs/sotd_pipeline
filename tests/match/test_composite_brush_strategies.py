#!/usr/bin/env python3
"""Tests for composite brush wrapper strategies."""

import pytest
from sotd.match.brush_matching_strategies.legacy_composite_wrapper_strategies import (
    LegacyDualComponentWrapperStrategy,
    LegacySingleComponentFallbackWrapperStrategy,
)


class TestLegacyDualComponentWrapperStrategy:
    """Test the legacy dual component wrapper strategy."""

    def setup_method(self):
        """Set up test fixtures."""
        self.strategy = LegacyDualComponentWrapperStrategy()

    def test_dual_component_matching(self):
        """Test dual component matching with composite brush."""
        # Test with "Summer Break Soaps Maize 26mm Timberwolf"
        result = self.strategy.match("Summer Break Soaps Maize 26mm Timberwolf")

        # Should return a composite brush result
        assert result is not None
        assert result["match_type"] == "composite"
        assert result["matched"]["brand"] is None  # Composite brush
        assert result["matched"]["model"] is None  # Composite brush
        assert "handle" in result["matched"]
        assert "knot" in result["matched"]

        # Handle section should contain Summer Break info
        handle = result["matched"]["handle"]
        assert handle["brand"] == "Summer Break"
        assert handle["_matched_by"] == "HandleMatcher"

        # Knot section should contain Generic Timberwolf info
        knot = result["matched"]["knot"]
        assert knot["brand"] == "Generic"
        assert knot["model"] == "Timberwolf"
        assert knot["_matched_by"] == "KnotMatcher"

    def test_no_dual_component_match(self):
        """Test when no dual component match is found."""
        # Test with simple brush that doesn't have both handle and knot
        result = self.strategy.match("Declaration B2")

        # Should return None (no composite brush)
        assert result is None

    def test_empty_input(self):
        """Test with empty input."""
        result = self.strategy.match("")
        assert result is None

    def test_none_input(self):
        """Test with None input."""
        result = self.strategy.match(None)  # type: ignore
        assert result is None


class TestLegacySingleComponentFallbackWrapperStrategy:
    """Test the legacy single component fallback wrapper strategy."""

    def setup_method(self):
        """Set up test fixtures."""
        self.strategy = LegacySingleComponentFallbackWrapperStrategy()

    def test_handle_only_matching(self):
        """Test handle-only matching."""
        # Test with handle-only input
        result = self.strategy.match("Summer Break Handle")

        # Should return a composite brush result with handle only
        assert result is not None
        assert result["match_type"] == "single_component"
        assert result["matched"]["brand"] is None  # Composite brush
        assert result["matched"]["model"] is None  # Composite brush
        assert "handle" in result["matched"]
        assert "knot" in result["matched"]

        # Handle section should contain Summer Break info
        handle = result["matched"]["handle"]
        assert handle["brand"] == "Summer Break"
        assert handle["_matched_by"] == "HandleMatcher"

        # Knot section should be empty
        knot = result["matched"]["knot"]
        assert knot["brand"] is None
        assert knot["model"] is None

    def test_knot_only_matching(self):
        """Test knot-only matching."""
        # Test with knot-only input
        result = self.strategy.match("Generic Timberwolf")

        # Should return a composite brush result with knot only
        assert result is not None
        assert result["match_type"] == "single_component"
        assert result["matched"]["brand"] is None  # Composite brush
        assert result["matched"]["model"] is None  # Composite brush
        assert "handle" in result["matched"]
        assert "knot" in result["matched"]

        # Handle section should be empty
        handle = result["matched"]["handle"]
        assert handle["brand"] is None
        assert handle["model"] is None

        # Knot section should contain Generic Timberwolf info
        knot = result["matched"]["knot"]
        assert knot["brand"] == "Generic"
        assert knot["model"] == "Timberwolf"
        assert knot["_matched_by"] == "KnotMatcher"

    def test_no_single_component_match(self):
        """Test when no single component match is found."""
        # Test with input that doesn't match handle or knot
        result = self.strategy.match("Unknown Brush XYZ")

        # Should return None
        assert result is None

    def test_empty_input(self):
        """Test with empty input."""
        result = self.strategy.match("")
        assert result is None

    def test_none_input(self):
        """Test with None input."""
        result = self.strategy.match(None)  # type: ignore
        assert result is None
