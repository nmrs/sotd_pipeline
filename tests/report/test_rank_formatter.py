"""Tests for rank formatting functionality in table generators."""

from sotd.report.table_generators.base import BaseTableGenerator


class TestRankFormatter:
    """Test cases for rank formatting functionality."""

    def test_format_ranks_no_ties(self):
        """Test rank formatting when no items are tied."""
        # Test data: [1, 2, 3] should produce ["1", "2", "3"]
        ranks = [1, 2, 3]
        expected = ["1", "2", "3"]

        # Create a concrete instance to test the method
        class ConcreteTableGenerator(BaseTableGenerator):
            def get_table_data(self):
                return []

            def get_table_title(self):
                return "Test"

            def get_column_config(self):
                return {}

        generator = ConcreteTableGenerator({})
        result = generator._format_ranks_with_ties(ranks)
        assert result == expected

    def test_format_ranks_two_way_ties(self):
        """Test rank formatting for two-way ties."""
        # Test data: [1, 2, 2, 3] should produce ["1", "2=", "2=", "3"]
        ranks = [1, 2, 2, 3]
        expected = ["1", "2=", "2=", "3"]

        class ConcreteTableGenerator(BaseTableGenerator):
            def get_table_data(self):
                return []

            def get_table_title(self):
                return "Test"

            def get_column_config(self):
                return {}

        generator = ConcreteTableGenerator({})
        result = generator._format_ranks_with_ties(ranks)
        assert result == expected

    def test_format_ranks_three_way_ties(self):
        """Test rank formatting for three-way ties."""
        # Test data: [1, 2, 2, 2, 3] should produce ["1", "2=", "2=", "2=", "3"]
        ranks = [1, 2, 2, 2, 3]
        expected = ["1", "2=", "2=", "2=", "3"]

        class ConcreteTableGenerator(BaseTableGenerator):
            def get_table_data(self):
                return []

            def get_table_title(self):
                return "Test"

            def get_column_config(self):
                return {}

        generator = ConcreteTableGenerator({})
        result = generator._format_ranks_with_ties(ranks)
        assert result == expected

    def test_format_ranks_all_tied(self):
        """Test rank formatting when all items are tied."""
        # Test data: [1, 1, 1] should produce ["1=", "1=", "1="]
        ranks = [1, 1, 1]
        expected = ["1=", "1=", "1="]

        class ConcreteTableGenerator(BaseTableGenerator):
            def get_table_data(self):
                return []

            def get_table_title(self):
                return "Test"

            def get_column_config(self):
                return {}

        generator = ConcreteTableGenerator({})
        result = generator._format_ranks_with_ties(ranks)
        assert result == expected

    def test_format_ranks_edge_cases(self):
        """Test rank formatting for edge cases."""

        class ConcreteTableGenerator(BaseTableGenerator):
            def get_table_data(self):
                return []

            def get_table_title(self):
                return "Test"

            def get_column_config(self):
                return {}

        generator = ConcreteTableGenerator({})

        # Empty list
        empty_ranks = []
        empty_expected = []
        result = generator._format_ranks_with_ties(empty_ranks)
        assert result == empty_expected

        # Single item
        single_ranks = [1]
        single_expected = ["1"]
        result = generator._format_ranks_with_ties(single_ranks)
        assert result == single_expected

    def test_format_ranks_mixed_patterns(self):
        """Test rank formatting for mixed tie patterns."""
        # Test data: [1, 1, 3, 3, 3, 6] should produce ["1=", "1=", "3=", "3=", "3=", "6"]
        ranks = [1, 1, 3, 3, 3, 6]
        expected = ["1=", "1=", "3=", "3=", "3=", "6"]

        class ConcreteTableGenerator(BaseTableGenerator):
            def get_table_data(self):
                return []

            def get_table_title(self):
                return "Test"

            def get_column_config(self):
                return {}

        generator = ConcreteTableGenerator({})
        result = generator._format_ranks_with_ties(ranks)
        assert result == expected

    def test_format_existing_ranks_with_ties(self):
        """Test that _format_existing_ranks_with_proper_ties correctly formats existing ranks with tie indicators."""

        class ConcreteTableGenerator(BaseTableGenerator):
            def get_table_data(self):
                return []

            def get_table_title(self):
                return "Test"

            def get_column_config(self):
                return {}

        generator = ConcreteTableGenerator({})

        # Test data with EXISTING ranks (from aggregators) - generators don't assign ranks
        test_data = [
            {"name": "Item A", "shaves": 10, "unique_users": 3, "rank": 1},
            {"name": "Item B", "shaves": 8, "unique_users": 2, "rank": 2},
            {"name": "Item C", "shaves": 8, "unique_users": 2, "rank": 2},  # Tied with Item B
            {"name": "Item D", "shaves": 6, "unique_users": 1, "rank": 3},
        ]

        result = generator._format_existing_ranks_with_proper_ties(test_data)

        # Check that ranks are formatted with tie indicators (not assigned)
        assert len(result) == 4
        assert result[0]["rank"] == "1"  # Item A: rank 1
        assert result[1]["rank"] == "2="  # Item B: rank 2 (tied)
        assert result[2]["rank"] == "2="  # Item C: rank 2 (tied)
        assert result[3]["rank"] == "3"  # Item D: rank 3

        # Check that data order is preserved (generators don't sort)
        assert result[0]["name"] == "Item A"
        assert result[1]["name"] == "Item B"
        assert result[2]["name"] == "Item C"
        assert result[3]["name"] == "Item D"

    def test_rank_column_in_table_output(self):
        """Test that the rank column appears in the actual table output."""

        class TestTableGenerator(BaseTableGenerator):
            def get_table_data(self):
                return [
                    {"name": "Item A", "shaves": 10, "unique_users": 3, "rank": 1},
                    {"name": "Item B", "shaves": 8, "unique_users": 2, "rank": 2},
                    {"name": "Item C", "shaves": 8, "unique_users": 2, "rank": 2},  # Tied with Item B
                    {"name": "Item D", "shaves": 6, "unique_users": 1, "rank": 4},
                ]

            def get_table_title(self):
                return "Test Table"

            def get_column_config(self):
                return {
                    "rank": {"display_name": "Rank"},
                    "name": {"display_name": "Name"},
                    "shaves": {"display_name": "Shaves", "format": "number"},
                    "unique_users": {"display_name": "Users", "format": "number"},
                }

        generator = TestTableGenerator({})

        # Generate the table
        table_output = generator.generate_table(max_rows=10, include_delta=False)

        # Check that the rank column appears in the output
        assert "Rank" in table_output
        assert "Item A" in table_output
        assert "Item B" in table_output
        assert "Item C" in table_output
        assert "Item D" in table_output

        # Check that tie indicators appear
        assert "2=" in table_output  # Should show tied ranks

        # Verify the table structure includes rank column
        lines = table_output.split("\n")
        header_line = None
        for line in lines:
            if "|" in line and "Rank" in line:
                header_line = line
                break

        assert header_line is not None, "Rank column header not found in table"

        # Check that rank column is first
        columns = [col.strip() for col in header_line.split("|") if col.strip()]
        assert columns[0] == "Rank", f"Rank column should be first, got: {columns}"
