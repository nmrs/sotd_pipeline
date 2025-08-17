#!/usr/bin/env python3
"""Tests for brand diversity aggregator."""

from sotd.aggregate.aggregators.manufacturers.brand_diversity_aggregator import (
    aggregate_brand_diversity,
)


class TestBrandDiversityAggregator:
    """Test the brand diversity aggregator."""

    def test_basic_functionality(self):
        """Test basic brand diversity aggregation."""
        soap_makers = [
            {"maker": "Barrister and Mann", "shaves": 172, "unique_users": 86},
            {"maker": "Stirling Soap Co.", "shaves": 145, "unique_users": 76},
        ]
        soaps = [
            {"name": "Barrister and Mann - Fougère Angelique"},
            {"name": "Barrister and Mann - Seville"},
            {"name": "Stirling Soap Co. - Executive Man"},
            {"name": "Stirling Soap Co. - Sharp Dressed Man"},
            {"name": "Stirling Soap Co. - Barbershop"},
        ]

        result = aggregate_brand_diversity(soap_makers, soaps)

        assert len(result) == 2
        # Should preserve full brand names
        assert result[0]["maker"] == "Stirling Soap Co."  # 3 unique soaps, first alphabetically
        assert result[0]["unique_soaps"] == 3
        assert result[0]["position"] == 1
        assert result[1]["maker"] == "Barrister and Mann"  # 2 unique soaps
        assert result[1]["unique_soaps"] == 2
        assert result[1]["position"] == 2

    def test_empty_data(self):
        """Test with empty data."""
        result = aggregate_brand_diversity([], [])
        assert result == []

        result = aggregate_brand_diversity([{"maker": "Test"}], [])
        assert result == []

        result = aggregate_brand_diversity([], [{"name": "Test"}])
        assert result == []

    def test_no_matching_brands(self):
        """Test when soap names don't match any brands in soap_makers."""
        soap_makers = [{"maker": "Barrister and Mann", "shaves": 172, "unique_users": 86}]
        soaps = [{"name": "Unknown Brand - Scent"}]

        result = aggregate_brand_diversity(soap_makers, soaps)
        assert result == []

    def test_single_soap_per_brand(self):
        """Test brands with only one unique soap."""
        soap_makers = [{"maker": "Single Soap Brand", "shaves": 50, "unique_users": 25}]
        soaps = [{"name": "Single Soap Brand - Only Scent"}]

        result = aggregate_brand_diversity(soap_makers, soaps)
        assert len(result) == 1
        assert result[0]["maker"] == "Single Soap Brand"
        assert result[0]["unique_soaps"] == 1
        assert result[0]["position"] == 1

    def test_soap_names_without_delimiter(self):
        """Test soap names that don't have the ' - ' delimiter."""
        soap_makers = [{"maker": "Simple Brand", "shaves": 100, "unique_users": 50}]
        soaps = [{"name": "Simple Brand"}]

        result = aggregate_brand_diversity(soap_makers, soaps)
        assert len(result) == 1
        assert result[0]["maker"] == "Simple Brand"
        assert result[0]["unique_soaps"] == 1
