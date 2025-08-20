#!/usr/bin/env python3
"""Tests for the sample usage metrics aggregator."""

from sotd.aggregate.aggregators.core.sample_usage_metrics_aggregator import (
    aggregate_sample_usage_metrics,
)


class TestSampleUsageMetricsAggregator:
    """Test cases for the sample usage metrics aggregator."""

    def test_empty_records(self):
        """Test aggregation with empty records."""
        result = aggregate_sample_usage_metrics([])

        assert result["total_samples"] == 0
        assert result["total_shaves"] == 0
        assert result["sample_percentage"] == 0.0
        assert result["sample_types"] == {}
        assert result["sample_users"] == 0
        assert result["sample_brands"] == 0
        assert result["sample_distribution"] == []

    def test_no_sample_records(self):
        """Test aggregation with no sample records."""
        records = [
            {
                "author": "user1",
                "soap": {
                    "enriched": {},
                    "matched": {"maker": "B&M", "scent": "Seville"},
                },
            },
            {
                "author": "user2",
                "soap": {
                    "enriched": {},
                    "matched": {"maker": "Declaration Grooming", "scent": "B2"},
                },
            },
        ]

        result = aggregate_sample_usage_metrics(records)

        assert result["total_samples"] == 0
        assert result["total_shaves"] == 2
        assert result["sample_percentage"] == 0.0
        assert result["sample_users"] == 0
        assert result["sample_brands"] == 0

    def test_basic_sample_records(self):
        """Test aggregation with basic sample records."""
        records = [
            {
                "author": "user1",
                "soap": {
                    "enriched": {"sample_type": "sample"},
                    "matched": {"maker": "B&M", "scent": "Seville"},
                },
            },
            {
                "author": "user2",
                "soap": {
                    "enriched": {"sample_type": "tester"},
                    "matched": {"maker": "Declaration Grooming", "scent": "B2"},
                },
            },
            {
                "author": "user3",
                "soap": {
                    "enriched": {"sample_type": "sample"},
                    "matched": {"maker": "B&M", "scent": "Seville"},
                },
            },
        ]

        result = aggregate_sample_usage_metrics(records)

        assert result["total_samples"] == 3
        assert result["total_shaves"] == 3
        assert result["sample_percentage"] == 100.0
        assert result["sample_users"] == 3
        assert result["sample_brands"] == 2
        assert len(result["sample_distribution"]) == 2

        # Check sample distribution
        sample_dist = {item["sample_type"]: item["count"] for item in result["sample_distribution"]}
        assert sample_dist["sample"] == 2
        assert sample_dist["tester"] == 1

    def test_sample_records_without_brand(self):
        """Test aggregation with sample records that have no brand."""
        records = [
            {
                "author": "user1",
                "soap": {
                    "enriched": {"sample_type": "sample"},
                    "matched": {"scent": "Seville"},  # No maker
                },
            },
            {
                "author": "user2",
                "soap": {
                    "enriched": {"sample_type": "sample"},
                    "matched": {"maker": "B&M", "scent": "Seville"},
                },
            },
        ]

        result = aggregate_sample_usage_metrics(records)

        assert result["total_samples"] == 2
        assert result["total_shaves"] == 2
        assert result["sample_percentage"] == 100.0
        assert result["sample_users"] == 2
        assert result["sample_brands"] == 1  # Only one has a brand
        assert "B&M" in result["unique_sample_brands"]

    def test_sample_records_without_author(self):
        """Test aggregation with sample records that have no author."""
        records = [
            {
                "soap": {
                    "enriched": {"sample_type": "sample"},
                    "matched": {"maker": "B&M", "scent": "Seville"},
                },
            },
            {
                "author": "user2",
                "soap": {
                    "enriched": {"sample_type": "sample"},
                    "matched": {"maker": "Declaration Grooming", "scent": "B2"},
                },
            },
        ]

        result = aggregate_sample_usage_metrics(records)

        assert result["total_samples"] == 2
        assert result["total_shaves"] == 2
        assert result["sample_percentage"] == 100.0
        assert result["sample_users"] == 1  # Only one has an author
        assert result["sample_brands"] == 2
        assert "user2" in result["unique_sample_users"]
