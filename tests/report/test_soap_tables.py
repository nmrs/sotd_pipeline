"""Tests for soap table generators."""

from sotd.report.table_generators.soap_tables import (
    SoapsTableGenerator,
    SoapMakersTableGenerator,
    BrandDiversityTableGenerator,
)


class TestSoapsTableGenerator:
    """Test the SoapsTableGenerator."""

    def test_empty_data(self):
        """Test with empty data."""
        generator = SoapsTableGenerator({}, debug=False)
        data = generator.get_table_data()
        assert data == []

    def test_valid_data(self):
        """Test with valid data."""
        sample_data = {
            "soaps": [
                {
                    "name": "Declaration Grooming Sellout",
                    "shaves": 35,
                    "unique_users": 18,
                },
                {
                    "name": "Stirling Executive Man",
                    "shaves": 25,
                    "unique_users": 12,
                },
            ]
        }
        generator = SoapsTableGenerator(sample_data, debug=False)
        data = generator.get_table_data()
        assert len(data) == 2
        assert data[0]["name"] == "Declaration Grooming Sellout"
        assert data[0]["shaves"] == 35

    def test_missing_required_fields(self):
        """Test with missing required fields."""
        sample_data = {
            "soaps": [
                {"name": "Declaration Grooming Sellout"},  # Missing shaves
                {
                    "name": "Stirling Executive Man",
                    "shaves": 25,
                    "unique_users": 12,
                },  # Valid
            ]
        }
        generator = SoapsTableGenerator(sample_data, debug=False)
        data = generator.get_table_data()
        # SoapsTableGenerator now filters missing fields, so only valid record should be included
        assert len(data) == 1
        assert data[0]["name"] == "Stirling Executive Man"

    def test_table_title(self):
        """Test table title."""
        generator = SoapsTableGenerator({}, debug=False)
        assert generator.get_table_title() == "Soaps"

    def test_column_config(self):
        """Test column configuration."""
        generator = SoapsTableGenerator({}, debug=False)
        config = generator.get_column_config()
        assert "name" in config
        assert "shaves" in config
        assert "unique_users" in config


class TestSoapMakersTableGenerator:
    """Test the SoapMakersTableGenerator."""

    def test_empty_data(self):
        """Test with empty data."""
        generator = SoapMakersTableGenerator({}, debug=False)
        data = generator.get_table_data()
        assert data == []

    def test_valid_data(self):
        """Test with valid data."""
        sample_data = {
            "soap_makers": [
                {"brand": "Declaration Grooming", "shaves": 70, "unique_users": 35},
                {"brand": "Stirling", "shaves": 55, "unique_users": 28},
            ]
        }
        generator = SoapMakersTableGenerator(sample_data, debug=False)
        data = generator.get_table_data()
        assert len(data) == 2
        assert data[0]["maker"] == "Declaration Grooming"
        assert data[0]["shaves"] == 70

    def test_missing_required_fields(self):
        """Test with missing required fields."""
        sample_data = {
            "soap_makers": [
                {"brand": "Declaration Grooming"},  # Missing shaves
                {"brand": "Stirling", "shaves": 55, "unique_users": 28},  # Valid
            ]
        }
        generator = SoapMakersTableGenerator(sample_data, debug=False)
        data = generator.get_table_data()
        # SoapMakersTableGenerator now filters missing fields, so only valid record
        # should be included
        assert len(data) == 1
        assert data[0]["maker"] == "Stirling"

    def test_table_title(self):
        """Test table title."""
        generator = SoapMakersTableGenerator({}, debug=False)
        assert generator.get_table_title() == "Soap Makers"

    def test_column_config(self):
        """Test column configuration."""
        generator = SoapMakersTableGenerator({}, debug=False)
        config = generator.get_column_config()
        assert "brand" in config  # Actual data field
        assert "shaves" in config
        assert "unique_users" in config
        assert "avg_shaves_per_user" in config
        # Check that brand maps to "Brand" display name
        assert config["brand"]["display_name"] == "Brand"


class TestBrandDiversityTableGenerator:
    """Test the BrandDiversityTableGenerator."""

    def test_empty_data(self):
        """Test with empty data."""
        generator = BrandDiversityTableGenerator({}, debug=False)
        data = generator.get_table_data()
        assert data == []

    def test_valid_data(self):
        """Test with valid data."""
        sample_data = {
            "brand_diversity": [
                {"brand": "Declaration Grooming", "unique_soaps": 5, "position": 1},
                {"brand": "Stirling Soap Co.", "unique_soaps": 6, "position": 2},
            ]
        }
        generator = BrandDiversityTableGenerator(sample_data, debug=False)
        data = generator.get_table_data()
        assert len(data) == 2
        assert data[0]["maker"] == "Declaration Grooming"
        assert data[0]["unique_soaps"] == 5
        assert data[1]["maker"] == "Stirling Soap Co."
        assert data[1]["unique_soaps"] == 6

    def test_missing_required_fields(self):
        """Test with missing required fields."""
        sample_data = {
            "brand_diversity": [
                {"brand": "", "unique_soaps": 5},  # Empty maker but field present
                {"brand": "Stirling Soap Co.", "unique_soaps": 6},  # Valid
            ]
        }
        generator = BrandDiversityTableGenerator(sample_data, debug=False)
        data = generator.get_table_data()
        # Both records should be included since they have required fields
        assert len(data) == 2
        assert data[0]["maker"] == ""
        assert data[1]["maker"] == "Stirling Soap Co."

    def test_table_title(self):
        """Test table title."""
        generator = BrandDiversityTableGenerator({}, debug=False)
        assert generator.get_table_title() == "Brand Diversity (Unique Soaps per Maker)"

    def test_column_config(self):
        """Test column configuration."""
        generator = BrandDiversityTableGenerator({}, debug=False)
        config = generator.get_column_config()
        assert "maker" in config
        assert "unique_soaps" in config
