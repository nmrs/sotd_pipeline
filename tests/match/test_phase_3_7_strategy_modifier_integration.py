"""
Tests for Phase 3.7: Strategy Modifier Integration.

This module tests the implementation of strategy-specific modifiers
that can adjust scores based on input characteristics.
"""

from unittest.mock import Mock

from sotd.match.brush_scoring_components.scoring_engine import ScoringEngine
from sotd.match.brush_scoring_config import BrushScoringConfig
from sotd.match.types import MatchResult


class TestStrategyModifierIntegration:
    """Test strategy modifier integration in scoring engine."""

    def setup_method(self):
        """Set up test fixtures."""
        self.config = Mock(spec=BrushScoringConfig)
        self.scoring_engine = ScoringEngine(self.config)

    def test_modifier_framework_calls_modifier_functions(self):
        """Test that modifier framework calls modifier functions."""
        # Setup mock config
        self.config.get_base_strategy_score.return_value = 70.0
        self.config.get_all_modifier_names.return_value = ["multiple_brands", "fiber_words"]
        self.config.get_strategy_modifier.side_effect = lambda strategy, modifier: {
            "multiple_brands": -5.0,
            "fiber_words": 3.0,
        }[modifier]

        # Create test result
        result = MatchResult(
            original="Simpson Chubby 2 / Omega 10098 Badger",
            matched={"brand": "Simpson", "model": "Chubby 2"},
            match_type="regex",
            pattern="simpson.*chubby",
            strategy="automated_split",
        )

        # Calculate score with modifiers
        score = self.scoring_engine._calculate_score(
            result, "Simpson Chubby 2 / Omega 10098 Badger"
        )

        # Verify modifier functions were called
        self.config.get_all_modifier_names.assert_called_with("automated_split")
        assert self.config.get_strategy_modifier.call_count == 2

        # Verify final score (multiple brands detected, fiber words detected)
        assert score == 68.0  # 70.0 - 5.0 + 3.0

    def test_multiple_brands_modifier_penalty(self):
        """Test multiple brands modifier applies penalty for multiple brand mentions."""
        # Setup mock config
        self.config.get_base_strategy_score.return_value = 70.0
        self.config.get_all_modifier_names.return_value = ["multiple_brands"]
        self.config.get_strategy_modifier.return_value = -5.0

        # Create test result
        result = MatchResult(
            original="Simpson Chubby 2 / Omega 10098",
            matched={"brand": "Simpson", "model": "Chubby 2"},
            match_type="regex",
            pattern="simpson.*chubby",
            strategy="automated_split",
        )

        # Calculate score
        score = self.scoring_engine._calculate_score(result, "Simpson Chubby 2 / Omega 10098")

        # Should have base score minus penalty
        assert score == 65.0  # 70.0 - 5.0

    def test_fiber_words_modifier_bonus(self):
        """Test fiber words modifier applies bonus for fiber-specific terminology."""
        # Setup mock config
        self.config.get_base_strategy_score.return_value = 70.0
        self.config.get_all_modifier_names.return_value = ["fiber_words"]
        self.config.get_strategy_modifier.return_value = 3.0

        # Create test result
        result = MatchResult(
            original="Badger brush with synthetic knot",
            matched={"brand": "Generic", "model": "Brush"},
            match_type="regex",
            pattern="badger.*brush",
            strategy="automated_split",
        )

        # Calculate score
        score = self.scoring_engine._calculate_score(result, "Badger brush with synthetic knot")

        # Should have base score plus bonus
        assert score == 73.0  # 70.0 + 3.0

    def test_size_specification_modifier_bonus(self):
        """Test size specification modifier applies bonus for size specifications."""
        # Setup mock config
        self.config.get_base_strategy_score.return_value = 70.0
        self.config.get_all_modifier_names.return_value = ["size_specification"]
        self.config.get_strategy_modifier.return_value = 2.0

        # Create test result
        result = MatchResult(
            original="26mm brush",
            matched={"brand": "Generic", "model": "Brush"},
            match_type="regex",
            pattern="26mm.*brush",
            strategy="automated_split",
        )

        # Calculate score
        score = self.scoring_engine._calculate_score(result, "26mm brush")

        # Should have base score plus bonus
        assert score == 72.0  # 70.0 + 2.0

    def test_delimiter_confidence_modifier_bonus(self):
        """Test delimiter confidence modifier applies bonus for high-confidence delimiters."""
        # Setup mock config
        self.config.get_base_strategy_score.return_value = 70.0
        self.config.get_all_modifier_names.return_value = ["delimiter_confidence"]
        self.config.get_strategy_modifier.return_value = 4.0

        # Create test result
        result = MatchResult(
            original="Handle w/ knot",
            matched={"brand": "Generic", "model": "Brush"},
            match_type="regex",
            pattern="handle.*w/.*knot",
            strategy="automated_split",
        )

        # Calculate score
        score = self.scoring_engine._calculate_score(result, "Handle w/ knot")

        # Should have base score plus bonus
        assert score == 74.0  # 70.0 + 4.0

    def test_multiple_modifiers_combined(self):
        """Test that multiple modifiers are combined correctly."""
        # Setup mock config
        self.config.get_base_strategy_score.return_value = 70.0
        self.config.get_all_modifier_names.return_value = [
            "multiple_brands",
            "fiber_words",
            "size_specification",
        ]
        self.config.get_strategy_modifier.side_effect = lambda strategy, modifier: {
            "multiple_brands": -5.0,
            "fiber_words": 3.0,
            "size_specification": 2.0,
        }[modifier]

        # Create test result
        result = MatchResult(
            original="Simpson Chubby 2 / Omega 10098 26mm Badger",
            matched={"brand": "Simpson", "model": "Chubby 2"},
            match_type="regex",
            pattern="simpson.*chubby",
            strategy="automated_split",
        )

        # Calculate score
        score = self.scoring_engine._calculate_score(
            result, "Simpson Chubby 2 / Omega 10098 26mm Badger"
        )

        # Should have base score plus all modifiers
        assert score == 70.0  # 70.0 - 5.0 + 3.0 + 2.0

    def test_modifier_functions_are_strategy_aware(self):
        """Test that modifier functions receive correct strategy name."""
        # Setup mock config
        self.config.get_base_strategy_score.return_value = 70.0
        self.config.get_all_modifier_names.return_value = ["multiple_brands"]
        self.config.get_strategy_modifier.return_value = -5.0

        # Create test result with specific strategy
        result = MatchResult(
            original="Test brush",
            matched={"brand": "Test", "model": "Brush"},
            match_type="regex",
            pattern="test.*brush",
            strategy="dual_component",
        )

        # Calculate score
        self.scoring_engine._calculate_score(result, "Test brush")

        # Verify strategy name was passed to modifier functions
        self.config.get_all_modifier_names.assert_called_with("dual_component")
        self.config.get_strategy_modifier.assert_called_with("dual_component", "multiple_brands")

    def test_modifier_functions_handle_empty_modifiers(self):
        """Test that modifier functions handle empty modifier lists."""
        # Setup mock config with no modifiers
        self.config.get_base_strategy_score.return_value = 70.0
        self.config.get_all_modifier_names.return_value = []

        # Create test result
        result = MatchResult(
            original="Test brush",
            matched={"brand": "Test", "model": "Brush"},
            match_type="regex",
            pattern="test.*brush",
            strategy="automated_split",
        )

        # Calculate score
        score = self.scoring_engine._calculate_score(result, "Test brush")

        # Should have base score only
        assert score == 70.0

    def test_modifier_functions_handle_unknown_strategy(self):
        """Test that modifier functions handle unknown strategy names."""
        # Setup mock config
        self.config.get_base_strategy_score.return_value = 70.0
        self.config.get_all_modifier_names.return_value = []

        # Create test result with unknown strategy
        result = MatchResult(
            original="Test brush",
            matched={"brand": "Test", "model": "Brush"},
            match_type="unknown",
            pattern="test.*brush",
            strategy="unknown_strategy",
        )

        # Calculate score
        score = self.scoring_engine._calculate_score(result, "Test brush")

        # Should handle gracefully
        assert score == 70.0

    def test_modifier_functions_preserve_base_score(self):
        """Test that modifier functions preserve base score when no modifiers apply."""
        # Setup mock config
        self.config.get_base_strategy_score.return_value = 75.0
        self.config.get_all_modifier_names.return_value = ["multiple_brands"]
        self.config.get_strategy_modifier.return_value = 0.0  # No modifier effect

        # Create test result
        result = MatchResult(
            original="Simple brush",
            matched={"brand": "Simple", "model": "Brush"},
            match_type="regex",
            pattern="simple.*brush",
            strategy="complete_brush",
        )

        # Calculate score
        score = self.scoring_engine._calculate_score(result, "Simple brush")

        # Should preserve base score
        assert score == 75.0

    def test_modifier_functions_with_negative_base_score(self):
        """Test that modifier functions work correctly with negative modifiers."""
        # Setup mock config
        self.config.get_base_strategy_score.return_value = 70.0
        self.config.get_all_modifier_names.return_value = ["multiple_brands"]
        self.config.get_strategy_modifier.return_value = -10.0  # Large penalty

        # Create test result
        result = MatchResult(
            original="Simpson Chubby 2 / Omega 10098",
            matched={"brand": "Brand1", "model": "Brush"},
            match_type="regex",
            pattern="brand1.*brush",
            strategy="automated_split",
        )

        # Calculate score
        score = self.scoring_engine._calculate_score(result, "Simpson Chubby 2 / Omega 10098")

        # Should have base score minus penalty (multiple brands detected)
        assert score == 60.0  # 70.0 - 10.0

    def test_modifier_functions_with_large_bonus(self):
        """Test that modifier functions work correctly with large bonuses."""
        # Setup mock config
        self.config.get_base_strategy_score.return_value = 70.0
        self.config.get_all_modifier_names.return_value = ["fiber_words"]
        self.config.get_strategy_modifier.return_value = 15.0  # Large bonus

        # Create test result
        result = MatchResult(
            original="Badger brush",
            matched={"brand": "Generic", "model": "Brush"},
            match_type="regex",
            pattern="badger.*brush",
            strategy="automated_split",
        )

        # Calculate score
        score = self.scoring_engine._calculate_score(result, "Badger brush")

        # Should have base score plus bonus
        assert score == 85.0  # 70.0 + 15.0


