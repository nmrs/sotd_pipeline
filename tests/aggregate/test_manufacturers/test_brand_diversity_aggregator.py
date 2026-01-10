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
            {"brand": "Barrister and Mann", "shaves": 172, "unique_users": 86},
            {"brand": "Stirling Soap Co.", "shaves": 145, "unique_users": 76},
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
        assert result[0]["brand"] == "Stirling Soap Co."  # 3 unique soaps, first alphabetically
        assert result[0]["unique_soaps"] == 3
        assert result[0]["rank"] == 1
        assert result[1]["brand"] == "Barrister and Mann"  # 2 unique soaps
        assert result[1]["unique_soaps"] == 2
        assert result[1]["rank"] == 2

    def test_empty_data(self):
        """Test with empty data."""
        result = aggregate_brand_diversity([], [])
        assert result == []

        result = aggregate_brand_diversity([{"brand": "Test"}], [])
        assert result == []

        result = aggregate_brand_diversity([], [{"name": "Test"}])
        assert result == []

    def test_no_matching_brands(self):
        """Test when soap names don't match any brands in soap_makers."""
        soap_makers = [{"brand": "Barrister and Mann", "shaves": 172, "unique_users": 86}]
        soaps = [{"name": "Unknown Brand - Scent"}]

        result = aggregate_brand_diversity(soap_makers, soaps)
        assert result == []

    def test_single_soap_per_brand(self):
        """Test brands with only one unique soap."""
        soap_makers = [{"brand": "Single Soap Brand", "shaves": 50, "unique_users": 25}]
        soaps = [{"name": "Single Soap Brand - Only Scent"}]

        result = aggregate_brand_diversity(soap_makers, soaps)
        assert len(result) == 1
        assert result[0]["brand"] == "Single Soap Brand"
        assert result[0]["unique_soaps"] == 1
        assert result[0]["rank"] == 1

    def test_soap_names_without_delimiter(self):
        """Test soap names that don't have the ' - ' delimiter."""
        soap_makers = [{"brand": "Simple Brand", "shaves": 100, "unique_users": 50}]
        soaps = [{"name": "Simple Brand"}]

        result = aggregate_brand_diversity(soap_makers, soaps)
        assert len(result) == 1
        assert result[0]["brand"] == "Simple Brand"
        assert result[0]["unique_soaps"] == 1

    def test_competition_ranking_with_ties(self):
        """Test competition ranking (1, 2, 2, 4, 5...) when ties exist."""
        soap_makers = [
            {"brand": "Barrister and Mann", "shaves": 172, "unique_users": 86},
            {"brand": "Stirling Soap Co.", "shaves": 145, "unique_users": 76},
            {"brand": "Declaration Grooming", "shaves": 100, "unique_users": 50},
        ]
        soaps = [
            # Barrister and Mann - 3 unique soaps
            {"name": "Barrister and Mann - Fougère Angelique"},
            {"name": "Barrister and Mann - Seville"},
            {"name": "Barrister and Mann - Vespers"},
            # Stirling Soap Co. - 3 unique soaps (tied with Barrister and Mann)
            {"name": "Stirling Soap Co. - Executive Man"},
            {"name": "Stirling Soap Co. - Sharp Dressed Man"},
            {"name": "Stirling Soap Co. - Barbershop"},
            # Declaration Grooming - 2 unique soaps (should be rank 3, not rank 2)
            {"name": "Declaration Grooming - Agua Fresca"},
            {"name": "Declaration Grooming - Massacre of the Innocents"},
        ]

        result = aggregate_brand_diversity(soap_makers, soaps)

        assert len(result) == 3
        # Both tied brands should get rank 1
        # Find brands by name since order may vary for tied entries
        brand_ranks = {item["brand"]: item["rank"] for item in result}
        assert brand_ranks["Barrister and Mann"] == 1
        assert brand_ranks["Stirling Soap Co."] == 1
        # Declaration Grooming should be rank 3 (competition ranking), not rank 2 (dense ranking)
        assert brand_ranks["Declaration Grooming"] == 3
