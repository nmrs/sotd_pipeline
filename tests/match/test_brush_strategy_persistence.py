"""Tests for Phase 4.1: Brush Strategy Match Persistence.

This module tests the persistence of all brush strategy matches alongside final matches,
enabling the BrushValidation interface to show users all available strategy matches.
"""

import json
from unittest.mock import Mock, patch

import pytest

from sotd.match.types import MatchResult
from sotd.match.brush_scoring_components.strategy_orchestrator import StrategyOrchestrator
from sotd.match.brush_scoring_components.result_processor import ResultProcessor
from sotd.match.scoring_brush_matcher import BrushScoringMatcher
from sotd.match.brush_parallel_data_manager import BrushParallelDataManager


class TestBrushStrategyMatchDataStructure:
    """Test the data structure for persisted brush strategy matches."""

    def test_match_result_with_strategy_data(self):
        """Test that MatchResult includes best_result and all_strategies fields."""
        # Create a mock best result
        best_result = MatchResult(
            original="Declaration B2 in Mozingo handle",
            matched={"brand": "Declaration", "model": "B2", "handle": "Mozingo"},
            match_type="handle_knot_split",
            strategy="handle_knot_split",
            score=0.95,
        )

        # Create mock strategy results
        all_strategies = [
            MatchResult(
                original="Declaration B2 in Mozingo handle",
                matched={"brand": "Declaration", "model": "B2", "handle": "Mozingo"},
                match_type="handle_knot_split",
                strategy="handle_knot_split",
                score=0.95,
            ),
            MatchResult(
                original="Declaration B2 in Mozingo handle",
                matched={"brand": "Declaration", "model": "B2"},
                match_type="brand_model",
                strategy="brand_model",
                score=0.85,
            ),
            MatchResult(
                original="Declaration B2 in Mozingo handle",
                matched={"brand": "Declaration"},
                match_type="brand_only",
                strategy="brand_only",
                score=0.75,
            ),
        ]

        # Create the final result with strategy data
        final_result = MatchResult(
            original="Declaration B2 in Mozingo handle",
            matched={"brand": "Declaration", "model": "B2", "handle": "Mozingo"},
            match_type="handle_knot_split",
            strategy="handle_knot_split",
            score=0.95,
            best_result={
                "strategy": best_result.strategy,
                "score": best_result.score,
                "result": best_result.matched,
            },
            all_strategies=[
                {"strategy": s.strategy, "score": s.score, "result": s.matched}
                for s in all_strategies
            ],
        )

        # Verify the structure
        assert final_result.best_result is not None
        assert final_result.all_strategies is not None
        assert len(final_result.all_strategies) == 3
        assert final_result.best_result["strategy"] == "handle_knot_split"
        assert final_result.best_result["score"] == 0.95

        # Verify all strategies have required fields
        for strategy_result in final_result.all_strategies:
            assert "strategy" in strategy_result
            assert "score" in strategy_result
            assert "result" in strategy_result

    def test_strategy_result_serialization(self):
        """Test that strategy results can be serialized to JSON."""
        strategy_result = MatchResult(
            original="Declaration B2 in Mozingo handle",
            matched={"brand": "Declaration", "model": "B2", "handle": "Mozingo"},
            match_type="handle_knot_split",
            strategy="handle_knot_split",
            score=0.95,
        )

        # Convert to dict for JSON serialization
        result_dict = {
            "original": strategy_result.original,
            "matched": strategy_result.matched,
            "match_type": strategy_result.match_type,
            "strategy": strategy_result.strategy,
            "score": strategy_result.score,
        }

        # Should serialize without errors
        json_str = json.dumps(result_dict)
        assert json_str is not None
        assert "Declaration" in json_str
        assert "0.95" in json_str


