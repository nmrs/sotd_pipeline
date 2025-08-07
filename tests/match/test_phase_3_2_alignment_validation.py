"""
Tests for Phase 3.2: Alignment Validation.

This test file implements the TDD approach for Phase 3.2 alignment validation,
testing that 100% alignment is maintained after replacing the complete_brush wrapper
with individual brush strategies.
"""


class TestPhase32AlignmentValidation:
    """Test Phase 3.2 alignment validation."""

    def test_individual_strategies_produce_same_results_as_wrapper(self):
        """Test that individual strategies produce same results as complete_brush wrapper."""
        from sotd.match.scoring_brush_matcher import BrushScoringMatcher
        from sotd.match.brush_matcher import BrushMatcher
        from sotd.match.config import BrushMatcherConfig

        # Create scoring system with individual strategies
        scoring_matcher = BrushScoringMatcher()

        # Create legacy system for comparison
        config = BrushMatcherConfig.create_default()
        legacy_matcher = BrushMatcher(config=config)

        # Test cases that should be handled by individual brush strategies
        test_cases = [
            "Simpson Chubby 2",
            "Omega 10049",
            "Semogue C3",
            "Zenith B2",
            "Elite Brush",
        ]

        for test_case in test_cases:
            # Get result from scoring system
            scoring_result = scoring_matcher.match(test_case)

            # Get result from legacy system
            legacy_result = legacy_matcher.match(test_case)

            # Compare results
            if legacy_result and legacy_result.matched:
                assert scoring_result is not None, f"Scoring system should match '{test_case}'"
                assert (
                    scoring_result.matched is not None
                ), f"Scoring system should produce match for '{test_case}'"

                # Compare key fields
                assert scoring_result.matched.get("brand") == legacy_result.matched.get("brand"), (
                    f"Brand mismatch for '{test_case}': "
                    f"scoring='{scoring_result.matched.get('brand')}', "
                    f"legacy='{legacy_result.matched.get('brand')}'"
                )
                assert scoring_result.matched.get("model") == legacy_result.matched.get("model"), (
                    f"Model mismatch for '{test_case}': "
                    f"scoring='{scoring_result.matched.get('model')}', "
                    f"legacy='{legacy_result.matched.get('model')}'"
                )
                assert scoring_result.matched.get("fiber") == legacy_result.matched.get("fiber"), (
                    f"Fiber mismatch for '{test_case}': "
                    f"scoring='{scoring_result.matched.get('fiber')}', "
                    f"legacy='{legacy_result.matched.get('fiber')}'"
                )
            else:
                # Both should return no match
                assert (
                    scoring_result is None or scoring_result.matched is None
                ), f"Scoring system should not match '{test_case}' when legacy doesn't"

    def test_strategy_priority_order_maintained(self):
        """Test that strategy priority order is maintained after Phase 3.2 changes."""
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

        # Find positions
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

    def test_scoring_weights_match_priority_order(self):
        """Test that scoring weights match the strategy priority order."""
        from sotd.match.scoring_brush_matcher import BrushScoringMatcher
        from sotd.match.brush_scoring_config import BrushScoringConfig

        matcher = BrushScoringMatcher()
        config = BrushScoringConfig()

        # Get strategy names and their positions
        strategies = matcher._create_strategies()
        strategy_names = [type(strategy).__name__ for strategy in strategies]

        # Check individual brush strategy weights
        individual_strategy_weights = {
            "KnownBrushMatchingStrategy": "known_brush",
            "OmegaSemogueBrushMatchingStrategy": "omega_semogue",
            "ZenithBrushMatchingStrategy": "zenith",
            "OtherBrushMatchingStrategy": "other_brush",
        }

        # Verify weights are in descending order
        weights = []
        for strategy_name, config_name in individual_strategy_weights.items():
            if strategy_name in strategy_names:
                try:
                    weight = config.get_base_strategy_score(config_name)
                    weights.append(weight)
                except KeyError:
                    # Strategy not in config yet, which is expected for Phase 3.2
                    pass

        # Verify weights are in descending order (highest priority first)
        if len(weights) > 1:
            assert weights == sorted(
                weights, reverse=True
            ), f"Individual strategy weights should be in descending order: {weights}"

    def test_individual_strategies_handle_edge_cases(self):
        """Test that individual strategies handle edge cases correctly."""
        from sotd.match.scoring_brush_matcher import BrushScoringMatcher

        matcher = BrushScoringMatcher()

        # Test edge cases
        edge_cases = [
            "",  # Empty string
            "   ",  # Whitespace only
            "Unknown Brush",  # No match
            "Simpson Chubby 2 Extra Large",  # Extended name
            "Omega 10049 Boar",  # With fiber specification
        ]

        for test_case in edge_cases:
            result = matcher.match(test_case)
            # Should not crash and should return a valid result structure
            # Note: Empty strings may return None, which is acceptable
            if result is not None:
                assert hasattr(
                    result, "matched"
                ), f"Result should have matched attribute for '{test_case}'"
                assert hasattr(
                    result, "strategy"
                ), f"Result should have strategy attribute for '{test_case}'"
            # If result is None, that's also acceptable for edge cases

    def test_individual_strategies_preserve_legacy_behavior(self):
        """Test that individual strategies preserve legacy behavior for known cases."""
        from sotd.match.scoring_brush_matcher import BrushScoringMatcher
        from sotd.match.brush_matcher import BrushMatcher
        from sotd.match.config import BrushMatcherConfig

        # Create both systems
        scoring_matcher = BrushScoringMatcher()
        config = BrushMatcherConfig.create_default()
        legacy_matcher = BrushMatcher(config=config)

        # Test specific cases that were handled by complete_brush wrapper
        known_cases = [
            "Simpson Chubby 2",
            "Omega 10049",
            "Semogue C3",
            "Zenith B2",
        ]

        for test_case in known_cases:
            scoring_result = scoring_matcher.match(test_case)
            legacy_result = legacy_matcher.match(test_case)

            # Both should produce the same result
            if legacy_result and legacy_result.matched:
                assert scoring_result is not None, f"Scoring should match '{test_case}'"
                assert (
                    scoring_result.matched is not None
                ), f"Scoring should produce match for '{test_case}'"

                # Key fields should match
                scoring_brand = scoring_result.matched.get("brand")
                legacy_brand = legacy_result.matched.get("brand")
                assert scoring_brand == legacy_brand, (
                    f"Brand mismatch for '{test_case}': "
                    f"scoring='{scoring_brand}', legacy='{legacy_brand}'"
                )

                scoring_model = scoring_result.matched.get("model")
                legacy_model = legacy_result.matched.get("model")
                assert scoring_model == legacy_model, (
                    f"Model mismatch for '{test_case}': "
                    f"scoring='{scoring_model}', legacy='{legacy_model}'"
                )
            else:
                # Both should return no match
                assert (
                    scoring_result is None or scoring_result.matched is None
                ), f"Scoring should not match '{test_case}' when legacy doesn't"
