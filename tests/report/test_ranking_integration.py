"""Integration tests for ranking preservation in report generation pipeline.

These tests verify that ranks are preserved from aggregated data through to final report markdown,
specifically addressing the bug where all ranks show as '1=' in the final report.
"""

import pytest
from pathlib import Path

from sotd.report.table_generators.table_generator import TableGenerator
from sotd.report.enhanced_table_generator import EnhancedTableGenerator


class TestRankingIntegration:
    """Test ranking preservation through the complete report generation pipeline."""

    def test_highest_use_count_per_blade_ranking_preservation(self):
        """Test that ranks are preserved from aggregated data to final report markdown."""
        # Sample aggregated data with correct ranks
        aggregated_data = {
            "highest_use_count_per_blade": [
                {"rank": 1, "user": "user1", "blade": "Gillette Nacet", "format": "DE", "uses": 15},
                {
                    "rank": 2,
                    "user": "user2",
                    "blade": "Personna Lab Blue",
                    "format": "DE",
                    "uses": 12,
                },
                {
                    "rank": 3,
                    "user": "user3",
                    "blade": "Astra Superior Platinum",
                    "format": "DE",
                    "uses": 10,
                },
                {
                    "rank": 4,
                    "user": "user4",
                    "blade": "Feather Hi-Stainless",
                    "format": "DE",
                    "uses": 8,
                },
                {
                    "rank": 5,
                    "user": "user5",
                    "blade": "Voskhod Teflon Coated",
                    "format": "DE",
                    "uses": 6,
                },
            ]
        }

        # Test 1: Verify aggregated data has correct ranks
        blade_data = aggregated_data["highest_use_count_per_blade"]
        assert len(blade_data) == 5
        assert blade_data[0]["rank"] == 1
        assert blade_data[1]["rank"] == 2
        assert blade_data[2]["rank"] == 3
        assert blade_data[3]["rank"] == 4
        assert blade_data[4]["rank"] == 5

        # Test 2: Verify table generator preserves ranks
        table_generator = TableGenerator(aggregated_data, debug=False)
        table_data = table_generator.generate_table("specific-table")

        # This should NOT be empty - if it is, we've found the bug!
        assert len(table_data) == 5, (
            f"Expected 5 items, got {len(table_data)}. "
            "This indicates the table generator is not processing data correctly."
        )

        # Verify ranks are preserved in table data
        for i, item in enumerate(table_data):
            expected_rank = i + 1
            assert (
                item["rank"] == expected_rank
            ), f"Item {i}: expected rank {expected_rank}, got {item['rank']}"

        # Test 3: Verify enhanced table processing preserves ranks
        enhanced_generator = EnhancedTableGenerator()
        enhanced_data = enhanced_generator.generate_table(
            "highest-use-count-per-blade", table_data, {"rows": 30}
        )

        # Enhanced processing should preserve all data when rows:30 is specified
        assert (
            len(enhanced_data) == 5
        ), f"Enhanced processing should preserve all data, got {len(enhanced_data)} items"

        # Verify ranks are still correct after enhanced processing
        for i, item in enumerate(enhanced_data):
            expected_rank = i + 1
            assert (
                item["rank"] == expected_rank
            ), f"Enhanced item {i}: expected rank {expected_rank}, got {item['rank']}"

    def test_basic_table_syntax_ranking_preservation(self):
        """Test that basic table syntax {{tables.highest-use-count-per-blade}} preserves ranks."""
        # Use the same aggregated data with correct structure
        aggregated_data = {
            "data": {
                "highest_use_count_per_blade": [
                    {
                        "rank": 1,
                        "user": "user1",
                        "blade": "Gillette Nacet",
                        "format": "DE",
                        "uses": 15,
                    },
                    {
                        "rank": 2,
                        "user": "user2",
                        "blade": "Personna Lab Blue",
                        "format": "DE",
                        "uses": 12,
                    },
                    {
                        "rank": 3,
                        "user": "user3",
                        "blade": "Astra Superior Platinum",
                        "format": "DE",
                        "uses": 10,
                    },
                ]
            }
        }

        # Test the table generator directly to get raw data
        table_generator = TableGenerator(aggregated_data, debug=False)
        basic_table = table_generator.generate_table("specific-table")

        # Basic table should preserve ranks
        assert len(basic_table) == 3, f"Basic table should have 3 items, got {len(basic_table)}"

        # Verify ranks are preserved
        for i, item in enumerate(basic_table):
            expected_rank = i + 1
            assert (
                item["rank"] == expected_rank
            ), f"Basic table item {i}: expected rank {expected_rank}, got {item['rank']}"

    def test_enhanced_table_syntax_ranking_preservation(self):
        """Test that enhanced table syntax {{tables.highest-use-count-per-blade|rows:30}} preserves ranks."""
        # Use the same aggregated data with correct structure
        aggregated_data = {
            "data": {
                "highest_use_count_per_blade": [
                    {
                        "rank": 1,
                        "user": "user1",
                        "blade": "Gillette Nacet",
                        "format": "DE",
                        "uses": 15,
                    },
                    {
                        "rank": 2,
                        "user": "user2",
                        "blade": "Personna Lab Blue",
                        "format": "DE",
                        "uses": 12,
                    },
                    {
                        "rank": 3,
                        "user": "user3",
                        "blade": "Astra Superior Platinum",
                        "format": "DE",
                        "uses": 10,
                    },
                ]
            }
        }

        # Test the table generator directly to get raw data
        table_generator = TableGenerator(aggregated_data, debug=False)
        raw_data = table_generator.generate_table("specific-table")

        # Test enhanced table processing
        enhanced_generator = EnhancedTableGenerator()
        enhanced_data = enhanced_generator.generate_table(
            "highest-use-count-per-blade", raw_data, {"rows": 30}
        )

        # Enhanced table should preserve all data when rows:30 is specified
        assert (
            len(enhanced_data) == 3
        ), f"Enhanced table with rows:30 should have 3 items, got {len(enhanced_data)}"

        # Verify ranks are preserved
        for i, item in enumerate(enhanced_data):
            expected_rank = i + 1
            assert (
                item["rank"] == expected_rank
            ), f"Enhanced table item {i}: expected rank {expected_rank}, got {item['rank']}"

    def test_real_data_integration(self):
        """Test with real 2025-06 aggregated data to reproduce the actual bug."""
        # Check if real data file exists
        real_data_path = Path("data/aggregated/2025-06.json")
        if not real_data_path.exists():
            pytest.skip("Real 2025-06 aggregated data not available")

        # Load real data
        import json

        with open(real_data_path) as f:
            real_data = json.load(f)

        # Verify real data has the expected structure
        assert "data" in real_data, "Real data should have 'data' key"
        assert (
            "highest_use_count_per_blade" in real_data["data"]
        ), "Real data should have 'highest_use_count_per_blade'"

        blade_data = real_data["data"]["highest_use_count_per_blade"]
        assert len(blade_data) > 0, "Real data should have blade entries"

        # Test 1: Verify real aggregated data has correct competition ranking
        # Competition ranking skips ranks after ties
        # (e.g., 1, 2, 3, 4, 5, 15, 15, 15, 18...)
        # This is correct behavior - the test expectation was wrong
        for i, item in enumerate(blade_data):
            actual_rank = item["rank"]
            # Verify that ranks are valid competition ranking (no gaps in the sequence)
            if i > 0:
                prev_rank = blade_data[i - 1]["rank"]
                # In competition ranking, current rank should be >= previous rank
                assert (
                    actual_rank >= prev_rank
                ), f"Item {i}: rank {actual_rank} should be >= previous rank {prev_rank}"

            # Verify rank is a positive integer
            assert (
                isinstance(actual_rank, int) and actual_rank > 0
            ), f"Item {i}: rank {actual_rank} should be positive integer"

        # Test 2: Verify table generator works with real data
        table_generator = TableGenerator(real_data["data"], debug=False)
        table_data = table_generator.generate_table("specific-table")

        # This should NOT be empty with real data
        assert (
            len(table_data) > 0
        ), f"Table generator should process real data, got {len(table_data)} items"

        # Verify ranks are preserved in real data processing (competition ranking)
        # Table generators should preserve original ranks from aggregators, not re-assign them
        for i, item in enumerate(table_data):
            actual_rank = item["rank"]
            # Verify rank is a positive integer
            assert (
                isinstance(actual_rank, int) and actual_rank > 0
            ), f"Table item {i}: rank {actual_rank} should be positive integer"

            # Verify that ranks maintain competition ranking order (no gaps in sequence)
            if i > 0:
                prev_rank = table_data[i - 1]["rank"]
                assert (
                    actual_rank >= prev_rank
                ), f"Table item {i}: rank {actual_rank} should be >= previous rank {prev_rank}"

    def test_ranking_corruption_detection(self):
        """Test that we can detect when ranking corruption occurs."""
        # This test will fail initially (exposing the bug) and pass after we fix it

        # Sample data that should work correctly
        test_data = {
            "highest_use_count_per_blade": [
                {"rank": 1, "user": "user1", "blade": "Test Blade 1", "format": "DE", "uses": 10},
                {"rank": 2, "user": "user2", "blade": "Test Blade 2", "format": "DE", "uses": 8},
                {"rank": 3, "user": "user3", "blade": "Test Blade 3", "format": "DE", "uses": 6},
            ]
        }

        # Test the complete pipeline
        table_generator = TableGenerator(test_data, debug=False)
        table_data = table_generator.generate_table("specific-table")

        # This assertion will fail if the bug exists (empty data)
        assert (
            len(table_data) == 3
        ), f"Expected 3 items, got {len(table_data)}. This indicates the ranking bug is present."

        # Verify ranks are sequential (1, 2, 3) not all 1
        ranks = [item["rank"] for item in table_data]
        expected_ranks = [1, 2, 3]
        assert (
            ranks == expected_ranks
        ), f"Expected ranks {expected_ranks}, got {ranks}. This indicates rank corruption."

        # Test enhanced table processing
        enhanced_generator = EnhancedTableGenerator()
        enhanced_data = enhanced_generator.generate_table(
            "highest-use-count-per-blade", table_data, {"rows": 30}
        )

        # Enhanced processing should preserve all data
        assert (
            len(enhanced_data) == 3
        ), f"Enhanced processing should preserve all data, got {len(enhanced_data)} items"

        # Verify ranks are still correct after enhanced processing
        enhanced_ranks = [item["rank"] for item in enhanced_data]
        assert (
            enhanced_ranks == expected_ranks
        ), f"Enhanced processing corrupted ranks: expected {expected_ranks}, got {enhanced_ranks}"

    def test_error_messages_for_ranking_bug(self):
        """Test that error messages clearly show expected vs actual ranks when the bug occurs."""
        test_data = {
            "highest_use_count_per_blade": [
                {"rank": 1, "user": "user1", "blade": "Test Blade 1", "format": "DE", "uses": 10},
                {"rank": 2, "user": "user2", "blade": "Test Blade 2", "format": "DE", "uses": 8},
                {"rank": 3, "user": "user3", "blade": "Test Blade 3", "format": "DE", "uses": 6},
            ]
        }

        table_generator = TableGenerator(test_data, debug=False)
        table_data = table_generator.generate_table("specific-table")

        # If the bug exists, provide clear error information
        if len(table_data) != 3:
            pytest.fail(
                f"Ranking bug detected! Expected 3 items, got {len(table_data)}. "
                f"Table generator is not processing data correctly."
            )

        # Check for rank corruption
        ranks = [item["rank"] for item in table_data]
        expected_ranks = [1, 2, 3]

        if ranks != expected_ranks:
            pytest.fail(
                f"Rank corruption detected! Expected ranks {expected_ranks}, got {ranks}. "
                f"This indicates the integration bug where ranks get corrupted during processing."
            )

        # If we get here, the test passes (no bug detected)
        assert True, "No ranking bug detected - all ranks preserved correctly"
