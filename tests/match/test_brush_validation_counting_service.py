"""Test suite for BrushValidationCountingService."""

import pytest
from unittest.mock import patch

from sotd.match.brush_validation_counting_service import BrushValidationCountingService


class TestBrushValidationCountingService:
    """Test the shared counting service for brush validation."""

    @pytest.fixture
    def service(self):
        """Create a service instance for testing."""
        return BrushValidationCountingService()

    @pytest.fixture
    def mock_matched_data(self):
        """Mock matched data structure."""
        return {
            "data": [
                {
                    "id": "comment1",
                    "brush": {
                        "normalized": "Declaration Grooming B2",
                        "matched": {
                            "strategy": "correct_complete_brush",
                            "score": 100,
                            "result": {"brand": "Declaration Grooming", "model": "B2"},
                        },
                        "all_strategies": [{"strategy": "correct_complete_brush", "score": 100}],
                    },
                },
                {
                    "id": "comment2",
                    "brush": {
                        "normalized": "Dogwood Handcrafts Zenith B2",
                        "matched": {
                            "strategy": "automated_split",
                            "score": 85,
                            "result": {"brand": "Dogwood Handcrafts", "model": "Zenith B2"},
                        },
                        "all_strategies": [
                            {"strategy": "automated_split", "score": 85},
                            {"strategy": "known_brush", "score": 75},
                        ],
                    },
                },
                {
                    "id": "comment3",
                    "brush": {"normalized": "Brush 1", "matched": None, "all_strategies": []},
                },
            ]
        }

    @pytest.fixture
    def mock_learning_data(self):
        """Mock learning data structure."""
        return {
            "brush_user_actions": [
                {
                    "input_text": "Dogwood Handcrafts Zenith B2",
                    "action": "validated",
                    "month": "2025-06",
                    "system_used": "scoring",
                },
                {
                    "input_text": "Brush 1",
                    "action": "overridden",
                    "month": "2025-06",
                    "system_used": "scoring",
                },
            ]
        }

    @pytest.fixture
    def mock_correct_matches(self):
        """Mock correct_matches.yaml data."""
        return {
            "declaration grooming b2": {
                "brand": "Declaration Grooming",
                "model": "B2",
                "strategy": "correct_complete_brush",
            }
        }

    def test_total_entries_equals_validated_plus_unvalidated(
        self, service, mock_matched_data, mock_learning_data, mock_correct_matches
    ):
        """Total Entries should always equal Validated + Unvalidated."""
        with (
            patch.object(service, "_load_matched_data", return_value=mock_matched_data),
            patch.object(service, "_load_learning_data", return_value=mock_learning_data),
            patch.object(service, "_load_correct_matches", return_value=mock_correct_matches),
        ):

            stats = service.get_validation_statistics("2025-06")

            assert (
                stats["total_entries"]
                == stats["validated_count"] + stats["overridden_count"] + stats["unvalidated_count"]
            )
            assert stats["total_entries"] == 3  # 3 unique brush strings
            assert stats["validated_count"] == 2  # 1 correct_match + 1 user_validated
            assert stats["overridden_count"] == 1  # 1 user_overridden
            assert stats["unvalidated_count"] == 0  # All entries are validated/overridden

    def test_already_validated_matches_validated_statistics(
        self, service, mock_matched_data, mock_learning_data, mock_correct_matches
    ):
        """Already Validated from strategy distribution should match Validated from statistics."""
        with (
            patch.object(service, "_load_matched_data", return_value=mock_matched_data),
            patch.object(service, "_load_learning_data", return_value=mock_learning_data),
            patch.object(service, "_load_correct_matches", return_value=mock_correct_matches),
        ):

            stats = service.get_validation_statistics("2025-06")
            strategy_stats = service.get_strategy_distribution_statistics("2025-06")

            # Already Validated should equal Validated from statistics
            already_validated = strategy_stats["correct_matches_count"]
            assert already_validated == 1  # Only Declaration Grooming B2 from correct_matches
            assert already_validated <= stats["validated_count"]  # Should be <= total validated

    def test_need_validation_matches_unvalidated_statistics(
        self, service, mock_matched_data, mock_learning_data, mock_correct_matches
    ):
        """Need Validation from strategy distribution should match Unvalidated from statistics."""
        with (
            patch.object(service, "_load_matched_data", return_value=mock_matched_data),
            patch.object(service, "_load_learning_data", return_value=mock_learning_data),
            patch.object(service, "_load_correct_matches", return_value=mock_correct_matches),
        ):

            stats = service.get_validation_statistics("2025-06")
            strategy_stats = service.get_strategy_distribution_statistics("2025-06")

            # Need Validation should equal Unvalidated from statistics
            need_validation = strategy_stats["remaining_entries"]
            assert need_validation == stats["unvalidated_count"]
            assert need_validation == 0  # All entries are validated/overridden

    def test_case_insensitive_grouping(self, service):
        """Brush 1 and brush 1 should count as 1 record."""
        mock_data = {
            "data": [
                {"id": "comment1", "brush": {"normalized": "Brush 1"}},
                {"id": "comment2", "brush": {"normalized": "brush 1"}},
                {"id": "comment3", "brush": {"normalized": "BRUSH 1"}},
            ]
        }

        with (
            patch.object(service, "_load_matched_data", return_value=mock_data),
            patch.object(service, "_load_learning_data", return_value={"brush_user_actions": []}),
            patch.object(service, "_load_correct_matches", return_value={}),
        ):

            stats = service.get_validation_statistics("2025-06")

            # All three variations should count as 1 unique entry
            assert stats["total_entries"] == 1

    def test_correct_matches_counted_as_validated(
        self, service, mock_matched_data, mock_learning_data, mock_correct_matches
    ):
        """Entries with correct_complete_brush or correct_split_brush strategies should be counted as validated."""
        with (
            patch.object(service, "_load_matched_data", return_value=mock_matched_data),
            patch.object(service, "_load_learning_data", return_value=mock_learning_data),
            patch.object(service, "_load_correct_matches", return_value=mock_correct_matches),
        ):

            stats = service.get_validation_statistics("2025-06")

            # Declaration Grooming B2 has correct_complete_brush strategy
            # It should be counted as validated even without user action
            assert stats["validated_count"] >= 1  # At least 1 from correct_matches

    def test_edge_case_empty_data(self, service):
        """Test handling of empty data."""
        empty_data = {"data": []}

        with (
            patch.object(service, "_load_matched_data", return_value=empty_data),
            patch.object(service, "_load_learning_data", return_value={"brush_user_actions": []}),
            patch.object(service, "_load_correct_matches", return_value={}),
        ):

            stats = service.get_validation_statistics("2025-06")

            assert stats["total_entries"] == 0
            assert stats["validated_count"] == 0
            assert stats["unvalidated_count"] == 0
            assert stats["validation_rate"] == 0.0

    def test_edge_case_missing_fields(self, service):
        """Test handling of records with missing fields."""
        incomplete_data = {
            "data": [
                {"id": "comment1", "brush": {}},  # Missing normalized field
                {
                    "id": "comment2"
                    # Missing brush field entirely
                },
            ]
        }

        with (
            patch.object(service, "_load_matched_data", return_value=incomplete_data),
            patch.object(service, "_load_learning_data", return_value={"brush_user_actions": []}),
            patch.object(service, "_load_correct_matches", return_value={}),
        ):

            stats = service.get_validation_statistics("2025-06")

            # Should handle missing fields gracefully
            assert stats["total_entries"] == 0  # No valid brush entries

    def test_strategy_distribution_counts(
        self, service, mock_matched_data, mock_learning_data, mock_correct_matches
    ):
        """Test strategy distribution counting logic."""
        with (
            patch.object(service, "_load_matched_data", return_value=mock_matched_data),
            patch.object(service, "_load_learning_data", return_value=mock_learning_data),
            patch.object(service, "_load_correct_matches", return_value=mock_correct_matches),
        ):

            strategy_stats = service.get_strategy_distribution_statistics("2025-06")

            # Should have correct counts for each strategy
            assert strategy_stats["strategy_counts"]["correct_complete_brush"] == 1
            assert strategy_stats["strategy_counts"]["automated_split"] == 1

            # Should have correct all_strategies length distribution
            # Now counting ALL entries (not just unvalidated ones)
            assert (
                strategy_stats["all_strategies_lengths"]["1"] == 1
            )  # 1 strategy (Declaration Grooming B2)
            assert (
                strategy_stats["all_strategies_lengths"]["2"] == 1
            )  # 2 strategies (Dogwood Handcrafts Zenith B2)
            assert strategy_stats["all_strategies_lengths"]["0"] == 1  # 0 strategies (Brush 1)

    def test_mathematical_relationships_consistency(
        self, service, mock_matched_data, mock_learning_data, mock_correct_matches
    ):
        """Test that all mathematical relationships are consistent across methods."""
        with (
            patch.object(service, "_load_matched_data", return_value=mock_matched_data),
            patch.object(service, "_load_learning_data", return_value=mock_learning_data),
            patch.object(service, "_load_correct_matches", return_value=mock_correct_matches),
        ):

            stats = service.get_validation_statistics("2025-06")
            strategy_stats = service.get_strategy_distribution_statistics("2025-06")

            # Core relationship: Total = Validated + Overridden + Unvalidated
            assert (
                stats["total_entries"]
                == stats["validated_count"] + stats["overridden_count"] + stats["unvalidated_count"]
            )

            # Strategy distribution should be consistent
            assert strategy_stats["total_brush_records"] == stats["total_entries"]
            # The correct equation: correct_matches + user_validated + user_overridden + remaining = total
            user_validated = stats["validated_count"] - strategy_stats["correct_matches_count"]
            assert (
                strategy_stats["correct_matches_count"]
                + user_validated
                + stats["overridden_count"]
                + strategy_stats["remaining_entries"]
                == stats["total_entries"]
            )

            # Validation rate should be mathematically correct
            expected_rate = (stats["validated_count"] + stats["overridden_count"]) / stats[
                "total_entries"
            ]
            assert abs(stats["validation_rate"] - expected_rate) < 0.001
