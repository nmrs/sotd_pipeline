"""Tests for brush specialized aggregators."""

from sotd.aggregate.aggregators.brush_specialized import (
    aggregate_handle_makers,
    aggregate_knot_makers,
    aggregate_fibers,
    aggregate_knot_sizes,
)


def test_aggregate_handle_makers():
    records = [
        {"author": "user1", "brush": {"matched": {"handle_maker": "Semogue"}}},
        {"author": "user2", "brush": {"matched": {"handle_maker": "Semogue"}}},
        {"author": "user1", "brush": {"matched": {"handle_maker": "AP Shave Co"}}},
    ]
    result = aggregate_handle_makers(records)
    assert len(result) == 2
    assert result[0]["handle_maker"] == "Semogue"
    assert result[0]["shaves"] == 2
    assert result[0]["unique_users"] == 2
    assert result[0]["position"] == 1
    assert result[1]["handle_maker"] == "AP Shave Co"
    assert result[1]["shaves"] == 1
    assert result[1]["unique_users"] == 1
    assert result[1]["position"] == 2


def test_aggregate_knot_makers():
    records = [
        {"author": "user1", "brush": {"matched": {"knot_maker": "Declaration Grooming"}}},
        {"author": "user2", "brush": {"matched": {"knot_maker": "Declaration Grooming"}}},
        {"author": "user1", "brush": {"matched": {"knot_maker": "Semogue"}}},
    ]
    result = aggregate_knot_makers(records)
    assert len(result) == 2
    assert result[0]["brand"] == "Declaration Grooming"
    assert result[0]["shaves"] == 2
    assert result[0]["unique_users"] == 2
    assert result[0]["position"] == 1
    assert result[1]["brand"] == "Semogue"
    assert result[1]["shaves"] == 1
    assert result[1]["unique_users"] == 1
    assert result[1]["position"] == 2


def test_aggregate_fibers():
    records = [
        {"author": "user1", "brush": {"matched": {"fiber": "Synthetic"}}},
        {"author": "user2", "brush": {"matched": {"fiber": "Synthetic"}}},
        {"author": "user1", "brush": {"matched": {"fiber": "Boar"}}},
    ]
    result = aggregate_fibers(records)
    assert len(result) == 2
    assert result[0]["fiber"] == "Synthetic"
    assert result[0]["shaves"] == 2
    assert result[0]["unique_users"] == 2
    assert result[0]["position"] == 1
    assert result[1]["fiber"] == "Boar"
    assert result[1]["shaves"] == 1
    assert result[1]["unique_users"] == 1
    assert result[1]["position"] == 2


def test_aggregate_knot_sizes():
    records = [
        {"author": "user1", "brush": {"matched": {"knot_size_mm": 24}}},
        {"author": "user2", "brush": {"matched": {"knot_size_mm": 24}}},
        {"author": "user1", "brush": {"matched": {"knot_size_mm": 26}}},
    ]
    result = aggregate_knot_sizes(records)
    assert len(result) == 2
    assert result[0]["knot_size_mm"] == 24
    assert result[0]["shaves"] == 2
    assert result[0]["unique_users"] == 2
    assert result[0]["position"] == 1
    assert result[1]["knot_size_mm"] == 26
    assert result[1]["shaves"] == 1
    assert result[1]["unique_users"] == 1
    assert result[1]["position"] == 2
