#!/usr/bin/env python3
"""Tests for BladeDiversityAggregator."""

from sotd.aggregate.aggregators.users.blade_diversity_aggregator import (
    BladeDiversityAggregator,
    aggregate_blade_diversity,
)


class TestBladeDiversityAggregator:
    """Test BladeDiversityAggregator functionality."""

    def test_extract_data_with_brand_and_model_info(self):
        """Test data extraction with brand and model information."""
        records = [
            {
                "author": "user1",
                "blade": {
                    "matched": {"brand": "Feather", "model": "Hi-Stainless"},
                },
            },
            {
                "author": "user2",
                "blade": {
                    "matched": {"brand": "Astra", "model": "Superior Platinum"},
                },
            },
        ]

        aggregator = BladeDiversityAggregator()
        extracted = aggregator._extract_data(records)

        assert len(extracted) == 2
        assert extracted[0]["brand"] == "Feather"
        assert extracted[0]["model"] == "Hi-Stainless"
        assert extracted[0]["author"] == "user1"
        assert extracted[1]["brand"] == "Astra"
        assert extracted[1]["model"] == "Superior Platinum"
        assert extracted[1]["author"] == "user2"

    def test_extract_data_skips_records_without_brand(self):
        """Test that records without brand are skipped."""
        records = [
            {
                "author": "user1",
                "blade": {
                    "matched": {"model": "Hi-Stainless"},
                },
            },
            {
                "author": "user2",
                "blade": {
                    "matched": {"brand": "Astra", "model": "Superior Platinum"},
                },
            },
        ]

        aggregator = BladeDiversityAggregator()
        extracted = aggregator._extract_data(records)

        assert len(extracted) == 1
        assert extracted[0]["brand"] == "Astra"
        assert extracted[0]["model"] == "Superior Platinum"

    def test_extract_data_skips_records_without_model(self):
        """Test that records without model are skipped."""
        records = [
            {
                "author": "user1",
                "blade": {
                    "matched": {"brand": "Feather"},
                },
            },
            {
                "author": "user2",
                "blade": {
                    "matched": {"brand": "Astra", "model": "Superior Platinum"},
                },
            },
        ]

        aggregator = BladeDiversityAggregator()
        extracted = aggregator._extract_data(records)

        assert len(extracted) == 1
        assert extracted[0]["brand"] == "Astra"
        assert extracted[0]["model"] == "Superior Platinum"

    def test_extract_data_skips_records_without_matched_blade(self):
        """Test that records without matched blade are skipped."""
        records = [
            {
                "author": "user1",
                "blade": {},
            },
            {
                "author": "user2",
                "blade": {
                    "matched": {"brand": "Astra", "model": "Superior Platinum"},
                },
            },
        ]

        aggregator = BladeDiversityAggregator()
        extracted = aggregator._extract_data(records)

        assert len(extracted) == 1
        assert extracted[0]["brand"] == "Astra"
        assert extracted[0]["model"] == "Superior Platinum"

    def test_create_composite_name(self):
        """Test composite name creation."""
        aggregator = BladeDiversityAggregator()
        
        # Mock DataFrame
        import pandas as pd
        df = pd.DataFrame({
            "brand": ["Feather", "Astra"],
            "model": ["Hi-Stainless", "Superior Platinum"],
        })
        
        composite_names = aggregator._create_composite_name(df)
        
        assert composite_names.iloc[0] == "Feather Hi-Stainless"
        assert composite_names.iloc[1] == "Astra Superior Platinum"

    def test_aggregate_blade_diversity(self):
        """Test complete aggregation of blade diversity data."""
        records = [
            {
                "author": "user1",
                "blade": {
                    "matched": {"brand": "Feather", "model": "Hi-Stainless"},
                },
            },
            {
                "author": "user1",
                "blade": {
                    "matched": {"brand": "Feather", "model": "Hi-Stainless"},
                },
            },
            {
                "author": "user1",
                "blade": {
                    "matched": {"brand": "Astra", "model": "Superior Platinum"},
                },
            },
            {
                "author": "user2",
                "blade": {
                    "matched": {"brand": "Feather", "model": "Hi-Stainless"},
                },
            },
        ]

        result = aggregate_blade_diversity(records)

        assert len(result) == 2
        
        # Check first result (user1 with 2 unique blades, 3 total shaves)
        assert result[0]["position"] == 1
        assert result[0]["user"] == "user1"
        assert result[0]["unique_blades"] == 2
        assert result[0]["total_shaves"] == 3
        assert result[0]["unique_users"] == 1
        
        # Check second result (user2 with 1 unique blade, 1 total shave)
        assert result[1]["position"] == 2
        assert result[1]["user"] == "user2"
        assert result[1]["unique_blades"] == 1
        assert result[1]["total_shaves"] == 1
        assert result[1]["unique_users"] == 1

    def test_aggregate_empty_records(self):
        """Test aggregation with empty records."""
        result = aggregate_blade_diversity([])
        assert result == []

    def test_aggregate_no_blade_records(self):
        """Test aggregation with no blade records."""
        records = [
            {
                "author": "user1",
                "blade": {
                    "matched": {"brand": "Feather"},
                },
            },
        ]

        result = aggregate_blade_diversity(records)
        assert result == []

    def test_aggregate_single_user_multiple_blades(self):
        """Test aggregation for single user with multiple blades."""
        records = [
            {
                "author": "user1",
                "blade": {
                    "matched": {"brand": "Feather", "model": "Hi-Stainless"},
                },
            },
            {
                "author": "user1",
                "blade": {
                    "matched": {"brand": "Astra", "model": "Superior Platinum"},
                },
            },
            {
                "author": "user1",
                "blade": {
                    "matched": {"brand": "Gillette", "model": "Silver Blue"},
                },
            },
        ]

        result = aggregate_blade_diversity(records)

        assert len(result) == 1
        assert result[0]["position"] == 1
        assert result[0]["user"] == "user1"
        assert result[0]["unique_blades"] == 3
        assert result[0]["total_shaves"] == 3
        assert result[0]["unique_users"] == 1

    def test_aggregate_same_brand_different_models(self):
        """Test aggregation for same brand with different models."""
        records = [
            {
                "author": "user1",
                "blade": {
                    "matched": {"brand": "Feather", "model": "Hi-Stainless"},
                },
            },
            {
                "author": "user1",
                "blade": {
                    "matched": {"brand": "Feather", "model": "Hi-Stainless"},
                },
            },
            {
                "author": "user1",
                "blade": {
                    "matched": {"brand": "Feather", "model": "Hi-Stainless"},
                },
            },
        ]

        result = aggregate_blade_diversity(records)

        assert len(result) == 1
        assert result[0]["position"] == 1
        assert result[0]["user"] == "user1"
        assert result[0]["unique_blades"] == 1
        assert result[0]["total_shaves"] == 3
        assert result[0]["unique_users"] == 1
