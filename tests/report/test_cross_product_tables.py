"""Tests for cross-product table generators."""

from sotd.report.table_generators.table_generator import TableGenerator


class TestRazorBladeCombinationsTableGenerator:
    """Test the RazorBladeCombinationsTableGenerator using the universal TableGenerator."""

    def test_empty_data(self):
        """Test with empty data."""
        # Provide sample data structure with empty lists for the tables
        sample_data = {"razor_blade_combinations": [], "highest_use_count_per_blade": []}
        generator = TableGenerator(sample_data)
        data = generator.generate_table("razor-blade-combinations")
        assert data == ""

    def test_valid_data(self):
        """Test with valid data."""
        sample_data = {
            "razor_blade_combinations": [
                {
                    "rank": 1,
                    "name": "Gillette Super Speed + Gillette Nacet",
                    "shaves": 50,
                    "unique_users": 25,
                },
                {
                    "rank": 2,
                    "name": "Merkur 34C + Feather Hi-Stainless",
                    "shaves": 30,
                    "unique_users": 15,
                },
            ]
        }
        generator = TableGenerator(sample_data)
        data = generator.generate_table("razor-blade-combinations")
        assert "Gillette Super Speed + Gillette Nacet" in data
        assert "Merkur 34C + Feather Hi-Stainless" in data

    def test_missing_required_fields(self):
        """Test with missing required fields."""
        sample_data = {
            "razor_blade_combinations": [
                {"name": "Gillette Super Speed + Gillette Nacet", "shaves": 50},  # Missing rank
                {"rank": 2, "shaves": 30},  # Missing name
            ]
        }
        generator = TableGenerator(sample_data)
        data = generator.generate_table("razor-blade-combinations")
        assert data != ""

    def test_table_name_mapping(self):
        """Test that table names are correctly mapped."""
        sample_data = {"razor_blade_combinations": [], "highest_use_count_per_blade": []}
        generator = TableGenerator(sample_data)
        # Test that kebab-case names are converted to snake_case
        assert "razor_blade_combinations" in generator.get_available_table_names()
        assert "highest_use_count_per_blade" in generator.get_available_table_names()


class TestHighestUseCountPerBladeTableGenerator:
    """Test the HighestUseCountPerBladeTableGenerator using the universal TableGenerator."""

    def test_empty_data(self):
        """Test with empty data."""
        # Provide sample data structure with empty lists for the tables
        sample_data = {"razor_blade_combinations": [], "highest_use_count_per_blade": []}
        generator = TableGenerator(sample_data)
        data = generator.generate_table("highest-use-count-per-blade")
        assert data == ""

    def test_valid_data(self):
        """Test with valid data."""
        sample_data = {
            "highest_use_count_per_blade": [
                {"rank": 1, "name": "Feather Hi-Stainless", "max_uses": 15, "shaves": 50},
                {"rank": 2, "name": "Astra Superior Platinum", "max_uses": 10, "shaves": 30},
            ]
        }
        generator = TableGenerator(sample_data)
        data = generator.generate_table("highest-use-count-per-blade")
        assert "Feather Hi-Stainless" in data
        assert "Astra Superior Platinum" in data

    def test_missing_required_fields(self):
        """Test with missing required fields."""
        sample_data = {
            "highest_use_count_per_blade": [
                {"name": "Feather Hi-Stainless", "max_uses": 15},  # Missing rank
                {"rank": 2, "max_uses": 10},  # Missing name
            ]
        }
        generator = TableGenerator(sample_data)
        data = generator.generate_table("highest-use-count-per-blade")
        assert data != ""

    def test_table_name_mapping(self):
        """Test that table names are correctly mapped."""
        sample_data = {"razor_blade_combinations": [], "highest_use_count_per_blade": []}
        generator = TableGenerator(sample_data)
        # Test that kebab-case names are converted to snake_case
        assert "razor_blade_combinations" in generator.get_available_table_names()
        assert "highest_use_count_per_blade" in generator.get_available_table_names()
