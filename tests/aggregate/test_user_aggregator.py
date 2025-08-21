#!/usr/bin/env python3
"""Tests for user aggregation."""

from sotd.aggregate.aggregators.users.user_aggregator import aggregate_users


class TestUserAggregator:
    """Test user aggregation functionality."""

    def test_aggregate_users_basic(self):
        """Test basic user aggregation."""
        records = [
            {
                "author": "user1",
                "thread_title": "Wednesday SOTD Thread - Jan 01, 2025",
            },
            {
                "author": "user1",
                "thread_title": "Thursday SOTD Thread - Jan 02, 2025",
            },
            {
                "author": "user2",
                "thread_title": "Friday SOTD Thread - Jan 03, 2025",
            },
        ]

        result = aggregate_users(records)

        assert len(result) == 2
        assert result[0]["user"] == "user1"
        assert result[0]["shaves"] == 2
        assert result[0]["rank"] == 1
        assert result[1]["user"] == "user2"
        assert result[1]["shaves"] == 1
        assert result[1]["rank"] == 2

    def test_aggregate_users_competition_ranking(self):
        """Test that competition ranking correctly handles ties based on shaves and missed_days."""
        records = [
            # User1: 3 shaves, 28 missed days (rank 1)
            {
                "author": "user1",
                "thread_title": "Wednesday SOTD Thread - Mar 01, 2025",
            },
            {
                "author": "user1",
                "thread_title": "Thursday SOTD Thread - Mar 02, 2025",
            },
            {
                "author": "user1",
                "thread_title": "Friday SOTD Thread - Mar 03, 2025",
            },
            # User2: 3 shaves, 29 missed days (rank 3 - posted twice on same day)
            {
                "author": "user2",
                "thread_title": "Wednesday SOTD Thread - Mar 01, 2025",
            },
            {
                "author": "user2",
                "thread_title": "Wednesday SOTD Thread - Mar 01, 2025",  # Same day twice
            },
            {
                "author": "user2",
                "thread_title": "Thursday SOTD Thread - Mar 02, 2025",
            },
            # User3: 3 shaves, 28 missed days (rank 1 - posted on 3 different days)
            {
                "author": "user3",
                "thread_title": "Wednesday SOTD Thread - Mar 01, 2025",
            },
            {
                "author": "user3",
                "thread_title": "Thursday SOTD Thread - Mar 02, 2025",
            },
            {
                "author": "user3",
                "thread_title": "Friday SOTD Thread - Mar 03, 2025",
            },
            # User4: 2 shaves, 29 missed days (rank 4 - different shaves)
            {
                "author": "user4",
                "thread_title": "Wednesday SOTD Thread - Mar 01, 2025",
            },
            {
                "author": "user4",
                "thread_title": "Thursday SOTD Thread - Mar 02, 2025",
            },
        ]

        result = aggregate_users(records)

        # Check competition ranking: 1, 1, 3, 4 (user1, user3, user2, user4)
        # User1: 3 shaves, 28 missed days -> rank 1
        assert result[0]["rank"] == 1
        assert result[0]["user"] == "user1"
        assert result[0]["shaves"] == 3
        assert result[0]["missed_days"] == 28

        # User3: 3 shaves, 28 missed days -> rank 1 (tied with user1, alphabetically second)
        assert result[1]["rank"] == 1
        assert result[1]["user"] == "user3"
        assert result[1]["shaves"] == 3
        assert result[1]["missed_days"] == 28

        # User2: 3 shaves, 29 missed days -> rank 3 (different missed_days)
        assert result[2]["rank"] == 3
        assert result[2]["user"] == "user2"
        assert result[2]["shaves"] == 3
        assert result[2]["missed_days"] == 29

        # User4: 2 shaves, 29 missed days -> rank 4 (different shaves)
        assert result[3]["rank"] == 4
        assert result[3]["user"] == "user4"
        assert result[3]["shaves"] == 2
        assert result[3]["missed_days"] == 29

        # Verify that ranks follow competition ranking pattern
        ranks = [item["rank"] for item in result]
        assert ranks == [1, 1, 3, 4], f"Expected [1, 1, 3, 4], got {ranks}"

    def test_aggregate_users_missed_days_calculation(self):
        """Test that missed days are calculated correctly."""
        records = [
            {
                "author": "user1",
                "thread_title": "Wednesday SOTD Thread - Jan 01, 2025",
            },
            {
                "author": "user1",
                "thread_title": "Friday SOTD Thread - Jan 03, 2025",
            },
        ]

        result = aggregate_users(records)

        assert len(result) == 1
        assert result[0]["user"] == "user1"
        assert result[0]["shaves"] == 2
        # January 2025 has 31 days, so missed_days should be 29
        assert result[0]["missed_days"] == 29
        assert len(result[0]["missed_dates"]) == 29

    def test_aggregate_users_empty_records(self):
        """Test aggregation with empty records."""
        result = aggregate_users([])
        assert result == []

    def test_aggregate_users_invalid_thread_titles(self):
        """Test aggregation with invalid thread titles."""
        records = [
            {
                "author": "user1",
                "thread_title": "Invalid thread title",
            },
            {
                "author": "user2",
                "thread_title": "Another invalid title",
            },
        ]

        result = aggregate_users(records)
        assert result == []

    def test_aggregate_users_missing_fields(self):
        """Test aggregation with missing required fields."""
        records = [
            {
                "author": "user1",
                # Missing thread_title
            },
            {
                "thread_title": "Wednesday SOTD Thread - Jan 01, 2025",
                # Missing author
            },
        ]

        result = aggregate_users(records)
        assert result == []
