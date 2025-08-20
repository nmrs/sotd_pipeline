#!/usr/bin/env python3
"""Tests for metrics utility functions."""

from sotd.aggregate.utils.metrics import (
    calculate_avg_shaves_per_user,
    calculate_median_shaves_per_user,
)


class TestUserMetrics:
    """Test user-related metric calculations."""

    def test_calculate_avg_shaves_per_user_empty(self):
        """Test average calculation with empty records."""
        result = calculate_avg_shaves_per_user([])
        assert result == 0.0

    def test_calculate_avg_shaves_per_user_single_user(self):
        """Test average calculation with single user."""
        records = [
            {"author": "user1"},
            {"author": "user1"},
            {"author": "user1"},
        ]
        result = calculate_avg_shaves_per_user(records)
        assert result == 3.0

    def test_calculate_avg_shaves_per_user_multiple_users(self):
        """Test average calculation with multiple users."""
        records = [
            {"author": "user1"},
            {"author": "user1"},
            {"author": "user2"},
            {"author": "user3"},
        ]
        result = calculate_avg_shaves_per_user(records)
        assert result == 1.33  # 4 shaves / 3 users

    def test_calculate_median_shaves_per_user_empty(self):
        """Test median calculation with empty records."""
        result = calculate_median_shaves_per_user([])
        assert result == 0.0

    def test_calculate_median_shaves_per_user_single_user(self):
        """Test median calculation with single user."""
        records = [
            {"author": "user1"},
            {"author": "user1"},
            {"author": "user1"},
        ]
        result = calculate_median_shaves_per_user(records)
        assert result == 3.0

    def test_calculate_median_shaves_per_user_odd_users(self):
        """Test median calculation with odd number of users."""
        records = [
            {"author": "user1"},  # 1 shave
            {"author": "user2"},  # 1 shave
            {"author": "user3"},  # 1 shave
            {"author": "user4"},  # 2 shaves
            {"author": "user4"},
            {"author": "user5"},  # 3 shaves
            {"author": "user5"},
            {"author": "user5"},
        ]
        result = calculate_median_shaves_per_user(records)
        assert result == 1.0  # Median of [1, 1, 1, 2, 3] is 1

    def test_calculate_median_shaves_per_user_even_users(self):
        """Test median calculation with even number of users."""
        records = [
            {"author": "user1"},  # 1 shave
            {"author": "user2"},  # 1 shave
            {"author": "user3"},  # 2 shaves
            {"author": "user3"},
            {"author": "user4"},  # 3 shaves
            {"author": "user4"},
            {"author": "user4"},
        ]
        result = calculate_median_shaves_per_user(records)
        assert result == 1.5  # Median of [1, 1, 2, 3] is (1+2)/2 = 1.5

    def test_calculate_median_shaves_per_user_mixed_shaves(self):
        """Test median calculation with mixed shave counts."""
        records = [
            {"author": "user1"},  # 1 shave
            {"author": "user2"},  # 2 shaves
            {"author": "user2"},
            {"author": "user3"},  # 3 shaves
            {"author": "user3"},
            {"author": "user3"},
            {"author": "user4"},  # 4 shaves
            {"author": "user4"},
            {"author": "user4"},
            {"author": "user4"},
        ]
        result = calculate_median_shaves_per_user(records)
        assert result == 2.5  # Median of [1, 2, 3, 4] is (2+3)/2 = 2.5

    def test_calculate_median_shaves_per_user_ignores_empty_authors(self):
        """Test median calculation ignores records with empty authors."""
        records = [
            {"author": "user1"},
            {"author": ""},  # Empty author
            {"author": None},  # None author
            {"author": "user2"},
            {"author": "user2"},
        ]
        result = calculate_median_shaves_per_user(records)
        assert result == 1.5  # Median of [1, 2] is (1+2)/2 = 1.5

    def test_calculate_median_shaves_per_user_rounds_to_two_decimals(self):
        """Test median calculation rounds to two decimal places."""
        records = [
            {"author": "user1"},  # 1 shave
            {"author": "user2"},  # 2 shaves
            {"author": "user2"},
            {"author": "user3"},  # 3 shaves
            {"author": "user3"},
            {"author": "user3"},
        ]
        result = calculate_median_shaves_per_user(records)
        assert result == 2.0  # Median of [1, 2, 3] is 2.0
