#!/usr/bin/env python3
"""Tests for the annual delta calculator module."""

import pytest
from typing import Any, Dict, List
from sotd.report.annual_delta_calculator import AnnualDeltaCalculator


class TestAnnualDeltaCalculator:
    """Test the AnnualDeltaCalculator class."""

    def test_init(self):
        """Test AnnualDeltaCalculator initialization."""
        calculator = AnnualDeltaCalculator(debug=True)
        assert calculator.debug is True

        calculator = AnnualDeltaCalculator(debug=False)
        assert calculator.debug is False

    def test_calculate_annual_deltas_basic(self):
        """Test basic annual delta calculation with position fields."""
        current_year_data = {
            "year": "2024",
            "meta": {
                "total_shaves": 1200,
                "unique_shavers": 100,
                "included_months": ["2024-01", "2024-02", "2024-03"],
                "missing_months": [],
            },
            "data": {
                "razors": [
                    {"name": "Razor A", "shaves": 100, "position": 1},
                    {"name": "Razor B", "shaves": 80, "position": 2},
                    {"name": "Razor C", "shaves": 60, "position": 3},
                ],
                "blades": [
                    {"name": "Blade A", "shaves": 50, "position": 1},
                    {"name": "Blade B", "shaves": 40, "position": 2},
                ],
            },
        }

        previous_year_data = {
            "year": "2023",
            "meta": {
                "total_shaves": 1100,
                "unique_shavers": 95,
                "included_months": ["2023-01", "2023-02", "2023-03"],
                "missing_months": [],
            },
            "data": {
                "razors": [
                    {"name": "Razor B", "shaves": 90, "position": 1},
                    {"name": "Razor A", "shaves": 85, "position": 2},
                    {"name": "Razor C", "shaves": 70, "position": 3},
                ],
                "blades": [
                    {"name": "Blade A", "shaves": 45, "position": 1},
                    {"name": "Blade B", "shaves": 35, "position": 2},
                ],
            },
        }

        calculator = AnnualDeltaCalculator()
        result = calculator.calculate_annual_deltas(current_year_data, previous_year_data)

        assert "razors" in result
        assert "blades" in result

        # Test razors deltas
        razors = result["razors"]
        assert len(razors) == 3

        # Razor A: moved from position 2 to 1 (improved by 1)
        assert razors[0]["name"] == "Razor A"
        assert razors[0]["delta"] == 1
        assert razors[0]["delta_symbol"] == "↑"
        assert razors[0]["delta_text"] == "↑"

        # Razor B: moved from position 1 to 2 (worsened by 1)
        assert razors[1]["name"] == "Razor B"
        assert razors[1]["delta"] == -1
        assert razors[1]["delta_symbol"] == "↓"
        assert razors[1]["delta_text"] == "↓"

        # Razor C: stayed at position 3 (no change)
        assert razors[2]["name"] == "Razor C"
        assert razors[2]["delta"] == 0
        assert razors[2]["delta_symbol"] == "="
        assert razors[2]["delta_text"] == "="

        # Test blades deltas
        blades = result["blades"]
        assert len(blades) == 2

        # Blade A: stayed at position 1 (no change)
        assert blades[0]["name"] == "Blade A"
        assert blades[0]["delta"] == 0
        assert blades[0]["delta_symbol"] == "="

        # Blade B: stayed at position 2 (no change)
        assert blades[1]["name"] == "Blade B"
        assert blades[1]["delta"] == 0
        assert blades[1]["delta_symbol"] == "="

    def test_calculate_annual_deltas_new_items(self):
        """Test annual delta calculation with new items not in previous year."""
        current_year_data = {
            "year": "2024",
            "meta": {"total_shaves": 1200, "unique_shavers": 100},
            "data": {
                "razors": [
                    {"name": "Razor A", "shaves": 100, "position": 1},
                    {"name": "New Razor", "shaves": 80, "position": 2},
                ],
            },
        }

        previous_year_data = {
            "year": "2023",
            "meta": {"total_shaves": 1100, "unique_shavers": 95},
            "data": {
                "razors": [
                    {"name": "Razor A", "shaves": 90, "position": 1},
                ],
            },
        }

        calculator = AnnualDeltaCalculator()
        result = calculator.calculate_annual_deltas(current_year_data, previous_year_data)

        razors = result["razors"]
        assert len(razors) == 2

        # New Razor: not in previous year data
        assert razors[1]["name"] == "New Razor"
        assert razors[1]["delta"] is None
        assert razors[1]["delta_symbol"] == "n/a"
        assert razors[1]["delta_text"] == "n/a"

    def test_calculate_annual_deltas_missing_position(self):
        """Test annual delta calculation with missing position fields."""
        current_year_data = {
            "year": "2024",
            "meta": {"total_shaves": 1200, "unique_shavers": 100},
            "data": {
                "razors": [
                    {"name": "Razor A", "shaves": 100, "position": 1},
                    {"name": "Razor B", "shaves": 80},  # Missing position
                ],
            },
        }

        previous_year_data = {
            "year": "2023",
            "meta": {"total_shaves": 1100, "unique_shavers": 95},
            "data": {
                "razors": [
                    {"name": "Razor A", "shaves": 90, "position": 2},
                    {"name": "Razor B", "shaves": 85, "position": 1},
                ],
            },
        }

        calculator = AnnualDeltaCalculator()
        result = calculator.calculate_annual_deltas(current_year_data, previous_year_data)

        # Should only process items with position fields
        razors = result["razors"]
        assert len(razors) == 1
        assert razors[0]["name"] == "Razor A"

    def test_calculate_annual_deltas_empty_data(self):
        """Test annual delta calculation with empty data."""
        calculator = AnnualDeltaCalculator()

        # Empty current year data
        current_year_data = {
            "year": "2024",
            "meta": {"total_shaves": 0, "unique_shavers": 0},
            "data": {"razors": []},
        }

        previous_year_data = {
            "year": "2023",
            "meta": {"total_shaves": 1100, "unique_shavers": 95},
            "data": {
                "razors": [{"name": "Razor A", "shaves": 90, "position": 1}],
            },
        }

        result = calculator.calculate_annual_deltas(current_year_data, previous_year_data)
        assert result["razors"] == []

        # Empty previous year data
        current_year_data = {
            "year": "2024",
            "meta": {"total_shaves": 1200, "unique_shavers": 100},
            "data": {
                "razors": [{"name": "Razor A", "shaves": 100, "position": 1}],
            },
        }

        previous_year_data = {
            "year": "2023",
            "meta": {"total_shaves": 0, "unique_shavers": 0},
            "data": {"razors": []},
        }

        result = calculator.calculate_annual_deltas(current_year_data, previous_year_data)
        razors = result["razors"]
        assert len(razors) == 1
        assert razors[0]["delta"] is None
        assert razors[0]["delta_text"] == "n/a"

    def test_calculate_annual_deltas_invalid_input(self):
        """Test annual delta calculation with invalid input types."""
        calculator = AnnualDeltaCalculator()

        with pytest.raises(ValueError, match="Expected dict for current_year_data"):
            calculator.calculate_annual_deltas("invalid", {})  # type: ignore

        with pytest.raises(ValueError, match="Expected dict for previous_year_data"):
            calculator.calculate_annual_deltas({}, "invalid")  # type: ignore

    def test_calculate_annual_deltas_missing_data_section(self):
        """Test annual delta calculation with missing data section."""
        calculator = AnnualDeltaCalculator()

        current_year_data = {
            "year": "2024",
            "meta": {"total_shaves": 1200, "unique_shavers": 100},
            # Missing data section
        }

        previous_year_data = {
            "year": "2023",
            "meta": {"total_shaves": 1100, "unique_shavers": 95},
            "data": {"razors": [{"name": "Razor A", "shaves": 90, "position": 1}]},
        }

        with pytest.raises(ValueError, match="Missing 'data' section in current year data"):
            calculator.calculate_annual_deltas(current_year_data, previous_year_data)

    def test_calculate_annual_deltas_max_items(self):
        """Test annual delta calculation with max_items limit."""
        current_year_data = {
            "year": "2024",
            "meta": {"total_shaves": 1200, "unique_shavers": 100},
            "data": {
                "razors": [
                    {"name": "Razor A", "shaves": 100, "position": 1},
                    {"name": "Razor B", "shaves": 80, "position": 2},
                    {"name": "Razor C", "shaves": 60, "position": 3},
                ],
            },
        }

        previous_year_data = {
            "year": "2023",
            "meta": {"total_shaves": 1100, "unique_shavers": 95},
            "data": {
                "razors": [
                    {"name": "Razor A", "shaves": 90, "position": 2},
                    {"name": "Razor B", "shaves": 85, "position": 1},
                    {"name": "Razor C", "shaves": 70, "position": 3},
                ],
            },
        }

        calculator = AnnualDeltaCalculator()
        result = calculator.calculate_annual_deltas(
            current_year_data, previous_year_data, max_items=2
        )

        razors = result["razors"]
        assert len(razors) == 2
        assert razors[0]["name"] == "Razor A"
        assert razors[1]["name"] == "Razor B"

    def test_calculate_annual_deltas_specific_categories(self):
        """Test annual delta calculation for specific categories only."""
        current_year_data = {
            "year": "2024",
            "meta": {"total_shaves": 1200, "unique_shavers": 100},
            "data": {
                "razors": [
                    {"name": "Razor A", "shaves": 100, "position": 1},
                    {"name": "Razor B", "shaves": 80, "position": 2},
                ],
                "blades": [
                    {"name": "Blade A", "shaves": 50, "position": 1},
                    {"name": "Blade B", "shaves": 40, "position": 2},
                ],
                "brushes": [
                    {"name": "Brush A", "shaves": 30, "position": 1},
                ],
            },
        }

        previous_year_data = {
            "year": "2023",
            "meta": {"total_shaves": 1100, "unique_shavers": 95},
            "data": {
                "razors": [
                    {"name": "Razor B", "shaves": 90, "position": 1},
                    {"name": "Razor A", "shaves": 85, "position": 2},
                ],
                "blades": [
                    {"name": "Blade A", "shaves": 45, "position": 1},
                    {"name": "Blade B", "shaves": 35, "position": 2},
                ],
                "brushes": [
                    {"name": "Brush A", "shaves": 25, "position": 1},
                ],
            },
        }

        calculator = AnnualDeltaCalculator()
        result = calculator.calculate_annual_deltas(
            current_year_data, previous_year_data, categories=["razors", "blades"]
        )

        # Should only include specified categories
        assert "razors" in result
        assert "blades" in result
        assert "brushes" not in result

        # Test razors deltas
        razors = result["razors"]
        assert len(razors) == 2
        assert razors[0]["name"] == "Razor A"
        assert razors[0]["delta"] == 1  # Improved from position 2 to 1

        # Test blades deltas
        blades = result["blades"]
        assert len(blades) == 2
        assert blades[0]["name"] == "Blade A"
        assert blades[0]["delta"] == 0  # Stayed at position 1

    def test_calculate_annual_deltas_all_categories(self):
        """Test annual delta calculation for all available categories."""
        current_year_data = {
            "year": "2024",
            "meta": {"total_shaves": 1200, "unique_shavers": 100},
            "data": {
                "razors": [
                    {"name": "Razor A", "shaves": 100, "position": 1},
                ],
                "blades": [
                    {"name": "Blade A", "shaves": 50, "position": 1},
                ],
                "brushes": [
                    {"name": "Brush A", "shaves": 30, "position": 1},
                ],
                "soaps": [
                    {"name": "Soap A", "shaves": 20, "position": 1},
                ],
            },
        }

        previous_year_data = {
            "year": "2023",
            "meta": {"total_shaves": 1100, "unique_shavers": 95},
            "data": {
                "razors": [
                    {"name": "Razor A", "shaves": 90, "position": 1},
                ],
                "blades": [
                    {"name": "Blade A", "shaves": 45, "position": 1},
                ],
                "brushes": [
                    {"name": "Brush A", "shaves": 25, "position": 1},
                ],
                "soaps": [
                    {"name": "Soap A", "shaves": 15, "position": 1},
                ],
            },
        }

        calculator = AnnualDeltaCalculator()
        result = calculator.calculate_annual_deltas(current_year_data, previous_year_data)

        # Should include all categories
        expected_categories = {"razors", "blades", "brushes", "soaps"}
        assert set(result.keys()) == expected_categories

        # All items should have no change (stayed at position 1)
        for category in expected_categories:
            items = result[category]
            assert len(items) == 1
            assert items[0]["delta"] == 0
            assert items[0]["delta_symbol"] == "="

    def test_calculate_annual_deltas_debug_mode(self):
        """Test annual delta calculation with debug mode enabled."""
        current_year_data = {
            "year": "2024",
            "meta": {"total_shaves": 1200, "unique_shavers": 100},
            "data": {
                "razors": [
                    {"name": "Razor A", "shaves": 100, "position": 1},
                    {"name": "Razor B", "shaves": 80, "position": 2},
                ],
            },
        }

        previous_year_data = {
            "year": "2023",
            "meta": {"total_shaves": 1100, "unique_shavers": 95},
            "data": {
                "razors": [
                    {"name": "Razor B", "shaves": 90, "position": 1},
                    {"name": "Razor A", "shaves": 85, "position": 2},
                ],
            },
        }

        calculator = AnnualDeltaCalculator(debug=True)
        result = calculator.calculate_annual_deltas(current_year_data, previous_year_data)

        # Should still work correctly with debug mode
        razors = result["razors"]
        assert len(razors) == 2
        assert razors[0]["name"] == "Razor A"
        assert razors[0]["delta"] == 1
        assert razors[1]["name"] == "Razor B"
        assert razors[1]["delta"] == -1

    def test_calculate_annual_deltas_invalid_category_data(self):
        """Test annual delta calculation with invalid category data."""
        calculator = AnnualDeltaCalculator()

        current_year_data = {
            "year": "2024",
            "meta": {"total_shaves": 1200, "unique_shavers": 100},
            "data": {
                "razors": "invalid",  # Should be a list
            },
        }

        previous_year_data = {
            "year": "2023",
            "meta": {"total_shaves": 1100, "unique_shavers": 95},
            "data": {
                "razors": [
                    {"name": "Razor A", "shaves": 90, "position": 1},
                ],
            },
        }

        result = calculator.calculate_annual_deltas(current_year_data, previous_year_data)

        # Should skip invalid category and return empty list
        assert "razors" in result
        assert result["razors"] == []

    def test_calculate_annual_deltas_missing_previous_category(self):
        """Test annual delta calculation when previous year is missing a category."""
        current_year_data = {
            "year": "2024",
            "meta": {"total_shaves": 1200, "unique_shavers": 100},
            "data": {
                "razors": [
                    {"name": "Razor A", "shaves": 100, "position": 1},
                ],
                "blades": [
                    {"name": "Blade A", "shaves": 50, "position": 1},
                ],
            },
        }

        previous_year_data = {
            "year": "2023",
            "meta": {"total_shaves": 1100, "unique_shavers": 95},
            "data": {
                "razors": [
                    {"name": "Razor A", "shaves": 90, "position": 1},
                ],
                # Missing blades category
            },
        }

        calculator = AnnualDeltaCalculator()
        result = calculator.calculate_annual_deltas(current_year_data, previous_year_data)

        # Razors should have normal deltas
        razors = result["razors"]
        assert len(razors) == 1
        assert razors[0]["delta"] == 0  # Stayed at position 1

        # Blades should have n/a deltas (no previous data)
        blades = result["blades"]
        assert len(blades) == 1
        assert blades[0]["delta"] is None
        assert blades[0]["delta_symbol"] == "n/a"
        assert blades[0]["delta_text"] == "n/a"
