#!/usr/bin/env python3
"""Tests for DeltaCalculator rank field updates (Step 2.1.1)."""

from sotd.report.delta_calculator import DeltaCalculator


class TestDeltaCalculatorRankField:
    """Test DeltaCalculator with rank field instead of position field."""

    def test_calculate_deltas_with_rank_field(self):
        """Test basic delta calculation with rank field instead of position field."""
        current_data = [
            {"name": "Razor A", "shaves": 100, "rank": 1},
            {"name": "Razor B", "shaves": 80, "rank": 2},
            {"name": "Razor C", "shaves": 60, "rank": 3},
        ]

        historical_data = [
            {"name": "Razor B", "shaves": 90, "rank": 1},
            {"name": "Razor A", "shaves": 85, "rank": 2},
            {"name": "Razor C", "shaves": 70, "rank": 3},
        ]

        calculator = DeltaCalculator()
        result = calculator.calculate_deltas(current_data, historical_data)

        assert len(result) == 3

        # Razor A: moved from rank 2 to 1 (improved by 1)
        assert result[0]["name"] == "Razor A"
        assert result[0]["delta"] == 1
        assert result[0]["delta_symbol"] == "↑1"  # Improved by 1 rank
        assert result[0]["delta_text"] == "↑1"  # Improved by 1 rank

        # Razor B: moved from rank 1 to 2 (worsened by 1)
        assert result[1]["name"] == "Razor B"
        assert result[1]["delta"] == -1
        assert result[1]["delta_symbol"] == "↓1"  # Worsened by 1 rank
        assert result[1]["delta_text"] == "↓1"  # Worsened by 1 rank

        # Razor C: stayed at rank 3 (no change)
        assert result[2]["name"] == "Razor C"
        assert result[2]["delta"] == 0
        assert result[2]["delta_symbol"] == "="
        assert result[2]["delta_text"] == "="

    def test_calculate_deltas_new_item_with_rank(self):
        """Test delta calculation with new items not in historical data using rank field."""
        current_data = [
            {"name": "Razor A", "shaves": 100, "rank": 1},
            {"name": "Razor B", "shaves": 80, "rank": 2},
            {"name": "New Razor", "shaves": 60, "rank": 3},
        ]

        historical_data = [
            {"name": "Razor A", "shaves": 90, "rank": 1},
            {"name": "Razor B", "shaves": 85, "rank": 2},
        ]

        calculator = DeltaCalculator()
        result = calculator.calculate_deltas(current_data, historical_data)

        assert len(result) == 3

        # New Razor: not in historical data
        assert result[2]["name"] == "New Razor"
        assert result[2]["delta"] is None
        assert result[2]["delta_symbol"] == "n/a"
        assert result[2]["delta_text"] == "n/a"

    def test_calculate_deltas_missing_rank_field(self):
        """Test delta calculation with missing rank fields."""
        current_data = [
            {"name": "Razor A", "shaves": 100, "rank": 1},
            {"name": "Razor B", "shaves": 80},  # Missing rank
        ]

        historical_data = [
            {"name": "Razor A", "shaves": 90, "rank": 2},
            {"name": "Razor B", "shaves": 85, "rank": 1},
        ]

        calculator = DeltaCalculator()
        result = calculator.calculate_deltas(current_data, historical_data)

        # Should only process items with rank fields
        assert len(result) == 1
        assert result[0]["name"] == "Razor A"

    def test_calculate_deltas_tier_based_ranking(self):
        """Test delta calculation with tier-based ranking (items with same rank)."""
        current_data = [
            {"name": "Razor A", "shaves": 100, "rank": 1},  # Tier 1
            {"name": "Razor B", "shaves": 80, "rank": 2},  # Tier 2 (tied)
            {"name": "Razor C", "shaves": 80, "rank": 2},  # Tier 2 (tied)
            {"name": "Razor D", "shaves": 60, "rank": 3},  # Tier 3
        ]

        historical_data = [
            {"name": "Razor A", "shaves": 90, "rank": 2},  # Was in Tier 2
            {"name": "Razor B", "shaves": 85, "rank": 1},  # Was in Tier 1
            {"name": "Razor C", "shaves": 85, "rank": 1},  # Was in Tier 1
            {"name": "Razor D", "shaves": 70, "rank": 2},  # Was in Tier 2
        ]

        calculator = DeltaCalculator()
        result = calculator.calculate_deltas(current_data, historical_data)

        assert len(result) == 4

        # Razor A: moved from Tier 2 to Tier 1 (improved by 1 tier)
        assert result[0]["name"] == "Razor A"
        assert result[0]["delta"] == 1
        assert result[0]["delta_symbol"] == "↑1"

        # Razor B: moved from Tier 1 to Tier 2 (worsened by 1 tier)
        assert result[1]["name"] == "Razor B"
        assert result[1]["delta"] == -1
        assert result[1]["delta_symbol"] == "↓1"

        # Razor C: moved from Tier 1 to Tier 2 (worsened by 1 tier)
        assert result[2]["name"] == "Razor C"
        assert result[2]["delta"] == -1
        assert result[2]["delta_symbol"] == "↓1"

        # Razor D: moved from Tier 2 to Tier 3 (worsened by 1 tier)
        assert result[3]["name"] == "Razor D"
        assert result[3]["delta"] == -1
        assert result[3]["delta_symbol"] == "↓1"

    def test_calculate_deltas_empty_data_with_rank(self):
        """Test delta calculation with empty data using rank field."""
        calculator = DeltaCalculator()

        # Empty current data
        result = calculator.calculate_deltas([], [{"name": "Razor A", "rank": 1}])
        assert result == []

        # Empty historical data
        result = calculator.calculate_deltas([{"name": "Razor A", "rank": 1}], [])
        assert len(result) == 1
        assert result[0]["delta"] is None
        assert result[0]["delta_symbol"] == "n/a"

    def test_calculate_deltas_debug_mode_with_rank(self):
        """Test delta calculation debug mode with rank field."""
        current_data = [
            {"name": "Razor A", "shaves": 100, "rank": 1},
            {"name": "Razor B", "shaves": 80, "rank": 2},
        ]

        historical_data = [
            {"name": "Razor A", "shaves": 90, "rank": 2},
            {"name": "Razor B", "shaves": 85, "rank": 1},
        ]

        calculator = DeltaCalculator(debug=True)
        result = calculator.calculate_deltas(current_data, historical_data)

        # Should work with debug mode and rank field
        assert len(result) == 2
        assert result[0]["delta"] == 1  # Razor A improved
        assert result[1]["delta"] == -1  # Razor B worsened
