#!/usr/bin/env python3
"""Tests for AnnualDeltaCalculator rank field updates (Step 2.2.1)."""

from sotd.report.annual_delta_calculator import AnnualDeltaCalculator


class TestAnnualDeltaCalculatorRankField:
    """Test AnnualDeltaCalculator with rank field instead of position field."""

    def test_calculate_annual_deltas_with_rank_field(self):
        """Test basic annual delta calculation with rank field instead of position field."""
        current_year_data = {
            "year": "2024",
            "meta": {"total_shaves": 1200, "unique_shavers": 100},
            "data": {
                "razors": [
                    {"name": "Razor A", "shaves": 100, "rank": 1},
                    {"name": "Razor B", "shaves": 80, "rank": 2},
                    {"name": "Razor C", "shaves": 60, "rank": 3},
                ],
                "blades": [
                    {"name": "Blade A", "shaves": 50, "rank": 1},
                    {"name": "Blade B", "shaves": 40, "rank": 2},
                ],
            },
        }

        previous_year_data = {
            "year": "2023",
            "meta": {"total_shaves": 1100, "unique_shavers": 95},
            "data": {
                "razors": [
                    {"name": "Razor B", "shaves": 90, "rank": 1},
                    {"name": "Razor A", "shaves": 85, "rank": 2},
                    {"name": "Razor C", "shaves": 70, "rank": 3},
                ],
                "blades": [
                    {"name": "Blade A", "shaves": 45, "rank": 1},
                    {"name": "Blade B", "shaves": 35, "rank": 2},
                ],
            },
        }

        calculator = AnnualDeltaCalculator()
        result = calculator.calculate_annual_deltas(current_year_data, previous_year_data)

        # Check razors
        assert "razors" in result
        razors = result["razors"]
        assert len(razors) == 3

        # Razor A: moved from rank 2 to rank 1 (improved by 1 tier)
        assert razors[0]["name"] == "Razor A"
        assert razors[0]["delta"] == 1
        assert razors[0]["delta_symbol"] == "↑1"

        # Razor B: moved from rank 1 to rank 2 (worsened by 1 tier)
        assert razors[1]["name"] == "Razor B"
        assert razors[1]["delta"] == -1
        assert razors[1]["delta_symbol"] == "↓1"

        # Razor C: stayed at rank 3 (no change)
        assert razors[2]["name"] == "Razor C"
        assert razors[2]["delta"] == 0
        assert razors[2]["delta_symbol"] == "="

        # Check blades
        assert "blades" in result
        blades = result["blades"]
        assert len(blades) == 2

        # Blade A: stayed at rank 1 (no change)
        assert blades[0]["name"] == "Blade A"
        assert blades[0]["delta"] == 0
        assert blades[0]["delta_symbol"] == "="

        # Blade B: stayed at rank 2 (no change)
        assert blades[1]["name"] == "Blade B"
        assert blades[1]["delta"] == 0
        assert blades[1]["delta_symbol"] == "="

    def test_calculate_annual_deltas_new_items_with_rank(self):
        """Test annual delta calculation with new items not in previous year."""
        current_year_data = {
            "year": "2024",
            "meta": {"total_shaves": 1200, "unique_shavers": 100},
            "data": {
                "razors": [
                    {"name": "Razor A", "shaves": 100, "rank": 1},
                    {"name": "New Razor", "shaves": 80, "rank": 2},
                ],
            },
        }

        previous_year_data = {
            "year": "2023",
            "meta": {"total_shaves": 1100, "unique_shavers": 95},
            "data": {
                "razors": [
                    {"name": "Razor A", "shaves": 90, "rank": 2},
                ],
            },
        }

        calculator = AnnualDeltaCalculator()
        result = calculator.calculate_annual_deltas(current_year_data, previous_year_data)

        razors = result["razors"]
        assert len(razors) == 2

        # Razor A: moved from rank 2 to rank 1 (improved by 1 tier)
        assert razors[0]["name"] == "Razor A"
        assert razors[0]["delta"] == 1
        assert razors[0]["delta_symbol"] == "↑1"

        # New Razor: not in previous year data
        assert razors[1]["name"] == "New Razor"
        assert razors[1]["delta"] is None
        assert razors[1]["delta_symbol"] == "n/a"

    def test_calculate_annual_deltas_missing_rank_field(self):
        """Test annual delta calculation with missing rank fields."""
        current_year_data = {
            "year": "2024",
            "meta": {"total_shaves": 1200, "unique_shavers": 100},
            "data": {
                "razors": [
                    {"name": "Razor A", "shaves": 100, "rank": 1},
                    {"name": "Razor B", "shaves": 80},  # Missing rank
                ],
            },
        }

        previous_year_data = {
            "year": "2023",
            "meta": {"total_shaves": 1100, "unique_shavers": 95},
            "data": {
                "razors": [
                    {"name": "Razor A", "shaves": 90, "rank": 2},
                    {"name": "Razor B", "shaves": 85, "rank": 1},
                ],
            },
        }

        calculator = AnnualDeltaCalculator()
        result = calculator.calculate_annual_deltas(current_year_data, previous_year_data)

        # Should only process items with rank fields
        razors = result["razors"]
        assert len(razors) == 1
        assert razors[0]["name"] == "Razor A"

    def test_calculate_annual_deltas_empty_data_with_rank(self):
        """Test annual delta calculation with empty data using rank field."""
        calculator = AnnualDeltaCalculator()

        # Empty current year data
        result = calculator.calculate_annual_deltas(
            {"year": "2024", "meta": {}, "data": {}},
            {"year": "2023", "meta": {}, "data": {"razors": [{"name": "Razor A", "rank": 1}]}}
        )
        assert result == {}

        # Empty previous year data
        result = calculator.calculate_annual_deltas(
            {"year": "2024", "meta": {}, "data": {"razors": [{"name": "Razor A", "rank": 1}]}},
            {"year": "2023", "meta": {}, "data": {}}
        )
        razors = result["razors"]
        assert len(razors) == 1
        assert razors[0]["delta"] is None
        assert razors[0]["delta_symbol"] == "n/a"

    def test_calculate_annual_deltas_debug_mode_with_rank(self):
        """Test annual delta calculation debug mode with rank field."""
        current_year_data = {
            "year": "2024",
            "meta": {"total_shaves": 1200, "unique_shavers": 100},
            "data": {
                "razors": [
                    {"name": "Razor A", "shaves": 100, "rank": 1},
                    {"name": "Razor B", "shaves": 80, "rank": 2},
                ],
            },
        }

        previous_year_data = {
            "year": "2023",
            "meta": {"total_shaves": 1100, "unique_shavers": 95},
            "data": {
                "razors": [
                    {"name": "Razor A", "shaves": 90, "rank": 2},
                    {"name": "Razor B", "shaves": 85, "rank": 1},
                ],
            },
        }

        calculator = AnnualDeltaCalculator(debug=True)
        result = calculator.calculate_annual_deltas(current_year_data, previous_year_data)

        # Should work with debug mode and rank field
        razors = result["razors"]
        assert len(razors) == 2
        assert razors[0]["delta"] == 1  # Razor A improved
        assert razors[1]["delta"] == -1  # Razor B worsened

    def test_calculate_multi_year_deltas_with_rank_field(self):
        """Test multi-year delta calculation with rank field."""
        current_year_data = {
            "year": "2024",
            "data": {
                "razors": [
                    {"name": "Razor A", "shaves": 100, "rank": 1},
                ],
            },
        }

        comparison_years_data = {
            "2023": {
                "year": "2023",
                "data": {
                    "razors": [
                        {"name": "Razor A", "shaves": 90, "rank": 2},
                    ],
                },
            },
            "2022": {
                "year": "2022",
                "data": {
                    "razors": [
                        {"name": "Razor A", "shaves": 80, "rank": 3},
                    ],
                },
            },
        }

        calculator = AnnualDeltaCalculator()
        result = calculator.calculate_multi_year_deltas(
            current_year_data, comparison_years_data, categories=["razors"]
        )

        assert "razors" in result
        razors = result["razors"]
        assert len(razors) == 1

        razor_a = razors[0]
        assert razor_a["name"] == "Razor A"

        # Should have delta information for both comparison years
        assert "delta_symbol_2023" in razor_a
        assert "delta_symbol_2022" in razor_a

        # 2023 comparison: rank 2 → rank 1 = improved by 1 tier
        assert razor_a["delta_symbol_2023"] == "↑1"

        # 2022 comparison: rank 3 → rank 1 = improved by 2 tiers
        assert razor_a["delta_symbol_2022"] == "↑2"

    def test_get_delta_column_config_with_rank_field(self):
        """Test that delta column configuration works with rank field terminology."""
        calculator = AnnualDeltaCalculator()
        config = calculator.get_delta_column_config(["2023", "2022"])

        # Should include rank delta columns
        assert "delta_rank_2023" in config
        assert "delta_rank_2022" in config

        # Check column titles
        assert config["delta_rank_2023"]["title"] == "Δ Rank 2023"
        assert config["delta_rank_2022"]["title"] == "Δ Rank 2022"

        # Check other delta columns
        assert "delta_shaves_2023" in config
        assert "delta_unique_users_2023" in config

    def test_annual_missing_month_handling(self):
        """Test handling of incomplete annual data (missing months)."""
        current_year_data = {
            "year": "2024",
            "meta": {"total_shaves": 800, "unique_shavers": 80},  # Lower due to missing months
            "data": {
                "razors": [
                    {"name": "Razor A", "shaves": 80, "rank": 1},  # Tier 1
                    {"name": "Razor B", "shaves": 60, "rank": 2},  # Tier 2
                ],
            },
        }

        previous_year_data = {
            "year": "2023",
            "meta": {"total_shaves": 1200, "unique_shavers": 100},  # Complete year
            "data": {
                "razors": [
                    {"name": "Razor A", "shaves": 100, "rank": 2},  # Was in Tier 2
                    {"name": "Razor B", "shaves": 120, "rank": 1},  # Was in Tier 1
                ],
            },
        }

        calculator = AnnualDeltaCalculator()
        result = calculator.calculate_annual_deltas(current_year_data, previous_year_data)

        razors = result["razors"]
        assert len(razors) == 2

        # Razor A: rank 2 → rank 1 = improved by 1 tier
        assert razors[0]["delta"] == 1
        assert razors[0]["delta_symbol"] == "↑1"

        # Razor B: rank 1 → rank 2 = worsened by 1 tier
        assert razors[1]["delta"] == -1
        assert razors[1]["delta_symbol"] == "↓1"

    def test_annual_data_gap_scenarios(self):
        """Test handling of missing historical data (data gaps)."""
        current_year_data = {
            "year": "2024",
            "data": {
                "razors": [
                    {"name": "Razor A", "shaves": 100, "rank": 1},
                    {"name": "Razor B", "shaves": 80, "rank": 2},
                ],
            },
        }

        # Historical data with gaps (missing some months)
        previous_year_data = {
            "year": "2023",
            "data": {
                "razors": [
                    {"name": "Razor A", "shaves": 90, "rank": 2},  # Only partial data
                    # Razor B missing from historical data (data gap)
                ],
            },
        }

        calculator = AnnualDeltaCalculator()
        result = calculator.calculate_annual_deltas(current_year_data, previous_year_data)

        razors = result["razors"]
        assert len(razors) == 2

        # Razor A: rank 2 → rank 1 = improved by 1 tier
        assert razors[0]["delta"] == 1
        assert razors[0]["delta_symbol"] == "↑1"

        # Razor B: not in historical data (new item or data gap)
        assert razors[1]["delta"] is None
        assert razors[1]["delta_symbol"] == "n/a"

    def test_annual_tie_scenarios(self):
        """Test annual delta calculation with items tied at same rank."""
        current_year_data = {
            "year": "2024",
            "data": {
                "razors": [
                    {"name": "Razor A", "shaves": 100, "rank": 1},  # Tier 1
                    {"name": "Razor B", "shaves": 80, "rank": 2},   # Tier 2 (tied)
                    {"name": "Razor C", "shaves": 80, "rank": 2},   # Tier 2 (tied)
                    {"name": "Razor D", "shaves": 60, "rank": 3},   # Tier 3
                ],
            },
        }

        previous_year_data = {
            "year": "2023",
            "data": {
                "razors": [
                    {"name": "Razor A", "shaves": 90, "rank": 2},   # Was in Tier 2
                    {"name": "Razor B", "shaves": 100, "rank": 1},  # Was in Tier 1
                    {"name": "Razor C", "shaves": 90, "rank": 2},   # Was in Tier 2
                    {"name": "Razor D", "shaves": 70, "rank": 3},   # Was in Tier 3
                ],
            },
        }

        calculator = AnnualDeltaCalculator()
        result = calculator.calculate_annual_deltas(current_year_data, previous_year_data)

        razors = result["razors"]
        assert len(razors) == 4

        # Razor A: rank 2 → rank 1 = improved by 1 tier
        assert razors[0]["delta"] == 1
        assert razors[0]["delta_symbol"] == "↑1"

        # Razor B: rank 1 → rank 2 = worsened by 1 tier
        assert razors[1]["delta"] == -1
        assert razors[1]["delta_symbol"] == "↓1"

        # Razor C: rank 2 → rank 2 = no change
        assert razors[2]["delta"] == 0
        assert razors[2]["delta_symbol"] == "="

        # Razor D: rank 3 → rank 3 = no change
        assert razors[3]["delta"] == 0
        assert razors[3]["delta_symbol"] == "="

    def test_annual_performance_with_large_datasets(self):
        """Test performance with large annual datasets."""
        # Create large annual datasets
        current_year_data = {
            "year": "2024",
            "data": {
                "razors": [
                    {"name": f"Razor {i}", "shaves": 100 - i, "rank": i}
                    for i in range(1, 101)  # 100 razors
                ],
            },
        }

        previous_year_data = {
            "year": "2023",
            "data": {
                "razors": [
                    {"name": f"Razor {i}", "shaves": 100 - i + 1, "rank": i + 1}
                    for i in range(1, 101)  # 100 razors, all moved down 1 tier
                ],
            },
        }

        calculator = AnnualDeltaCalculator()

        # Measure performance
        import time
        start_time = time.time()
        result = calculator.calculate_annual_deltas(
            current_year_data, previous_year_data, max_items=100
        )
        end_time = time.time()

        processing_time = end_time - start_time

        # Validate results
        razors = result["razors"]
        assert len(razors) == 100
        assert processing_time < 1.0  # Should complete within 1 second

        # Check that deltas are calculated correctly
        # All razors should have moved up 1 tier (rank +1 → rank)
        for razor in razors:
            assert razor["delta"] == 1  # All improved by 1 tier
            assert razor["delta_symbol"] == "↑1"
