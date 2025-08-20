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
