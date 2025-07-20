"""Tests for brush specialized aggregators."""

from sotd.aggregate.aggregators.brush_specialized import (
    aggregate_handle_makers,
    aggregate_knot_makers,
    aggregate_fibers,
    aggregate_knot_sizes,
)


def test_aggregate_handle_makers():
    records = [
        {"author": "user1", "brush": {"matched": {"handle": {"brand": "Semogue"}}}},
        {"author": "user2", "brush": {"matched": {"handle": {"brand": "Semogue"}}}},
        {"author": "user1", "brush": {"matched": {"handle": {"brand": "AP Shave Co"}}}},
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
        {"author": "user1", "brush": {"matched": {"knot": {"brand": "Declaration Grooming"}}}},
        {"author": "user2", "brush": {"matched": {"knot": {"brand": "Declaration Grooming"}}}},
        {"author": "user1", "brush": {"matched": {"knot": {"brand": "Semogue"}}}},
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
        {"author": "user1", "brush": {"matched": {"knot": {"fiber": "Synthetic"}}}},
        {"author": "user2", "brush": {"matched": {"knot": {"fiber": "Synthetic"}}}},
        {"author": "user1", "brush": {"matched": {"knot": {"fiber": "Boar"}}}},
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
        {"author": "user1", "brush": {"matched": {"knot": {"knot_size_mm": 24}}}},
        {"author": "user2", "brush": {"matched": {"knot": {"knot_size_mm": 24}}}},
        {"author": "user1", "brush": {"matched": {"knot": {"knot_size_mm": 26}}}},
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


def test_aggregate_knot_makers_skips_custom_knots():
    """Test that custom knots are skipped in knot maker aggregation."""
    records = [
        {
            "author": "user1",
            "brush": {
                "matched": {
                    "knot": {
                        "brand": "Simpson",
                        "model": "Chubby 2",
                        "fiber": "Badger",
                        "knot_size_mm": 27.0,
                    }
                },
                "enriched": {
                    "_custom_knot": True,
                    "_custom_knot_reason": ["fiber_mismatch:Badger->Boar"],
                    "fiber": "Boar",
                    "knot_size_mm": 28.0,
                },
            },
        },
        {
            "author": "user2",
            "brush": {
                "matched": {
                    "knot": {
                        "brand": "Simpson",
                        "model": "Chubby 2",
                        "fiber": "Badger",
                        "knot_size_mm": 27.0,
                    }
                },
                "enriched": {
                    "_custom_knot": False,  # Factory knot
                    "fiber": "Badger",
                    "knot_size_mm": 27.0,
                },
            },
        },
        {
            "author": "user3",
            "brush": {
                "matched": {
                    "knot": {
                        "brand": "Declaration Grooming",
                        "model": "B15",
                        "fiber": "Badger",
                        "knot_size_mm": 28.0,
                    }
                },
                "enriched": {
                    "_custom_knot": False,  # Factory knot
                    "fiber": "Badger",
                    "knot_size_mm": 28.0,
                },
            },
        },
    ]

    result = aggregate_knot_makers(records)

    # Should only include factory knots, skip custom knots
    assert len(result) == 2

    # Check that Simpson and Declaration Grooming are included
    brands = [item["brand"] for item in result]
    assert "Simpson" in brands
    assert "Declaration Grooming" in brands

    # Check that custom knot (user1) is not counted
    simpson_item = next(item for item in result if item["brand"] == "Simpson")
    assert simpson_item["shaves"] == 1  # Only user2's factory Simpson
    assert simpson_item["unique_users"] == 1  # Only user2
