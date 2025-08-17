"""Tests for razor table generators."""

from sotd.report.table_generators.razor_tables import (
    RazorFormatsTableGenerator,
    RazorsTableGenerator,
    RazorManufacturersTableGenerator,
)


class TestRazorFormatsTableGenerator:
    """Test the RazorFormatsTableGenerator."""

    def test_empty_data(self):
        """Test with empty data."""
        generator = RazorFormatsTableGenerator({}, debug=False)
        data = generator.get_table_data()
        assert data == []

    def test_invalid_data_type(self):
        """Test with invalid data type."""
        generator = RazorFormatsTableGenerator({"razor_formats": "not a list"}, debug=False)
        data = generator.get_table_data()
        assert data == []

    def test_valid_data(self):
        """Test with valid data."""
        sample_data = {
            "razor_formats": [
                {"format": "DE", "shaves": 100, "unique_users": 50},
                {"format": "Straight", "shaves": 50, "unique_users": 25},
            ]
        }
        generator = RazorFormatsTableGenerator(sample_data, debug=False)
        data = generator.get_table_data()
        assert len(data) == 2
        assert data[0]["format"] == "DE"
        assert data[0]["shaves"] == 100
        assert data[1]["format"] == "Straight"
        assert data[1]["shaves"] == 50

    def test_missing_required_fields(self):
        """Test with missing required fields."""
        sample_data = {
            "razor_formats": [
                {"format": "DE"},  # Missing shaves
                {"shaves": 100},  # Missing format
                {"format": "Straight", "shaves": 50, "unique_users": 25},  # Valid
            ]
        }
        generator = RazorFormatsTableGenerator(sample_data, debug=False)
        data = generator.get_table_data()
        assert len(data) == 1  # Only the valid record should be included
        assert data[0]["format"] == "Straight"
        assert data[0]["shaves"] == 50

    def test_table_title(self):
        """Test table title."""
        generator = RazorFormatsTableGenerator({}, debug=False)
        assert generator.get_table_title() == "Razor Formats"

    def test_column_config(self):
        """Test column configuration."""
        generator = RazorFormatsTableGenerator({}, debug=False)
        config = generator.get_column_config()
        assert "format" in config  # Actual data field
        assert "shaves" in config
        assert "unique_users" in config
        assert "avg_shaves_per_user" in config
        # Check that format maps to "Format" display name
        assert config["format"]["display_name"] == "Format"


class TestRazorsTableGenerator:
    """Test the RazorsTableGenerator."""

    def test_empty_data(self):
        """Test with empty data."""
        generator = RazorsTableGenerator({}, debug=False)
        data = generator.get_table_data()
        assert data == []

    def test_valid_data(self):
        """Test with valid data."""
        sample_data = {
            "razors": [
                {
                    "name": "Gillette Super Speed DE",
                    "shaves": 25,
                    "unique_users": 10,
                },
                {
                    "name": "Blackland Blackbird DE",
                    "shaves": 15,
                    "unique_users": 8,
                },
            ]
        }
        generator = RazorsTableGenerator(sample_data, debug=False)
        data = generator.get_table_data()
        assert len(data) == 2
        assert data[0]["name"] == "Gillette Super Speed DE"
        assert data[0]["shaves"] == 25

    def test_missing_required_fields(self):
        """Test with missing required fields."""
        sample_data = {
            "razors": [
                {"name": "Gillette Super Speed"},  # Missing shaves
                {
                    "name": "Blackland Blackbird DE",
                    "shaves": 15,
                    "unique_users": 8,
                },  # Valid
            ]
        }
        generator = RazorsTableGenerator(sample_data, debug=False)
        data = generator.get_table_data()
        assert len(data) == 1  # Only the valid record should be included

    def test_table_title(self):
        """Test table title."""
        generator = RazorsTableGenerator({}, debug=False)
        assert generator.get_table_title() == "Razors"

    def test_column_config(self):
        """Test column configuration."""
        generator = RazorsTableGenerator({}, debug=False)
        config = generator.get_column_config()
        assert "name" in config
        assert "shaves" in config
        assert "unique_users" in config


class TestRazorManufacturersTableGenerator:
    """Test the RazorManufacturersTableGenerator."""

    def test_empty_data(self):
        """Test with empty data."""
        generator = RazorManufacturersTableGenerator({}, debug=False)
        data = generator.get_table_data()
        assert data == []

    def test_valid_data(self):
        """Test with valid data."""
        sample_data = {
            "razor_manufacturers": [
                {"brand": "Gillette", "shaves": 100, "unique_users": 50},
                {"brand": "Blackland", "shaves": 75, "unique_users": 30},
            ]
        }
        generator = RazorManufacturersTableGenerator(sample_data, debug=False)
        data = generator.get_table_data()
        assert len(data) == 2
        assert data[0]["brand"] == "Gillette"
        assert data[0]["shaves"] == 100

    def test_missing_required_fields(self):
        """Test with missing required fields."""
        sample_data = {
            "razor_manufacturers": [
                {"brand": "Gillette"},  # Missing shaves
                {"brand": "Blackland", "shaves": 75, "unique_users": 30},  # Valid
            ]
        }
        generator = RazorManufacturersTableGenerator(sample_data, debug=False)
        data = generator.get_table_data()
        assert len(data) == 1  # Only the valid record should be included

    def test_table_title(self):
        """Test table title."""
        generator = RazorManufacturersTableGenerator({}, debug=False)
        assert generator.get_table_title() == "Razor Manufacturers"

    def test_column_config(self):
        """Test column configuration."""
        generator = RazorManufacturersTableGenerator({}, debug=False)
        config = generator.get_column_config()
        assert "brand" in config  # Actual data field
        assert "shaves" in config
        assert "unique_users" in config
        assert "avg_shaves_per_user" in config
        # Check that brand maps to "Manufacturer" display name
        assert config["brand"]["display_name"] == "Manufacturer"
