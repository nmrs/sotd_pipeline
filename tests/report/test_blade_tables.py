#!/usr/bin/env python3
"""Tests for blade table generation using the universal TableGenerator."""

import pytest

from sotd.report.table_generators.table_generator import TableGenerator


class TestBladesTableGenerator:
    """Test cases for blade table generation using universal TableGenerator."""

    @pytest.fixture
    def generator(self):
        """Create a TableGenerator instance for testing blade tables."""
        data = {
            "blades": [
                {"rank": 1, "name": "Feather Hi-Stainless", "shaves": 10, "unique_users": 5},
                {"rank": 2, "name": "Astra SP", "shaves": 8, "unique_users": 4}]
        }
        return TableGenerator(data, debug=False)

    def test_empty_data(self, generator):
        """Test with empty data."""
        generator.data = {"blades": []}
        result = generator.generate_table("blades")
        assert result == ""

    def test_valid_data(self, generator):
        """Test with valid data."""
        result = generator.generate_table("blades")
        assert "Feather Hi-Stainless" in result
        assert "Astra SP" in result
        assert "Rank" in result
        assert "Name" in result

    def test_missing_required_fields(self, generator):
        """Test with missing required fields."""
        generator.data = {"blades": [{"name": "Invalid"}]}
        # Should fail because missing rank column
        with pytest.raises(ValueError, match="missing 'rank' column"):
            generator.generate_table("blades")

    def test_table_generation(self, generator):
        """Test table generation with the new universal system."""
        result = generator.generate_table("blades")
        assert "Rank" in result
        assert "Name" in result
        assert "Shaves" in result
        assert "Unique Users" in result
        assert "Feather Hi-Stainless" in result
        assert "Astra SP" in result


class TestBladeManufacturersTableGenerator:
    """Test cases for blade manufacturers table generation using universal TableGenerator."""

    @pytest.fixture
    def generator(self):
        """Create a TableGenerator instance for testing blade manufacturers tables."""
        data = {
            "blade_manufacturers": [
                {"rank": 1, "brand": "Feather", "shaves": 15, "unique_users": 8},
                {"rank": 2, "brand": "Astra", "shaves": 12, "unique_users": 6}]
        }
        return TableGenerator(data, debug=False)

    def test_empty_data(self, generator):
        """Test with empty data."""
        generator.data = {"blade_manufacturers": []}
        result = generator.generate_table("blade-manufacturers")
        assert result == ""

    def test_valid_data(self, generator):
        """Test with valid data."""
        result = generator.generate_table("blade-manufacturers")
        assert "Feather" in result
        assert "Astra" in result
        assert "Rank" in result
        assert "Brand" in result

    def test_missing_required_fields(self, generator):
        """Test with missing required fields."""
        generator.data = {"blade_manufacturers": [{"brand": "Invalid"}]}
        # Should fail because missing rank column
        with pytest.raises(ValueError, match="missing 'rank' column"):
            generator.generate_table("blade-manufacturers")

    def test_table_generation(self, generator):
        """Test table generation with the new universal system."""
        result = generator.generate_table("blade-manufacturers")
        assert "Rank" in result
        assert "Brand" in result
        assert "Shaves" in result
        assert "Unique Users" in result
        assert "Feather" in result
        assert "Astra" in result


class TestBladeUsageDistributionTableGenerator:
    """Test cases for blade usage distribution table generation using universal TableGenerator."""

    @pytest.fixture
    def generator(self):
        """Create a TableGenerator instance for testing blade usage distribution tables."""
        data = {
            "blade_usage_distribution": [
                {"rank": 1, "use_count": 1, "shaves": 20, "unique_users": 15},
                {"rank": 2, "use_count": 2, "shaves": 15, "unique_users": 10},
                {"rank": 3, "use_count": 3, "shaves": 10, "unique_users": 5}]
        }
        return TableGenerator(data, debug=False)

    def test_empty_data(self, generator):
        """Test with empty data."""
        generator.data = {"blade_usage_distribution": []}
        result = generator.generate_table("blade-usage-distribution")
        assert result == ""

    def test_valid_data(self, generator):
        """Test with valid data."""
        result = generator.generate_table("blade-usage-distribution")
        assert "1" in result
        assert "2" in result
        assert "3" in result
        assert "Rank" in result
        assert "Use Count" in result

    def test_missing_required_fields(self, generator):
        """Test with missing required fields."""
        generator.data = {"blade_usage_distribution": [{"use_count": 1}]}
        # Should fail because missing rank column
        with pytest.raises(ValueError, match="missing 'rank' column"):
            generator.generate_table("blade-usage-distribution")

    def test_table_generation(self, generator):
        """Test table generation with the new universal system."""
        result = generator.generate_table("blade-usage-distribution")
        assert "Rank" in result
        assert "Use Count" in result
        assert "Shaves" in result
        assert "Unique Users" in result
        assert "1" in result
        assert "2" in result
        assert "3" in result
