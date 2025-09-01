"""Tests for razor specialized aggregators."""

from sotd.aggregate.aggregators.razor_specialized import (
    aggregate_blackbird_plates,
    aggregate_christopher_bradley_plates,
    aggregate_game_changer_plates,
    aggregate_super_speed_tips,
    aggregate_straight_widths,
    aggregate_straight_grinds,
    aggregate_straight_points,
)


def test_aggregate_blackbird_plates():
    records = [
        {
            "author": "user1",
            "razor": {
                "matched": {"brand": "Blackland", "model": "Blackbird"},
                "enriched": {"plate": "Standard"},
            },
        },
        {
            "author": "user2",
            "razor": {
                "matched": {"brand": "Blackland", "model": "Blackbird"},
                "enriched": {"plate": "Standard"},
            },
        },
        {
            "author": "user1",
            "razor": {
                "matched": {"brand": "Blackland", "model": "Blackbird"},
                "enriched": {"plate": "Lite"},
            },
        },
    ]
    result = aggregate_blackbird_plates(records)
    assert len(result) == 2
    assert result[0]["plate"] == "Standard"
    assert result[0]["shaves"] == 2
    assert result[0]["unique_users"] == 2
    assert result[0]["rank"] == 1
    assert result[1]["plate"] == "Lite"
    assert result[1]["shaves"] == 1
    assert result[1]["unique_users"] == 1
    assert result[1]["rank"] == 2


def test_aggregate_christopher_bradley_plates():
    records = [
        {"author": "user1", "razor": {"enriched": {"plate_type": "SB", "plate_level": "C"}}},
        {"author": "user2", "razor": {"enriched": {"plate_type": "SB", "plate_level": "C"}}},
        {"author": "user1", "razor": {"enriched": {"plate_type": "SB", "plate_level": "D"}}},
    ]
    result = aggregate_christopher_bradley_plates(records)
    assert len(result) == 2
    assert result[0]["plate"] == "SB-C"
    assert result[0]["shaves"] == 2
    assert result[0]["unique_users"] == 2
    assert result[0]["rank"] == 1
    assert result[1]["plate"] == "SB-D"
    assert result[1]["shaves"] == 1
    assert result[1]["unique_users"] == 1
    assert result[1]["rank"] == 2


def test_aggregate_game_changer_plates():
    records = [
        {"author": "user1", "razor": {"enriched": {"gap": "1.05"}}},
        {"author": "user2", "razor": {"enriched": {"gap": "1.05"}}},
        {"author": "user1", "razor": {"enriched": {"gap": ".84"}}},
    ]
    result = aggregate_game_changer_plates(records)
    assert len(result) == 2
    assert result[0]["gap"] == "1.05"
    assert result[0]["shaves"] == 2
    assert result[0]["unique_users"] == 2
    assert result[0]["rank"] == 1
    assert result[1]["gap"] == ".84"
    assert result[1]["shaves"] == 1
    assert result[1]["unique_users"] == 1
    assert result[1]["rank"] == 2


def test_aggregate_super_speed_tips():
    records = [
        {"author": "user1", "razor": {"enriched": {"super_speed_tip": "Flare"}}},
        {"author": "user2", "razor": {"enriched": {"super_speed_tip": "Flare"}}},
        {"author": "user1", "razor": {"enriched": {"super_speed_tip": "Black"}}},
    ]
    result = aggregate_super_speed_tips(records)
    assert len(result) == 2
    assert result[0]["super_speed_tip"] == "Flare"
    assert result[0]["shaves"] == 2
    assert result[0]["unique_users"] == 2
    assert result[0]["rank"] == 1
    assert result[1]["super_speed_tip"] == "Black"
    assert result[1]["shaves"] == 1
    assert result[1]["unique_users"] == 1
    assert result[1]["rank"] == 2


def test_aggregate_straight_widths():
    records = [
        {"author": "user1", "razor": {"enriched": {"width": "6/8"}}},
        {"author": "user2", "razor": {"enriched": {"width": "6/8"}}},
        {"author": "user1", "razor": {"enriched": {"width": "5/8"}}},
    ]
    result = aggregate_straight_widths(records)
    assert len(result) == 2
    assert result[0]["width"] == "6/8"
    assert result[0]["shaves"] == 2
    assert result[0]["unique_users"] == 2
    assert result[0]["rank"] == 1
    assert result[1]["width"] == "5/8"
    assert result[1]["shaves"] == 1
    assert result[1]["unique_users"] == 1
    assert result[1]["rank"] == 2


def test_aggregate_straight_grinds():
    records = [
        {"author": "user1", "razor": {"enriched": {"grind": "Full Hollow"}}},
        {"author": "user2", "razor": {"enriched": {"grind": "Full Hollow"}}},
        {"author": "user1", "razor": {"enriched": {"grind": "Hollow"}}},
    ]
    result = aggregate_straight_grinds(records)
    assert len(result) == 2
    assert result[0]["grind"] == "Full Hollow"
    assert result[0]["shaves"] == 2
    assert result[0]["unique_users"] == 2
    assert result[0]["rank"] == 1
    assert result[1]["grind"] == "Hollow"
    assert result[1]["shaves"] == 1
    assert result[1]["unique_users"] == 1
    assert result[1]["rank"] == 2


def test_aggregate_straight_points():
    records = [
        {"author": "user1", "razor": {"enriched": {"point": "Round"}}},
        {"author": "user2", "razor": {"enriched": {"point": "Round"}}},
        {"author": "user1", "razor": {"enriched": {"point": "Barber's Notch"}}},
    ]
    result = aggregate_straight_points(records)
    assert len(result) == 2
    assert result[0]["point"] == "Round"
    assert result[0]["shaves"] == 2
    assert result[0]["unique_users"] == 2
    assert result[0]["rank"] == 1
    assert result[1]["point"] == "Barber's Notch"
    assert result[1]["shaves"] == 1
    assert result[1]["unique_users"] == 1
    assert result[1]["rank"] == 2