class TestModifierConfiguration:
    """Test modifier configuration integration."""

    def test_yaml_configuration_with_modifiers(self):
        """Test that YAML configuration supports modifier weights."""
        config = BrushScoringConfig()

        # Verify modifier structure exists
        assert "strategy_modifiers" in config.weights

        # Verify specific strategies have modifiers
        automated_split_modifiers = config.weights["strategy_modifiers"].get(
            "automated_split", {}
        )
        assert "multiple_brands" in automated_split_modifiers
        assert "fiber_words" in automated_split_modifiers
        assert "size_specification" in automated_split_modifiers
        assert "handle_confidence" in automated_split_modifiers
        assert "knot_confidence" in automated_split_modifiers
        assert "word_count_balance" in automated_split_modifiers

    def test_modifier_weights_are_configurable(self):
        """Test that modifier weights can be configured via YAML."""
        config = BrushScoringConfig()

        # Get modifier weights for a strategy
        dual_component_modifiers = config.weights["strategy_modifiers"].get("dual_component", {})

        # Verify weights are numeric
        for modifier_name, weight in dual_component_modifiers.items():
            assert isinstance(
                weight, (int, float)
            ), f"Modifier {modifier_name} weight should be numeric"

    def test_all_strategies_have_modifier_support(self):
        """Test that all strategies support modifiers."""
        config = BrushScoringConfig()

        # Get all strategy names
        strategy_names = config.get_all_strategy_names()

        # Verify each strategy has modifier support
        for strategy_name in strategy_names:
            modifier_names = config.get_all_modifier_names(strategy_name)
            assert isinstance(
                modifier_names, list
            ), f"Strategy {strategy_name} should have modifier list"

    def test_modifier_names_are_consistent(self):
        """Test that modifier names are consistent across strategies."""
        config = BrushScoringConfig()

        # Get modifier names for different strategies
        high_priority_modifiers = config.get_all_modifier_names("automated_split")
        medium_priority_modifiers = config.get_all_modifier_names("medium_priority_automated_split")

        # Verify common modifiers exist
        common_modifiers = ["multiple_brands", "fiber_words", "size_specification"]
        for modifier in common_modifiers:
            assert modifier in high_priority_modifiers, f"High priority should have {modifier}"
            assert modifier in medium_priority_modifiers, f"Medium priority should have {modifier}"


