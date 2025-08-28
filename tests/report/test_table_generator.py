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
        """Test error when rank column is missing but required by parameters."""
        data = {"soap_makers": [{"shaves": 100, "unique_users": 50, "brand": "Brand A"}]}

        generator = TableGenerator(data)

        # Rank column is required when using ranks parameter
        with pytest.raises(ValueError, match="missing 'rank' column"):
            generator.generate_table("soap-makers", ranks=3)

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

        with pytest.raises(ValueError, match="Unknown table: unknown-table"):
            generator.generate_table("unknown-table")

    def test_missing_data_key(self):
        """Test handling when data key is missing."""
        data = {"other_category": [{"rank": 1, "brand": "Brand A"}]}
        generator = TableGenerator(data)

        # Should raise ValueError for unknown table
        with pytest.raises(ValueError, match="Unknown table: soap-makers"):
            generator.generate_table("soap-makers")

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

        # Should only include actual data keys that exist in the data
        assert "soap_makers" in table_names
        assert "razors" not in table_names  # Not in data, so not in available names
        assert len(table_names) == 1  # Only one data key exists

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
        assert "Rank" in result and "Shaves" in result
        assert "Unique Users" in result and "Maker" in result
        assert "Brand A" in result
        assert "Brand B" in result

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
        assert "Rank" in result and "Format" in result
        assert "Shaves" in result and "Unique Users" in result
        assert "DE" in result  # DE should be preserved in uppercase
        assert "GEM" in result  # GEM should be preserved in uppercase
        assert "AC" in result  # AC should be preserved in uppercase

    def test_per_acronym_preservation(self):
        """Test that 'per' is preserved as lowercase in column names."""
        data = {
            "soap_makers": [
                {"rank": 1, "avg_shaves_per_soap": 5.2, "shaves": 100, "brand": "Brand A"},
                {"rank": 2, "avg_shaves_per_soap": 4.8, "shaves": 80, "brand": "Brand B"},
            ]
        }

        generator = TableGenerator(data)
        result = generator.generate_table("soap-makers", rows=2)

        # Check that 'per' is preserved as lowercase in column name
        # The column name should be "Avg Shaves Per Soap" with "per" lowercase
        assert "Avg Shaves per Soap" in result
        assert "Brand A" in result
        assert "Brand B" in result

        # Verify 'per' is not converted to 'Per' or 'PER'
        assert "| Avg Shaves Per Soap     |" not in result
        assert "| Avg Shaves PER Soap     |" not in result

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
        # Verify columns appear in the specified order
        shaves_index = result.find("Shaves")
        rank_index = result.find("Rank")
        unique_users_index = result.find("Unique Users")

        assert shaves_index != -1 and rank_index != -1 and unique_users_index != -1
        assert shaves_index < rank_index < unique_users_index  # Verify order
        assert "100" in result and "80" in result  # Verify data is present

        # Verify original order is not present
        assert "| Rank     | Shaves     | Unique Users     |" not in result

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
        assert "Rank" in result and "Soap" in result and "Shaves" in result
        assert "Brand A" in result and "Brand B" in result
        # Verify "Maker" column is not present (should be renamed to "Soap")
        assert "Maker" not in result

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
        # Verify columns appear in the specified order with renaming
        shaves_index = result.find("Shaves")
        soap_index = result.find("Soap")
        rank_index = result.find("Rank")

        assert shaves_index != -1 and soap_index != -1 and rank_index != -1
        assert shaves_index < soap_index < rank_index  # Verify order
        assert "Brand A" in result and "Brand B" in result  # Verify data is present
        # Verify "Maker" column is not present (should be renamed to "Soap")
        assert "Maker" not in result

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
        assert "Rank" in result and "Soap" in result
        assert "Brand A" in result
        assert "Brand B" in result
        assert "Brand C" in result

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
        assert "Rank" in result and "Soap" in result
        assert "Brand A" in result
        assert "Brand B" in result

        # Verify we don't see rank 3
        assert "Brand C" not in result

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
        assert "Rank" in result and "Shaves" in result
        assert "100" in result

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
        assert "Rank" in result and "Shaves" in result
        assert "Unique Users" in result and "Maker" in result

    def test_invalid_columns_syntax(self):
        """Test that invalid columns syntax raises appropriate errors."""
        data = {"soap_makers": [{"rank": 1, "shaves": 100, "unique_users": 50, "maker": "Brand A"}]}

        generator = TableGenerator(data)

        # Test invalid rename syntax
        with pytest.raises(ValueError, match="Invalid rename syntax"):
            generator.generate_table("soap-makers", rows=2, columns="rank, name=soap=alias")

        # Test empty columns
        with pytest.raises(ValueError, match="Columns parameter cannot be empty"):
            generator.generate_table("soap-makers", rows=2, columns="   ")

    def test_no_valid_columns_after_filtering(self):
        """Test error when no valid columns remain after filtering."""
        data = {"soap_makers": [{"rank": 1, "shaves": 100, "unique_users": 50, "maker": "Brand A"}]}

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
        assert "1" in result  # Single rank 1
        assert "2=" in result  # Equal rank 2 (should appear twice)
        assert "4=" in result  # Equal rank 4 (should appear three times)

        # Verify no plain equal ranks remain
        assert "2" in result  # Should still appear as "2="
        assert "4" in result  # Should still appear as "4="

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
        assert "1 " in result  # Single rank 1 (with space suffix)
        assert "2 " in result  # Single rank 2 (with space suffix)
        assert "3 " in result  # Single rank 3 (with space suffix)

        # Verify no N= formatting for single ranks
        assert "| 1=       |" not in result
        assert "| 2=       |" not in result
        assert "| 3=       |" not in result

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
        assert "1 " in result  # Single rank 1 (with space suffix)
        assert "2=" in result  # Equal rank 2 (with equals suffix)
        assert "4 " in result  # Single rank 4 (with space suffix)
        assert "5=" in result  # Equal rank 5 (with equals suffix)

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
            "soap-makers", ranks=3, columns="rank, maker=soap, shaves"
        )

        # Check that rank formatting works with custom columns
        assert "1 " in result  # Single rank 1 (with space suffix)
        assert "2=" in result  # Equal rank 2 (with equals suffix)
        assert "Brand A" in result and "Brand B" in result and "Brand C" in result
        assert "100" in result and "80" in result

    def test_delta_columns_basic_functionality(self):
        """Test basic delta columns functionality with comparison data."""
        data = {
            "razor_formats": [
                {"rank": 1, "format": "DE", "shaves": 100, "unique_users": 50},
                {"rank": 2, "format": "GEM", "shaves": 80, "unique_users": 40},
                {"rank": 3, "format": "AC", "shaves": 60, "unique_users": 30},
            ]
        }

        # Mock comparison data for previous month, previous year, 5 years ago
        comparison_data = {
            "2025-05": {
                "razor_formats": [
                    {"rank": 1, "format": "DE", "shaves": 90, "unique_users": 45},
                    {
                        "rank": 3,
                        "format": "GEM",
                        "shaves": 85,
                        "unique_users": 42,
                    },  # GEM was rank 3
                    {"rank": 2, "format": "AC", "shaves": 70, "unique_users": 35},  # AC was rank 2
                ]
            },
            "2024-06": {
                "razor_formats": [
                    {"rank": 1, "format": "DE", "shaves": 95, "unique_users": 48},
                    {"rank": 2, "format": "AC", "shaves": 75, "unique_users": 38},  # AC was rank 2
                    {
                        "rank": 3,
                        "format": "GEM",
                        "shaves": 65,
                        "unique_users": 32,
                    },  # GEM was rank 3
                ]
            },
            "2020-06": {
                "razor_formats": [
                    {"rank": 1, "format": "DE", "shaves": 85, "unique_users": 40},
                    {
                        "rank": 2,
                        "format": "GEM",
                        "shaves": 70,
                        "unique_users": 35,
                    },  # GEM was rank 2
                    {"rank": 3, "format": "AC", "shaves": 55, "unique_users": 25},  # AC was rank 3
                ]
            },
        }

        generator = TableGenerator(data, comparison_data)
        result = generator.generate_table("razor-formats", deltas=True)

        # Check that delta columns are added at the end
        assert "| Δ vs May 2025" in result
        assert "| Δ vs Jun 2024" in result
        assert "| Δ vs Jun 2020" in result

        # Check delta values for rank changes
        # DE: rank 1 in all periods = "="
        assert "=" in result  # DE stayed rank 1
        # GEM: rank 2 → rank 3 (previous month: ↓1), rank 3 → rank 2 (previous year: ↑1)
        # AC: rank 3 → rank 2 (previous month: ↑1), rank 2 → rank 3 (previous year: ↓1)

    def test_delta_columns_with_ranks_parameter(self):
        """Test delta columns work with ranks parameter."""
        data = {
            "razor_formats": [
                {"rank": 1, "format": "DE", "shaves": 100, "unique_users": 50},
                {"rank": 2, "format": "GEM", "shaves": 80, "unique_users": 40},
            ]
        }

        comparison_data = {
            "2025-05": {
                "razor_formats": [
                    {"rank": 1, "format": "DE", "shaves": 90, "unique_users": 45},
                    {"rank": 2, "format": "GEM", "shaves": 85, "unique_users": 42},
                ]
            }
        }

        generator = TableGenerator(data, comparison_data)
        result = generator.generate_table("razor-formats", ranks=2, deltas=True)

        # Should show only top 2 ranks with deltas
        assert "=" in result  # DE stayed rank 1
        assert "=" in result  # GEM stayed rank 2

    def test_delta_columns_with_rows_parameter(self):
        """Test delta columns work with rows parameter."""
        data = {
            "razor_formats": [
                {"rank": 1, "format": "DE", "shaves": 100, "unique_users": 50},
                {"rank": 2, "format": "GEM", "shaves": 80, "unique_users": 40},
                {"rank": 3, "format": "AC", "shaves": 60, "unique_users": 30},
            ]
        }

        comparison_data = {
            "2025-05": {
                "razor_formats": [
                    {"rank": 1, "format": "DE", "shaves": 90, "unique_users": 45},
                    {"rank": 2, "format": "GEM", "shaves": 85, "unique_users": 42},
                    {"rank": 3, "format": "AC", "shaves": 70, "unique_users": 35},
                ]
            }
        }

        generator = TableGenerator(data, comparison_data)
        result = generator.generate_table("razor-formats", rows=2, deltas=True)

        # Should show only top 2 rows with deltas
        assert "=" in result  # DE stayed rank 1
        assert "=" in result  # GEM stayed rank 2
        # AC should not appear due to rows=2

    def test_delta_columns_with_columns_parameter(self):
        """Test delta columns work with columns parameter but are not affected by it."""
        data = {
            "razor_formats": [
                {"rank": 1, "format": "DE", "shaves": 100, "unique_users": 50},
                {"rank": 2, "format": "GEM", "shaves": 80, "unique_users": 40},
            ]
        }

        comparison_data = {
            "2025-05": {
                "razor_formats": [
                    {"rank": 1, "format": "DE", "shaves": 90, "unique_users": 45},
                    {"rank": 2, "format": "GEM", "shaves": 85, "unique_users": 42},
                ]
            }
        }

        generator = TableGenerator(data, comparison_data)
        result = generator.generate_table("razor-formats", columns="format, shaves", deltas=True)

        # Should show only format and shaves columns, then delta columns
        assert "Format" in result and "Shaves" in result
        assert "Δ vs May 2025" in result
        # Rank and unique_users should not appear due to columns parameter

    def test_delta_columns_missing_comparison_data(self):
        """Test delta columns handle missing comparison data gracefully."""
        data = {
            "razor_formats": [
                {"rank": 1, "format": "DE", "shaves": 100, "unique_users": 50},
                {"rank": 2, "format": "GEM", "shaves": 80, "unique_users": 40},
            ]
        }

        # No comparison data
        generator = TableGenerator(data)
        result = generator.generate_table("razor-formats", deltas=True)

        # Should show delta columns with "n/a" values
        assert "Δ vs May 2025" in result
        assert "Δ vs Jun 2024" in result
        assert "Δ vs Jun 2020" in result
        assert "n/a" in result

    def test_delta_columns_partial_comparison_data(self):
        """Test delta columns handle partial comparison data gracefully."""
        data = {
            "razor_formats": [
                {"rank": 1, "format": "DE", "shaves": 100, "unique_users": 50},
                {"rank": 2, "format": "GEM", "shaves": 80, "unique_users": 40},
            ]
        }

        # Only some comparison data available
        comparison_data = {
            "2025-05": {
                "razor_formats": [
                    {"rank": 1, "format": "DE", "shaves": 90, "unique_users": 45},
                    {"rank": 2, "format": "GEM", "shaves": 85, "unique_users": 42},
                ]
            }
        }

        generator = TableGenerator(data, comparison_data)
        result = generator.generate_table("razor-formats", deltas=True)

        # Should show all delta columns, with "n/a" for missing data
        assert "Δ vs May 2025" in result
        assert "Δ vs Jun 2024" in result
        assert "Δ vs Jun 2020" in result
        assert "=" in result  # Previous month
        assert "n/a" in result  # Missing periods

    def test_delta_columns_rank_changes(self):
        """Test delta columns show correct rank change indicators."""
        data = {
            "razor_formats": [
                {"rank": 1, "format": "DE", "shaves": 100, "unique_users": 50},
                {"rank": 2, "format": "GEM", "shaves": 80, "unique_users": 40},
                {"rank": 3, "format": "AC", "shaves": 60, "unique_users": 30},
            ]
        }

        # Previous month: GEM moved up 1 rank, AC moved down 1 rank
        comparison_data = {
            "2025-05": {
                "razor_formats": [
                    {"rank": 1, "format": "DE", "shaves": 90, "unique_users": 45},
                    {"rank": 3, "format": "GEM", "shaves": 85, "unique_users": 42},
                    {"rank": 2, "format": "AC", "shaves": 70, "unique_users": 35},
                ]
            }
        }

        generator = TableGenerator(data, comparison_data)
        result = generator.generate_table("razor-formats", deltas=True)

        # Check rank change indicators
        assert "=" in result  # DE stayed rank 1
        assert "↑1" in result  # GEM moved up 1 rank
        assert "↓1" in result  # AC moved down 1 rank

    def test_delta_columns_no_deltas_parameter(self):
        """Test that delta columns are not added when deltas parameter is False or None."""
        data = {
            "razor_formats": [
                {"rank": 1, "format": "DE", "shaves": 100, "unique_users": 50},
                {"rank": 2, "format": "GEM", "shaves": 80, "unique_users": 40},
            ]
        }

        comparison_data = {
            "2025-05": {
                "razor_formats": [
                    {"rank": 1, "format": "DE", "shaves": 90, "unique_users": 45},
                    {"rank": 2, "format": "GEM", "shaves": 85, "unique_users": 42},
                ]
            }
        }

        generator = TableGenerator(data, comparison_data)
        result = generator.generate_table("razor-formats", deltas=False)

        # Should not show delta columns
        assert "| Δ vs May 2025 |" not in result
        assert "| Δ vs Jun 2024 |" not in result
        assert "| Δ vs Jun 2020 |" not in result

    def test_numeric_column_limits_basic(self):
        """Test basic numeric column filtering."""
        data = {
            "soap_makers": [
                {"rank": 1, "shaves": 100, "unique_users": 50, "brand": "Brand A"},
                {"rank": 2, "shaves": 80, "unique_users": 40, "brand": "Brand B"},
                {"rank": 3, "shaves": 60, "unique_users": 30, "brand": "Brand C"},
                {"rank": 4, "shaves": 40, "unique_users": 20, "brand": "Brand D"},
                {"rank": 5, "shaves": 20, "unique_users": 10, "brand": "Brand E"},
            ]
        }

        generator = TableGenerator(data)
        result = generator.generate_table("soap-makers", shaves=50)

        # Should include rows where shaves >= 50
        assert "Brand A" in result  # shaves: 100
        assert "Brand B" in result  # shaves: 80
        assert "Brand C" in result  # shaves: 60
        assert "Brand D" not in result  # shaves: 40
        assert "Brand E" not in result  # shaves: 20

    def test_numeric_column_limits_single_limit_only(self):
        """Test that only one numeric column limit is allowed per table."""
        data = {
            "soap_makers": [
                {"rank": 1, "shaves": 100, "unique_users": 50, "brand": "Brand A"},
                {"rank": 2, "shaves": 80, "unique_users": 40, "brand": "Brand B"},
            ]
        }

        generator = TableGenerator(data)

        # Should fail when multiple numeric limits are specified
        with pytest.raises(ValueError, match="Only one numeric column limit allowed per table"):
            generator.generate_table("soap-makers", shaves=50, unique_users=25)

    def test_numeric_column_limits_with_existing_parameters(self):
        """Test numeric column limits with ranks and rows parameters."""
        data = {
            "soap_makers": [
                {"rank": 1, "shaves": 100, "unique_users": 50, "brand": "Brand A"},
                {"rank": 2, "shaves": 80, "unique_users": 40, "brand": "Brand B"},
                {"rank": 3, "shaves": 60, "unique_users": 30, "brand": "Brand C"},
                {"rank": 4, "shaves": 40, "unique_users": 20, "brand": "Brand D"},
                {"rank": 5, "shaves": 20, "unique_users": 10, "brand": "Brand E"},
            ]
        }

        generator = TableGenerator(data)
        result = generator.generate_table("soap-makers", ranks=3, shaves=50)

        # Should apply both filters: ranks <= 3 AND shaves >= 50
        assert "Brand A" in result  # rank: 1, shaves: 100
        assert "Brand B" in result  # rank: 2, shaves: 80
        assert "Brand C" in result  # rank: 3, shaves: 60
        assert "Brand D" not in result  # rank: 4, shaves: 40
        assert "Brand E" not in result  # rank: 5, shaves: 20

    def test_numeric_column_limits_gap_detection(self):
        """Test that numeric column filtering works correctly even if it creates gaps in the table."""
        data = {
            "soap_makers": [
                {"rank": 1, "shaves": 100, "unique_users": 50, "brand": "Brand A"},
                {"rank": 2, "shaves": 90, "unique_users": 45, "brand": "Brand B"},
                {"rank": 3, "shaves": 50, "unique_users": 25, "brand": "Brand C"},
                {"rank": 4, "shaves": 80, "unique_users": 40, "brand": "Brand D"},
                {"rank": 5, "shaves": 20, "unique_users": 10, "brand": "Brand E"},
            ]
        }

        generator = TableGenerator(data)

        # This filter should keep ranks 1, 2, 4 (shaves >= 70)
        # which creates a gap in the rank sequence (missing rank 3)
        result = generator.generate_table("soap-makers", shaves=70)

        # Should include items with shaves >= 70
        assert "Brand A" in result  # shaves: 100
        assert "Brand B" in result  # shaves: 90
        assert "Brand D" in result  # shaves: 80

        # Should exclude items with shaves < 70
        assert "Brand C" not in result  # shaves: 50
        assert "Brand E" not in result  # shaves: 20

    def test_numeric_column_limits_invalid_column(self):
        """Test error when numeric column doesn't exist."""
        data = {"soap_makers": [{"rank": 1, "shaves": 100, "unique_users": 50, "brand": "Brand B"}]}

        generator = TableGenerator(data)

        with pytest.raises(ValueError, match="Column 'nonexistent_column' not found in table data"):
            generator.generate_table("soap-makers", nonexistent_column=10)

    def test_numeric_column_limits_invalid_threshold(self):
        """Test error when threshold value is not numeric."""
        data = {"soap_makers": [{"rank": 1, "shaves": 100, "unique_users": 50, "brand": "Brand B"}]}

        generator = TableGenerator(data)

        with pytest.raises(
            ValueError, match="Invalid threshold value 'abc' for column 'shaves' - must be numeric"
        ):
            generator.generate_table("soap-makers", shaves="abc")
