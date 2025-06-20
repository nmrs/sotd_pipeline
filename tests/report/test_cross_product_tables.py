"""Tests for cross-product table generators."""

from sotd.report.table_generators.cross_product_tables import (
    RazorBladeCombinationsTableGenerator,
    HighestUseCountPerBladeTableGenerator,
)


class TestRazorBladeCombinationsTableGenerator:
    """Test the RazorBladeCombinationsTableGenerator."""

    def test_empty_data(self):
        """Test with empty data."""
        generator = RazorBladeCombinationsTableGenerator({}, debug=False)
        data = generator.get_table_data()
        assert data == []

    def test_valid_data(self):
        """Test with valid data."""
        sample_data = {
            "razor_blade_combinations": [
                {
                    "name": "Gillette Super Speed + Gillette Nacet",
                    "shaves": 25,
                    "unique_users": 12,
                },
                {
                    "name": "Karve CB + Personna Lab Blue",
                    "shaves": 18,
                    "unique_users": 8,
                },
            ]
        }
        generator = RazorBladeCombinationsTableGenerator(sample_data, debug=False)
        data = generator.get_table_data()
        assert len(data) == 2
        assert data[0]["name"] == "Gillette Super Speed + Gillette Nacet"
        assert data[0]["shaves"] == 25

    def test_missing_required_fields(self):
        """Test with missing required fields."""
        sample_data = {
            "razor_blade_combinations": [
                {"name": "Gillette Super Speed + Gillette Nacet"},  # Missing shaves
                {
                    "name": "Karve CB + Personna Lab Blue",
                    "shaves": 18,
                    "unique_users": 8,
                },  # Valid
            ]
        }
        generator = RazorBladeCombinationsTableGenerator(sample_data, debug=False)
        data = generator.get_table_data()
        assert len(data) == 1  # Only the valid record should be included

    def test_table_title(self):
        """Test table title."""
        generator = RazorBladeCombinationsTableGenerator({}, debug=False)
        assert generator.get_table_title() == "Most Used Blades in Most Used Razors"

    def test_column_config(self):
        """Test column configuration."""
        generator = RazorBladeCombinationsTableGenerator({}, debug=False)
        config = generator.get_column_config()
        assert "name" in config
        assert "shaves" in config
        assert "unique_users" in config


class TestHighestUseCountPerBladeTableGenerator:
    """Test the HighestUseCountPerBladeTableGenerator."""

    def test_empty_data(self):
        """Test with empty data."""
        generator = HighestUseCountPerBladeTableGenerator({}, debug=False)
        data = generator.get_table_data()
        assert data == []

    def test_valid_data(self):
        """Test with valid data."""
        sample_data = {
            "highest_use_count_per_blade": [
                {
                    "user": "user1",
                    "blade": "Gillette Nacet",
                    "format": "DE",
                    "uses": 15,
                },
                {
                    "user": "user2",
                    "blade": "Personna Lab Blue",
                    "format": "DE",
                    "uses": 12,
                },
            ]
        }
        generator = HighestUseCountPerBladeTableGenerator(sample_data, debug=False)
        data = generator.get_table_data()
        assert len(data) == 2
        assert data[0]["user"] == "user1"
        assert data[0]["blade"] == "Gillette Nacet"
        assert data[0]["uses"] == 15

    def test_missing_required_fields(self):
        """Test with missing required fields."""
        sample_data = {
            "highest_use_count_per_blade": [
                {"user": "user1"},  # Missing blade and uses
                {
                    "user": "user2",
                    "blade": "Personna Lab Blue",
                    "format": "DE",
                    "uses": 12,
                },  # Valid
            ]
        }
        generator = HighestUseCountPerBladeTableGenerator(sample_data, debug=False)
        data = generator.get_table_data()
        assert len(data) == 1  # Only the valid record should be included

    def test_table_title(self):
        """Test table title."""
        generator = HighestUseCountPerBladeTableGenerator({}, debug=False)
        assert generator.get_table_title() == "Highest Use Count per Blade"

    def test_column_config(self):
        """Test column configuration."""
        generator = HighestUseCountPerBladeTableGenerator({}, debug=False)
        config = generator.get_column_config()
        assert "user" in config
        assert "blade" in config
        assert "format" in config
        assert "uses" in config