class TestModifierIntegrationWithScoringEngine:
    """Test modifier integration with the full scoring engine."""

    def setup_method(self):
        """Set up test fixtures."""
        self.config = BrushScoringConfig()
        self.scoring_engine = ScoringEngine(self.config)

    def test_scoring_engine_applies_modifiers_to_results(self):
        """Test that scoring engine applies modifiers when scoring results."""
        # Create test results
        results = [
            MatchResult(
                original="Test brush",
                matched={"brand": "Test", "model": "Brush"},
                match_type="regex",
                pattern="test.*brush",
                strategy="automated_split",
            ),
            MatchResult(
                original="Another brush",
                matched={"brand": "Another", "model": "Brush"},
                match_type="regex",
                pattern="another.*brush",
                strategy="complete_brush",
            ),
        ]

        # Score results
        scored_results = self.scoring_engine.score_results(results, "Test brush")

        # Verify all results have scores
        for result in scored_results:
            assert hasattr(result, "score"), "Result should have score attribute"
            assert isinstance(result.score, (int, float)), "Score should be numeric"

    def test_scoring_engine_preserves_result_order_with_modifiers(self):
        """Test that scoring engine preserves result order when applying modifiers."""
        # Create test results with different base scores
        results = [
            MatchResult(
                original="High priority brush",
                matched={"brand": "High", "model": "Priority"},
                match_type="regex",
                pattern="high.*priority",
                strategy="automated_split",
            ),
            MatchResult(
                original="Complete brush",
                matched={"brand": "Complete", "model": "Brush"},
                match_type="regex",
                pattern="complete.*brush",
                strategy="complete_brush",
            ),
        ]

        # Score results
        scored_results = self.scoring_engine.score_results(results, "Test input")

        # Verify order is preserved
        assert len(scored_results) == 2
        assert scored_results[0].strategy == "automated_split"
        assert scored_results[1].strategy == "complete_brush"

    def test_scoring_engine_handles_empty_results_with_modifiers(self):
        """Test that scoring engine handles empty results when modifiers are enabled."""
        # Create empty results list
        results = []

        # Score results
        scored_results = self.scoring_engine.score_results(results, "Test input")

        # Should return empty list
        assert scored_results == []

    def test_scoring_engine_handles_none_matched_with_modifiers(self):
        """Test that scoring engine handles results with None matched when modifiers are enabled."""
        # Create result with None matched
        results = [
            MatchResult(
                original="No match",
                matched=None,
                match_type=None,
                pattern=None,
                strategy="automated_split",
            ),
        ]

        # Score results
        scored_results = self.scoring_engine.score_results(results, "Test input")

        # Should handle gracefully
        assert len(scored_results) == 1
        assert scored_results[0].matched is None
