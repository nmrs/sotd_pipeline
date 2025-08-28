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
        """Test basic delta calculation with rank fields."""
        current_data = [
            {"name": "Razor A", "shaves": 100},
            {"name": "Razor B", "shaves": 80, "rank": 2},
            {"name": "Razor C", "shaves": 60, "rank": 3},
        ]

        historical_data = [
            {"name": "Razor B", "shaves": 90},
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

    def test_calculate_deltas_new_item(self):
        """Test delta calculation with new items not in historical data."""
        current_data = [
            {"name": "Razor A", "shaves": 100},
            {"name": "Razor B", "shaves": 80, "rank": 2},
            {"name": "New Razor", "shaves": 60, "rank": 3},
        ]

        historical_data = [
            {"name": "Razor A", "shaves": 90},
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

    def test_calculate_deltas_missing_rank(self):
        """Test delta calculation with missing rank fields."""
        current_data = [
            {"name": "Razor A", "shaves": 100},
            {"name": "Razor B", "shaves": 80},  # Missing rank
        ]

        historical_data = [
            {"name": "Razor A", "shaves": 90, "rank": 2},
            {"name": "Razor B", "shaves": 85},
        ]

        calculator = DeltaCalculator()
        result = calculator.calculate_deltas(current_data, historical_data)

        # Should only process items with rank fields
        assert len(result) == 1
        assert result[0]["name"] == "Razor A"

    def test_calculate_deltas_empty_data(self):
        """Test delta calculation with empty data."""
        calculator = DeltaCalculator()

        # Empty current data
        result = calculator.calculate_deltas([], [{"name": "Razor A"}])
        assert result == []

        # Empty historical data
        result = calculator.calculate_deltas([{"name": "Razor A"}], [])
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
            {"name": "Razor A", "shaves": 100},
            {"name": "Razor B", "shaves": 80, "rank": 2},
            {"name": "Razor C", "shaves": 60, "rank": 3},
        ]

        historical_data = [
            {"name": "Razor A", "shaves": 90, "rank": 2},
            {"name": "Razor B", "shaves": 85},
            {"name": "Razor C", "shaves": 70, "rank": 3},
        ]

        calculator = DeltaCalculator()
        result = calculator.calculate_deltas(current_data, historical_data, max_items=2)

        assert len(result) == 2
        assert result[0]["name"] == "Razor A"
        assert result[1]["name"] == "Razor B"

    def test_calculate_deltas_custom_name_key(self):
        """Test delta calculation with custom name key."""
        current_data = [
            {"product": "Razor A", "shaves": 100},
            {"product": "Razor B", "shaves": 80, "rank": 2},
        ]

        historical_data = [
            {"product": "Razor A", "shaves": 90, "rank": 2},
            {"product": "Razor B", "shaves": 85},
        ]

        calculator = DeltaCalculator()
        result = calculator.calculate_deltas(current_data, historical_data, name_key="product")

        assert len(result) == 2
        assert result[0]["product"] == "Razor A"
        assert result[0]["delta"] == 1

    def test_get_delta_symbol(self):
        """Test delta symbol generation."""
        calculator = DeltaCalculator()

        assert calculator._get_delta_symbol(1) == "↑1"  # Improved by 1 rank
        assert calculator._get_delta_symbol(-1) == "↓1"  # Worsened by 1 rank
        assert calculator._get_delta_symbol(0) == "="  # No change
        assert calculator._get_delta_symbol(None) == "n/a"  # New item

    def test_calculate_category_deltas(self):
        """Test delta calculation for multiple categories."""
        current_data = {
            "razors": [
                {"name": "Razor A", "shaves": 100},
                {"name": "Razor B", "shaves": 80, "rank": 2},
            ],
            "blades": [
                {"name": "Blade A", "shaves": 50},
                {"name": "Blade B", "shaves": 40, "rank": 2},
            ],
        }

        historical_data = {
            "razors": [
                {"name": "Razor B", "shaves": 90},
                {"name": "Razor A", "shaves": 85, "rank": 2},
            ],
            "blades": [
                {"name": "Blade A", "shaves": 45},
                {"name": "Blade B", "shaves": 35, "rank": 2},
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
        current_data = {"razors": [{"name": "Razor A", "shaves": 100}], "invalid": "not a list"}

        historical_data = {
            "razors": [{"name": "Razor A", "shaves": 90, "rank": 2}],
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
            {"name": "Item A", "delta_text": "↑1", "delta_symbol": "↑1"},
            {"name": "Item B", "delta_text": "↓2", "delta_symbol": "↓2"},
            {"name": "Item C", "delta_text": "=", "delta_symbol": "="},
            {"name": "Item D", "delta_text": "n/a", "delta_symbol": "n/a"},
        ]

        calculator = DeltaCalculator()
        formatted = calculator.format_delta_column(items)

        assert formatted == ["↑1", "↓2", "=", "n/a"]

    def test_format_delta_column_missing_keys(self):
        """Test delta column formatting with missing keys."""
        items = [
            {"name": "Item A", "delta_text": "↑"},  # Missing delta_symbol
            {"name": "Item B"},  # Missing both
        ]

        calculator = DeltaCalculator()
        formatted = calculator.format_delta_column(items)

        assert formatted == ["↑", "n/a"]

    def test_format_delta_column_invalid_items(self):
        """Test delta column formatting with invalid items."""
        items = [
            {"name": "Item A", "delta_text": "↑", "delta_symbol": "↑"},
            "not a dict",  # Invalid item
            {"name": "Item B", "delta_text": "↓", "delta_symbol": "↓"},
        ]

        calculator = DeltaCalculator()
        formatted = calculator.format_delta_column(items)

        assert formatted == ["↑", "n/a", "↓"]

    def test_calculate_deltas_christopher_bradley_plates_bug(self):
        """Test that Christopher Bradley plates delta calculations work correctly.

        This test exposes a bug where Christopher Bradley plates show "n/a" in all
        delta columns even when they exist in previous month data.
        """
        # Current month data (June 2025)
        current_data = [
            {"name": "SBC", "shaves": 22, "unique_users": 8},
            {"name": "SBD", "shaves": 31, "unique_users": 6, "rank": 2},
            {"name": "OCF", "shaves": 9, "unique_users": 1, "rank": 3},
        ]

        # Previous month data (May 2025) - these plates definitely existed
        historical_data = [
            {"name": "SBC", "shaves": 23, "unique_users": 3},
            {"name": "SBD", "shaves": 23, "unique_users": 3, "rank": 2},
            {"name": "OCF", "shaves": 3, "unique_users": 1, "rank": 3},
        ]

        # Calculate deltas for Christopher Bradley plates
        calculator = DeltaCalculator()
        deltas = calculator.calculate_deltas(
            current_data, historical_data, name_key="name", max_items=20
        )

        # The bug: all deltas should NOT be "n/a" since these plates existed in
        # previous month. Expected: plates should show position changes (↑, ↓, or =)
        # Actual: all showing "n/a"

        # Verify that deltas are calculated correctly
        assert len(deltas) == 3, f"Expected 3 delta results, got {len(deltas)}"

        # Check that SBC plate delta is calculated (was position 1, still position 1)
        sbc_delta = next((d for d in deltas if d["name"] == "SBC"), None)
        assert sbc_delta is not None, "SBC plate delta not found"
        assert (
            sbc_delta["delta"] == 0
        ), f"Expected SBC delta to be 0 (no change), got {sbc_delta['delta']}"
        assert (
            sbc_delta["delta_symbol"] == "="
        ), f"Expected SBC delta symbol to be '=', got '{sbc_delta['delta_symbol']}'"

        # Check that SBD plate delta is calculated (was rank 2, still rank 2)
        sbd_delta = next((d for d in deltas if d["name"] == "SBD"), None)
        assert sbd_delta is not None, "SBD plate delta not found"
        assert (
            sbd_delta["delta"] == 0
        ), f"Expected SBD delta to be 0 (no change), got {sbd_delta['delta']}"
        assert (
            sbd_delta["delta_symbol"] == "="
        ), f"Expected SBD delta symbol to be '=', got '{sbd_delta['delta_symbol']}'"

        # Check that OCF plate delta is calculated (was rank 3, still rank 3)
        ocf_delta = next((d for d in deltas if d["name"] == "OCF"), None)
        assert ocf_delta is not None, "OCF plate delta not found"
        assert (
            ocf_delta["delta"] == 0
        ), f"Expected OCF delta to be 0 (no change), got {ocf_delta['delta']}"
        assert (
            ocf_delta["delta_symbol"] == "="
        ), f"Expected OCF delta symbol to be '=', got '{ocf_delta['delta_symbol']}'"

        # Verify that no deltas show "n/a" for items that existed in previous month
        for delta in deltas:
            assert (
                delta["delta_symbol"] != "n/a"
            ), f"Plate {delta['name']} shows 'n/a' but should have a delta value"

    def test_christopher_bradley_plates_table_delta_integration(self):
        """Test that Christopher Bradley plates table properly generates deltas.

        This test exposes the bug where the table generation process fails to
        include delta calculations even though the DeltaCalculator works correctly.
        """
        from sotd.report.table_generators.table_generator import TableGenerator

        # Current month data (June 2025) - includes ranks assigned by aggregator
        current_data = {
            "christopher_bradley_plates": [
                {
                    "plate_type": "S",
                    "plate_level": "BC",
                    "shaves": 22,
                    "unique_users": 8,
                    "rank": 2,
                },
                {
                    "plate_type": "S",
                    "plate_level": "BD",
                    "shaves": 31,
                    "unique_users": 6,
                    "rank": 1,
                },
                {"plate_type": "OC", "plate_level": "F", "shaves": 9, "unique_users": 1, "rank": 3},
            ]
        }

        # Previous month data (May 2025) - these plates definitely existed
        comparison_data = {
            "previous month": (
                {"month": "2025-05", "total_shaves": 1625, "unique_shavers": 110},
                {
                    "christopher_bradley_plates": [
                        {
                            "plate_type": "S",
                            "plate_level": "BC",
                            "shaves": 23,
                            "unique_users": 3,
                            "rank": 1,
                        },
                        {
                            "plate_type": "S",
                            "plate_level": "BD",
                            "shaves": 23,
                            "unique_users": 3,
                            "rank": 1,
                        },
                        {
                            "plate_type": "OC",
                            "plate_level": "F",
                            "shaves": 3,
                            "unique_users": 1,
                            "rank": 3,
                        },
                    ]
                },
            )
        }

        # Create the table generator
        generator = ChristopherBradleyPlatesTableGenerator(current_data, debug=True)

        # Generate the table with delta calculations enabled
        table_markdown = generator.generate_table(
            max_rows=20, include_delta=True, comparison_data=comparison_data
        )

        # The bug: the generated table should include delta columns with proper values
        # Expected: table should show rank changes (↑, ↓, or =) for plates that existed
        # Actual: table shows "n/a" for all delta columns

        # Verify that the table includes delta columns
        assert "Δ vs previous month" in table_markdown, "Table should include delta column header"

        # Verify that the table shows proper delta values, not just "n/a"
        # This is where the bug manifests - the table generation process fails to
        # properly integrate delta calculations
        assert (
            "n/a" not in table_markdown
            or "=" in table_markdown
            or "↑" in table_markdown
            or "↓" in table_markdown
        ), "Table should show proper delta values, not just 'n/a'"

    def test_straight_grinds_table_delta_integration(self):
        """Test that Straight Grinds table properly generates deltas.

        This test confirms the same bug exists in Straight Grinds table generation.
        """
        from sotd.report.table_generators.table_generator import TableGenerator

        # Current month data (June 2025) - includes ranks assigned by aggregator
        current_data = {
            "straight_grinds": [
                {"grind": "Full Hollow", "shaves": 71, "unique_users": 18},
                {"grind": "Hollow", "shaves": 32, "unique_users": 12, "rank": 2},
                {"grind": "Extra Hollow", "shaves": 8, "unique_users": 6, "rank": 3},
            ]
        }

        # Previous month data (May 2025) - these grinds definitely existed
        comparison_data = {
            "previous month": (
                {"month": "2025-05", "total_shaves": 800, "unique_shavers": 40},
                {
                    "straight_grinds": [
                        {"grind": "Full Hollow", "shaves": 65, "unique_users": 16},
                        {"grind": "Hollow", "shaves": 35, "unique_users": 14, "rank": 2},
                        {"grind": "Extra Hollow", "shaves": 10, "unique_users": 5, "rank": 3},
                    ]
                },
            )
        }

        # Create the table generator
        generator = StraightGrindsTableGenerator(current_data, debug=True)

        # Generate the table with delta calculations enabled
        table_markdown = generator.generate_table(
            max_rows=20, include_delta=True, comparison_data=comparison_data
        )

        # The bug: the generated table should include delta columns with proper values
        # Expected: table should show position changes (↑, ↓, or =) for grinds that existed
        # Actual: table shows "n/a" for all delta columns

        # Verify that the table includes delta columns
        assert "Δ vs previous month" in table_markdown, "Table should include delta column header"

        # Verify that the table shows proper delta values, not just "n/a"
        # This is where the bug manifests - the table generation process fails to
        # properly integrate delta calculations
        assert (
            "n/a" not in table_markdown
            or "=" in table_markdown
            or "↑" in table_markdown
            or "↓" in table_markdown
        ), "Table should show proper delta values, not just 'n/a'"

    def test_straight_points_table_delta_integration(self):
        """Test that Straight Points table properly generates deltas.

        This test confirms the Straight Points table is working with the new base class.
        """
        from sotd.report.table_generators.table_generator import TableGenerator

        # Current month data (June 2025) - includes ranks assigned by aggregator
        current_data = {
            "straight_points": [
                {"point": "Square", "shaves": 44, "unique_users": 15},
                {"point": "Round", "shaves": 32, "unique_users": 11, "rank": 2},
                {"point": "Barber's Notch", "shaves": 10, "unique_users": 6, "rank": 3},
            ]
        }

        # Previous month data (May 2025) - these points definitely existed
        comparison_data = {
            "previous_month": (
                {"month": "2025-05", "total_shaves": 800, "unique_shavers": 40},
                {
                    "straight_points": [
                        {"point": "Square", "shaves": 40, "unique_users": 14},
                        {"point": "Round", "shaves": 35, "unique_users": 12, "rank": 2},
                        {"point": "Barber's Notch", "shaves": 12, "unique_users": 5, "rank": 3},
                    ]
                },
            )
        }

        # Create the table generator
        generator = StraightPointsTableGenerator(current_data, debug=True)

        # Generate the table with delta calculations enabled
        table_markdown = generator.generate_table(
            max_rows=20, include_delta=True, comparison_data=comparison_data
        )

        # Verify that the table includes delta columns
        assert "Δ vs previous_month" in table_markdown, "Table should include delta column header"

        # Verify that the table shows proper delta values, not just "n/a"
        # This should now work with the new base class
        assert (
            "n/a" not in table_markdown
            or "=" in table_markdown
            or "↑" in table_markdown
            or "↓" in table_markdown
        ), "Table should show proper delta values, not just 'n/a'"

    def test_straight_widths_table_delta_integration(self):
        """Test that Straight Widths table properly generates deltas.

        This test confirms the Straight Widths table is working with the new base class.
        """
        from sotd.report.table_generators.table_generator import TableGenerator

        # Current month data (June 2025) - includes ranks assigned by aggregator
        current_data = {
            "straight_widths": [
                {"width": "5/8", "shaves": 45, "unique_users": 12},
                {"width": "6/8", "shaves": 38, "unique_users": 10, "rank": 2},
                {"width": "4/8", "shaves": 22, "unique_users": 8, "rank": 3},
            ]
        }

        # Previous month data (May 2025) - these widths definitely existed
        comparison_data = {
            "previous_month": (
                {"month": "2025-05", "total_shaves": 800, "unique_shavers": 40},
                {
                    "straight_widths": [
                        {"width": "5/8", "shaves": 42, "unique_users": 11},
                        {"width": "6/8", "shaves": 40, "unique_users": 12, "rank": 2},
                        {"width": "4/8", "shaves": 25, "unique_users": 9, "rank": 3},
                    ]
                },
            )
        }

        # Create the table generator
        generator = StraightWidthsTableGenerator(current_data, debug=True)

        # Generate the table with delta calculations enabled
        table_markdown = generator.generate_table(
            max_rows=20, include_delta=True, comparison_data=comparison_data
        )

        # Verify that the table includes delta columns
        assert "Δ vs previous_month" in table_markdown, "Table should include delta column header"

        # Verify that the table shows proper delta values, not just "n/a"
        # This should now work with the new base class
        assert (
            "n/a" not in table_markdown
            or "=" in table_markdown
            or "↑" in table_markdown
            or "↓" in table_markdown
        ), "Table should show proper delta values, not just 'n/a'"

    def test_game_changer_plates_table_delta_integration(self):
        """Test that Game Changer plates table properly generates deltas.

        This test exposes the bug where Game Changer plates table fails to
        include delta calculations because it doesn't inherit from DataTransformingTableGenerator.
        """
        from sotd.report.table_generators.table_generator import TableGenerator

        # Current month data (June 2025) - includes ranks assigned by aggregator
        current_data = {
            "game_changer_plates": [
                {"gap": ".84", "shaves": 71, "unique_users": 10},
                {"gap": ".68", "shaves": 1, "unique_users": 1, "rank": 2},
                {"gap": ".76", "shaves": 1, "unique_users": 1, "rank": 3},
            ]
        }

        # Previous month data (May 2025) - these gaps definitely existed
        comparison_data = {
            "previous month": (
                {"month": "2025-05", "total_shaves": 800, "unique_shavers": 40},
                {
                    "game_changer_plates": [
                        {"gap": ".84", "shaves": 65, "unique_users": 8},
                        {"gap": ".68", "shaves": 3, "unique_users": 2, "rank": 2},
                        {"gap": ".76", "shaves": 2, "unique_users": 1, "rank": 3},
                    ]
                },
            )
        }

        # Create the table generator
        generator = GameChangerPlatesTableGenerator(current_data, debug=True)

        # Generate the table with delta calculations enabled
        table_markdown = generator.generate_table(
            max_rows=20, include_delta=True, comparison_data=comparison_data
        )

        # The bug: the generated table should include delta columns with proper values
        # Expected: table should show position changes (↑, ↓, or =) for gaps that existed
        # Actual: table shows "n/a" for all delta columns

        # Verify that the table includes delta columns
        assert "Δ vs previous month" in table_markdown, "Table should include delta column header"

        # Verify that the table shows proper delta values, not just "n/a"
        # This is where the bug manifests - the table generation process fails to
        # properly integrate delta calculations
        assert (
            "n/a" not in table_markdown
            or "=" in table_markdown
            or "↑" in table_markdown
            or "↓" in table_markdown
        ), "Table should show proper delta values, not just 'n/a'"

    def test_super_speed_tips_table_delta_integration(self):
        """Test that Super Speed tips table properly generates deltas.

        This test exposes the bug where Super Speed tips table fails to
        include delta calculations because it doesn't inherit from DataTransformingTableGenerator.
        """
        from sotd.report.table_generators.table_generator import TableGenerator

        # Current month data (June 2025) - includes ranks assigned by aggregator
        current_data = {
            "super_speed_tips": [
                {"super_speed_tip": "Regular", "shaves": 25, "unique_users": 8},
                {"super_speed_tip": "Long", "shaves": 15, "unique_users": 5, "rank": 2},
                {"super_speed_tip": "Short", "shaves": 8, "unique_users": 3, "rank": 3},
            ]
        }

        # Previous month data (May 2025) - these tips definitely existed
        comparison_data = {
            "previous month": (
                {"month": "2025-05", "total_shaves": 800, "unique_shavers": 40},
                {
                    "super_speed_tips": [
                        {"super_speed_tip": "Regular", "shaves": 22, "unique_users": 7},
                        {"super_speed_tip": "Long", "shaves": 18, "unique_users": 6, "rank": 2},
                        {"super_speed_tip": "Short", "shaves": 10, "unique_users": 4, "rank": 3},
                    ]
                },
            )
        }

        # Create the table generator
        generator = SuperSpeedTipsTableGenerator(current_data, debug=True)

        # Generate the table with delta calculations enabled
        table_markdown = generator.generate_table(
            max_rows=20, include_delta=True, comparison_data=comparison_data
        )

        # The bug: the generated table should include delta columns with proper values
        # Expected: table should show position changes (↑, ↓, or =) for tips that existed
        # Actual: table shows "n/a" for all delta columns

        # Verify that the table includes delta columns
        assert "Δ vs previous month" in table_markdown, "Table should include delta column header"

        # Verify that the table shows proper delta values, not just "n/a"
        # This is where the bug manifests - the table generation process fails to
        # properly integrate delta calculations
        assert (
            "n/a" not in table_markdown
            or "=" in table_markdown
            or "↑" in table_markdown
            or "↓" in table_markdown
        ), "Table should show proper delta values, not just 'n/a'"

    def test_blackbird_plates_table_delta_integration(self):
        """Test that Blackbird plates table properly generates deltas.

        This test validates that Blackbird plates table works correctly
        since it already inherits from DataTransformingTableGenerator.
        """
        from sotd.report.table_generators.table_generator import TableGenerator

        # Current month data (June 2025) - includes ranks assigned by aggregator
        current_data = {
            "blackbird_plates": [
                {"plate": "OC", "shaves": 45, "unique_users": 12},
                {"plate": "SB", "shaves": 38, "unique_users": 10, "rank": 2},
                {"plate": "OC-SB", "shaves": 22, "unique_users": 8, "rank": 3},
            ]
        }

        # Previous month data (May 2025) - these plates definitely existed
        comparison_data = {
            "previous month": (
                {"month": "2025-05", "total_shaves": 800, "unique_shavers": 40},
                {
                    "blackbird_plates": [
                        {"plate": "OC", "shaves": 42, "unique_users": 11},
                        {"plate": "SB", "shaves": 40, "unique_users": 12, "rank": 2},
                        {"plate": "OC-SB", "shaves": 25, "unique_users": 9, "rank": 3},
                    ]
                },
            )
        }

        # Create the table generator
        generator = BlackbirdPlatesTableGenerator(current_data, debug=True)

        # Generate the table with delta calculations enabled
        table_markdown = generator.generate_table(
            max_rows=20, include_delta=True, comparison_data=comparison_data
        )

        # This table should work correctly since it inherits from DataTransformingTableGenerator
        # Verify that the table includes delta columns
        assert "Δ vs previous month" in table_markdown, "Table should include delta column header"

        # Verify that the table shows proper delta values, not just "n/a"
        assert (
            "n/a" not in table_markdown
            or "=" in table_markdown
            or "↑" in table_markdown
            or "↓" in table_markdown
        ), "Table should show proper delta values, not just 'n/a'"


class TestCalculateDeltasForPeriod:
    """Test the calculate_deltas_for_period function."""

    def test_calculate_deltas_for_period_success(self):
        """Test successful delta calculation for a period."""
        current_data = {
            "razors": [
                {"name": "Razor A", "shaves": 100},
                {"name": "Razor B", "shaves": 80, "rank": 2},
            ]
        }

        comparison_data: Dict[str, Tuple[Dict[str, Any], Dict[str, Any]]] = {
            "previous_month": (
                {"month": "2024-12"},
                {
                    "razors": [
                        {"name": "Razor B", "shaves": 90},
                        {"name": "Razor A", "shaves": 85, "rank": 2},
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
        current_data = {"razors": [{"name": "Razor A", "shaves": 100}]}

        comparison_data: Dict[str, Tuple[Dict[str, Any], Dict[str, Any]]] = {
            "previous_month": (
                {"month": "2024-12"},
                {"razors": [{"name": "Razor A", "shaves": 90, "rank": 2}]},
            )
        }

        result = calculate_deltas_for_period(
            current_data, comparison_data, "previous_month", ["razors"], debug=True
        )

        assert result is not None
        assert "razors" in result
        assert len(result["razors"]) == 1
        assert result["razors"][0]["delta"] == 1
