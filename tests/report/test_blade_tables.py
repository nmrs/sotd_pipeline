"""Tests for blade table generators."""

from sotd.report.table_generators.blade_tables import (
    BladesTableGenerator,
    BladeManufacturersTableGenerator,
)


class TestBladesTableGenerator:
    """Test the BladesTableGenerator."""

    def test_empty_data(self):
        """Test with empty data."""
        generator = BladesTableGenerator({}, debug=False)
        data = generator.get_table_data()
        assert data == []

    def test_valid_data(self):
        """Test with valid data."""
        sample_data = {
            "blades": [
                {
                    "name": "Gillette Nacet",
                    "shaves": 50,
                    "unique_users": 25,
                },
                {
                    "name": "Personna Lab Blue",
                    "shaves": 30,
                    "unique_users": 15,
                },
            ]
        }
        generator = BladesTableGenerator(sample_data, debug=False)
        data = generator.get_table_data()
        assert len(data) == 2
        assert data[0]["name"] == "Gillette Nacet"
        assert data[0]["shaves"] == 50

    def test_missing_required_fields(self):
        """Test with missing required fields."""
        sample_data = {
            "blades": [
                {"name": "Gillette Nacet"},  # Missing shaves
                {
                    "name": "Personna Lab Blue",
                    "shaves": 30,
                    "unique_users": 15,
                },  # Valid
            ]
        }
        generator = BladesTableGenerator(sample_data, debug=False)
        data = generator.get_table_data()
        assert len(data) == 1  # Only the valid record should be included

    def test_table_title(self):
        """Test table title."""
        generator = BladesTableGenerator({}, debug=False)
        assert generator.get_table_title() == "Blades"

    def test_column_config(self):
        """Test column configuration."""
        generator = BladesTableGenerator({}, debug=False)
        config = generator.get_column_config()
        assert "name" in config
        assert "shaves" in config
        assert "unique_users" in config


class TestBladeManufacturersTableGenerator:
    """Test the BladeManufacturersTableGenerator."""

    def test_empty_data(self):
        """Test with empty data."""
        generator = BladeManufacturersTableGenerator({}, debug=False)
        data = generator.get_table_data()
        assert data == []

    def test_valid_data(self):
        """Test with valid data."""
        sample_data = {
            "blade_manufacturers": [
                {"brand": "Gillette", "shaves": 100, "unique_users": 50},
                {"brand": "Personna", "shaves": 75, "unique_users": 30},
            ]
        }
        generator = BladeManufacturersTableGenerator(sample_data, debug=False)
        data = generator.get_table_data()
        assert len(data) == 2
        assert data[0]["brand"] == "Gillette"
        assert data[0]["shaves"] == 100

    def test_missing_required_fields(self):
        """Test with missing required fields."""
        sample_data = {
            "blade_manufacturers": [
                {"brand": "Gillette"},  # Missing shaves
                {"brand": "Personna", "shaves": 75, "unique_users": 30},  # Valid
            ]
        }
        generator = BladeManufacturersTableGenerator(sample_data, debug=False)
        data = generator.get_table_data()
        assert len(data) == 1  # Only the valid record should be included

    def test_table_title(self):
        """Test table title."""
        generator = BladeManufacturersTableGenerator({}, debug=False)
        assert generator.get_table_title() == "Blade Manufacturers"

    def test_column_config(self):
        """Test column configuration."""
        generator = BladeManufacturersTableGenerator({}, debug=False)
        config = generator.get_column_config()
        assert "brand" in config
        assert "shaves" in config
        assert "unique_users" in config
