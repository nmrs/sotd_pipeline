#!/usr/bin/env python3
"""Tests for RazorDiversityAggregator."""

from sotd.aggregate.aggregators.users.razor_diversity_aggregator import (
    RazorDiversityAggregator,
    aggregate_razor_diversity,
)


class TestRazorDiversityAggregator:
    """Test RazorDiversityAggregator functionality."""

    def test_extract_data_with_brand_and_model_info(self):
        """Test data extraction with brand and model information."""
        records = [
            {
                "author": "user1",
                "razor": {
                    "matched": {"brand": "Merkur", "model": "34C"},
                },
            },
            {
                "author": "user2",
                "razor": {
                    "matched": {"brand": "Gillette", "model": "Super Speed"},
                },
            },
        ]

        aggregator = RazorDiversityAggregator()
        extracted = aggregator._extract_data(records)

        assert len(extracted) == 2
        assert extracted[0]["brand"] == "Merkur"
        assert extracted[0]["model"] == "34C"
        assert extracted[0]["author"] == "user1"
        assert extracted[1]["brand"] == "Gillette"
        assert extracted[1]["model"] == "Super Speed"
        assert extracted[1]["author"] == "user2"

    def test_extract_data_skips_records_without_brand(self):
        """Test that records without brand are skipped."""
        records = [
            {
                "author": "user1",
                "razor": {
                    "matched": {"model": "34C"},
                },
            },
            {
                "author": "user2",
                "razor": {
                    "matched": {"brand": "Gillette", "model": "Super Speed"},
                },
            },
        ]

        aggregator = RazorDiversityAggregator()
        extracted = aggregator._extract_data(records)

        assert len(extracted) == 1
        assert extracted[0]["brand"] == "Gillette"
        assert extracted[0]["model"] == "Super Speed"

    def test_extract_data_skips_records_without_model(self):
        """Test that records without model are skipped."""
        records = [
            {
                "author": "user1",
                "razor": {
                    "matched": {"brand": "Merkur"},
                },
            },
            {
                "author": "user2",
                "razor": {
                    "matched": {"brand": "Gillette", "model": "Super Speed"},
                },
            },
        ]

        aggregator = RazorDiversityAggregator()
        extracted = aggregator._extract_data(records)

        assert len(extracted) == 1
        assert extracted[0]["brand"] == "Gillette"
        assert extracted[0]["model"] == "Super Speed"

    def test_extract_data_skips_records_without_matched_razor(self):
        """Test that records without matched razor are skipped."""
        records = [
            {
                "author": "user1",
                "razor": {},
            },
            {
                "author": "user2",
                "razor": {
                    "matched": {"brand": "Gillette", "model": "Super Speed"},
                },
            },
        ]

        aggregator = RazorDiversityAggregator()
        extracted = aggregator._extract_data(records)

        assert len(extracted) == 1
        assert extracted[0]["brand"] == "Gillette"
        assert extracted[0]["model"] == "Super Speed"

    def test_create_composite_name(self):
        """Test composite name creation."""
        aggregator = RazorDiversityAggregator()

        # Mock DataFrame
        import pandas as pd

        df = pd.DataFrame(
            {
                "brand": ["Merkur", "Gillette"],
                "model": ["34C", "Super Speed"],
            }
        )

        composite_names = aggregator._create_composite_name(df)

        assert composite_names.iloc[0] == "Merkur 34C"
        assert composite_names.iloc[1] == "Gillette Super Speed"

    def test_aggregate_razor_diversity(self):
        """Test complete aggregation of razor diversity data."""
        records = [
            {
                "author": "user1",
                "razor": {
                    "matched": {"brand": "Merkur", "model": "34C"},
                },
            },
            {
                "author": "user1",
                "razor": {
                    "matched": {"brand": "Merkur", "model": "37C"},
                },
            },
            {
                "author": "user1",
                "razor": {
                    "matched": {"brand": "Gillette", "model": "Super Speed"},
                },
            },
            {
                "author": "user2",
                "razor": {
                    "matched": {"brand": "Merkur", "model": "34C"},
                },
            },
        ]

        result = aggregate_razor_diversity(records)

        assert len(result) == 2

        # Check first result (user1 with 3 unique razors, 3 total shaves)
        assert result[0]["rank"] == 1
        assert result[0]["user"] == "user1"
        assert result[0]["unique_razors"] == 3
        assert result[0]["shaves"] == 3
        assert result[0]["avg_shaves_per_razor"] == 1.0

        # Check second result (user2 with 1 unique razor, 1 total shave)
        assert result[1]["rank"] == 2
        assert result[1]["user"] == "user2"
        assert result[1]["unique_razors"] == 1
        assert result[1]["shaves"] == 1
        assert result[1]["avg_shaves_per_razor"] == 1.0

    def test_aggregate_empty_records(self):
        """Test aggregation with empty records."""
        result = aggregate_razor_diversity([])
        assert result == []

    def test_aggregate_no_razor_records(self):
        """Test aggregation with no razor records."""
        records = [
            {
                "author": "user1",
                "razor": {
                    "matched": {"brand": "Merkur"},
                },
            },
        ]

        result = aggregate_razor_diversity(records)
        assert result == []

    def test_aggregate_single_user_multiple_razors(self):
        """Test aggregation for single user with multiple razors."""
        records = [
            {
                "author": "user1",
                "razor": {
                    "matched": {"brand": "Merkur", "model": "34C"},
                },
            },
            {
                "author": "user1",
                "razor": {
                    "matched": {"brand": "Gillette", "model": "Super Speed"},
                },
            },
            {
                "author": "user1",
                "razor": {
                    "matched": {"brand": "Rockwell", "model": "6C"},
                },
            },
        ]

        result = aggregate_razor_diversity(records)

        assert len(result) == 1
        assert result[0]["rank"] == 1
        assert result[0]["user"] == "user1"
        assert result[0]["unique_razors"] == 3
        assert result[0]["shaves"] == 3
        assert result[0]["avg_shaves_per_razor"] == 1.0

    def test_aggregate_same_brand_different_models(self):
        """Test aggregation for same brand with different models."""
        records = [
            {
                "author": "user1",
                "razor": {
                    "matched": {"brand": "Merkur", "model": "34C"},
                },
            },
            {
                "author": "user1",
                "razor": {
                    "matched": {"brand": "Merkur", "model": "37C"},
                },
            },
            {
                "author": "user1",
                "razor": {
                    "matched": {"brand": "Merkur", "model": "39C"},
                },
            },
        ]

        result = aggregate_razor_diversity(records)

        assert len(result) == 1
        assert result[0]["rank"] == 1
        assert result[0]["user"] == "user1"
        assert result[0]["unique_razors"] == 3
        assert result[0]["shaves"] == 3
        assert result[0]["avg_shaves_per_razor"] == 1.0
