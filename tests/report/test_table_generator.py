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

    def test_column_name_formatting(self):
        """Test that column names are automatically formatted to Title Case."""
        data = {
            "soap_makers": [
                {"rank": 1, "shaves": 100, "unique_users": 50, "maker": "Brand A"},
                {"rank": 2, "shaves": 80, "unique_users": 40, "maker": "Brand B"},
            ]
        }

        generator = TableGenerator(data)
        result = generator.generate_table("soap-makers", rows=2)

        # Check that column names are formatted
        assert "|   Rank |   Shaves |   Unique Users | Maker" in result
        assert "|-------:|---------:|---------------:|:--------" in result

        # Verify no snake_case remains
        assert "unique_users" not in result
        assert "Unique Users" in result

    def test_acronym_preservation(self):
        """Test that acronyms are preserved in uppercase."""
        data = {
            "razor_formats": [
                {"rank": 1, "format": "DE", "shaves": 100, "unique_users": 50},
                {"rank": 2, "format": "GEM", "shaves": 80, "unique_users": 40},
                {"rank": 3, "format": "AC", "shaves": 60, "unique_users": 30},
            ]
        }

        generator = TableGenerator(data)
        result = generator.generate_table("razor-formats", rows=3)

        # Check that acronyms are preserved
        assert "|   Rank | Format   |   Shaves |   Unique Users |" in result
        assert "|      1 | DE       |" in result
        assert "|      2 | GEM      |" in result
        assert "|      3 | AC       |" in result

        # Verify acronyms are not converted to title case
        assert "|      1 | De       |" not in result
        assert "|      2 | Gem      |" not in result

    def test_column_reordering(self):
        """Test column reordering functionality."""
        data = {
            "soap_makers": [
                {"rank": 1, "shaves": 100, "unique_users": 50, "maker": "Brand A"},
                {"rank": 2, "shaves": 80, "unique_users": 40, "maker": "Brand B"},
            ]
        }

        generator = TableGenerator(data)
        result = generator.generate_table(
            "soap-makers", rows=2, columns="shaves, rank, unique_users"
        )

        # Check that columns are reordered
        assert "|   Shaves |   Rank |   Unique Users |" in result
        assert "|      100 |      1 |             50 |" in result

        # Verify original order is not present
        assert "|   Rank |   Shaves |   Unique Users |" not in result

    def test_column_renaming(self):
        """Test column renaming functionality."""
        data = {
            "soap_makers": [
                {"rank": 1, "shaves": 100, "unique_users": 50, "maker": "Brand A"},
                {"rank": 2, "shaves": 80, "unique_users": 40, "maker": "Brand B"},
            ]
        }

        generator = TableGenerator(data)
        result = generator.generate_table("soap-makers", rows=2, columns="rank, maker=soap, shaves")

        # Check that column is renamed
        assert "|   Rank | Soap    |   Shaves |" in result
        assert "|      1 | Brand A |      100 |" in result

        # Verify original name is not present
        assert "|   Rank | Maker   |   Shaves |" not in result

    def test_column_reordering_and_renaming(self):
        """Test combined column reordering and renaming."""
        data = {
            "soap_makers": [
                {"rank": 1, "shaves": 100, "unique_users": 50, "maker": "Brand A"},
                {"rank": 2, "shaves": 80, "unique_users": 40, "maker": "Brand B"},
            ]
        }

        generator = TableGenerator(data)
        result = generator.generate_table("soap-makers", rows=2, columns="shaves, maker=soap, rank")

        # Check that columns are reordered and renamed
        assert "|   Shaves | Soap    |   Rank |" in result
        assert "|      100 | Brand A |      1 |" in result

    def test_columns_with_ranks_parameter(self):
        """Test columns parameter combined with ranks parameter."""
        data = {
            "soap_makers": [
                {"rank": 1, "shaves": 100, "unique_users": 50, "maker": "Brand A"},
                {"rank": 2, "shaves": 80, "unique_users": 40, "maker": "Brand B"},
                {"rank": 3, "shaves": 60, "unique_users": 30, "maker": "Brand C"},
            ]
        }

        generator = TableGenerator(data)
        result = generator.generate_table("soap-makers", ranks=3, columns="rank, maker=soap")

        # Check that both parameters work together
        assert "|   Rank | Soap    |" in result
        assert "|      1 | Brand A |" in result
        assert "|      2 | Brand B |" in result
        assert "|      3 | Brand C |" in result

    def test_columns_with_rows_parameter(self):
        """Test columns parameter combined with rows parameter."""
        data = {
            "soap_makers": [
                {"rank": 1, "shaves": 100, "unique_users": 50, "maker": "Brand A"},
                {"rank": 2, "shaves": 80, "unique_users": 40, "maker": "Brand B"},
                {"rank": 3, "shaves": 60, "unique_users": 30, "maker": "Brand C"},
            ]
        }

        generator = TableGenerator(data)
        result = generator.generate_table("soap-makers", rows=2, columns="rank, maker=soap")

        # Check that both parameters work together
        assert "|   Rank | Soap    |" in result
        assert "|      1 | Brand A |" in result
        assert "|      2 | Brand B |" in result

        # Verify we don't see rank 3
        assert "|      3 | Brand C |" not in result

    def test_missing_columns_handling(self):
        """Test that missing columns are silently omitted."""
        data = {
            "soap_makers": [
                {"rank": 1, "shaves": 100, "unique_users": 50, "maker": "Brand A"},
                {"rank": 2, "shaves": 80, "unique_users": 40, "maker": "Brand B"},
            ]
        }

        generator = TableGenerator(data)
        result = generator.generate_table(
            "soap-makers", rows=2, columns="rank, nonexistent_column, shaves"
        )

        # Check that only existing columns are shown
        assert "|   Rank |   Shaves |" in result
        assert "|      1 |      100 |" in result

        # Verify missing column is not present
        assert "nonexistent_column" not in result

    def test_empty_columns_parameter(self):
        """Test that empty columns parameter shows all columns."""
        data = {
            "soap_makers": [
                {"rank": 1, "shaves": 100, "unique_users": 50, "maker": "Brand A"},
                {"rank": 2, "shaves": 80, "unique_users": 40, "maker": "Brand B"},
            ]
        }

        generator = TableGenerator(data)
        result = generator.generate_table("soap-makers", rows=2, columns="")

        # Should show all columns in original order
        assert "|   Rank |   Shaves |   Unique Users | Maker" in result

    def test_invalid_columns_syntax(self):
        """Test that invalid columns syntax raises appropriate errors."""
        data = {
            "soap_makers": [
                {"rank": 1, "shaves": 100, "unique_users": 50, "maker": "Brand A"},
            ]
        }

        generator = TableGenerator(data)

        # Test invalid rename syntax
        with pytest.raises(ValueError, match="Invalid rename syntax"):
            generator.generate_table("soap-makers", rows=2, columns="rank, name=soap=alias")

        # Test empty columns
        with pytest.raises(ValueError, match="Columns parameter cannot be empty"):
            generator.generate_table("soap-makers", rows=2, columns="   ")

    def test_no_valid_columns_after_filtering(self):
        """Test error when no valid columns remain after filtering."""
        data = {
            "soap_makers": [
                {"rank": 1, "shaves": 100, "unique_users": 50, "maker": "Brand A"},
            ]
        }

        generator = TableGenerator(data)

        with pytest.raises(ValueError, match="No valid columns found in data"):
            generator.generate_table("soap-makers", rows=2, columns="nonexistent1, nonexistent2")

    def test_rank_column_formatting_equal_ranks(self):
        """Test that equal ranks are formatted as N= in the rank column."""
        data = {
            "soap_makers": [
                {"rank": 1, "shaves": 100, "unique_users": 50, "maker": "Brand A"},
                {"rank": 2, "shaves": 80, "unique_users": 40, "maker": "Brand B"},
                {"rank": 2, "shaves": 80, "unique_users": 40, "maker": "Brand C"},
                {"rank": 4, "shaves": 60, "unique_users": 30, "maker": "Brand D"},
                {"rank": 4, "shaves": 60, "unique_users": 30, "maker": "Brand E"},
                {"rank": 4, "shaves": 60, "unique_users": 30, "maker": "Brand F"},
            ]
        }
        
        generator = TableGenerator(data)
        result = generator.generate_table("soap-makers", rows=6)
        
        # Check that equal ranks are formatted as N=
        assert "| 1      |" in result  # Single rank 1
        assert "| 2=     |" in result  # Equal rank 2 (should appear twice)
        assert "| 4=     |" in result  # Equal rank 4 (should appear three times)
        
        # Verify no plain equal ranks remain
        assert "| 2      |" not in result
        assert "| 4      |" not in result

    def test_rank_column_formatting_single_ranks(self):
        """Test that single ranks (no ties) are formatted normally."""
        data = {
            "soap_makers": [
                {"rank": 1, "shaves": 100, "unique_users": 50, "maker": "Brand A"},
                {"rank": 2, "shaves": 80, "unique_users": 40, "maker": "Brand B"},
                {"rank": 3, "shaves": 60, "unique_users": 30, "maker": "Brand C"},
            ]
        }
        
        generator = TableGenerator(data)
        result = generator.generate_table("soap-makers", rows=3)
        
        # Check that single ranks are formatted normally (numeric format, 
        # no rank formatting applied)
        assert "|      1 |" in result  # Single rank 1 (6 spaces, pandas numeric format)
        assert "|      2 |" in result  # Single rank 2 (6 spaces, pandas numeric format)
        assert "|      3 |" in result  # Single rank 3 (6 spaces, pandas numeric format)
        
        # Verify no N= formatting for single ranks
        assert "| 1=     |" not in result
        assert "| 2=     |" not in result
        assert "| 3=     |" not in result

    def test_rank_column_formatting_mixed_ranks(self):
        """Test mixed scenario with both single and equal ranks."""
        data = {
            "soap_makers": [
                {"rank": 1, "shaves": 100, "unique_users": 50, "maker": "Brand A"},
                {"rank": 2, "shaves": 80, "unique_users": 40, "maker": "Brand B"},
                {"rank": 2, "shaves": 80, "unique_users": 40, "maker": "Brand C"},
                {"rank": 4, "shaves": 60, "unique_users": 30, "maker": "Brand D"},
                {"rank": 5, "shaves": 50, "unique_users": 25, "maker": "Brand E"},
                {"rank": 5, "shaves": 50, "unique_users": 25, "maker": "Brand F"},
            ]
        }
        
        generator = TableGenerator(data)
        result = generator.generate_table("soap-makers", rows=6)
        
        # Check mixed formatting
        assert "| 1      |" in result  # Single rank 1 (2 spaces, pandas string format)
        assert "| 2=     |" in result  # Equal rank 2 (2 spaces, pandas string format)
        assert "| 4      |" in result  # Single rank 4 (2 spaces, pandas string format)
        assert "| 5=     |" in result  # Equal rank 5 (2 spaces, pandas string format)

    def test_rank_column_formatting_with_parameters(self):
        """Test rank formatting works with ranks and columns parameters."""
        data = {
            "soap_makers": [
                {"rank": 1, "shaves": 100, "unique_users": 50, "maker": "Brand A"},
                {"rank": 2, "shaves": 80, "unique_users": 40, "maker": "Brand B"},
                {"rank": 2, "shaves": 80, "unique_users": 40, "maker": "Brand C"},
                {"rank": 4, "shaves": 60, "unique_users": 30, "maker": "Brand D"},
            ]
        }
        
        generator = TableGenerator(data)
        result = generator.generate_table(
            "soap-makers", 
            ranks=3, 
            columns="rank, maker=soap, shaves"
        )
        
        # Check that rank formatting works with custom columns
        assert "| 1      |" in result  # Single rank 1 (2 spaces, pandas string format)
        assert "| 2=     |" in result  # Equal rank 2 (2 spaces, pandas string format)
        
        # Verify custom columns are working
        assert "| Soap    |" in result
        assert "|   Shaves |" in result
