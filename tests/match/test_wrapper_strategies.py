"""
Tests for wrapper strategies that call legacy methods exactly.

These tests verify that wrapper strategies correctly call legacy methods
and return results that can be scored by the scoring engine.
"""

from unittest.mock import Mock

from sotd.match.types import MatchResult
from sotd.match.brush_matcher import BrushMatcher


class TestWrapperStrategies:
    """Test wrapper strategies for legacy method calls."""

    def setup_method(self):
        """Set up test fixtures."""
        # Create mock legacy matcher
        self.legacy_matcher = Mock(spec=BrushMatcher)

        # Mock legacy method results
        self.mock_complete_brush_result = MatchResult(
            original="Simpson Chubby 2",
            matched={
                "brand": "Simpson",
                "model": "Chubby 2",
                "fiber": "badger",
                "knot_size_mm": 26.0,
            },
            match_type="regex",
            pattern="simpson.*chubby",
        )

        self.mock_dual_component_result = MatchResult(
            original="Chisel & Hound 'The Duke' / Omega 10098 Boar",
            matched={
                "brand": None,
                "model": None,
                "handle": {"brand": "Chisel & Hound", "model": "The Duke"},
                "knot": {"brand": "Omega", "model": "10098", "fiber": "boar"},
            },
            match_type="regex",
            pattern="dual_component",
        )

    def test_correct_complete_brush_wrapper_strategy(self):
        """Test CorrectCompleteBrushWrapperStrategy calls legacy method correctly."""
        from sotd.match.brush_matching_strategies.correct_matches_wrapper_strategies import (
            CorrectCompleteBrushWrapperStrategy,
        )

        # Setup mock legacy method
        self.legacy_matcher._match_correct_complete_brush.return_value = (
            self.mock_complete_brush_result
        )

        # Create wrapper strategy
        strategy = CorrectCompleteBrushWrapperStrategy(self.legacy_matcher)

        # Test strategy call
        result = strategy.match("Simpson Chubby 2")

        # Verify legacy method was called
        self.legacy_matcher._match_correct_complete_brush.assert_called_once_with(
            "Simpson Chubby 2"
        )

        # Verify result is returned unchanged
        assert result == self.mock_complete_brush_result

    def test_correct_split_brush_wrapper_strategy(self):
        """Test CorrectSplitBrushWrapperStrategy calls legacy method correctly."""
        from sotd.match.brush_matching_strategies.correct_matches_wrapper_strategies import (
            CorrectSplitBrushWrapperStrategy,
        )

        # Setup mock legacy method
        self.legacy_matcher._match_correct_split_brush.return_value = (
            self.mock_dual_component_result
        )

        # Create wrapper strategy
        strategy = CorrectSplitBrushWrapperStrategy(self.legacy_matcher)

        # Test strategy call
        result = strategy.match("Chisel & Hound 'The Duke' / Omega 10098 Boar")

        # Verify legacy method was called
        self.legacy_matcher._match_correct_split_brush.assert_called_once_with(
            "Chisel & Hound 'The Duke' / Omega 10098 Boar"
        )

        # Verify result is returned unchanged
        assert result == self.mock_dual_component_result

    def test_known_split_wrapper_strategy(self):
        """Test KnownSplitWrapperStrategy calls legacy method correctly."""
        from sotd.match.brush_matching_strategies.known_split_wrapper_strategy import (
            KnownSplitWrapperStrategy,
        )

        # Setup mock legacy method
        self.legacy_matcher._match_known_split.return_value = self.mock_dual_component_result

        # Create wrapper strategy
        strategy = KnownSplitWrapperStrategy(self.legacy_matcher)

        # Test strategy call
        result = strategy.match("Chisel & Hound 'The Duke' / Omega 10098 Boar")

        # Verify legacy method was called
        self.legacy_matcher._match_known_split.assert_called_once_with(
            "Chisel & Hound 'The Duke' / Omega 10098 Boar"
        )

        # Verify result is returned unchanged
        assert result == self.mock_dual_component_result

    def test_high_priority_automated_split_wrapper_strategy(self):
        """Test HighPriorityAutomatedSplitWrapperStrategy calls legacy method correctly."""
        from sotd.match.brush_matching_strategies.automated_split_wrapper_strategies import (
            HighPriorityAutomatedSplitWrapperStrategy,
        )

        # Setup mock legacy method
        self.legacy_matcher._match_high_priority_automated_split.return_value = (
            self.mock_dual_component_result
        )

        # Create wrapper strategy
        strategy = HighPriorityAutomatedSplitWrapperStrategy(self.legacy_matcher)

        # Test strategy call
        result = strategy.match("Chisel & Hound 'The Duke' / Omega 10098 Boar")

        # Verify legacy method was called
        self.legacy_matcher._match_high_priority_automated_split.assert_called_once_with(
            "Chisel & Hound 'The Duke' / Omega 10098 Boar"
        )

        # Verify result is returned unchanged
        assert result == self.mock_dual_component_result

    def test_complete_brush_wrapper_strategy(self):
        """Test CompleteBrushWrapperStrategy calls legacy method correctly."""
        from sotd.match.brush_matching_strategies.complete_brush_wrapper_strategy import (
            CompleteBrushWrapperStrategy,
        )

        # Setup mock legacy method
        self.legacy_matcher._match_complete_brush.return_value = self.mock_complete_brush_result

        # Create wrapper strategy
        strategy = CompleteBrushWrapperStrategy(self.legacy_matcher)

        # Test strategy call
        result = strategy.match("Simpson Chubby 2")

        # Verify legacy method was called
        self.legacy_matcher._match_complete_brush.assert_called_once_with("Simpson Chubby 2")

        # Verify result is returned unchanged
        assert result == self.mock_complete_brush_result

    def test_dual_component_wrapper_strategy(self):
        """Test DualComponentWrapperStrategy calls legacy method correctly."""
        from sotd.match.brush_matching_strategies.legacy_composite_wrapper_strategies import (
            LegacyDualComponentWrapperStrategy,
        )

        # Setup mock legacy method
        self.legacy_matcher._match_dual_component.return_value = self.mock_dual_component_result

        # Create wrapper strategy
        strategy = LegacyDualComponentWrapperStrategy(self.legacy_matcher)

        # Test strategy call
        result = strategy.match("Chisel & Hound 'The Duke' / Omega 10098 Boar")

        # Verify legacy method was called
        self.legacy_matcher._match_dual_component.assert_called_once_with(
            "Chisel & Hound 'The Duke' / Omega 10098 Boar"
        )

        # Verify result is returned unchanged
        assert result == self.mock_dual_component_result

    def test_medium_priority_automated_split_wrapper_strategy(self):
        """Test MediumPriorityAutomatedSplitWrapperStrategy calls legacy method correctly."""
        from sotd.match.brush_matching_strategies.automated_split_wrapper_strategies import (
            MediumPriorityAutomatedSplitWrapperStrategy,
        )

        # Setup mock legacy method
        self.legacy_matcher._match_medium_priority_automated_split.return_value = (
            self.mock_dual_component_result
        )

        # Create wrapper strategy
        strategy = MediumPriorityAutomatedSplitWrapperStrategy(self.legacy_matcher)

        # Test strategy call
        result = strategy.match("Chisel & Hound 'The Duke' / Omega 10098 Boar")

        # Verify legacy method was called
        self.legacy_matcher._match_medium_priority_automated_split.assert_called_once_with(
            "Chisel & Hound 'The Duke' / Omega 10098 Boar"
        )

        # Verify result is returned unchanged
        assert result == self.mock_dual_component_result

    def test_single_component_fallback_wrapper_strategy(self):
        """Test SingleComponentFallbackWrapperStrategy calls legacy method correctly."""
        from sotd.match.brush_matching_strategies.legacy_composite_wrapper_strategies import (
            LegacySingleComponentFallbackWrapperStrategy,
        )

        # Setup mock legacy method
        self.legacy_matcher._match_single_component_fallback.return_value = (
            self.mock_complete_brush_result
        )

        # Create wrapper strategy
        strategy = LegacySingleComponentFallbackWrapperStrategy(self.legacy_matcher)

        # Test strategy call
        result = strategy.match("Simpson Chubby 2")

        # Verify legacy method was called
        self.legacy_matcher._match_single_component_fallback.assert_called_once_with(
            "Simpson Chubby 2"
        )

        # Verify result is returned unchanged
        assert result == self.mock_complete_brush_result

    def test_wrapper_strategies_return_none_when_legacy_returns_none(self):
        """Test wrapper strategies return None when legacy methods return None."""
        from sotd.match.brush_matching_strategies.correct_matches_wrapper_strategies import (
            CorrectCompleteBrushWrapperStrategy,
        )

        # Setup mock legacy method to return None
        self.legacy_matcher._match_correct_complete_brush.return_value = None

        # Create wrapper strategy
        strategy = CorrectCompleteBrushWrapperStrategy(self.legacy_matcher)

        # Test strategy call
        result = strategy.match("Unmatched Brush")

        # Verify legacy method was called
        self.legacy_matcher._match_correct_complete_brush.assert_called_once_with("Unmatched Brush")

        # Verify result is None
        assert result is None

    def test_wrapper_strategies_preserve_legacy_result_structure(self):
        """Test wrapper strategies preserve exact legacy result structure."""
        from sotd.match.brush_matching_strategies.correct_matches_wrapper_strategies import (
            CorrectCompleteBrushWrapperStrategy,
        )

        # Create complex legacy result with nested structure
        complex_result = MatchResult(
            original="Complex Brush Input",
            matched={
                "brand": None,
                "model": None,
                "handle": {
                    "brand": "Handle Brand",
                    "model": "Handle Model",
                    "_matched_by_section": "artisan_handles",
                },
                "knot": {
                    "brand": "Knot Brand",
                    "model": "Knot Model",
                    "fiber": "badger",
                    "_matched_by_section": "known_knots",
                },
            },
            match_type="regex",
            pattern="complex_pattern",
        )

        # Setup mock legacy method
        self.legacy_matcher._match_correct_complete_brush.return_value = complex_result

        # Create wrapper strategy
        strategy = CorrectCompleteBrushWrapperStrategy(self.legacy_matcher)

        # Test strategy call
        result = strategy.match("Complex Brush Input")

        # Verify result structure is preserved exactly
        assert result == complex_result
        assert result.matched["handle"]["_matched_by_section"] == "artisan_handles"
        assert result.matched["knot"]["_matched_by_section"] == "known_knots"
