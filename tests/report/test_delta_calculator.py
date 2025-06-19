#!/usr/bin/env python3
"""Tests for the delta calculator module."""

import pytest
from typing import Any, Dict, Tuple
from sotd.report.delta_calculator import DeltaCalculator, calculate_deltas_for_period


class TestDeltaCalculator:
    """Test the DeltaCalculator class."""

    def test_init(self):
        """Test DeltaCalculator initialization."""
        calculator = DeltaCalculator(debug=True)
        assert calculator.debug is True

        calculator = DeltaCalculator(debug=False)
        assert calculator.debug is False

    def test_calculate_deltas_basic(self):
        """Test basic delta calculation with position fields."""
        current_data = [
            {"name": "Razor A", "shaves": 100, "position": 1},
            {"name": "Razor B", "shaves": 80, "position": 2},
            {"name": "Razor C", "shaves": 60, "position": 3},
        ]

        historical_data = [
            {"name": "Razor B", "shaves": 90, "position": 1},
            {"name": "Razor A", "shaves": 85, "position": 2},
            {"name": "Razor C", "shaves": 70, "position": 3},
        ]

        calculator = DeltaCalculator()
        result = calculator.calculate_deltas(current_data, historical_data)

        assert len(result) == 3

        # Razor A: moved from position 2 to 1 (improved by 1)
        assert result[0]["name"] == "Razor A"
        assert result[0]["delta"] == 1
        assert result[0]["delta_symbol"] == "↑"
        assert result[0]["delta_text"] == "+1"

        # Razor B: moved from position 1 to 2 (worsened by 1)
        assert result[1]["name"] == "Razor B"
        assert result[1]["delta"] == -1
        assert result[1]["delta_symbol"] == "↓"
        assert result[1]["delta_text"] == "-1"

        # Razor C: stayed at position 3 (no change)
        assert result[2]["name"] == "Razor C"
        assert result[2]["delta"] == 0
        assert result[2]["delta_symbol"] == "↔"
        assert result[2]["delta_text"] == "0"

    def test_calculate_deltas_new_item(self):
        """Test delta calculation with new items not in historical data."""
        current_data = [
            {"name": "Razor A", "shaves": 100, "position": 1},
            {"name": "Razor B", "shaves": 80, "position": 2},
            {"name": "New Razor", "shaves": 60, "position": 3},
        ]

        historical_data = [
            {"name": "Razor A", "shaves": 90, "position": 1},
            {"name": "Razor B", "shaves": 85, "position": 2},
        ]

        calculator = DeltaCalculator()
        result = calculator.calculate_deltas(current_data, historical_data)

        assert len(result) == 3

        # New Razor: not in historical data
        assert result[2]["name"] == "New Razor"
        assert result[2]["delta"] is None
        assert result[2]["delta_symbol"] == "↔"
        assert result[2]["delta_text"] == "n/a"

    def test_calculate_deltas_missing_position(self):
        """Test delta calculation with missing position fields."""
        current_data = [
            {"name": "Razor A", "shaves": 100, "position": 1},
            {"name": "Razor B", "shaves": 80},  # Missing position
        ]

        historical_data = [
            {"name": "Razor A", "shaves": 90, "position": 2},
            {"name": "Razor B", "shaves": 85, "position": 1},
        ]

        calculator = DeltaCalculator()
        result = calculator.calculate_deltas(current_data, historical_data)

        # Should only process items with position fields
        assert len(result) == 1
        assert result[0]["name"] == "Razor A"

    def test_calculate_deltas_empty_data(self):
        """Test delta calculation with empty data."""
        calculator = DeltaCalculator()

        # Empty current data
        result = calculator.calculate_deltas([], [{"name": "Razor A", "position": 1}])
        assert result == []

        # Empty historical data
        result = calculator.calculate_deltas([{"name": "Razor A", "position": 1}], [])
        assert len(result) == 1
        assert result[0]["delta"] is None
        assert result[0]["delta_text"] == "n/a"

    def test_calculate_deltas_invalid_input(self):
        """Test delta calculation with invalid input types."""
        calculator = DeltaCalculator()

        with pytest.raises(ValueError, match="Expected list for current_data"):
            calculator.calculate_deltas("invalid", [])  # type: ignore

        with pytest.raises(ValueError, match="Expected list for historical_data"):
            calculator.calculate_deltas([], "invalid")  # type: ignore

    def test_calculate_deltas_max_items(self):
        """Test delta calculation with max_items limit."""
        current_data = [
            {"name": "Razor A", "shaves": 100, "position": 1},
            {"name": "Razor B", "shaves": 80, "position": 2},
            {"name": "Razor C", "shaves": 60, "position": 3},
        ]

        historical_data = [
            {"name": "Razor A", "shaves": 90, "position": 2},
            {"name": "Razor B", "shaves": 85, "position": 1},
            {"name": "Razor C", "shaves": 70, "position": 3},
        ]

        calculator = DeltaCalculator()
        result = calculator.calculate_deltas(current_data, historical_data, max_items=2)

        assert len(result) == 2
        assert result[0]["name"] == "Razor A"
        assert result[1]["name"] == "Razor B"

    def test_calculate_deltas_custom_name_key(self):
        """Test delta calculation with custom name key."""
        current_data = [
            {"product": "Razor A", "shaves": 100, "position": 1},
            {"product": "Razor B", "shaves": 80, "position": 2},
        ]

        historical_data = [
            {"product": "Razor A", "shaves": 90, "position": 2},
            {"product": "Razor B", "shaves": 85, "position": 1},
        ]

        calculator = DeltaCalculator()
        result = calculator.calculate_deltas(current_data, historical_data, name_key="product")

        assert len(result) == 2
        assert result[0]["product"] == "Razor A"
        assert result[0]["delta"] == 1

    def test_get_delta_symbol(self):
        """Test delta symbol generation."""
        calculator = DeltaCalculator()

        assert calculator._get_delta_symbol(1) == "↑"  # Improved
        assert calculator._get_delta_symbol(-1) == "↓"  # Worsened
        assert calculator._get_delta_symbol(0) == "↔"  # No change
        assert calculator._get_delta_symbol(None) == "↔"  # New item

    def test_calculate_category_deltas(self):
        """Test delta calculation for multiple categories."""
        current_data = {
            "razors": [
                {"name": "Razor A", "shaves": 100, "position": 1},
                {"name": "Razor B", "shaves": 80, "position": 2},
            ],
            "blades": [
                {"name": "Blade A", "shaves": 50, "position": 1},
                {"name": "Blade B", "shaves": 40, "position": 2},
            ],
        }

        historical_data = {
            "razors": [
                {"name": "Razor B", "shaves": 90, "position": 1},
                {"name": "Razor A", "shaves": 85, "position": 2},
            ],
            "blades": [
                {"name": "Blade A", "shaves": 45, "position": 1},
                {"name": "Blade B", "shaves": 35, "position": 2},
            ],
        }

        calculator = DeltaCalculator()
        result = calculator.calculate_category_deltas(
            current_data, historical_data, ["razors", "blades"]
        )

        assert "razors" in result
        assert "blades" in result

        # Check razors
        razors = result["razors"]
        assert len(razors) == 2
        assert razors[0]["name"] == "Razor A"
        assert razors[0]["delta"] == 1

        # Check blades
        blades = result["blades"]
        assert len(blades) == 2
        assert blades[0]["name"] == "Blade A"
        assert blades[0]["delta"] == 0

    def test_calculate_category_deltas_invalid_category(self):
        """Test delta calculation with invalid category data."""
        current_data = {
            "razors": [
                {"name": "Razor A", "shaves": 100, "position": 1},
            ],
            "invalid": "not a list",
        }

        historical_data = {
            "razors": [
                {"name": "Razor A", "shaves": 90, "position": 2},
            ],
            "invalid": "not a list",
        }

        calculator = DeltaCalculator(debug=True)
        result = calculator.calculate_category_deltas(
            current_data, historical_data, ["razors", "invalid"]
        )

        assert "razors" in result
        assert "invalid" not in result  # Invalid categories should be skipped
        assert len(result["razors"]) == 1
        assert len(result) == 1  # Only valid categories should be included

    def test_format_delta_column(self):
        """Test delta column formatting."""
        items = [
            {"name": "Item A", "delta_text": "+2", "delta_symbol": "↑"},
            {"name": "Item B", "delta_text": "-1", "delta_symbol": "↓"},
            {"name": "Item C", "delta_text": "0", "delta_symbol": "↔"},
            {"name": "Item D", "delta_text": "n/a", "delta_symbol": "↔"},
        ]

        calculator = DeltaCalculator()
        formatted = calculator.format_delta_column(items)

        assert formatted == ["+2 ↑", "-1 ↓", "0 ↔", "n/a"]

    def test_format_delta_column_missing_keys(self):
        """Test delta column formatting with missing keys."""
        items = [
            {"name": "Item A", "delta_text": "+2"},  # Missing delta_symbol
            {"name": "Item B"},  # Missing both
        ]

        calculator = DeltaCalculator()
        formatted = calculator.format_delta_column(items)

        assert formatted == ["+2 ↔", "n/a"]

    def test_format_delta_column_invalid_items(self):
        """Test delta column formatting with invalid items."""
        items = [
            {"name": "Item A", "delta_text": "+2", "delta_symbol": "↑"},
            "not a dict",  # Invalid item
            {"name": "Item B", "delta_text": "-1", "delta_symbol": "↓"},
        ]

        calculator = DeltaCalculator()
        formatted = calculator.format_delta_column(items)

        assert formatted == ["+2 ↑", "n/a", "-1 ↓"]


