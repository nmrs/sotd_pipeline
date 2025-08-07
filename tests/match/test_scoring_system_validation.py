#!/usr/bin/env python3
"""Test validation for scoring system behavior."""

import tempfile
from pathlib import Path
from typing import Dict, Any

import pytest
import yaml

from sotd.match.scoring_brush_matcher import BrushScoringMatcher
from sotd.match.types import MatchResult


class TestScoringSystemValidation:
    """Test that scoring system runs all strategies and uses weights correctly."""

    def setup_method(self):
        """Set up test with custom scoring config."""
        # Create temporary scoring config for testing
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
                    "correct_complete_brush": 90.0,
                    "correct_split_brush": 85.0,
                    "known_split": 80.0,
                    "high_priority_automated_split": 75.0,
                    "complete_brush": 75.0,  # Higher priority than dual_component (matches legacy order)
                    "dual_component": 65.0,  # Lower priority than complete_brush (matches legacy order)
                    "medium_priority_automated_split": 60.0,
                    "single_component_fallback": 55.0,
                },
                "strategy_modifiers": {
                    "dual_component": {
                        "multiple_brands": 0.0,
                        "fiber_words": 0.0,
                        "size_specification": 0.0,
                    },
                    "complete_brush": {
                        "multiple_brands": 0.0,
                        "fiber_words": 0.0,
                        "size_specification": 0.0,
                    },
                    "single_component_fallback": {
                        "multiple_brands": 0.0,
                        "fiber_words": 0.0,
                        "size_specification": 0.0,
                    },
                },
            }
        }

        # Create temporary file
        temp_file = tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False)
        yaml.dump(config_data, temp_file)
        temp_file.close()
        return Path(temp_file.name)

    def test_composite_brush_should_win_over_individual_strategies(self):
        """Test that composite brush strategy wins when both individual and composite strategies match."""
        # Test string that should trigger both individual and composite strategies
        test_string = "Summer Break Soaps Maize 26mm Timberwolf"

        # Run all strategies
        strategy_results = self.matcher.strategy_orchestrator.run_all_strategies(test_string)

        # Verify we get multiple strategy results
        assert len(strategy_results) > 1, "Should get multiple strategy results"

        # Find composite brush result
        composite_result = None
        individual_results = []
        for result in strategy_results:
            if result.match_type == "composite":
                composite_result = result
            elif result.match_type in ["regex", "fiber_fallback", "size_fallback"]:
                individual_results.append(result)

        # Verify we have both composite and individual results
        assert composite_result is not None, "Should have composite brush result"
        assert len(individual_results) > 0, "Should have individual strategy results"

        # Score the results
        scored_results = self.matcher.scoring_engine.score_results(strategy_results, test_string)

        # Find the best result
        best_result = self.matcher.scoring_engine.get_best_result(scored_results)

        # Verify composite brush strategy wins (higher weight: 75.0 vs 65.0)
        assert best_result is not None, "Should have a best result"
        assert best_result.match_type == "composite", "Composite strategy should win"
        assert best_result.score == 75.0, "Composite strategy should have score 75.0"

        # Verify the final result structure matches legacy system
        final_result = self.matcher.match(test_string)
        assert final_result is not None, "Should return a result"
        assert final_result.matched.get("brand") is None, "Composite brush should have brand=None"
        assert final_result.matched.get("model") is None, "Composite brush should have model=None"
        assert "handle" in final_result.matched, "Should have handle section"
        assert "knot" in final_result.matched, "Should have knot section"

    def test_composite_brush_wins_over_individual_for_simpson_chubby(self):
        """Test that composite brush strategy wins over individual strategies for Simpson Chubby 2."""
        # Test string that should trigger both individual and composite strategies
        test_string = "Simpson Chubby 2"

        # Run all strategies
        strategy_results = self.matcher.strategy_orchestrator.run_all_strategies(test_string)

        # Verify we get multiple strategy results
        assert len(strategy_results) > 1, "Should get multiple strategy results"

        # Find composite brush result
        composite_result = None
        individual_results = []
        for result in strategy_results:
            if result.match_type == "composite":
                composite_result = result
            elif result.match_type in ["regex", "fiber_fallback", "size_fallback"]:
                individual_results.append(result)

        # Verify we have both composite and individual results
        assert composite_result is not None, "Should have composite brush result"
        assert len(individual_results) > 0, "Should have individual strategy results"

        # Score the results
        scored_results = self.matcher.scoring_engine.score_results(strategy_results, test_string)

        # Find the best result
        best_result = self.matcher.scoring_engine.get_best_result(scored_results)

        # Verify composite brush strategy wins (higher weight: 75.0 vs 65.0)
        assert best_result is not None, "Should have a best result"
        assert best_result.match_type == "composite", "Composite strategy should win"
        assert best_result.score == 75.0, "Composite strategy should have score 75.0"

    def test_scoring_weights_are_applied_correctly(self):
        """Test that scoring weights are applied correctly to all strategy types."""
        test_string = "Summer Break Soaps Maize 26mm Timberwolf"

        # Run all strategies
        strategy_results = self.matcher.strategy_orchestrator.run_all_strategies(test_string)

        # Score the results
        scored_results = self.matcher.scoring_engine.score_results(strategy_results, test_string)

        # Verify expected scores for different strategy types
        expected_scores = {
            "composite": 75.0,
            "single_component": 55.0,
            "regex": 65.0,
            "fiber_fallback": 55.0,
            "size_fallback": 55.0,
        }

        for result in scored_results:
            if result.match_type in expected_scores:
                assert result.score == expected_scores[result.match_type], (
                    f"Strategy {result.match_type} should have score {expected_scores[result.match_type]}, "
                    f"but got {result.score}"
                )

    def test_multiple_strategies_return_results_for_composite_brush(self):
        """Test that multiple strategies return results for composite brush input."""
        test_string = "Summer Break Soaps Maize 26mm Timberwolf"

        # Run all strategies
        strategy_results = self.matcher.strategy_orchestrator.run_all_strategies(test_string)

        # Count results by type
        result_counts = {}
        for result in strategy_results:
            result_type = result.match_type or "unknown"
            result_counts[result_type] = result_counts.get(result_type, 0) + 1

        # Verify we have results from multiple strategy types
        assert len(result_counts) > 1, "Should have results from multiple strategy types"

        # Verify we have composite brush result
        assert "composite" in result_counts, "Should have composite brush result"

        # Verify we have individual strategy results
        individual_types = ["regex", "fiber_fallback", "size_fallback", "single_component"]
        individual_count = sum(result_counts.get(t, 0) for t in individual_types)
        assert individual_count > 0, "Should have individual strategy results"

        print(f"Strategy result counts: {result_counts}")

    def test_scoring_system_maintains_architecture(self):
        """Test that scoring system maintains 'run all strategies and score them' architecture."""
        test_string = "Summer Break Soaps Maize 26mm Timberwolf"

        # Verify the matcher uses the scoring system approach
        # (This is tested by the fact that we can call run_all_strategies and score_results separately)
        strategy_results = self.matcher.strategy_orchestrator.run_all_strategies(test_string)
        scored_results = self.matcher.scoring_engine.score_results(strategy_results, test_string)
        best_result = self.matcher.scoring_engine.get_best_result(scored_results)

        # Verify this matches the direct match result
        direct_result = self.matcher.match(test_string)

        # Both should return the same best strategy result
        assert (
            best_result.match_type == direct_result.match_type
        ), "Should return same strategy type"
        assert best_result.score == getattr(
            direct_result, "score", None
        ), "Should return same score"

    def test_scoring_system_behavior_for_complete_vs_composite_brushes(self):
        """Test that scoring system correctly distinguishes between complete and composite brushes."""
        test_cases = [
            {
                "name": "Complete brush - Simpson Chubby 2",
                "input": "Simpson Chubby 2",
                "expected_winner": "regex",  # Individual brush strategy should win
                "expected_score": 75.0,  # complete_brush strategy has higher priority
                "expected_brand": "Simpson",
                "expected_model": "Chubby 2",
                "should_have_handle": False,
                "should_have_knot": False,
                "description": "Complete brush should be caught by individual strategy",
            },
            {
                "name": "Summer Break Soaps Maize 26mm Timberwolf",
                "input": "Summer Break Soaps Maize 26mm Timberwolf",
                "expected_winner": "regex",  # Individual brush strategy should win (matches legacy)
                "expected_score": 75.0,  # complete_brush strategy has higher priority
                "expected_brand": "Generic",  # Scoring system matches Timberwolf
                "expected_model": "Timberwolf",  # Scoring system matches Timberwolf
                "should_have_handle": True,
                "should_have_knot": True,
                "description": "Should be caught by individual strategy (matches legacy behavior)",
            },
        ]

        for test_case in test_cases:
            print(f"\nTesting: {test_case['name']}")
            print(f"Input: {test_case['input']}")
            print(f"Expected: {test_case['description']}")

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
            print(f"   Winner: {best_result.match_type} (score: {best_result.score})")
            print(f"   Brand: {matched.get('brand')}, Model: {matched.get('model')}")
            print(f"   Has handle: {'handle' in matched}, Has knot: {'knot' in matched}")
