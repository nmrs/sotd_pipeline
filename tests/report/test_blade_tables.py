#!/usr/bin/env python3
"""Tests for blade table generators."""

import pytest

from sotd.report.table_generators.blade_tables import (
    BladeManufacturersTableGenerator,
    BladeUsageDistributionTableGenerator,
    BladesTableGenerator,
)


class TestBladesTableGenerator:
    """Test cases for BladesTableGenerator."""

    @pytest.fixture
    def generator(self):
        """Create a BladesTableGenerator instance for testing."""
        data = {
            "blades": [
                {"name": "Feather Hi-Stainless", "shaves": 10, "unique_users": 5},
                {"name": "Astra SP", "shaves": 8, "unique_users": 4},
            ]
        }
        return BladesTableGenerator(data, debug=False)

    def test_empty_data(self, generator):
        """Test with empty data."""
        generator.data = {"blades": []}
        result = generator.get_table_data()
        assert result == []

    def test_valid_data(self, generator):
        """Test with valid data."""
        result = generator.get_table_data()
        assert len(result) == 2
        assert result[0]["name"] == "Feather Hi-Stainless"
        assert result[1]["name"] == "Astra SP"

    def test_missing_required_fields(self, generator):
        """Test with missing required fields."""
        generator.data = {"blades": [{"name": "Invalid"}]}
        result = generator.get_table_data()
        assert result == []

    def test_table_title(self, generator):
        """Test table title."""
        assert generator.get_table_title() == "Blades"

    def test_column_config(self, generator):
        """Test column configuration."""
        config = generator.get_column_config()
        assert "name" in config
        assert config["name"]["display_name"] == "Blade"


class TestBladeManufacturersTableGenerator:
    """Test cases for BladeManufacturersTableGenerator."""

    @pytest.fixture
    def generator(self):
        """Create a BladeManufacturersTableGenerator instance for testing."""
        data = {
            "blade_manufacturers": [
                {"brand": "Feather", "shaves": 15, "unique_users": 8},
                {"brand": "Astra", "shaves": 12, "unique_users": 6},
            ]
        }
        return BladeManufacturersTableGenerator(data, debug=False)

    def test_empty_data(self, generator):
        """Test with empty data."""
        generator.data = {"blade_manufacturers": []}
        result = generator.get_table_data()
        assert result == []

    def test_valid_data(self, generator):
        """Test with valid data."""
        result = generator.get_table_data()
        assert len(result) == 2
        assert result[0]["brand"] == "Feather"
        assert result[1]["brand"] == "Astra"

    def test_missing_required_fields(self, generator):
        """Test with missing required fields."""
        generator.data = {"blade_manufacturers": [{"brand": "Invalid"}]}
        result = generator.get_table_data()
        assert result == []

    def test_table_title(self, generator):
        """Test table title."""
        assert generator.get_table_title() == "Blade Manufacturers"

    def test_column_config(self, generator):
        """Test column configuration."""
        config = generator.get_column_config()
        assert "brand" in config
        assert config["brand"]["display_name"] == "Manufacturer"


class TestBladeUsageDistributionTableGenerator:
    """Test cases for BladeUsageDistributionTableGenerator."""

    @pytest.fixture
    def generator(self):
        """Create a BladeUsageDistributionTableGenerator instance for testing."""
        data = {
            "blade_usage_distribution": [
                {"use_count": 1, "shaves": 20, "unique_users": 15},
                {"use_count": 2, "shaves": 15, "unique_users": 10},
                {"use_count": 3, "shaves": 10, "unique_users": 5},
            ]
        }
        return BladeUsageDistributionTableGenerator(data, debug=False)

    def test_empty_data(self, generator):
        """Test with empty data."""
        generator.data = {"blade_usage_distribution": []}
        result = generator.get_table_data()
        assert result == []

    def test_valid_data(self, generator):
        """Test with valid data."""
        result = generator.get_table_data()
        assert len(result) == 3
        assert result[0]["use_count"] == 1
        assert result[1]["use_count"] == 2
        assert result[2]["use_count"] == 3

    def test_missing_required_fields(self, generator):
        """Test with missing required fields."""
        generator.data = {"blade_usage_distribution": [{"use_count": 1}]}
        result = generator.get_table_data()
        assert result == []

    def test_table_title(self, generator):
        """Test table title."""
        assert generator.get_table_title() == "Blade Usage Distribution"

    def test_column_config(self, generator):
        """Test column configuration."""
        config = generator.get_column_config()
        assert "use_count" in config
        assert "shaves" in config
        assert "unique_users" in config
        assert config["use_count"]["display_name"] == "Uses per Blade"
        assert config["shaves"]["display_name"] == "Total Shaves"
        assert config["unique_users"]["display_name"] == "Unique Users"

    def test_should_limit_rows(self, generator):
        """Test that row limiting is disabled."""
        assert generator.should_limit_rows() is False
