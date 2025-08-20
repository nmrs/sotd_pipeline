"""Tests for blade usage distribution aggregator."""

from sotd.aggregate.aggregators.core.blade_usage_distribution_aggregator import (
    aggregate_blade_usage_distribution,
)


class TestBladeUsageDistributionAggregator:
    """Test cases for the blade usage distribution aggregator."""

    def test_empty_records(self):
        """Test with empty records."""
        result = aggregate_blade_usage_distribution([])
        assert result == []

    def test_no_blade_records(self):
        """Test with records that don't have blade data."""
        records = [
            {"author": "user1", "razor": {"matched": {"brand": "Gillette"}}},
            {"author": "user2", "soap": {"matched": {"maker": "B&M"}}},
        ]
        result = aggregate_blade_usage_distribution(records)
        assert result == []

    def test_basic_blade_usage_distribution(self):
        """Test basic blade usage distribution aggregation."""
        records = [
            {
                "author": "user1",
                "blade": {
                    "matched": {"brand": "Feather", "model": "Hi-Stainless"},
                    "enriched": {"use_count": 1},
                },
            },
            {
                "author": "user2",
                "blade": {
                    "matched": {"brand": "Astra", "model": "SP"},
                    "enriched": {"use_count": 2},
                },
            },
            {
                "author": "user3",
                "blade": {
                    "matched": {"brand": "Feather", "model": "Hi-Stainless"},
                    "enriched": {"use_count": 3},
                },
            },
            {
                "author": "user4",
                "blade": {
                    "matched": {"brand": "Astra", "model": "SP"},
                    "enriched": {"use_count": 1},
                },
            },
        ]
        result = aggregate_blade_usage_distribution(records)

        # Should have 3 usage levels: 1, 2, 3
        assert len(result) == 3

        # Check first usage level (1 use)
        level_1 = result[0]
        assert level_1["use_count"] == 1
        assert level_1["shaves"] == 2  # user1 and user4
        assert level_1["unique_users"] == 2
        assert level_1["position"] == 1

        # Check second usage level (2 uses)
        level_2 = result[1]
        assert level_2["use_count"] == 2
        assert level_2["shaves"] == 1  # user2
        assert level_2["unique_users"] == 1
        assert level_2["position"] == 2

        # Check third usage level (3 uses)
        level_3 = result[2]
        assert level_3["use_count"] == 3
        assert level_3["shaves"] == 1  # user3
        assert level_3["unique_users"] == 1
        assert level_3["position"] == 3

    def test_missing_enriched_data_defaults_to_one(self):
        """Test that missing enriched data defaults to use_count of 1."""
        records = [
            {
                "author": "user1",
                "blade": {
                    "matched": {"brand": "Feather", "model": "Hi-Stainless"},
                    # No enriched data
                },
            },
            {
                "author": "user2",
                "blade": {
                    "matched": {"brand": "Astra", "model": "SP"},
                    "enriched": {"use_count": 2},
                },
            },
        ]
        result = aggregate_blade_usage_distribution(records)

        assert len(result) == 2

        # Level 1 (default)
        level_1 = result[0]
        assert level_1["use_count"] == 1
        assert level_1["shaves"] == 1
        assert level_1["unique_users"] == 1

        # Level 2
        level_2 = result[1]
        assert level_2["use_count"] == 2
        assert level_2["shaves"] == 1
        assert level_2["unique_users"] == 1

    def test_legacy_blade_enriched_format(self):
        """Test compatibility with legacy blade_enriched format."""
        records = [
            {
                "author": "user1",
                "blade": {"matched": {"brand": "Feather", "model": "Hi-Stainless"}},
                "blade_enriched": {"use_count": 3},  # Legacy format
            },
        ]
        result = aggregate_blade_usage_distribution(records)

        assert len(result) == 1
        level_3 = result[0]
        assert level_3["use_count"] == 3
        assert level_3["shaves"] == 1
        assert level_3["unique_users"] == 1

    def test_invalid_use_count_handling(self):
        """Test handling of invalid use_count values."""
        records = [
            {
                "author": "user1",
                "blade": {
                    "matched": {"brand": "Feather", "model": "Hi-Stainless"},
                    "enriched": {"use_count": "invalid"},
                },
            },
            {
                "author": "user2",
                "blade": {
                    "matched": {"brand": "Astra", "model": "SP"},
                    "enriched": {"use_count": 2},
                },
            },
        ]
        result = aggregate_blade_usage_distribution(records)

        # Should handle invalid data gracefully
        assert len(result) == 2

        # Level 1 (default for invalid)
        level_1 = result[0]
        assert level_1["use_count"] == 1
        assert level_1["shaves"] == 1

        # Level 2
        level_2 = result[1]
        assert level_2["use_count"] == 2
        assert level_2["shaves"] == 1
