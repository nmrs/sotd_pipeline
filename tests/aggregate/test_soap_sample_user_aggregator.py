#!/usr/bin/env python3
"""Tests for SoapSampleUserAggregator."""

from sotd.aggregate.aggregators.users.soap_sample_user_aggregator import (
    SoapSampleUserAggregator,
    aggregate_soap_sample_users,
)


class TestSoapSampleUserAggregator:
    """Test SoapSampleUserAggregator functionality."""

    def test_extract_data_with_sample_info(self):
        """Test data extraction with sample information."""
        records = [
            {
                "author": "user1",
                "soap": {
                    "enriched": {
                        "sample_type": "Sample",
                        "sample_number": 1,
                        "total_samples": 5,
                    },
                    "matched": {"brand": "Declaration Grooming", "scent": "B2"},
                },
            },
            {
                "author": "user2",
                "soap": {
                    "enriched": {
                        "sample_type": "Sample",
                        "sample_number": 2,
                        "total_samples": 5,
                    },
                    "matched": {"brand": "Declaration Grooming", "scent": "B2"},
                },
            },
        ]

        aggregator = SoapSampleUserAggregator()
        extracted = aggregator._extract_data(records)

        assert len(extracted) == 2
        assert extracted[0]["sample_type"] == "Sample"
        assert extracted[0]["brand"] == "Declaration Grooming"
        assert extracted[0]["scent"] == "B2"
        assert extracted[0]["author"] == "user1"

    def test_extract_data_skips_non_sample_records(self):
        """Test that non-sample records are skipped."""
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
                    "enriched": {
                        "sample_type": "Sample",
                        "sample_number": 1,
                        "total_samples": 5,
                    },
                    "matched": {"brand": "Barrister & Mann", "scent": "Seville"},
                },
            },
        ]

        aggregator = SoapSampleUserAggregator()
        extracted = aggregator._extract_data(records)

        assert len(extracted) == 1
        assert extracted[0]["brand"] == "Barrister & Mann"
        assert extracted[0]["scent"] == "Seville"

    def test_extract_data_handles_missing_brand_or_scent(self):
        """Test data extraction when brand or scent is missing."""
        records = [
            {
                "author": "user1",
                "soap": {
                    "enriched": {
                        "sample_type": "Sample",
                        "sample_number": 1,
                        "total_samples": 5,
                    },
                    "matched": {"brand": "Declaration Grooming"},
                },
            },
            {
                "author": "user2",
                "soap": {
                    "enriched": {
                        "sample_type": "Sample",
                        "sample_number": 2,
                        "total_samples": 5,
                    },
                    "matched": {"scent": "B2"},
                },
            },
        ]

        aggregator = SoapSampleUserAggregator()
        extracted = aggregator._extract_data(records)

        assert len(extracted) == 2
        assert extracted[0]["brand"] == "Declaration Grooming"
        assert extracted[0]["scent"] == ""
        assert extracted[1]["brand"] == ""
        assert extracted[1]["scent"] == "B2"

    def test_create_composite_name_with_brand_and_scent(self):
        """Test composite name creation with brand and scent."""
        aggregator = SoapSampleUserAggregator()
        
        # Mock DataFrame
        import pandas as pd
        df = pd.DataFrame({
            "sample_type": ["Sample", "Sample"],
            "brand": ["Declaration Grooming", "Barrister & Mann"],
            "scent": ["B2", "Seville"],
        })
        
        composite_names = aggregator._create_composite_name(df)
        
        assert composite_names.iloc[0] == "Sample - Declaration Grooming - B2"
        assert composite_names.iloc[1] == "Sample - Barrister & Mann - Seville"

    def test_create_composite_name_with_brand_only(self):
        """Test composite name creation with brand only."""
        aggregator = SoapSampleUserAggregator()
        
        # Mock DataFrame
        import pandas as pd
        df = pd.DataFrame({
            "sample_type": ["Sample", "Sample"],
            "brand": ["Declaration Grooming", ""],
            "scent": ["", ""],
        })
        
        composite_names = aggregator._create_composite_name(df)
        
        assert composite_names.iloc[0] == "Sample - Declaration Grooming"
        assert composite_names.iloc[1] == "Sample"

    def test_aggregate_sample_data(self):
        """Test complete aggregation of sample data."""
        records = [
            {
                "author": "user1",
                "soap": {
                    "enriched": {
                        "sample_type": "Sample",
                        "sample_number": 1,
                        "total_samples": 5,
                    },
                    "matched": {"brand": "Declaration Grooming", "scent": "B2"},
                },
            },
            {
                "author": "user1",
                "soap": {
                    "enriched": {
                        "sample_type": "Sample",
                        "sample_number": 2,
                        "total_samples": 5,
                    },
                    "matched": {"brand": "Declaration Grooming", "scent": "B2"},
                },
            },
            {
                "author": "user2",
                "soap": {
                    "enriched": {
                        "sample_type": "Sample",
                        "sample_number": 1,
                        "total_samples": 3,
                    },
                    "matched": {"brand": "Barrister & Mann", "scent": "Seville"},
                },
            },
        ]

        result = aggregate_soap_sample_users(records)

        assert len(result) == 2
        
        # Check first result (user1 with 2 sample shaves)
        assert result[0]["position"] == 1
        assert result[0]["user"] == "user1"
        assert result[0]["shaves"] == 2
        assert result[0]["unique_users"] == 1
        
        # Check second result (user2 with 1 sample shave)
        assert result[1]["position"] == 2
        assert result[1]["user"] == "user2"
        assert result[1]["shaves"] == 1
        assert result[1]["unique_users"] == 1

    def test_aggregate_empty_records(self):
        """Test aggregation with empty records."""
        result = aggregate_soap_sample_users([])
        assert result == []

    def test_aggregate_no_sample_records(self):
        """Test aggregation with no sample records."""
        records = [
            {
                "author": "user1",
                "soap": {
                    "matched": {"brand": "Declaration Grooming", "scent": "B2"},
                },
            },
        ]

        result = aggregate_soap_sample_users(records)
        assert result == []
