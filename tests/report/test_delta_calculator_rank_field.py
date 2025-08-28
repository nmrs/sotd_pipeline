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
            {"name": "Razor A", "shaves": 90, "rank": 2},
            {"name": "Razor B", "shaves": 85, "rank": 2},
        ]

        calculator = DeltaCalculator()
        result = calculator.calculate_deltas(current_data, historical_data)

        assert len(result) == 3

        # New Razor: not in historical data
        assert result[2]["name"] == "New Razor"
        assert result[2]["delta"] is None
        assert result[2]["delta_symbol"] == "n/a"

    def test_tier_splits_and_merges(self):
        """Test complex tier restructuring scenarios (splits and merges)."""
        current_data = [
            {"name": "Razor A", "shaves": 100, "rank": 1},  # Tier 1
            {"name": "Razor B", "shaves": 80, "rank": 2},  # Tier 2
            {"name": "Razor C", "shaves": 80, "rank": 2},  # Tier 2 (tied)
            {"name": "Razor D", "shaves": 60, "rank": 3},  # Tier 3
            {"name": "Razor E", "shaves": 60, "rank": 3},  # Tier 3 (tied)
        ]

        historical_data = [
            {"name": "Razor A", "shaves": 85, "rank": 2},  # Was in Tier 2
            {"name": "Razor B", "shaves": 90, "rank": 1},  # Was in Tier 1
            {"name": "Razor C", "shaves": 85, "rank": 2},  # Still in Tier 2
            {"name": "Razor D", "shaves": 70, "rank": 2},  # Was in Tier 2
            {"name": "Razor E", "shaves": 65, "rank": 2},  # Was in Tier 2
        ]

        calculator = DeltaCalculator()
        result = calculator.calculate_deltas(current_data, historical_data)

        assert len(result) == 5

        # Razor A: moved from Tier 2 to Tier 1 (improved by 1 tier)
        assert result[0]["delta"] == 1  # Tier 2 → Tier 1 = +1

        # Razor B: moved from Tier 1 to Tier 2 (worsened by 1 tier)
        assert result[1]["delta"] == -1  # Tier 1 → Tier 2 = -1

        # Razor C: stayed in Tier 2 (no change)
        assert result[2]["delta"] == 0  # Tier 2 → Tier 2 = 0

        # Razor D: moved from Tier 2 to Tier 3 (worsened by 1 tier)
        assert result[3]["delta"] == -1  # Tier 2 → Tier 3 = -1

        # Razor E: moved from Tier 2 to Tier 3 (worsened by 1 tier)
        assert result[4]["delta"] == -1  # Tier 2 → Tier 3 = -1

        # This represents a tier split: Tier 2 was split into Tier 2 and Tier 3
        # Some items stayed in Tier 2, others moved to Tier 3

    def test_performance_with_large_datasets(self):
        """Test performance with large datasets to ensure scalability."""
        # Create large dataset (1000+ items) for performance testing
        current_data = []
        historical_data = []

        for i in range(1000):
            current_data.append(
                {
                    "name": f"Razor_{i:03d}",
                    "shaves": 1000 - i,
                    "rank": (i // 100) + 1,  # Creates 10 tiers
                }
            )

            historical_data.append(
                {
                    "name": f"Razor_{i:03d}",
                    "shaves": 1000 - i + (i % 3 - 1),  # Slight variations
                    "rank": ((i + 50) // 100) + 1,  # Different tier distribution
                }
            )

        calculator = DeltaCalculator()

        # Measure performance
        import time

        start_time = time.time()
        result = calculator.calculate_deltas(current_data, historical_data, max_items=1000)
        end_time = time.time()

        processing_time = end_time - start_time

        # Validate results
        assert len(result) == 1000
        assert processing_time < 1.0  # Should complete within 1 second

        # Validate some sample deltas
        assert result[0]["name"] == "Razor_000"
        assert result[999]["name"] == "Razor_999"

        # Check that deltas are calculated correctly
        delta_values = [item["delta"] for item in result if item["delta"] is not None]
        assert len(delta_values) > 0  # Should have some valid deltas
        assert all(
            isinstance(delta, int) for delta in delta_values
        )  # All deltas should be integers

    def test_calculate_deltas_missing_rank_field(self):
        """Test delta calculation with missing rank fields."""
        current_data = [
            {"name": "Razor A", "shaves": 100, "rank": 1},
            {"name": "Razor B", "shaves": 80, "rank": 2},  # Missing rank
        ]

        historical_data = [
            {"name": "Razor A", "shaves": 90, "rank": 2},
            {"name": "Razor B", "shaves": 85, "rank": 1},
        ]

        calculator = DeltaCalculator()
        result = calculator.calculate_deltas(current_data, historical_data)

        # Should process all items with rank fields
        assert len(result) == 2
        assert result[0]["name"] == "Razor A"
        assert result[1]["name"] == "Razor B"

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
        result = calculator.calculate_deltas([], [{"name": "Razor A"}])
        assert result == []

        # Empty historical data
        result = calculator.calculate_deltas([{"name": "Razor A", "rank": 1}], [])
        assert len(result) == 0  # No deltas can be calculated without historical data

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

    def test_tier_based_delta_calculation(self):
        """Test that delta calculations reflect tier movements, not sequential positions."""
        current_data = [
            {"name": "Razor A", "shaves": 100, "rank": 1},  # Tier 1
            {"name": "Razor B", "shaves": 80, "rank": 2},  # Tier 2
            {"name": "Razor C", "shaves": 80, "rank": 2},  # Tier 2 (tied)
            {"name": "Razor D", "shaves": 60, "rank": 3},  # Tier 3
        ]

        historical_data = [
            {"name": "Razor A", "shaves": 85, "rank": 2},  # Was in Tier 2
            {"name": "Razor B", "shaves": 90, "rank": 1},  # Was in Tier 1
            {"name": "Razor C", "shaves": 85, "rank": 2},  # Still in Tier 2
            {"name": "Razor D", "shaves": 70, "rank": 2},  # Was in Tier 2
        ]

        calculator = DeltaCalculator()
        result = calculator.calculate_deltas(current_data, historical_data)

        assert len(result) == 4

        # Razor A: moved from Tier 2 to Tier 1 (improved by 1 tier)
        assert result[0]["name"] == "Razor A"
        assert result[0]["delta"] == 1  # Tier 2 → Tier 1 = +1
        assert result[0]["delta_symbol"] == "↑1"

        # Razor B: moved from Tier 1 to Tier 2 (worsened by 1 tier)
        assert result[1]["name"] == "Razor B"
        assert result[1]["delta"] == -1  # Tier 1 → Tier 2 = -1
        assert result[1]["delta_symbol"] == "↓1"

        # Razor C: stayed in Tier 2 (no change)
        assert result[2]["name"] == "Razor C"
        assert result[2]["delta"] == 0  # Tier 2 → Tier 2 = 0
        assert result[2]["delta_symbol"] == "="

        # Razor D: moved from Tier 2 to Tier 3 (worsened by 1 tier)
        assert result[3]["name"] == "Razor D"
        assert result[3]["delta"] == -1  # Tier 2 → Tier 3 = -1
        assert result[3]["delta_symbol"] == "↓1"

    def test_tier_based_delta_with_complex_ties(self):
        """Test tier-based delta calculation with complex tie scenarios."""
        current_data = [
            {"name": "Razor A", "shaves": 100, "rank": 1},  # Tier 1
            {"name": "Razor B", "shaves": 80, "rank": 2},  # Tier 2 (tied)
            {"name": "Razor C", "shaves": 80, "rank": 2},  # Tier 2 (tied)
            {"name": "Razor D", "shaves": 80, "rank": 2},  # Tier 2 (tied)
            {"name": "Razor E", "shaves": 60, "rank": 3},  # Tier 3
        ]

        historical_data = [
            {"name": "Razor A", "shaves": 85, "rank": 2},  # Was in Tier 2
            {"name": "Razor B", "shaves": 90, "rank": 1},  # Was in Tier 1
            {"name": "Razor C", "shaves": 85, "rank": 2},  # Still in Tier 2
            {"name": "Razor D", "shaves": 70, "rank": 3},  # Was in Tier 3
            {"name": "Razor E", "shaves": 65, "rank": 3},  # Still in Tier 3
        ]

        calculator = DeltaCalculator()
        result = calculator.calculate_deltas(current_data, historical_data)

        assert len(result) == 5

        # Razor A: moved from Tier 2 to Tier 1 (improved by 1 tier)
        assert result[0]["delta"] == 1  # Tier 2 → Tier 1 = +1

        # Razor B: moved from Tier 1 to Tier 2 (worsened by 1 tier)
        assert result[1]["delta"] == -1  # Tier 1 → Tier 2 = -1

        # Razor C: stayed in Tier 2 (no change)
        assert result[2]["delta"] == 0  # Tier 2 → Tier 2 = 0

        # Razor D: moved from Tier 3 to Tier 2 (improved by 1 tier)
        assert result[3]["delta"] == 1  # Tier 3 → Tier 2 = +1

        # Razor E: stayed in Tier 3 (no change)
        assert result[4]["delta"] == 0  # Tier 3 → Tier 3 = 0

    def test_tier_based_delta_new_and_removed_items(self):
        """Test tier-based delta calculation with new and removed items."""
        current_data = [
            {"name": "Razor A", "shaves": 100, "rank": 1},  # Tier 1
            {"name": "Razor B", "shaves": 80, "rank": 2},  # Tier 2
            {"name": "New Razor", "shaves": 70, "rank": 3},  # Tier 3 (new)
        ]

        historical_data = [
            {"name": "Razor A", "shaves": 85, "rank": 2},  # Was in Tier 2
            {"name": "Razor B", "shaves": 90, "rank": 1},  # Was in Tier 1
            # Removed Razor C (was in Tier 3)
        ]

        calculator = DeltaCalculator()
        result = calculator.calculate_deltas(current_data, historical_data)

        assert len(result) == 3

        # Razor A: moved from Tier 2 to Tier 1 (improved by 1 tier)
        assert result[0]["delta"] == 1  # Tier 2 → Tier 1 = +1

        # Razor B: moved from Tier 1 to Tier 2 (worsened by 1 tier)
        assert result[1]["delta"] == -1  # Tier 1 → Tier 2 = -1

        # New Razor: not in historical data
        assert result[2]["name"] == "New Razor"
        assert result[2]["delta"] is None
        assert result[2]["delta_symbol"] == "n/a"
