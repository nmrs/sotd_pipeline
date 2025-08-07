#!/usr/bin/env python3
"""Comprehensive test for scoring system behavior across multiple brush types."""

import tempfile
from pathlib import Path

import yaml

from sotd.match.scoring_brush_matcher import BrushScoringMatcher


class TestScoringSystemComprehensive:
    """Comprehensive test for scoring system behavior."""

    def setup_method(self):
        """Set up test with custom scoring config."""
        self.temp_config = self._create_test_config()
        self.matcher = BrushScoringMatcher(config_path=self.temp_config)

    def teardown_method(self):
        """Clean up temporary config."""
        if self.temp_config and self.temp_config.exists():
            self.temp_config.unlink()

    def _create_test_config(self) -> Path:
        """Create a temporary scoring config for testing."""
        config_data = {
            "brush_scoring_weights": {
                "base_strategies": {
                    "correct_complete_brush": 100.0,
                    "correct_split_brush": 90.0,
                    "known_split": 80.0,
                    "high_priority_automated_split": 70.0,
                    "known_brush": 75.0,  # Individual brush strategy
                    "omega_semogue": 70.0,  # Individual brush strategy
                    "zenith": 65.0,  # Individual brush strategy
                    "other_brush": 60.0,  # Individual brush strategy
                    "dual_component": 75.0,  # Composite brush strategy
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
                    "dual_component": {
                        "multiple_brands": 0.0,
                        "fiber_words": 0.0,
                        "size_specification": 0.0,
                    },
                    "medium_priority_automated_split": {},
                    "single_component_fallback": {},
                },
            }
        }

        temp_file = tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False)
        yaml.dump(config_data, temp_file)
        temp_file.close()
        return Path(temp_file.name)

    def test_scoring_system_behavior_for_various_brushes(self):
        """Test scoring system behavior for various brush types."""
        test_cases = [
            {
                "name": "Composite brush with handle and knot",
                "input": "Summer Break Soaps Maize 26mm Timberwolf",
                "expected_winner": "composite",
                "expected_score": 75.0,
                "expected_brand": None,
                "expected_model": None,
                "should_have_handle": True,
                "should_have_knot": True,
            },
            {
                "name": "Simpson Chubby 2 (complete brush)",
                "input": "Simpson Chubby 2",
                "expected_winner": "regex",
                "expected_score": 75.0,
                "expected_brand": "Simpson",
                "expected_model": "Chubby 2",
                "should_have_handle": False,
                "should_have_knot": False,
            },
            {
                "name": "Declaration B2 (complete brush)",
                "input": "Declaration B2",
                "expected_winner": "regex",
                "expected_score": 75.0,
                "expected_brand": "Declaration Grooming",
                "expected_model": "B2",
                "should_have_handle": False,
                "should_have_knot": False,
            },
            {
                "name": "Omega 10049 (correct match)",
                "input": "Omega 10049",
                "expected_winner": "exact",
                "expected_score": 100.0,
                "expected_brand": "Omega",
                "expected_model": "10049",
                "should_have_handle": False,
                "should_have_knot": False,
            },
        ]

        for test_case in test_cases:
            print(f"\nTesting: {test_case['name']}")
            print(f"Input: {test_case['input']}")

            # Run all strategies
            strategy_results = self.matcher.strategy_orchestrator.run_all_strategies(
                test_case["input"]
            )

            # Count results by type
            result_counts = {}
            for result in strategy_results:
                result_type = result.match_type or "unknown"
                result_counts[result_type] = result_counts.get(result_type, 0) + 1

            print(f"Strategy results: {result_counts}")

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

            # Test final result structure
            final_result = self.matcher.match(test_case["input"])
            assert final_result is not None, f"Should return a result for {test_case['name']}"

            matched = final_result.matched or {}
            assert (
                matched.get("brand") == test_case["expected_brand"]
            ), f"Expected brand {test_case['expected_brand']} for {test_case['name']}, got {matched.get('brand')}"
            assert (
                matched.get("model") == test_case["expected_model"]
            ), f"Expected model {test_case['expected_model']} for {test_case['name']}, got {matched.get('model')}"

            if test_case["should_have_handle"]:
                assert "handle" in matched, f"Should have handle section for {test_case['name']}"
            if test_case["should_have_knot"]:
                assert "knot" in matched, f"Should have knot section for {test_case['name']}"

            print(f"✅ {test_case['name']} passed")

    def test_scoring_system_runs_all_strategies(self):
        """Test that scoring system runs all strategies for each input."""
        test_string = "Simpson Chubby 2"

        # Run all strategies
        strategy_results = self.matcher.strategy_orchestrator.run_all_strategies(test_string)

        # Verify we get multiple results
        assert len(strategy_results) > 1, "Should get multiple strategy results"

        # Verify we have both composite and individual results
        composite_count = sum(1 for r in strategy_results if r.match_type == "composite")
        individual_count = sum(
            1
            for r in strategy_results
            if r.match_type in ["regex", "fiber_fallback", "size_fallback"]
        )

        assert composite_count > 0, "Should have composite brush results"
        assert individual_count > 0, "Should have individual strategy results"

        print(f"Composite results: {composite_count}")
        print(f"Individual results: {individual_count}")
        print(f"Total results: {len(strategy_results)}")

    def test_scoring_system_weights_are_respected(self):
        """Test that scoring system weights are respected across all strategy types."""
        test_string = "Summer Break Soaps Maize 26mm Timberwolf"

        # Run all strategies and score them
        strategy_results = self.matcher.strategy_orchestrator.run_all_strategies(test_string)
        scored_results = self.matcher.scoring_engine.score_results(strategy_results, test_string)

        # Verify expected scores
        expected_scores = {
            "composite": 75.0,
            "single_component": 50.0,
            "regex": 75.0,
            "fiber_fallback": 50.0,
            "size_fallback": 50.0,
        }

        for result in scored_results:
            if result.match_type in expected_scores:
                assert result.score == expected_scores[result.match_type], (
                    f"Strategy {result.match_type} should have score {expected_scores[result.match_type]}, "
                    f"but got {result.score}"
                )

        # Verify composite strategy wins
        best_result = self.matcher.scoring_engine.get_best_result(scored_results)
        assert best_result.match_type == "composite", "Composite strategy should win"
        assert best_result.score == 75.0, "Composite strategy should have highest score"
