#!/usr/bin/env python3
"""Tests for SoapBrandDiversityAggregator."""

from sotd.aggregate.aggregators.users.soap_brand_diversity_aggregator import (
    SoapBrandDiversityAggregator,
    aggregate_soap_brand_diversity,
)


class TestSoapBrandDiversityAggregator:
    """Test SoapBrandDiversityAggregator functionality."""

    def test_extract_data_with_brand_info(self):
        """Test data extraction with brand information."""
        records = [
            {
                "author": "user1",
                "soap": {
                    "matched": {"brand": "Declaration Grooming", "scent": "B2"},
                },
            },
            {
                "author": "user2",
                "soap": {
                    "matched": {"brand": "Barrister & Mann", "scent": "Seville"},
                },
            },
        ]

        aggregator = SoapBrandDiversityAggregator()
        extracted = aggregator._extract_data(records)

        assert len(extracted) == 2
        assert extracted[0]["brand"] == "Declaration Grooming"
        assert extracted[0]["author"] == "user1"
        assert extracted[1]["brand"] == "Barrister & Mann"
        assert extracted[1]["author"] == "user2"

    def test_extract_data_skips_records_without_brand(self):
        """Test that records without brand are skipped."""
        records = [
            {
                "author": "user1",
                "soap": {
                    "matched": {"scent": "B2"},
                },
            },
            {
                "author": "user2",
                "soap": {
                    "matched": {"brand": "Barrister & Mann", "scent": "Seville"},
                },
            },
        ]

        aggregator = SoapBrandDiversityAggregator()
        extracted = aggregator._extract_data(records)

        assert len(extracted) == 1
        assert extracted[0]["brand"] == "Barrister & Mann"

    def test_extract_data_skips_records_without_matched_soap(self):
        """Test that records without matched soap are skipped."""
        records = [
            {
                "author": "user1",
                "soap": {},
            },
            {
                "author": "user2",
                "soap": {
                    "matched": {"brand": "Barrister & Mann", "scent": "Seville"},
                },
            },
        ]

        aggregator = SoapBrandDiversityAggregator()
        extracted = aggregator._extract_data(records)

        assert len(extracted) == 1
        assert extracted[0]["brand"] == "Barrister & Mann"

    def test_create_composite_name(self):
        """Test composite name creation."""
        aggregator = SoapBrandDiversityAggregator()

        # Mock DataFrame
        import pandas as pd

        df = pd.DataFrame(
            {
                "brand": ["Declaration Grooming", "Barrister & Mann"],
            }
        )

        composite_names = aggregator._create_composite_name(df)

        assert composite_names.iloc[0] == "Declaration Grooming"
        assert composite_names.iloc[1] == "Barrister & Mann"

    def test_aggregate_brand_diversity(self):
        """Test complete aggregation of brand diversity data."""
        records = [
            {
                "author": "user1",
                "soap": {
                    "matched": {"brand": "Declaration Grooming", "scent": "B2"},
                },
            },
            {
                "author": "user1",
                "soap": {
                    "matched": {"brand": "Declaration Grooming", "scent": "B3"},
                },
            },
            {
                "author": "user1",
                "soap": {
                    "matched": {"brand": "Barrister & Mann", "scent": "Seville"},
                },
            },
            {
                "author": "user2",
                "soap": {
                    "matched": {"brand": "Declaration Grooming", "scent": "B2"},
                },
            },
        ]

        result = aggregate_soap_brand_diversity(records)

        assert len(result) == 2

        # Check first result (user1 with 2 unique brands, 3 total shaves)
        assert result[0]["position"] == 1
        assert result[0]["user"] == "user1"
        assert result[0]["unique_brands"] == 2
        assert result[0]["total_shaves"] == 3
        assert result[0]["unique_users"] == 1

        # Check second result (user2 with 1 unique brand, 1 total shave)
        assert result[1]["position"] == 2
        assert result[1]["user"] == "user2"
        assert result[1]["unique_brands"] == 1
        assert result[1]["total_shaves"] == 1
        assert result[1]["unique_users"] == 1

    def test_aggregate_empty_records(self):
        """Test aggregation with empty records."""
        result = aggregate_soap_brand_diversity([])
        assert result == []

    def test_aggregate_no_brand_records(self):
        """Test aggregation with no brand records."""
        records = [
            {
                "author": "user1",
                "soap": {
                    "matched": {"scent": "B2"},
                },
            },
        ]

        result = aggregate_soap_brand_diversity(records)
        assert result == []

    def test_aggregate_single_user_multiple_brands(self):
        """Test aggregation for single user with multiple brands."""
        records = [
            {
                "author": "user1",
                "soap": {
                    "matched": {"brand": "Declaration Grooming", "scent": "B2"},
                },
            },
            {
                "author": "user1",
                "soap": {
                    "matched": {"brand": "Barrister & Mann", "scent": "Seville"},
                },
            },
            {
                "author": "user1",
                "soap": {
                    "matched": {"brand": "Noble Otter", "scent": "Lonestar"},
                },
            },
        ]

        result = aggregate_soap_brand_diversity(records)

        assert len(result) == 1
        assert result[0]["position"] == 1
        assert result[0]["user"] == "user1"
        assert result[0]["unique_brands"] == 3
        assert result[0]["total_shaves"] == 3
        assert result[0]["unique_users"] == 1
