#!/usr/bin/env python3
"""Tests for SoapSampleBrandAggregator."""

from sotd.aggregate.aggregators.core.soap_sample_brand_aggregator import (
    SoapSampleBrandAggregator,
    aggregate_soap_sample_brands,
)


class TestSoapSampleBrandAggregator:
    """Test SoapSampleBrandAggregator functionality."""

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

        aggregator = SoapSampleBrandAggregator()
        extracted = aggregator._extract_data(records)

        assert len(extracted) == 2
        assert extracted[0]["sample_type"] == "Sample"
        assert extracted[0]["brand"] == "Declaration Grooming"
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

        aggregator = SoapSampleBrandAggregator()
        extracted = aggregator._extract_data(records)

        assert len(extracted) == 1
        assert extracted[0]["brand"] == "Barrister & Mann"

    def test_extract_data_handles_missing_brand(self):
        """Test data extraction when brand is missing."""
        records = [
            {
                "author": "user1",
                "soap": {
                    "enriched": {
                        "sample_type": "Sample",
                        "sample_number": 1,
                        "total_samples": 5,
                    },
                    "matched": {},
                },
            },
        ]

        aggregator = SoapSampleBrandAggregator()
        extracted = aggregator._extract_data(records)

        assert len(extracted) == 1
        assert extracted[0]["brand"] == ""

    def test_create_composite_name_with_brand(self):
        """Test composite name creation with brand."""
        aggregator = SoapSampleBrandAggregator()
        
        # Mock DataFrame
        import pandas as pd
        df = pd.DataFrame({
            "sample_type": ["Sample", "Sample"],
            "brand": ["Declaration Grooming", "Barrister & Mann"],
        })
        
        composite_names = aggregator._create_composite_name(df)
        
        assert composite_names.iloc[0] == "Sample - Declaration Grooming"
        assert composite_names.iloc[1] == "Sample - Barrister & Mann"

    def test_create_composite_name_without_brand(self):
        """Test composite name creation without brand."""
        aggregator = SoapSampleBrandAggregator()
        
        # Mock DataFrame
        import pandas as pd
        df = pd.DataFrame({
            "sample_type": ["Sample", "Sample"],
            "brand": ["", ""],
        })
        
        composite_names = aggregator._create_composite_name(df)
        
        assert composite_names.iloc[0] == "Sample"
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
            {
                "author": "user3",
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

        result = aggregate_soap_sample_brands(records)

        assert len(result) == 2
        
        # Check first result (Declaration Grooming)
        assert result[0]["position"] == 1
        assert result[0]["name"] == "Sample - Declaration Grooming"
        assert result[0]["shaves"] == 2
        assert result[0]["unique_users"] == 2
        
        # Check second result (Barrister & Mann)
        assert result[1]["position"] == 2
        assert result[1]["name"] == "Sample - Barrister & Mann"
        assert result[1]["shaves"] == 1
        assert result[1]["unique_users"] == 1

    def test_aggregate_empty_records(self):
        """Test aggregation with empty records."""
        result = aggregate_soap_sample_brands([])
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

        result = aggregate_soap_sample_brands(records)
        assert result == []
