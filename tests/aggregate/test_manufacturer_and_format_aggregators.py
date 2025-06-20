"""Tests for manufacturer and format aggregators."""

from sotd.aggregate.aggregators.manufacturers import (
    aggregate_razor_manufacturers,
    aggregate_blade_manufacturers,
    aggregate_soap_makers,
)
from sotd.aggregate.aggregators.formats import aggregate_razor_formats


def test_aggregate_razor_manufacturers():
    records = [
        {"author": "user1", "razor": {"matched": {"brand": "Gillette"}}},
        {"author": "user2", "razor": {"matched": {"brand": "Gillette"}}},
        {"author": "user1", "razor": {"matched": {"brand": "Fatip"}}},
    ]
    result = aggregate_razor_manufacturers(records)
    assert len(result) == 2
    assert result[0]["brand"] == "Gillette"
    assert result[0]["shaves"] == 2
    assert result[0]["unique_users"] == 2
    assert result[0]["position"] == 1
    assert result[1]["brand"] == "Fatip"
    assert result[1]["shaves"] == 1
    assert result[1]["unique_users"] == 1
    assert result[1]["position"] == 2


def test_aggregate_blade_manufacturers():
    records = [
        {"author": "user1", "blade": {"matched": {"brand": "Gillette"}}},
        {"author": "user2", "blade": {"matched": {"brand": "Gillette"}}},
        {"author": "user1", "blade": {"matched": {"brand": "Personna"}}},
    ]
    result = aggregate_blade_manufacturers(records)
    assert len(result) == 2
    assert result[0]["brand"] == "Gillette"
    assert result[0]["shaves"] == 2
    assert result[0]["unique_users"] == 2
    assert result[0]["position"] == 1
    assert result[1]["brand"] == "Personna"
    assert result[1]["shaves"] == 1
    assert result[1]["unique_users"] == 1
    assert result[1]["position"] == 2


def test_aggregate_soap_makers():
    records = [
        {"author": "user1", "soap": {"matched": {"maker": "Grooming Dept"}}},
        {"author": "user2", "soap": {"matched": {"maker": "Grooming Dept"}}},
        {"author": "user1", "soap": {"matched": {"maker": "Declaration Grooming"}}},
    ]
    result = aggregate_soap_makers(records)
    assert len(result) == 2
    assert result[0]["maker"] == "Grooming Dept"
    assert result[0]["shaves"] == 2
    assert result[0]["unique_users"] == 2
    assert result[0]["position"] == 1
    assert result[1]["maker"] == "Declaration Grooming"
    assert result[1]["shaves"] == 1
    assert result[1]["unique_users"] == 1
    assert result[1]["position"] == 2


def test_aggregate_razor_formats():
    records = [
        {"author": "user1", "razor": {"matched": {"format": "DE"}}},
        {"author": "user2", "razor": {"matched": {"format": "DE"}}},
        {"author": "user1", "razor": {"matched": {"format": "Straight"}}},
    ]
    result = aggregate_razor_formats(records)
    assert len(result) == 2
    assert result[0]["format"] == "DE"
    assert result[0]["shaves"] == 2
    assert result[0]["unique_users"] == 2
    assert result[0]["position"] == 1
    assert result[1]["format"] == "Straight"
    assert result[1]["shaves"] == 1
    assert result[1]["unique_users"] == 1
    assert result[1]["position"] == 2