class TestCalculateDeltasForPeriod:
    """Test the calculate_deltas_for_period function."""

    def test_calculate_deltas_for_period_success(self):
        """Test successful delta calculation for a period."""
        current_data = {
            "razors": [
                {"name": "Razor A", "shaves": 100, "position": 1},
                {"name": "Razor B", "shaves": 80, "position": 2},
            ]
        }

        comparison_data: Dict[str, Tuple[Dict[str, Any], Dict[str, Any]]] = {
            "previous_month": (
                {"month": "2024-12"},
                {
                    "razors": [
                        {"name": "Razor B", "shaves": 90, "position": 1},
                        {"name": "Razor A", "shaves": 85, "position": 2},
                    ]
                },
            )
        }

        result = calculate_deltas_for_period(
            current_data, comparison_data, "previous_month", ["razors"]
        )

        assert result is not None
        assert "razors" in result
        assert len(result["razors"]) == 2

        # Razor A improved from position 2 to 1
        assert result["razors"][0]["name"] == "Razor A"
        assert result["razors"][0]["delta"] == 1

    def test_calculate_deltas_for_period_not_found(self):
        """Test delta calculation for non-existent period."""
        current_data = {"razors": []}
        comparison_data: Dict[str, Tuple[Dict[str, Any], Dict[str, Any]]] = {}

        result = calculate_deltas_for_period(
            current_data, comparison_data, "previous_month", ["razors"]
        )

        assert result is None

    def test_calculate_deltas_for_period_invalid_historical_data(self):
        """Test delta calculation with invalid historical data structure."""
        current_data = {"razors": []}
        comparison_data: Dict[str, Tuple[Dict[str, Any], Any]] = {
            "previous_month": (
                {"month": "2024-12"},
                "not a dict",  # Invalid historical data
            )
        }

        result = calculate_deltas_for_period(
            current_data, comparison_data, "previous_month", ["razors"], debug=True  # type: ignore
        )

        assert result is None

    def test_calculate_deltas_for_period_with_debug(self):
        """Test delta calculation with debug mode enabled."""
        current_data = {
            "razors": [
                {"name": "Razor A", "shaves": 100, "position": 1},
            ]
        }

        comparison_data: Dict[str, Tuple[Dict[str, Any], Dict[str, Any]]] = {
            "previous_month": (
                {"month": "2024-12"},
                {
                    "razors": [
                        {"name": "Razor A", "shaves": 90, "position": 2},
                    ]
                },
            )
        }

        result = calculate_deltas_for_period(
            current_data, comparison_data, "previous_month", ["razors"], debug=True
        )

        assert result is not None
        assert "razors" in result
        assert len(result["razors"]) == 1
        assert result["razors"][0]["delta"] == 1
