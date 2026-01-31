#!/usr/bin/env python3
"""Tests for SoapMashupUserAggregator."""

from sotd.aggregate.aggregators.users.soap_mashup_user_aggregator import (
    SoapMashupUserAggregator,
    aggregate_soap_mashup_users,
)


class TestSoapMashupUserAggregator:
    """Test SoapMashupUserAggregator functionality."""

    def test_extract_data_with_mashup_info(self):
        """Test data extraction with is_mashup True."""
        records = [
            {
                "author": "user1",
                "soap": {
                    "enriched": {"is_mashup": True},
                    "matched": {"brand": "Mama Bear Soaps", "scent": "Sample Mashup"},
                },
            },
            {
                "author": "user2",
                "soap": {
                    "enriched": {"is_mashup": True},
                    "matched": None,
                },
            },
        ]

        aggregator = SoapMashupUserAggregator()
        extracted = aggregator._extract_data(records)

        assert len(extracted) == 2
        assert extracted[0]["author"] == "user1"
        assert extracted[1]["author"] == "user2"

    def test_extract_data_skips_non_mashup_records(self):
        """Test that non-mashup records are skipped."""
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
                    "enriched": {"is_mashup": False},
                    "matched": {"brand": "Barrister & Mann", "scent": "Seville"},
                },
            },
            {
                "author": "user3",
                "soap": {
                    "enriched": {"is_mashup": True},
                    "matched": {"brand": "Mama Bear Soaps", "scent": "Sample Mashup"},
                },
            },
        ]

        aggregator = SoapMashupUserAggregator()
        extracted = aggregator._extract_data(records)

        assert len(extracted) == 1
        assert extracted[0]["author"] == "user3"

    def test_extract_data_skips_empty_enriched(self):
        """Test that records without is_mashup True are skipped."""
        records = [
            {
                "author": "user1",
                "soap": {"enriched": {}},
            },
        ]

        aggregator = SoapMashupUserAggregator()
        extracted = aggregator._extract_data(records)

        assert len(extracted) == 0

    def test_create_composite_name_uses_author(self):
        """Test composite name is author (user) for mashup user aggregator."""
        import pandas as pd

        aggregator = SoapMashupUserAggregator()
        df = pd.DataFrame({"author": ["user1", "user2"]})
        composite_names = aggregator._create_composite_name(df)
        assert composite_names.iloc[0] == "user1"
        assert composite_names.iloc[1] == "user2"

    def test_aggregate_mashup_data(self):
        """Test complete aggregation of mashup data by user."""
        records = [
            {
                "author": "user1",
                "soap": {
                    "enriched": {"is_mashup": True},
                    "matched": {"brand": "Mama Bear Soaps", "scent": "Sample Mashup"},
                },
            },
            {
                "author": "user1",
                "soap": {
                    "enriched": {"is_mashup": True},
                    "matched": None,
                },
            },
            {
                "author": "user2",
                "soap": {
                    "enriched": {"is_mashup": True},
                    "matched": {"brand": "Other", "scent": "Mashup"},
                },
            },
        ]

        result = aggregate_soap_mashup_users(records)

        assert len(result) == 2

        assert result[0]["rank"] == 1
        assert result[0]["user"] == "user1"
        assert result[0]["shaves"] == 2
        assert result[0]["unique_users"] == 1

        assert result[1]["rank"] == 2
        assert result[1]["user"] == "user2"
        assert result[1]["shaves"] == 1
        assert result[1]["unique_users"] == 1

    def test_aggregate_empty_records(self):
        """Test aggregation with empty records."""
        result = aggregate_soap_mashup_users([])
        assert result == []

    def test_aggregate_no_mashup_records(self):
        """Test aggregation with no mashup records."""
        records = [
            {
                "author": "user1",
                "soap": {
                    "matched": {"brand": "Declaration Grooming", "scent": "B2"},
                },
            },
        ]

        result = aggregate_soap_mashup_users(records)
        assert result == []
