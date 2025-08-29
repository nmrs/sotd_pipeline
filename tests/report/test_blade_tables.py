#!/usr/bin/env python3
"""Tests for blade table generators."""

from sotd.report.table_generators.table_generator import TableGenerator


class TestBladesTableGenerator:
    """Test the BladesTableGenerator using the universal TableGenerator."""

    def test_empty_data(self):
        """Test with empty data."""
        # Provide sample data structure with empty lists for the tables
        sample_data = {"blades": [], "blade_manufacturers": [], "blade_usage_distribution": []}
        generator = TableGenerator(sample_data)
        data = generator.generate_table("blades")
        assert data == ""

    def test_valid_data(self):
        """Test with valid data."""
        sample_data = {
            "blades": [
                {"rank": 1, "name": "Feather Hi-Stainless", "shaves": 50, "unique_users": 25},
                {"rank": 2, "name": "Astra Superior Platinum", "shaves": 30, "unique_users": 15},
            ]
        }
        generator = TableGenerator(sample_data)
        data = generator.generate_table("blades")
        assert "Feather Hi-Stainless" in data
        assert "Astra Superior Platinum" in data

    def test_missing_required_fields(self):
        """Test with missing required fields."""
        sample_data = {
            "blades": [
                {"name": "Feather Hi-Stainless", "shaves": 50},  # Missing rank
                {"rank": 2, "shaves": 30},  # Missing name
            ]
        }
        generator = TableGenerator(sample_data)
        data = generator.generate_table("blades")
        assert data != ""

    def test_table_name_mapping(self):
        """Test that table names are correctly mapped."""
        sample_data = {"blades": [], "blade_manufacturers": [], "blade_usage_distribution": []}
        generator = TableGenerator(sample_data)
        # Test that kebab-case names are converted to snake_case
        assert "blades" in generator.get_available_table_names()
        assert "blade_manufacturers" in generator.get_available_table_names()
        assert "blade_usage_distribution" in generator.get_available_table_names()


class TestBladeManufacturersTableGenerator:
    """Test the BladeManufacturersTableGenerator using the universal TableGenerator."""

    def test_empty_data(self):
        """Test with empty data."""
        # Provide sample data structure with empty lists for the tables
        sample_data = {"blades": [], "blade_manufacturers": [], "blade_usage_distribution": []}
        generator = TableGenerator(sample_data)
        data = generator.generate_table("blade-manufacturers")
        assert data == ""

    def test_valid_data(self):
        """Test with valid data."""
        sample_data = {
            "blade_manufacturers": [
                {"rank": 1, "name": "Feather", "shaves": 50, "unique_users": 25},
                {"rank": 2, "name": "Gillette", "shaves": 30, "unique_users": 15},
            ]
        }
        generator = TableGenerator(sample_data)
        data = generator.generate_table("blade-manufacturers")
        assert "Feather" in data
        assert "Gillette" in data

    def test_missing_required_fields(self):
        """Test with missing required fields."""
        sample_data = {
            "blade_manufacturers": [
                {"name": "Feather", "shaves": 50},  # Missing rank
                {"rank": 2, "shaves": 30},  # Missing name
            ]
        }
        generator = TableGenerator(sample_data)
        data = generator.generate_table("blade-manufacturers")
        assert data != ""

    def test_table_name_mapping(self):
        """Test that table names are correctly mapped."""
        sample_data = {"blades": [], "blade_manufacturers": [], "blade_usage_distribution": []}
        generator = TableGenerator(sample_data)
        # Test that kebab-case names are converted to snake_case
        assert "blades" in generator.get_available_table_names()
        assert "blade_manufacturers" in generator.get_available_table_names()
        assert "blade_usage_distribution" in generator.get_available_table_names()


class TestBladeUsageDistributionTableGenerator:
    """Test the BladeUsageDistributionTableGenerator using the universal TableGenerator."""

    def test_empty_data(self):
        """Test with empty data."""
        # Provide sample data structure with empty lists for the tables
        sample_data = {"blades": [], "blade_manufacturers": [], "blade_usage_distribution": []}
        generator = TableGenerator(sample_data)
        data = generator.generate_table("blade-usage-distribution")
        assert data == ""

    def test_valid_data(self):
        """Test with valid data."""
        sample_data = {
            "blade_usage_distribution": [
                {"rank": 1, "name": "1-5 shaves", "shaves": 50, "unique_users": 25},
                {"rank": 2, "name": "6-10 shaves", "shaves": 30, "unique_users": 15},
            ]
        }
        generator = TableGenerator(sample_data)
        data = generator.generate_table("blade-usage-distribution")
        assert "1-5 shaves" in data
        assert "6-10 shaves" in data

    def test_missing_required_fields(self):
        """Test with missing required fields."""
        sample_data = {
            "blade_usage_distribution": [
                {"name": "1-5 shaves", "shaves": 50},  # Missing rank
                {"rank": 2, "shaves": 30},  # Missing name
            ]
        }
        generator = TableGenerator(sample_data)
        data = generator.generate_table("blade-usage-distribution")
        assert data != ""

    def test_table_name_mapping(self):
        """Test that table names are correctly mapped."""
        sample_data = {"blades": [], "blade_manufacturers": [], "blade_usage_distribution": []}
        generator = TableGenerator(sample_data)
        # Test that kebab-case names are converted to snake_case
        assert "blades" in generator.get_available_table_names()
        assert "blade_manufacturers" in generator.get_available_table_names()
        assert "blade_usage_distribution" in generator.get_available_table_names()