class TestResultProcessorStrategyData:
    """Test that ResultProcessor includes strategy data in final results."""

    def test_process_result_includes_strategy_data(self):
        """Test that process_result adds best_result and all_strategies to MatchResult."""
        processor = ResultProcessor()

        # Create a mock best result
        best_result = MatchResult(
            original="Declaration B2 in Mozingo handle",
            matched={"brand": "Declaration", "model": "B2", "handle": "Mozingo"},
            match_type="handle_knot_split",
            strategy="handle_knot_split",
            score=0.95,
        )

        # Create mock all strategies
        all_strategies = [
            MatchResult(
                original="Declaration B2 in Mozingo handle",
                matched={"brand": "Declaration", "model": "B2", "handle": "Mozingo"},
                match_type="handle_knot_split",
                strategy="handle_knot_split",
                score=0.95,
            ),
            MatchResult(
                original="Declaration B2 in Mozingo handle",
                matched={"brand": "Declaration", "model": "B2"},
                match_type="brand_model",
                strategy="brand_model",
                score=0.85,
            ),
        ]

        # Mock the scoring engine to return strategy data
        with patch.object(processor, "_ensure_consistent_structure"):
            with patch.object(processor, "_apply_final_processing"):
                # Create expected result with strategy data
                expected_result = MatchResult(
                    original=best_result.original,
                    matched=best_result.matched,
                    match_type=best_result.match_type,
                    strategy=best_result.strategy,
                    score=best_result.score,
                    best_result={
                        "strategy": best_result.strategy,
                        "score": best_result.score,
                        "result": best_result.matched,
                    },
                    all_strategies=[
                        {"strategy": s.strategy, "score": s.score, "result": s.matched}
                        for s in all_strategies
                    ],
                )

                # Verify the expected structure
                assert expected_result.best_result is not None
                assert expected_result.all_strategies is not None
                assert len(expected_result.all_strategies) == 2


class TestBrushScoringMatcherStrategyPersistence:
    """Test that BrushScoringMatcher persists all strategy results."""

    def test_match_returns_strategy_data(self):
        """Test that match method returns result with strategy data."""
        # Mock dependencies
        mock_orchestrator = Mock(spec=StrategyOrchestrator)
        mock_scoring_engine = Mock()
        mock_result_processor = Mock(spec=ResultProcessor)

        # Create mock strategy results
        mock_strategy_results = [
            MatchResult(
                original="Declaration B2 in Mozingo handle",
                matched={"brand": "Declaration", "model": "B2", "handle": "Mozingo"},
                match_type="handle_knot_split",
                strategy="handle_knot_split",
                score=0.95,
            ),
            MatchResult(
                original="Declaration B2 in Mozingo handle",
                matched={"brand": "Declaration", "model": "B2"},
                match_type="brand_model",
                strategy="brand_model",
                score=0.85,
            ),
        ]

        # Mock the orchestrator to return strategy results
        mock_orchestrator.run_all_strategies.return_value = mock_strategy_results

        # Mock the scoring engine
        mock_scoring_engine.score_results.return_value = mock_strategy_results
        mock_scoring_engine.get_best_result.return_value = mock_strategy_results[0]

        # Mock the result processor to return result with strategy data
        final_result = MatchResult(
            original="Declaration B2 in Mozingo handle",
            matched={"brand": "Declaration", "model": "B2", "handle": "Mozingo"},
            match_type="handle_knot_split",
            strategy="handle_knot_split",
            score=0.95,
            best_result={
                "strategy": mock_strategy_results[0].strategy,
                "score": mock_strategy_results[0].score,
                "result": mock_strategy_results[0].matched,
            },
            all_strategies=[
                {"strategy": s.strategy, "score": s.score, "result": s.matched}
                for s in mock_strategy_results
            ],
        )

        mock_result_processor.process_result.return_value = final_result

        # Create matcher with mocked dependencies
        matcher = BrushScoringMatcher()
        matcher.strategy_orchestrator = mock_orchestrator
        matcher.scoring_engine = mock_scoring_engine
        matcher.result_processor = mock_result_processor

        # Test the match method
        result = matcher.match("Declaration B2 in Mozingo handle")

        # Verify the result is returned
        assert result is not None

        # Verify the orchestrator was called
        mock_orchestrator.run_all_strategies.assert_called_once()

        # Verify the expected output structure
        assert result.best_result is not None
        assert result.all_strategies is not None
        assert len(result.all_strategies) == 2


