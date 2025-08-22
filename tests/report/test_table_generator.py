"""Tests for the TableGenerator."""

import pytest

from sotd.report.table_generators.table_generator import TableGenerator


class TestTableGenerator:
    """Test cases for TableGenerator."""

    def test_basic_table_generation(self):
        """Test basic table generation without parameters."""
        data = {
            "soap_makers": [
                {"rank": 1, "shaves": 100, "unique_users": 50, "brand": "Brand A"},
                {"rank": 2, "shaves": 80, "unique_users": 40, "brand": "Brand B"},
                {"rank": 3, "shaves": 60, "unique_users": 30, "brand": "Brand C"},
            ]
        }

        generator = TableGenerator(data)
        result = generator.generate_table("soap-makers")

        # Should contain all rows
        assert "Brand A" in result
        assert "Brand B" in result
        assert "Brand C" in result
        assert "100" in result
        assert "80" in result
        assert "60" in result

    def test_ranks_filtering(self):
        """Test ranks parameter filtering."""
        data = {
            "soap_makers": [
                {"rank": 1, "shaves": 100, "unique_users": 50, "brand": "Brand A"},
                {"rank": 2, "shaves": 80, "unique_users": 40, "brand": "Brand B"},
                {"rank": 3, "shaves": 60, "unique_users": 30, "brand": "Brand C"},
            ]
        }

        generator = TableGenerator(data)
        result = generator.generate_table("soap-makers", ranks=2)

        # Should include rank 1 and 2 (inclusive)
        assert "Brand A" in result
        assert "Brand B" in result
        assert "Brand C" not in result

    def test_rows_limiting(self):
        """Test rows parameter limiting."""
        data = {
            "soap_makers": [
                {"rank": 1, "shaves": 100, "unique_users": 50, "brand": "Brand A"},
                {"rank": 2, "shaves": 80, "unique_users": 40, "brand": "Brand B"},
                {"rank": 3, "shaves": 60, "unique_users": 30, "brand": "Brand C"},
            ]
        }

        generator = TableGenerator(data)
        result = generator.generate_table("soap-makers", rows=2)

        # Should include first 2 rows
        assert "Brand A" in result
        assert "Brand B" in result
        assert "Brand C" not in result

    def test_both_parameters(self):
        """Test both ranks and rows parameters together."""
        data = {
            "soap_makers": [
                {"rank": 1, "shaves": 100, "unique_users": 50, "brand": "Brand A"},
                {"rank": 2, "shaves": 80, "unique_users": 40, "brand": "Brand B"},
                {"rank": 3, "shaves": 60, "unique_users": 30, "brand": "Brand C"},
            ]
        }

        generator = TableGenerator(data)
        result = generator.generate_table("soap-makers", ranks=3, rows=2)

        # Should stop at rows limit (2) even though ranks allows 3
        assert "Brand A" in result
        assert "Brand B" in result
        assert "Brand C" not in result

    def test_empty_data(self):
        """Test handling of empty data."""
        data = {"soap_makers": []}
        generator = TableGenerator(data)
        result = generator.generate_table("soap-makers")

        assert result == ""

    def test_missing_rank_column(self):
        """Test error when rank column is missing."""
        data = {
            "soap_makers": [
                {"shaves": 100, "unique_users": 50, "brand": "Brand A"},
            ]
        }

        generator = TableGenerator(data)

        with pytest.raises(ValueError, match="missing 'rank' column"):
            generator.generate_table("soap-makers")

    def test_invalid_ranks_parameter(self):
        """Test error for invalid ranks parameter."""
        data = {"soap_makers": [{"rank": 1, "brand": "Brand A"}]}
        generator = TableGenerator(data)

        with pytest.raises(ValueError, match="ranks must be greater than 0"):
            generator.generate_table("soap-makers", ranks=0)

        with pytest.raises(ValueError, match="ranks must be greater than 0"):
            generator.generate_table("soap-makers", ranks=-1)

    def test_invalid_rows_parameter(self):
        """Test error for invalid rows parameter."""
        data = {"soap_makers": [{"rank": 1, "brand": "Brand A"}]}
        generator = TableGenerator(data)

        with pytest.raises(ValueError, match="rows must be greater than 0"):
            generator.generate_table("soap-makers", rows=0)

        with pytest.raises(ValueError, match="rows must be greater than 0"):
            generator.generate_table("soap-makers", rows=-1)

    def test_unknown_table_name(self):
        """Test error for unknown table name."""
        data = {"soap_makers": [{"rank": 1, "brand": "Brand A"}]}
        generator = TableGenerator(data)

        with pytest.raises(ValueError, match="Unknown table name: unknown-table"):
            generator.generate_table("unknown-table")

    def test_missing_data_key(self):
        """Test handling when data key is missing."""
        data = {"other_category": [{"rank": 1, "brand": "Brand A"}]}
        generator = TableGenerator(data)
        result = generator.generate_table("soap-makers")

        assert result == "*No data available for soap-makers*"

    def test_empty_data_key(self):
        """Test handling when data key exists but is empty."""
        data = {"soap_makers": []}
        generator = TableGenerator(data)
        result = generator.generate_table("soap-makers")

        assert result == ""

    def test_get_available_table_names(self):
        """Test getting available table names."""
        data = {"soap_makers": [{"rank": 1, "brand": "Brand A"}]}
        generator = TableGenerator(data)
        table_names = generator.get_available_table_names()

        # Should include all the mapped table names
        assert "razors" in table_names
        assert "soap-makers" in table_names
        assert "test-category" not in table_names  # Only mapped names
