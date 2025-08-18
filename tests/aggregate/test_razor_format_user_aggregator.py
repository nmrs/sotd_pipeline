#!/usr/bin/env python3
"""Tests for RazorFormatUserAggregator."""

from sotd.aggregate.aggregators.users.razor_format_user_aggregator import (
    RazorFormatUserAggregator,
    aggregate_razor_format_users,
)


class TestRazorFormatUserAggregator:
    """Test RazorFormatUserAggregator functionality."""

    def test_extract_data_with_format_info(self):
        """Test data extraction with razor format information."""
        records = [
            {
                "author": "user1",
                "razor": {
                    "matched": {"format": "DE"},
                },
            },
            {
                "author": "user2",
                "razor": {
                    "matched": {"format": "Straight"},
                },
            },
        ]

        aggregator = RazorFormatUserAggregator()
        extracted = aggregator._extract_data(records)

        assert len(extracted) == 2
        assert extracted[0]["format"] == "DE"
        assert extracted[0]["author"] == "user1"
        assert extracted[1]["format"] == "Straight"
        assert extracted[1]["author"] == "user2"

    def test_extract_data_skips_records_without_format(self):
        """Test that records without format are skipped."""
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
                    "matched": {"format": "DE", "brand": "Merkur"},
                },
            },
        ]

        aggregator = RazorFormatUserAggregator()
        extracted = aggregator._extract_data(records)

        assert len(extracted) == 1
        assert extracted[0]["format"] == "DE"
        assert extracted[0]["author"] == "user2"

    def test_extract_data_skips_records_without_author(self):
        """Test that records without author are skipped."""
        records = [
            {
                "razor": {
                    "matched": {"format": "DE"},
                },
            },
            {
                "author": "user2",
                "razor": {
                    "matched": {"format": "Straight"},
                },
            },
        ]

        aggregator = RazorFormatUserAggregator()
        extracted = aggregator._extract_data(records)

        assert len(extracted) == 1
        assert extracted[0]["format"] == "Straight"
        assert extracted[0]["author"] == "user2"

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
                    "matched": {"format": "DE"},
                },
            },
        ]

        aggregator = RazorFormatUserAggregator()
        extracted = aggregator._extract_data(records)

        assert len(extracted) == 1
        assert extracted[0]["format"] == "DE"
        assert extracted[0]["author"] == "user2"

    def test_group_and_aggregate_by_format_and_user(self):
        """Test grouping by format and user."""
        aggregator = RazorFormatUserAggregator()

        import pandas as pd

        df = pd.DataFrame(
            {
                "format": ["DE", "DE", "Straight", "Straight"],
                "author": ["user1", "user2", "user1", "user3"],
            }
        )

        grouped = aggregator._group_and_aggregate(df)

        assert len(grouped) == 4
        assert grouped.iloc[0]["format"] == "DE"
        assert grouped.iloc[0]["author"] == "user1"
        assert grouped.iloc[0]["shaves"] == 1
        assert grouped.iloc[1]["format"] == "DE"
        assert grouped.iloc[1]["author"] == "user2"
        assert grouped.iloc[1]["shaves"] == 1

    def test_sort_and_rank_with_multiple_formats(self):
        """Test sorting and ranking with multiple formats."""
        aggregator = RazorFormatUserAggregator()

        import pandas as pd

        df = pd.DataFrame(
            {
                "format": ["DE", "DE", "Straight", "Straight", "GEM"],
                "author": ["user1", "user2", "user1", "user3", "user4"],
                "shaves": [5, 3, 8, 2, 1],
                "unique_users": [1, 1, 1, 1, 1],
            }
        )

        result = aggregator._sort_and_rank(df)

        assert len(result) == 5

        # Check DE format (alphabetically first)
        assert result[0]["format"] == "DE"
        assert result[0]["position"] == 1
        assert result[0]["user"] == "user1"
        assert result[0]["shaves"] == 5

        assert result[1]["format"] == "DE"
        assert result[1]["position"] == 2
        assert result[1]["user"] == "user2"
        assert result[1]["shaves"] == 3

        # Check GEM format
        assert result[2]["format"] == "GEM"
        assert result[2]["position"] == 1
        assert result[2]["user"] == "user4"
        assert result[2]["shaves"] == 1

        # Check Straight format
        assert result[3]["format"] == "Straight"
        assert result[3]["position"] == 1
        assert result[3]["user"] == "user1"
        assert result[3]["shaves"] == 8

        assert result[4]["format"] == "Straight"
        assert result[4]["position"] == 2
        assert result[4]["user"] == "user3"
        assert result[4]["shaves"] == 2

    def test_aggregate_razor_format_users(self):
        """Test complete aggregation of razor format usage data."""
        records = [
            {
                "author": "user1",
                "razor": {
                    "matched": {"format": "DE"},
                },
            },
            {
                "author": "user1",
                "razor": {
                    "matched": {"format": "DE"},
                },
            },
            {
                "author": "user1",
                "razor": {
                    "matched": {"format": "Straight"},
                },
            },
            {
                "author": "user2",
                "razor": {
                    "matched": {"format": "DE"},
                },
            },
            {
                "author": "user3",
                "razor": {
                    "matched": {"format": "Straight"},
                },
            },
        ]

        result = aggregate_razor_format_users(records)

        assert len(result) == 4

        # Check DE format (alphabetically first)
        assert result[0]["format"] == "DE"
        assert result[0]["position"] == 1
        assert result[0]["user"] == "user1"
        assert result[0]["shaves"] == 2
        assert result[0]["unique_users"] == 1

        assert result[1]["format"] == "DE"
        assert result[1]["position"] == 2
        assert result[1]["user"] == "user2"
        assert result[1]["shaves"] == 1
        assert result[1]["unique_users"] == 1

        # Check Straight format
        assert result[2]["format"] == "Straight"
        assert result[2]["position"] == 1
        assert result[2]["user"] == "user1"
        assert result[2]["shaves"] == 1
        assert result[2]["unique_users"] == 1

        assert result[3]["format"] == "Straight"
        assert result[3]["position"] == 2
        assert result[3]["user"] == "user3"
        assert result[3]["shaves"] == 1
        assert result[3]["unique_users"] == 1

    def test_aggregate_empty_records(self):
        """Test aggregation with empty records."""
        result = aggregate_razor_format_users([])
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

        result = aggregate_razor_format_users(records)
        assert result == []

    def test_aggregate_single_format_multiple_users(self):
        """Test aggregation for single format with multiple users."""
        records = [
            {
                "author": "user1",
                "razor": {
                    "matched": {"format": "DE"},
                },
            },
            {
                "author": "user2",
                "razor": {
                    "matched": {"format": "DE"},
                },
            },
            {
                "author": "user3",
                "razor": {
                    "matched": {"format": "DE"},
                },
            },
        ]

        result = aggregate_razor_format_users(records)

        assert len(result) == 3
        assert result[0]["format"] == "DE"
        assert result[0]["position"] == 1
        assert result[0]["user"] == "user1"
        assert result[0]["shaves"] == 1
        assert result[1]["format"] == "DE"
        assert result[1]["position"] == 2
        assert result[1]["user"] == "user2"
        assert result[1]["shaves"] == 1
        assert result[2]["format"] == "DE"
        assert result[2]["position"] == 3
        assert result[2]["user"] == "user3"
        assert result[2]["shaves"] == 1

    def test_aggregate_same_user_same_format_multiple_shaves(self):
        """Test aggregation for same user using same format multiple times."""
        records = [
            {
                "author": "user1",
                "razor": {
                    "matched": {"format": "DE"},
                },
            },
            {
                "author": "user1",
                "razor": {
                    "matched": {"format": "DE"},
                },
            },
            {
                "author": "user1",
                "razor": {
                    "matched": {"format": "DE"},
                },
            },
        ]

        result = aggregate_razor_format_users(records)

        assert len(result) == 1
        assert result[0]["format"] == "DE"
        assert result[0]["position"] == 1
        assert result[0]["user"] == "user1"
        assert result[0]["shaves"] == 3
        assert result[0]["unique_users"] == 1
