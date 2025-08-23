"""Tests for user and cross-product aggregators."""

from sotd.aggregate.aggregators.users import aggregate_users
from sotd.aggregate.aggregators.cross_product import (
    aggregate_razor_blade_combos,
    aggregate_highest_use_count_per_blade,
)


def test_aggregate_users():
    records = [
        {"author": "user1", "thread_title": "SOTD Thread - Jan 01, 2025"},
        {"author": "user2", "thread_title": "SOTD Thread - Jan 01, 2025"},
        {"author": "user1", "thread_title": "SOTD Thread - Jan 02, 2025"},
    ]
    # For simplicity, missed_days is not calculated here (would require more context)
    result = aggregate_users(records)
    assert len(result) == 2
    assert result[0]["user"] == "u/user1"
    assert result[0]["shaves"] == 2
    assert result[0]["rank"] == 1
    assert result[1]["user"] == "u/user2"
    assert result[1]["shaves"] == 1
    assert result[1]["rank"] == 2


def test_aggregate_razor_blade_combos():
    records = [
        {
            "author": "user1",
            "razor": {"matched": {"brand": "Fatip", "model": "Grande"}},
            "blade": {"matched": {"brand": "Gillette", "model": "Minora"}},
        },
        {
            "author": "user2",
            "razor": {"matched": {"brand": "Fatip", "model": "Grande"}},
            "blade": {"matched": {"brand": "Gillette", "model": "Minora"}},
        },
        {
            "author": "user1",
            "razor": {"matched": {"brand": "Gillette", "model": "Tech"}},
            "blade": {"matched": {"brand": "Personna", "model": "Lab Blue"}},
        },
    ]
    result = aggregate_razor_blade_combos(records)
    assert len(result) == 2
    assert result[0]["name"] == "Fatip Grande + Gillette Minora"
    assert result[0]["shaves"] == 2
    assert result[0]["unique_users"] == 2
    assert result[0]["rank"] == 1
    assert result[1]["name"] == "Gillette Tech + Personna Lab Blue"
    assert result[1]["shaves"] == 1
    assert result[1]["unique_users"] == 1
    assert result[1]["rank"] == 2


def test_aggregate_highest_use_count_per_blade():
    records = [
        {
            "author": "user1",
            "blade": {"matched": {"brand": "Gillette", "model": "Minora", "format": "DE"}},
            "blade_enriched": {"use_count": 15},
        },
        {
            "author": "user2",
            "blade": {"matched": {"brand": "Personna", "model": "Lab Blue", "format": "DE"}},
            "blade_enriched": {"use_count": 12},
        },
    ]
    # The actual aggregator may expect blade.enriched.use_count, so adapt as needed
    # Here we provide both blade.matched and blade_enriched for test flexibility
    # The output fields per spec: user, blade, format, uses, position
    result = aggregate_highest_use_count_per_blade(records)
    assert len(result) == 2
    assert result[0]["user"] == "u/user1"
    assert result[0]["blade"] == "Gillette Minora"
    assert result[0]["format"] == "DE"
    assert result[0]["uses"] == 15
    assert result[0]["rank"] == 1
    assert result[1]["user"] == "u/user2"
    assert result[1]["blade"] == "Personna Lab Blue"
    assert result[1]["format"] == "DE"
    assert result[1]["uses"] == 12
    assert result[1]["rank"] == 2


def test_aggregate_highest_use_count_per_blade_multiple_users_same_blade():
    """Test that when multiple users have the same blade, the user with highest use count
    is correctly attributed."""
    records = [
        {
            "author": "AdWorried2804",  # Alphabetically first
            "blade": {
                "matched": {"brand": "Gillette", "model": "Platinum", "format": "DE"},
                "enriched": {"use_count": 7},
            },
        },
        {
            "author": "B_S80",  # Alphabetically second, but has higher use count
            "blade": {
                "matched": {"brand": "Gillette", "model": "Platinum", "format": "DE"},
                "enriched": {"use_count": 275},
            },
        },
        {
            "author": "user3",
            "blade": {
                "matched": {"brand": "Personna", "model": "Lab Blue", "format": "DE"},
                "enriched": {"use_count": 50},
            },
        },
    ]

    result = aggregate_highest_use_count_per_blade(records)

    # Should have 2 unique blades
    assert len(result) == 2

    # Gillette Platinum should be first (highest use count: 275)
    gillette_platinum = next(item for item in result if item["blade"] == "Gillette Platinum")
    assert gillette_platinum["uses"] == 275
    # BUG: This should be "B_S80" but currently returns "AdWorried2804"
    # due to alphabetical ordering
    expected_user = "u/B_S80"
    actual_user = gillette_platinum["user"]
    assert (
        actual_user == expected_user
    ), f"Expected user '{expected_user}' but got '{actual_user}' - this exposes the bug!"

    # Personna Lab Blue should be second
    personna_lab_blue = next(item for item in result if item["blade"] == "Personna Lab Blue")
    assert personna_lab_blue["uses"] == 50
    assert personna_lab_blue["user"] == "u/user3"
