#!/usr/bin/env python3
"""Tests for the mashup usage metrics aggregator."""

from sotd.aggregate.aggregators.core.mashup_usage_metrics_aggregator import (
    aggregate_mashup_usage_metrics,
)


class TestMashupUsageMetricsAggregator:
    """Test cases for the mashup usage metrics aggregator."""

    def test_empty_records(self):
        """Test aggregation with empty records."""
        result = aggregate_mashup_usage_metrics([])

        assert result["total_mashup_shaves"] == 0
        assert result["total_shaves"] == 0
        assert result["mashup_percentage"] == 0.0
        assert result["mashup_users"] == 0

    def test_no_mashup_records(self):
        """Test aggregation with no mashup records."""
        records = [
            {
                "author": "user1",
                "soap": {
                    "enriched": {},
                    "matched": {"brand": "B&M", "scent": "Seville"},
                },
            },
            {
                "author": "user2",
                "soap": {
                    "enriched": {"is_mashup": False},
                    "matched": {"brand": "Declaration Grooming", "scent": "B2"},
                },
            },
        ]

        result = aggregate_mashup_usage_metrics(records)

        assert result["total_mashup_shaves"] == 0
        assert result["total_shaves"] == 2
        assert result["mashup_percentage"] == 0.0
        assert result["mashup_users"] == 0

    def test_basic_mashup_records(self):
        """Test aggregation with mashup records (is_mashup True)."""
        records = [
            {
                "author": "user1",
                "soap": {
                    "enriched": {"is_mashup": True},
                    "matched": {"brand": "Mama Bear", "scent": "Sample Mashup"},
                },
            },
            {
                "author": "user2",
                "soap": {
                    "enriched": {"is_mashup": True},
                    "matched": None,
                },
            },
            {
                "author": "user1",
                "soap": {
                    "enriched": {"is_mashup": True},
                    "matched": {"brand": "Mama Bear", "scent": "Sample Mashup"},
                },
            },
        ]

        result = aggregate_mashup_usage_metrics(records)

        assert result["total_mashup_shaves"] == 3
        assert result["total_shaves"] == 3
        assert result["mashup_percentage"] == 100.0
        assert result["mashup_users"] == 2
