#!/usr/bin/env python3
"""Tests for the SoapSampleAggregator."""

from sotd.aggregate.aggregators.core.soap_sample_aggregator import (
    SoapSampleAggregator,
    aggregate_soap_samples,
)


class TestSoapSampleAggregator:
    """Test cases for the SoapSampleAggregator."""

    def test_aggregate_soap_samples_basic(self):
        """Test basic soap sample aggregation."""
        records = [
            {
                "author": "user1",
                "soap": {
                    "matched": {"maker": "B&M", "scent": "Seville"},
                    "enriched": {"sample_type": "sample"},
                },
            },
            {
                "author": "user2",
                "soap": {
                    "matched": {"maker": "B&M", "scent": "Seville"},
                    "enriched": {"sample_type": "sample"},
                },
            },
            {
                "author": "user1",
                "soap": {
                    "matched": {"maker": "Declaration Grooming", "scent": "Persephone"},
                    "enriched": {"sample_type": "tester"},
                },
            },
        ]

        result = aggregate_soap_samples(records)

        assert len(result) == 2
        assert result[0]["name"] == "sample - B&M - Seville"
        assert result[0]["shaves"] == 2
        assert result[0]["unique_users"] == 2
        assert result[0]["position"] == 1
        assert result[1]["name"] == "tester - Declaration Grooming - Persephone"
        assert result[1]["shaves"] == 1
        assert result[1]["unique_users"] == 1
        assert result[1]["position"] == 2

    def test_aggregate_soap_samples_with_numbers(self):
        """Test soap sample aggregation with sample numbers."""
        records = [
            {
                "author": "user1",
                "soap": {
                    "matched": {"maker": "Stirling", "scent": "Bay Rum"},
                    "enriched": {
                        "sample_type": "sample",
                        "sample_number": 5,
                        "total_samples": 10,
                    },
                },
            },
            {
                "author": "user2",
                "soap": {
                    "matched": {"maker": "Stirling", "scent": "Bay Rum"},
                    "enriched": {
                        "sample_type": "sample",
                        "sample_number": 7,
                        "total_samples": 10,
                    },
                },
            },
        ]

        result = aggregate_soap_samples(records)

        assert len(result) == 1
        assert result[0]["name"] == "sample - Stirling - Bay Rum"
        assert result[0]["shaves"] == 2
        assert result[0]["unique_users"] == 2
        assert result[0]["position"] == 1

    def test_aggregate_soap_samples_no_enrichment(self):
        """Test soap sample aggregation with no enrichment data."""
        records = [
            {
                "author": "user1",
                "soap": {
                    "matched": {"maker": "B&M", "scent": "Seville"},
                    # No enriched section
                },
            },
            {
                "author": "user2",
                "soap": {
                    "matched": {"maker": "Declaration Grooming", "scent": "Persephone"},
                    # No enriched section
                },
            },
        ]

        result = aggregate_soap_samples(records)

        assert result == []

    def test_aggregate_soap_samples_no_sample_type(self):
        """Test soap sample aggregation with enrichment but no sample_type."""
        records = [
            {
                "author": "user1",
                "soap": {
                    "matched": {"maker": "B&M", "scent": "Seville"},
                    "enriched": {"other_field": "value"},  # No sample_type
                },
            },
        ]

        result = aggregate_soap_samples(records)

        assert result == []

    def test_aggregate_soap_samples_missing_maker_scent(self):
        """Test soap sample aggregation with missing maker or scent."""
        records = [
            {
                "author": "user1",
                "soap": {
                    "matched": {},  # No maker/scent
                    "enriched": {"sample_type": "sample"},
                },
            },
            {
                "author": "user2",
                "soap": {
                    "matched": {"maker": "B&M"},  # No scent
                    "enriched": {"sample_type": "tester"},
                },
            },
        ]

        result = aggregate_soap_samples(records)

        assert len(result) == 2
        assert result[0]["name"] == "sample"
        assert result[0]["shaves"] == 1
        assert result[0]["unique_users"] == 1
        assert result[1]["name"] == "tester - B&M"
        assert result[1]["shaves"] == 1
        assert result[1]["unique_users"] == 1

    def test_aggregate_soap_samples_no_matches(self):
        """Test soap sample aggregation with no matched soaps."""
        records = [
            {"author": "user1", "soap": {"original": "Unknown Soap"}},
            {"author": "user2", "soap": {"original": "Another Unknown"}},
        ]

        result = aggregate_soap_samples(records)

        assert result == []

    def test_aggregate_soap_samples_empty_records(self):
        """Test soap sample aggregation with empty records."""
        records = []

        result = aggregate_soap_samples(records)

        assert result == []

    def test_aggregate_soap_samples_mixed_data(self):
        """Test soap sample aggregation with mixed sample and non-sample data."""
        records = [
            {
                "author": "user1",
                "soap": {
                    "matched": {"maker": "B&M", "scent": "Seville"},
                    "enriched": {"sample_type": "sample"},
                },
            },
            {
                "author": "user2",
                "soap": {
                    "matched": {"maker": "B&M", "scent": "Seville"},
                    # No enriched section - regular soap
                },
            },
            {
                "author": "user3",
                "soap": {
                    "matched": {"maker": "Declaration Grooming", "scent": "Persephone"},
                    "enriched": {"sample_type": "tester"},
                },
            },
        ]

        result = aggregate_soap_samples(records)

        # Should only include records with sample enrichment
        assert len(result) == 2
        sample_names = [r["name"] for r in result]
        assert "sample - B&M - Seville" in sample_names
        assert "tester - Declaration Grooming - Persephone" in sample_names

    def test_aggregate_soap_samples_samp_abbreviation(self):
        """Test soap sample aggregation with 'samp' abbreviation."""
        records = [
            {
                "author": "user1",
                "soap": {
                    "matched": {"maker": "Zingari Man", "scent": "The Wanderer"},
                    "enriched": {"sample_type": "samp"},  # Abbreviation
                },
            },
        ]

        result = aggregate_soap_samples(records)

        assert len(result) == 1
        assert result[0]["name"] == "samp - Zingari Man - The Wanderer"
        assert result[0]["shaves"] == 1
        assert result[0]["unique_users"] == 1

    def test_aggregate_soap_samples_complex_grouping(self):
        """Test that grouping works correctly with multiple fields."""
        aggregator = SoapSampleAggregator()
        
        records = [
            {
                "author": "user1",
                "soap": {
                    "matched": {"maker": "B&M", "scent": "Seville"},
                    "enriched": {"sample_type": "sample"},
                },
            },
            {
                "author": "user2",
                "soap": {
                    "matched": {"maker": "B&M", "scent": "Seville"},
                    "enriched": {"sample_type": "sample"},
                },
            },
            {
                "author": "user3",
                "soap": {
                    "matched": {"maker": "B&M", "scent": "Seville"},
                    "enriched": {"sample_type": "tester"},  # Different sample type
                },
            },
        ]

        result = aggregator.aggregate(records)

        # Should have separate entries for sample vs tester
        assert len(result) == 2
        sample_entry = next(r for r in result if "sample" in r["name"])
        tester_entry = next(r for r in result if "tester" in r["name"])
        
        assert sample_entry["shaves"] == 2
        assert tester_entry["shaves"] == 1
