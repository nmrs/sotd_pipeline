#!/usr/bin/env python3
"""Integration tests for annual delta calculator refactoring."""

import pytest

from sotd.report.annual_delta_calculator import AnnualDeltaCalculator


class TestAnnualDeltaCalculatorRefactoring:
    """Test that annual delta calculator refactoring preserves functionality."""

    def test_annual_delta_calculator_creation(self):
        """Test creating annual delta calculator with unified patterns."""
        calculator = AnnualDeltaCalculator(debug=True)
        assert calculator.debug is True
        assert hasattr(calculator, "delta_calculator")

    def test_calculate_annual_deltas_basic_functionality(self):
        """Test basic annual delta calculation with unified patterns."""
        calculator = AnnualDeltaCalculator(debug=True)

        current_year_data = {
            "year": "2024",
            "data": {
                "razors": [
                    {"name": "Razor A", "shaves": 100, "position": 1},
                    {"name": "Razor B", "shaves": 80, "position": 2},
                ]
            },
        }

        previous_year_data = {
            "year": "2023",
            "data": {
                "razors": [
                    {"name": "Razor B", "shaves": 90, "position": 1},
                    {"name": "Razor A", "shaves": 85, "position": 2},
                ]
            },
        }

        result = calculator.calculate_annual_deltas(
            current_year_data, previous_year_data, categories=["razors"]
        )

        assert "razors" in result
        assert len(result["razors"]) == 2

        # Check delta information
        razor_a = result["razors"][0]
        assert razor_a["name"] == "Razor A"
        assert "delta" in razor_a
        assert "delta_symbol" in razor_a
        assert "delta_text" in razor_a

    def test_calculate_annual_deltas_multiple_categories(self):
        """Test annual delta calculation with multiple categories."""
        calculator = AnnualDeltaCalculator(debug=True)

        current_year_data = {
            "year": "2024",
            "data": {
                "razors": [
                    {"name": "Razor A", "shaves": 100, "position": 1},
                ],
                "blades": [
                    {"name": "Blade A", "shaves": 200, "position": 1},
                ],
            },
        }

        previous_year_data = {
            "year": "2023",
            "data": {
                "razors": [
                    {"name": "Razor A", "shaves": 90, "position": 2},
                ],
                "blades": [
                    {"name": "Blade A", "shaves": 180, "position": 2},
                ],
            },
        }

        result = calculator.calculate_annual_deltas(current_year_data, previous_year_data)

        assert "razors" in result
        assert "blades" in result
        assert len(result["razors"]) == 1
        assert len(result["blades"]) == 1

    def test_calculate_annual_deltas_new_items(self):
        """Test annual delta calculation with new items."""
        calculator = AnnualDeltaCalculator(debug=True)

        current_year_data = {
            "year": "2024",
            "data": {
                "razors": [
                    {"name": "New Razor", "shaves": 100, "position": 1},
                ]
            },
        }

        previous_year_data = {
            "year": "2023",
            "data": {
                "razors": [
                    {"name": "Old Razor", "shaves": 90, "position": 1},
                ]
            },
        }

        result = calculator.calculate_annual_deltas(
            current_year_data, previous_year_data, categories=["razors"]
        )

        assert "razors" in result
        new_razor = result["razors"][0]
        assert new_razor["name"] == "New Razor"
        assert new_razor["delta_symbol"] == "n/a"  # New item

    def test_calculate_annual_deltas_missing_categories(self):
        """Test annual delta calculation with missing categories."""
        calculator = AnnualDeltaCalculator(debug=True)

        current_year_data = {
            "year": "2024",
            "data": {
                "razors": [
                    {"name": "Razor A", "shaves": 100, "position": 1},
                ]
            },
        }

        previous_year_data = {
            "year": "2023",
            "data": {
                "blades": [
                    {"name": "Blade A", "shaves": 200, "position": 1},
                ]
            },
        }

        result = calculator.calculate_annual_deltas(
            current_year_data, previous_year_data, categories=["razors"]
        )

        assert "razors" in result
        razor_a = result["razors"][0]
        assert razor_a["delta_symbol"] == "n/a"  # No previous data for razors

    def test_calculate_multi_year_deltas(self):
        """Test multi-year delta calculation with unified patterns."""
        calculator = AnnualDeltaCalculator(debug=True)

        current_year_data = {
            "year": "2024",
            "data": {
                "razors": [
                    {"name": "Razor A", "shaves": 100, "position": 1},
                ]
            },
        }

        comparison_years_data = {
            "2023": {
                "year": "2023",
                "data": {
                    "razors": [
                        {"name": "Razor A", "shaves": 90, "position": 2},
                    ]
                },
            },
            "2022": {
                "year": "2022",
                "data": {
                    "razors": [
                        {"name": "Razor A", "shaves": 80, "position": 3},
                    ]
                },
            },
        }

        result = calculator.calculate_multi_year_deltas(
            current_year_data, comparison_years_data, categories=["razors"]
        )

        assert "razors" in result
        razor_a = result["razors"][0]
        assert razor_a["name"] == "Razor A"
        # Should have delta information for both comparison years
        assert "delta_symbol_2023" in razor_a
        assert "delta_symbol_2022" in razor_a
        assert "delta_text_2023" in razor_a
        assert "delta_text_2022" in razor_a

    def test_calculate_multi_year_deltas_empty_comparison(self):
        """Test multi-year delta calculation with empty comparison data."""
        calculator = AnnualDeltaCalculator(debug=True)

        current_year_data = {
            "year": "2024",
            "data": {
                "razors": [
                    {"name": "Razor A", "shaves": 100, "position": 1},
                ]
            },
        }

        result = calculator.calculate_multi_year_deltas(
            current_year_data, {}, categories=["razors"]
        )

        assert result == {}

    def test_get_delta_column_config(self):
        """Test delta column configuration generation."""
        calculator = AnnualDeltaCalculator(debug=True)

        comparison_years = ["2023", "2022"]
        config = calculator.get_delta_column_config(comparison_years)

        # Check that config contains expected columns for each year
        for year in comparison_years:
            assert f"delta_position_{year}" in config
            assert f"delta_shaves_{year}" in config
            assert f"delta_unique_users_{year}" in config

            # Check column properties
            pos_col = config[f"delta_position_{year}"]
            assert pos_col["title"] == f"Δ Pos {year}"
            assert pos_col["align"] == "right"
            assert pos_col["format"] == "number"

    def test_calculate_annual_deltas_invalid_input(self):
        """Test annual delta calculation with invalid input."""
        calculator = AnnualDeltaCalculator(debug=True)

        # Test with non-dict input
        with pytest.raises(ValueError, match="Expected dict for current_year_data"):
            calculator.calculate_annual_deltas("invalid", {}, categories=["razors"])  # type: ignore

        with pytest.raises(ValueError, match="Expected dict for previous_year_data"):
            calculator.calculate_annual_deltas({}, "invalid", categories=["razors"])  # type: ignore

        # Test with missing data section
        current_year_data = {"year": "2024"}  # Missing "data" section
        previous_year_data = {"year": "2023", "data": {}}

        with pytest.raises(ValueError, match="Missing 'data' section in current year data"):
            calculator.calculate_annual_deltas(
                current_year_data, previous_year_data, categories=["razors"]
            )

    def test_calculate_annual_deltas_max_items(self):
        """Test annual delta calculation with max_items limit."""
        calculator = AnnualDeltaCalculator(debug=True)

        current_year_data = {
            "year": "2024",
            "data": {
                "razors": [
                    {"name": "Razor A", "shaves": 100, "position": 1},
                    {"name": "Razor B", "shaves": 80, "position": 2},
                    {"name": "Razor C", "shaves": 60, "position": 3},
                ]
            },
        }

        previous_year_data = {
            "year": "2023",
            "data": {
                "razors": [
                    {"name": "Razor A", "shaves": 90, "position": 2},
                    {"name": "Razor B", "shaves": 85, "position": 1},
                    {"name": "Razor C", "shaves": 70, "position": 3},
                ]
            },
        }

        result = calculator.calculate_annual_deltas(
            current_year_data, previous_year_data, categories=["razors"], max_items=2
        )

        assert "razors" in result
        assert len(result["razors"]) == 2  # Limited by max_items

    def test_calculate_annual_deltas_performance_monitoring(self):
        """Test that annual delta calculator includes performance monitoring."""
        calculator = AnnualDeltaCalculator(debug=True)

        current_year_data = {
            "year": "2024",
            "data": {
                "razors": [
                    {"name": "Razor A", "shaves": 100, "position": 1},
                ]
            },
        }

        previous_year_data = {
            "year": "2023",
            "data": {
                "razors": [
                    {"name": "Razor A", "shaves": 90, "position": 2},
                ]
            },
        }

        # Test that performance monitoring works without errors
        result = calculator.calculate_annual_deltas(
            current_year_data, previous_year_data, categories=["razors"]
        )

        assert "razors" in result
        assert len(result["razors"]) == 1
