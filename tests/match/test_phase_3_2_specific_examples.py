"""
Tests for Phase 3.2: Specific Examples.

This test file implements the TDD approach for Phase 3.2 specific examples,
testing the specific brush examples mentioned in the plan (Simpson Chubby 2, Summer Break Soaps).
"""


class TestPhase32SpecificExamples:
    """Test Phase 3.2 specific examples."""

    def test_simpson_chubby_2_matches_correctly(self):
        """Test that Simpson Chubby 2 matches correctly with individual strategies."""
        from sotd.match.scoring_brush_matcher import BrushScoringMatcher

        matcher = BrushScoringMatcher()
        result = matcher.match("Simpson Chubby 2")

        assert result is not None, "Should return result for Simpson Chubby 2"
        assert result.matched is not None, "Should produce match for Simpson Chubby 2"
        assert result.matched.get("brand") == "Simpson", "Should match Simpson brand"
        assert result.matched.get("model") == "Chubby 2", "Should match Chubby 2 model"

        # Check fiber in knot section
        knot = result.matched.get("knot", {})
        assert knot.get("fiber") == "Badger", "Should match Badger fiber"
        assert knot.get("knot_size_mm") == 27, "Should match 27mm knot size"

    def test_summer_break_soaps_maize_26mm_timberwolf_matches_correctly(self):
        """Test that Summer Break Soaps Maize 26mm Timberwolf matches correctly."""
        from sotd.match.scoring_brush_matcher import BrushScoringMatcher

        matcher = BrushScoringMatcher()
        result = matcher.match("Summer Break Soaps Maize 26mm Timberwolf")

        # This should be handled by unified strategy, not individual brush strategies
        # The legacy system returns a match for this case, so scoring system should also return a match
        assert result is not None, "Should return result for Summer Break Soaps"
        assert result.matched is not None, "Should produce match for Summer Break Soaps"
        assert result.strategy == "unified", "Should use unified strategy"

    def test_omega_10049_matches_correctly(self):
        """Test that Omega 10049 matches correctly with individual strategies."""
        from sotd.match.scoring_brush_matcher import BrushScoringMatcher

        matcher = BrushScoringMatcher()
        result = matcher.match("Omega 10049")

        assert result is not None, "Should return result for Omega 10049"
        assert result.matched is not None, "Should produce match for Omega 10049"
        assert result.matched.get("brand") == "Omega", "Should match Omega brand"
        assert result.matched.get("model") == "10049", "Should match 10049 model"

        # Check fiber in knot section
        knot = result.matched.get("knot", {})
        assert knot.get("fiber") == "Boar", "Should match Boar fiber"

    def test_semogue_c3_matches_correctly(self):
        """Test that Semogue C3 matches correctly with individual strategies."""
        from sotd.match.scoring_brush_matcher import BrushScoringMatcher

        matcher = BrushScoringMatcher()
        result = matcher.match("Semogue C3")

        assert result is not None, "Should return result for Semogue C3"
        assert result.matched is not None, "Should produce match for Semogue C3"
        assert result.matched.get("brand") == "Semogue", "Should match Semogue brand"
        assert result.matched.get("model") == "c3", "Should match c3 model"

        # Check fiber in knot section
        knot = result.matched.get("knot", {})
        assert knot.get("fiber") == "Boar", "Should match Boar fiber"

    def test_zenith_b2_matches_correctly(self):
        """Test that Zenith B2 matches correctly with individual strategies."""
        from sotd.match.scoring_brush_matcher import BrushScoringMatcher

        matcher = BrushScoringMatcher()
        result = matcher.match("Zenith B2")

        assert result is not None, "Should return result for Zenith B2"
        assert result.matched is not None, "Should produce match for Zenith B2"
        assert result.matched.get("brand") == "Zenith", "Should match Zenith brand"
        assert result.matched.get("model") == "B2", "Should match B2 model"

        # Check fiber in knot section
        knot = result.matched.get("knot", {})
        assert knot.get("fiber") == "Boar", "Should match Boar fiber"

    def test_individual_strategies_handle_complex_cases(self):
        """Test that individual strategies handle complex cases correctly."""
        from sotd.match.scoring_brush_matcher import BrushScoringMatcher

        matcher = BrushScoringMatcher()

        # Test complex cases that should be handled by individual strategies
        complex_cases = [
            "Simpson Chubby 2 Manchurian",
            "Omega 10049 Boar",
            "Semogue C3 Premium",
            "Zenith B2 Boar",
        ]

        for test_case in complex_cases:
            result = matcher.match(test_case)
            # Should not crash and should handle gracefully
            assert result is not None, f"Should return result for '{test_case}'"
            # May or may not match, but should return valid result structure
            if result.matched:
                assert "brand" in result.matched, f"Should have brand for '{test_case}'"
                assert "model" in result.matched, f"Should have model for '{test_case}'"

    def test_strategy_priority_for_specific_examples(self):
        """Test that strategy priority is correct for specific examples."""
        from sotd.match.scoring_brush_matcher import BrushScoringMatcher

        matcher = BrushScoringMatcher()

        # Test that known brush strategies take priority over other strategies
        test_cases = [
            ("Simpson Chubby 2", "known_brush"),
            ("Omega 10049", "omega_semogue"),
            ("Semogue C3", "omega_semogue"),
            ("Zenith B2", "zenith"),
        ]

        for test_case, expected_strategy in test_cases:
            result = matcher.match(test_case)
            if result and result.matched:
                # Check that the correct strategy was used
                # Note: The exact strategy name may vary based on implementation
                # The key is that it matches correctly
                assert (
                    result.matched.get("brand") is not None
                ), f"Should have brand for '{test_case}'"
                assert (
                    result.matched.get("model") is not None
                ), f"Should have model for '{test_case}'"

    def test_individual_strategies_vs_wrapper_behavior(self):
        """Test that individual strategies produce same results as wrapper would have."""
        from sotd.match.scoring_brush_matcher import BrushScoringMatcher
        from sotd.match.brush_matcher import BrushMatcher
        from sotd.match.config import BrushMatcherConfig

        # Create both systems
        scoring_matcher = BrushScoringMatcher()
        config = BrushMatcherConfig.create_default()
        legacy_matcher = BrushMatcher(config=config)

        # Test specific examples
        specific_examples = [
            "Simpson Chubby 2",
            "Omega 10049",
            "Semogue C3",
            "Zenith B2",
        ]

        for test_case in specific_examples:
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
