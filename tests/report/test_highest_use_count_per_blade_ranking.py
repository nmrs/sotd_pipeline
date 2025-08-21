"""Test ranking functionality for HighestUseCountPerBladeTableGenerator."""

from sotd.report.table_generators.cross_product_tables import (
    HighestUseCountPerBladeTableGenerator,
)


class TestHighestUseCountPerBladeRanking:
    """Test that ranking is properly preserved and displayed."""

    def test_ranking_preserves_existing_ranks(self):
        """Test that existing ranks from aggregator are preserved, not recalculated."""
        # Mock data with existing ranks from aggregator
        # Note: data structure matches actual aggregator output:
        # data['data']['highest_use_count_per_blade']
        mock_data = {
            "data": {
                "highest_use_count_per_blade": [
                    {
                        "rank": 1,
                        "user": "u/user1",
                        "blade": "Feather",
                        "uses": 100,
                    },
                    {
                        "rank": 2,
                        "user": "u/user2",
                        "blade": "Astra",
                        "uses": 90,
                    },
                    {
                        "rank": 3,
                        "user": "u/user3",
                        "blade": "Derby",
                        "uses": 80,
                    },
                ]
            }
        }

        generator = HighestUseCountPerBladeTableGenerator(mock_data)
        table_data = generator.get_table_data()

        # Verify that ranks are preserved exactly as provided
        assert table_data[0]["rank"] == 1
        assert table_data[1]["rank"] == 2
        assert table_data[2]["rank"] == 3

        # Verify that user field is properly formatted (u/ prefix preserved as-is)
        assert table_data[0]["user"] == "u/user1"  # Preserved as-is since it already has u/ prefix
        assert table_data[1]["user"] == "u/user2"
        assert table_data[2]["user"] == "u/user3"

    def test_ranking_with_ties_handled_correctly(self):
        """Test that tied ranks are handled correctly with '=' suffix."""
        # Mock data with tied ranks
        mock_data = {
            "data": {
                "highest_use_count_per_blade": [
                    {
                        "rank": 1,
                        "user": "u/user1",
                        "blade": "Feather",
                        "uses": 100,
                    },
                    {
                        "rank": 1,  # Tied for first
                        "user": "u/user2",
                        "blade": "Astra",
                        "uses": 100,
                    },
                    {
                        "rank": 3,
                        "user": "u/user3",
                        "blade": "Derby",
                        "uses": 80,
                    },
                ]
            }
        }

        generator = HighestUseCountPerBladeTableGenerator(mock_data)
        table_data = generator.get_table_data()

        # Verify that tied ranks are preserved
        assert table_data[0]["rank"] == 1
        assert table_data[1]["rank"] == 1  # Should still be 1, not recalculated
        assert table_data[2]["rank"] == 3

    def test_ranking_not_recalculated_by_table_generator(self):
        """Test that table generator does not recalculate ranks, only formats them."""
        # Mock data with sequential ranks
        mock_data = {
            "data": {
                "highest_use_count_per_blade": [
                    {
                        "rank": 1,
                        "user": "u/user1",
                        "blade": "Feather",
                        "uses": 100,
                    },
                    {
                        "rank": 2,
                        "user": "u/user2",
                        "blade": "Astra",
                        "uses": 90,
                    },
                    {
                        "rank": 3,
                        "user": "u/user3",
                        "blade": "Derby",
                        "uses": 80,
                    },
                ]
            }
        }

        generator = HighestUseCountPerBladeTableGenerator(mock_data)
        table_data = generator.get_table_data()

        # The table generator should NOT change the rank values
        # It should only format them for display (e.g., adding "=" for ties)
        assert len([item for item in table_data if item["rank"] == 1]) == 1
        assert len([item for item in table_data if item["rank"] == 2]) == 1
        assert len([item for item in table_data if item["rank"] == 3]) == 1

        # Verify that the original rank values are preserved exactly
        assert table_data[0]["rank"] == 1
        assert table_data[1]["rank"] == 2
        assert table_data[2]["rank"] == 3

    def test_ranking_with_real_aggregator_data_structure(self):
        """Test with data structure that matches actual aggregator output."""
        # This structure matches what the highest_use_count_per_blade aggregator produces
        mock_data = {
            "data": {
                "highest_use_count_per_blade": [
                    {
                        "rank": 1,
                        "user": "u/tsrblke",
                        "blade": "Derby Premium",
                        "uses": 275,
                    },
                    {
                        "rank": 2,
                        "user": "u/another_user",
                        "blade": "Feather",
                        "uses": 112,
                    },
                    {
                        "rank": 3,
                        "user": "u/third_user",
                        "blade": "Astra",
                        "uses": 110,
                    },
                ]
            }
        }

        generator = HighestUseCountPerBladeTableGenerator(mock_data)
        table_data = generator.get_table_data()

        # Verify ranks are preserved exactly as provided by aggregator
        assert table_data[0]["rank"] == 1
        assert table_data[1]["rank"] == 2
        assert table_data[2]["rank"] == 3

        # Verify that user field is properly formatted
        # Preserved as-is since it already has u/ prefix
        assert table_data[0]["user"] == "u/tsrblke"
        assert table_data[1]["user"] == "u/another_user"
        assert table_data[2]["user"] == "u/third_user"