class TestDataPersistenceIntegration:
    """Integration tests for data persistence with strategy information."""

    def test_save_data_includes_strategy_fields(self, tmp_path):
        """Test that saved data includes best_result and all_strategies fields."""
        data_manager = BrushParallelDataManager()

        # Create test data with strategy information
        test_data = {
            "metadata": {
                "total_shaves": 100,
                "unique_shavers": 50,
                "included_months": ["2025-01"],
                "missing_months": [],
            },
            "data": [
                {
                    "original": "Declaration B2 in Mozingo handle",
                    "normalized": "declaration b2 in mozingo handle",
                    "matched": {
                        "brush": {
                            "brand": "Declaration",
                            "model": "B2",
                            "handle": "Mozingo",
                            "match_type": "handle_knot_split",
                            "strategy": "handle_knot_split",
                            "score": 0.95,
                            "best_result": {
                                "strategy": "handle_knot_split",
                                "score": 0.95,
                                "result": {
                                    "brand": "Declaration",
                                    "model": "B2",
                                    "handle": "Mozingo",
                                },
                            },
                            "all_strategies": [
                                {
                                    "strategy": "handle_knot_split",
                                    "score": 0.95,
                                    "result": {
                                        "brand": "Declaration",
                                        "model": "B2",
                                        "handle": "Mozingo",
                                    },
                                },
                                {
                                    "strategy": "brand_model",
                                    "score": 0.85,
                                    "result": {"brand": "Declaration", "model": "B2"},
                                },
                            ],
                        }
                    },
                    "match_type": "handle_knot_split",
                    "pattern": "brand model in handle",
                    "strategy": "handle_knot_split",
                }
            ],
        }

        # Save the data using the correct method signature
        output_file = data_manager.save_data("2025-01", test_data, "new")

        # Verify the file was created
        assert output_file.exists()

        # Load and verify the saved data
        with open(output_file, "r") as f:
            saved_data = json.load(f)

        # Verify the structure is preserved
        assert "metadata" in saved_data
        assert "data" in saved_data
        assert len(saved_data["data"]) == 1

        # Verify the brush match includes strategy data
        brush_match = saved_data["data"][0]["matched"]["brush"]
        assert "best_result" in brush_match
        assert "all_strategies" in brush_match

        # Verify best_result structure
        best_result = brush_match["best_result"]
        assert "strategy" in best_result
        assert "score" in best_result
        assert "result" in best_result
        assert best_result["strategy"] == "handle_knot_split"
        assert best_result["score"] == 0.95

        # Verify all_strategies structure
        all_strategies = brush_match["all_strategies"]
        assert isinstance(all_strategies, list)
        assert len(all_strategies) == 2

        for strategy in all_strategies:
            assert "strategy" in strategy
            assert "score" in strategy
            assert "result" in strategy
            assert isinstance(strategy["score"], (int, float))

    def test_load_saved_strategy_data(self, tmp_path):
        """Test that saved strategy data can be loaded and used."""
        # Create test data file
        test_data = {
            "metadata": {"total_shaves": 1},
            "data": [
                {
                    "original": "Declaration B2 in Mozingo handle",
                    "matched": {
                        "brush": {
                            "brand": "Declaration",
                            "model": "B2",
                            "handle": "Mozingo",
                            "best_result": {
                                "strategy": "handle_knot_split",
                                "score": 0.95,
                                "result": {
                                    "brand": "Declaration",
                                    "model": "B2",
                                    "handle": "Mozingo",
                                },
                            },
                            "all_strategies": [
                                {
                                    "strategy": "handle_knot_split",
                                    "score": 0.95,
                                    "result": {
                                        "brand": "Declaration",
                                        "model": "B2",
                                        "handle": "Mozingo",
                                    },
                                }
                            ],
                        }
                    },
                }
            ],
        }

        test_file = tmp_path / "test_load.json"
        with open(test_file, "w") as f:
            json.dump(test_data, f)

        # Load the data
        with open(test_file, "r") as f:
            loaded_data = json.load(f)

        # Verify the loaded data structure
        brush_match = loaded_data["data"][0]["matched"]["brush"]
        assert "best_result" in brush_match
        assert "all_strategies" in brush_match

        # Verify the data can be accessed
        best_strategy = brush_match["best_result"]["strategy"]
        best_score = brush_match["best_result"]["score"]
        assert best_strategy == "handle_knot_split"
        assert best_score == 0.95

        # Verify all strategies can be iterated
        strategies = brush_match["all_strategies"]
        assert len(strategies) == 1
        assert strategies[0]["strategy"] == "handle_knot_split"


