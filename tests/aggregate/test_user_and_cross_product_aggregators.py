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
    assert result[0]["user"] == "user1"
    assert result[0]["shaves"] == 2
    assert result[0]["position"] == 1
    assert result[1]["user"] == "user2"
    assert result[1]["shaves"] == 1
    assert result[1]["position"] == 2


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
    assert result[0]["position"] == 1
    assert result[1]["name"] == "Gillette Tech + Personna Lab Blue"
    assert result[1]["shaves"] == 1
    assert result[1]["unique_users"] == 1
    assert result[1]["position"] == 2


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
    assert result[0]["user"] == "user1"
    assert result[0]["blade"] == "Gillette Minora"
    assert result[0]["format"] == "DE"
    assert result[0]["uses"] == 15
    assert result[0]["position"] == 1
    assert result[1]["user"] == "user2"
    assert result[1]["blade"] == "Personna Lab Blue"
    assert result[1]["format"] == "DE"
    assert result[1]["uses"] == 12
    assert result[1]["position"] == 2
