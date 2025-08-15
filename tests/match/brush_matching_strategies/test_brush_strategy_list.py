"""
Tests for Brush Strategy List Updates.

This test file tests that the complete_brush wrapper is removed and individual strategies are added.
"""


class TestBrushStrategyList:
    """Test brush strategy list updates."""

    def test_complete_brush_wrapper_removed_from_strategy_list(self):
        """Test that complete_brush wrapper is removed from strategy list."""
        from sotd.match.scoring_brush_matcher import BrushScoringMatcher

        matcher = BrushScoringMatcher()
        strategies = matcher._create_strategies()

        # Get strategy names
        strategy_names = [type(strategy).__name__ for strategy in strategies]

        # Check that CompleteBrushWrapperStrategy is not in the list
        assert (
            "CompleteBrushWrapperStrategy" not in strategy_names
        ), "CompleteBrushWrapperStrategy should be removed from strategy list"

    def test_individual_brush_strategies_added_to_strategy_list(self):
        """Test that individual brush strategies are added to strategy list."""
        from sotd.match.scoring_brush_matcher import BrushScoringMatcher

        matcher = BrushScoringMatcher()
        strategies = matcher._create_strategies()

        # Get strategy names
        strategy_names = [type(strategy).__name__ for strategy in strategies]

        # Check that individual brush strategies are in the list
        expected_individual_strategies = [
            "KnownBrushMatchingStrategy",
            "OmegaSemogueBrushMatchingStrategy",
            "ZenithBrushMatchingStrategy",
            "OtherBrushMatchingStrategy",
        ]

        for strategy_name in expected_individual_strategies:
            assert (
                strategy_name in strategy_names
            ), f"Strategy {strategy_name} should be in strategy list"

    def test_strategy_list_maintains_correct_order(self):
        """Test that strategy list maintains correct priority order."""
        from sotd.match.scoring_brush_matcher import BrushScoringMatcher

        matcher = BrushScoringMatcher()
        strategies = matcher._create_strategies()

        # Get strategy names
        strategy_names = [type(strategy).__name__ for strategy in strategies]

        # Check that individual brush strategies come before composite strategies
        individual_strategies = [
            "KnownBrushMatchingStrategy",
            "OmegaSemogueBrushMatchingStrategy",
            "ZenithBrushMatchingStrategy",
            "OtherBrushMatchingStrategy",
        ]

        composite_strategies = [
            "LegacyDualComponentWrapperStrategy",
            "MediumPriorityAutomatedSplitWrapperStrategy",
            "LegacySingleComponentFallbackWrapperStrategy",
        ]

        # Find positions of strategies
        individual_positions = []
        for strategy in individual_strategies:
            if strategy in strategy_names:
                individual_positions.append(strategy_names.index(strategy))

        composite_positions = []
        for strategy in composite_strategies:
            if strategy in strategy_names:
                composite_positions.append(strategy_names.index(strategy))

        # Individual strategies should come before composite strategies
        if individual_positions and composite_positions:
            max_individual_pos = max(individual_positions)
            min_composite_pos = min(composite_positions)
            assert (
                max_individual_pos < min_composite_pos
            ), "Individual brush strategies should come before composite strategies"

    def test_strategy_list_contains_all_required_strategies(self):
        """Test that strategy list contains all required strategies."""
        from sotd.match.scoring_brush_matcher import BrushScoringMatcher

        matcher = BrushScoringMatcher()
        strategies = matcher._create_strategies()

        # Get strategy names
        strategy_names = [type(strategy).__name__ for strategy in strategies]

        # Check that all required strategies are present (current implementation)
        required_strategies = [
            "CorrectCompleteBrushWrapperStrategy",
            "CorrectSplitBrushWrapperStrategy",
            "KnownSplitWrapperStrategy",
            "FullInputComponentMatchingStrategy",
            "KnownBrushMatchingStrategy",
            "OmegaSemogueBrushMatchingStrategy",
            "ZenithBrushMatchingStrategy",
            "OtherBrushMatchingStrategy",
            "AutomatedSplitStrategy",
            "HandleOnlyStrategy",
            "KnotOnlyStrategy",
        ]

        for strategy_name in required_strategies:
            assert (
                strategy_name in strategy_names
            ), f"Required strategy {strategy_name} should be in strategy list"

    def test_strategy_list_has_correct_length(self):
        """Test that strategy list has the correct length."""
        from sotd.match.scoring_brush_matcher import BrushScoringMatcher

        matcher = BrushScoringMatcher()
        strategies = matcher._create_strategies()

        # Should have 11 strategies total (current implementation):
        # - 3 wrapper strategies (correct_complete, correct_split, known_split)
        # - 1 unified component strategy (FullInputComponentMatchingStrategy)
        # - 4 individual brush strategies (known_brush, omega_semogue, zenith, other_brush)
        # - 1 automated split strategy (AutomatedSplitStrategy)
        # - 2 single component strategies (handle_only, knot_only)
        expected_length = 11
        actual_length = len(strategies)

        assert actual_length == expected_length, (
            f"Strategy list should have {expected_length} strategies, " f"got {actual_length}"
        )

    def test_individual_strategies_have_correct_strategy_names(self):
        """Test that individual strategies have correct strategy names set."""
        from sotd.match.scoring_brush_matcher import BrushScoringMatcher

        matcher = BrushScoringMatcher()
        strategies = matcher._create_strategies()

        # Check that individual strategies have correct strategy names
        expected_strategy_names = {
            "KnownBrushMatchingStrategy": "known_brush",
            "OmegaSemogueBrushMatchingStrategy": "omega_semogue",
            "ZenithBrushMatchingStrategy": "zenith",
            "OtherBrushMatchingStrategy": "other_brush",
        }

        for strategy in strategies:
            strategy_class_name = type(strategy).__name__
            if strategy_class_name in expected_strategy_names:
                # Test that strategy name is set correctly when match is called
                result = strategy.match("test")
                if hasattr(result, "strategy") and result.strategy:
                    assert result.strategy == expected_strategy_names[strategy_class_name], (
                        f"Strategy {strategy_class_name} should have strategy name "
                        f"'{expected_strategy_names[strategy_class_name]}', "
                        f"got '{result.strategy}'"
                    )