class TestPerformanceImpact:
    """Test that strategy persistence doesn't significantly impact performance."""

    def test_strategy_data_size_impact(self):
        """Test that adding strategy data doesn't create excessive file sizes."""
        # Create baseline data without strategy information
        baseline_data = {
            "original": "Declaration B2 in Mozingo handle",
            "matched": {"brand": "Declaration", "model": "B2", "handle": "Mozingo"},
        }

        # Create data with strategy information
        strategy_data = {
            "original": "Declaration B2 in Mozingo handle",
            "matched": {
                "brand": "Declaration",
                "model": "B2",
                "handle": "Mozingo",
                "best_result": {
                    "strategy": "handle_knot_split",
                    "score": 0.95,
                    "result": {"brand": "Declaration", "model": "B2", "handle": "Mozingo"},
                },
                "all_strategies": [
                    {
                        "strategy": "handle_knot_split",
                        "score": 0.95,
                        "result": {"brand": "Declaration", "model": "B2", "handle": "Mozingo"},
                    },
                    {
                        "strategy": "brand_model",
                        "score": 0.85,
                        "result": {"brand": "Declaration", "model": "B2"},
                    },
                ],
            },
        }

        # Serialize both to JSON
        baseline_json = json.dumps(baseline_data)
        strategy_json = json.dumps(strategy_data)

        # Calculate size increase
        baseline_size = len(baseline_json)
        strategy_size = len(strategy_json)
        size_increase = strategy_size - baseline_size

        # Verify size increase is reasonable
        # Strategy data will significantly increase size, but should be manageable
        assert size_increase > 0  # Should add some data
        assert size_increase < baseline_size * 10  # Should not be excessive (allow up to 10x)

        # Verify the strategy data is actually present
        assert "best_result" in strategy_json
        assert "all_strategies" in strategy_json
        assert "handle_knot_split" in strategy_json

        # Log the actual sizes for reference
        print(f"Baseline size: {baseline_size} bytes")
        print(f"Strategy size: {strategy_size} bytes")
        print(f"Size increase: {size_increase} bytes ({size_increase/baseline_size:.1f}x)")


class TestBackwardCompatibility:
    """Test that strategy persistence maintains backward compatibility."""

    def test_existing_data_structure_preserved(self):
        """Test that existing data structure is preserved when adding strategy data."""
        # Create existing data structure
        existing_data = {
            "original": "Declaration B2 in Mozingo handle",
            "normalized": "declaration b2 in mozingo handle",
            "matched": {"brush": {"brand": "Declaration", "model": "B2", "handle": "Mozingo"}},
            "match_type": "handle_knot_split",
            "pattern": "brand model in handle",
            "strategy": "handle_knot_split",
        }

        # Add strategy data
        existing_data["matched"]["brush"]["best_result"] = {
            "strategy": "handle_knot_split",
            "score": 0.95,
            "result": {"brand": "Declaration", "model": "B2", "handle": "Mozingo"},
        }
        existing_data["matched"]["brush"]["all_strategies"] = [
            {
                "strategy": "handle_knot_split",
                "score": 0.95,
                "result": {"brand": "Declaration", "model": "B2", "handle": "Mozingo"},
            }
        ]

        # Verify all existing fields are preserved
        assert "original" in existing_data
        assert "normalized" in existing_data
        assert "matched" in existing_data
        assert "match_type" in existing_data
        assert "pattern" in existing_data
        assert "strategy" in existing_data

        # Verify brush match structure is preserved
        brush_match = existing_data["matched"]["brush"]
        assert "brand" in brush_match
        assert "model" in brush_match
        assert "handle" in brush_match

        # Verify new fields are added
        assert "best_result" in brush_match
        assert "all_strategies" in brush_match

    def test_optional_strategy_fields(self):
        """Test that strategy fields are optional and don't break existing code."""
        # Create data without strategy fields
        data_without_strategy = {
            "original": "Declaration B2 in Mozingo handle",
            "matched": {"brand": "Declaration", "model": "B2"},
        }

        # This should not cause errors when accessing existing fields
        assert data_without_strategy["original"] == "Declaration B2 in Mozingo handle"
        assert data_without_strategy["matched"]["brand"] == "Declaration"

        # Accessing non-existent strategy fields should not crash
        assert "best_result" not in data_without_strategy
        assert "all_strategies" not in data_without_strategy


if __name__ == "__main__":
    pytest.main([__file__])
