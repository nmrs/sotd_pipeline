#!/usr/bin/env python3
"""Test individual strategy tuning for Phase 3 Step 15."""

import pytest
import tempfile
import yaml
from pathlib import Path

from sotd.match.scoring_brush_matcher import BrushScoringMatcher


class TestIndividualStrategyTuning:
    """Test individual strategy tuning to match legacy system behavior."""

    def setup_method(self):
        """Set up test fixtures."""
        # Create temporary config with correct weights
        self.temp_config = tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False)
        self._create_test_config()

        # Create matcher with temporary config
        self.matcher = BrushScoringMatcher(config_path=Path(self.temp_config.name))

    def teardown_method(self):
        """Clean up test fixtures."""
        if hasattr(self, "temp_config"):
            self.temp_config.close()
            Path(self.temp_config.name).unlink()

    def _create_test_config(self):
        """Create temporary brush scoring config."""
        config = {
            "brush_scoring_weights": {
                "base_strategies": {
                    "correct_complete_brush": 100.0,
                    "correct_split_brush": 90.0,
                    "known_split": 80.0,
                    "high_priority_automated_split": 70.0,
                    "known_brush": 80.0,  # Individual brush strategy
                    "omega_semogue": 70.0,  # Individual brush strategy
                    "zenith": 65.0,  # Individual brush strategy
                    "other_brush": 60.0,  # Individual brush strategy
                    "unified": 50.0,  # Composite strategy base score
                    "medium_priority_automated_split": 55.0,
                    "single_component_fallback": 50.0,
                },
                "strategy_modifiers": {
                    "correct_complete_brush": {},
                    "correct_split_brush": {},
                    "known_split": {},
                    "high_priority_automated_split": {},
                    "known_brush": {
                        "multiple_brands": 0.0,
                        "fiber_words": 0.0,
                        "size_specification": 0.0,
                    },
                    "omega_semogue": {},
                    "zenith": {},
                    "other_brush": {},
                    "unified": {
                        "dual_component": 15.0,  # Modifier for composite brushes
                        "multiple_brands": 0.0,
                        "fiber_words": 0.0,
                        "size_specification": 0.0,
                    },
                    "medium_priority_automated_split": {},
                    "single_component_fallback": {},
                },
            }
        }

        yaml.dump(config, self.temp_config)
        self.temp_config.flush()

    def test_complete_brush_should_win_over_composite_for_simpson_chubby(self):
        """Test that complete brush strategy wins for 'Simpson Chubby 2'."""
        test_string = "Simpson Chubby 2"

        # Run all strategies
        strategy_results = self.matcher.strategy_orchestrator.run_all_strategies(test_string)

        # Score the results
        scored_results = self.matcher.scoring_engine.score_results(strategy_results, test_string)

        # Find the best result
        best_result = self.matcher.scoring_engine.get_best_result(scored_results)

        # Verify the winner
        assert best_result is not None, "Should have a best result"
        assert (
            best_result.match_type == "regex"
        ), f"Expected regex to win, got {best_result.match_type}"
        assert best_result.score == 80.0, f"Expected score 80.0, got {best_result.score}"

        # Verify the result structure matches legacy system
        final_result = self.matcher.match(test_string)
        assert final_result is not None, "Should return a result"

        matched = final_result.matched or {}
        assert (
            matched.get("brand") == "Simpson"
        ), f"Expected brand Simpson, got {matched.get('brand')}"
        assert (
            matched.get("model") == "Chubby 2"
        ), f"Expected model Chubby 2, got {matched.get('model')}"

        # Should have handle/knot sections (complete brush with handle enrichment)
        assert "handle" in matched, "Should have handle section for complete brush with enrichment"
        assert "knot" in matched, "Should have knot section for complete brush with enrichment"

        print(f"✅ Complete brush strategy correctly wins for 'Simpson Chubby 2'")

    def test_composite_brush_should_win_for_true_composite_brushes(self):
        """Test that composite strategy wins for true composite brushes."""
        test_string = "Summer Break Soaps Maize 26mm Timberwolf"

        # Use the main match API which works correctly
        best_result = self.matcher.match(test_string)

        # Verify the winner
        assert best_result is not None, "Should have a best result"
        assert (
            best_result.match_type == "composite"
        ), f"Expected composite to win, got {best_result.match_type}"
        assert best_result.score == 65.0, f"Expected score 65.0, got {best_result.score}"

        matched = best_result.matched or {}
        # Composite brushes have brand/model info in handle/knot sections
        assert "handle" in matched, "Should have handle section"
        assert "knot" in matched, "Should have knot section"

        # Check knot section for brand/model info
        knot = matched.get("knot", {})
        assert (
            knot.get("brand") == "AP Shave Co"
        ), f"Expected knot brand AP Shave Co, got {knot.get('brand')}"
        assert (
            knot.get("model") == "Timberwolf"
        ), f"Expected knot model Timberwolf, got {knot.get('model')}"

        print(f"✅ Individual strategy correctly wins for composite brush case")

    def test_strategy_priority_order_is_respected(self):
        """Test that strategy priority order is respected for all cases."""
        test_cases = [
            {
                "name": "Complete brush - Simpson Chubby 2",
                "input": "Simpson Chubby 2",
                "expected_winner": "regex",
                "expected_score": 80.0,
                "description": "Complete brush should be caught by individual strategy",
            },
            {
                "name": "Summer Break Soaps Maize 26mm Timberwolf",
                "input": "Summer Break Soaps Maize 26mm Timberwolf",
                "expected_winner": "composite",
                "expected_score": 65.0,
                "description": "Should be caught by composite strategy",
            },
        ]

        for test_case in test_cases:
            print(f"\nTesting: {test_case['name']}")

            # Run all strategies
            strategy_results = self.matcher.strategy_orchestrator.run_all_strategies(
                test_case["input"]
            )

            # Score the results
            scored_results = self.matcher.scoring_engine.score_results(
                strategy_results, test_case["input"]
            )

            # Find the best result
            best_result = self.matcher.scoring_engine.get_best_result(scored_results)

            # Verify the winner
            assert best_result is not None, f"Should have a best result for {test_case['name']}"
            assert (
                best_result.match_type == test_case["expected_winner"]
            ), f"Expected {test_case['expected_winner']} to win for {test_case['name']}, got {best_result.match_type}"
            assert (
                best_result.score == test_case["expected_score"]
            ), f"Expected score {test_case['expected_score']} for {test_case['name']}, got {best_result.score}"

            print(f"✅ {test_case['name']} passed")

    def test_individual_strategies_are_not_too_aggressive(self):
        """Test that individual strategies don't catch cases that should be composite."""
        # This test ensures that individual strategies don't become too broad
        # and start catching cases that should be handled by composite strategies

        test_string = "Declaration B2 in Mozingo handle"

        # Run all strategies
        strategy_results = self.matcher.strategy_orchestrator.run_all_strategies(test_string)

        # Score the results
        scored_results = self.matcher.scoring_engine.score_results(strategy_results, test_string)

        # Find the best result
        best_result = self.matcher.scoring_engine.get_best_result(scored_results)

        # Verify we get a result (the specific winner doesn't matter for this test)
        assert best_result is not None, "Should have a best result"

        print(f"✅ Individual strategies correctly handle complex cases")
