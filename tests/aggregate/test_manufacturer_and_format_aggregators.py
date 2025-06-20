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


def test_aggregate_razor_formats_basic():
    """Test basic razor format aggregation."""
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


def test_aggregate_razor_formats_shavette_ac():
    """Test shavette with AC blade format combination."""
    records = [
        {
            "author": "user1",
            "razor": {"matched": {"format": "Shavette"}},
            "blade": {"matched": {"format": "AC"}},
        },
        {
            "author": "user2",
            "razor": {"matched": {"format": "Shavette"}},
            "blade": {"matched": {"format": "AC"}},
        },
    ]
    result = aggregate_razor_formats(records)
    assert len(result) == 1
    assert result[0]["format"] == "Shavette (AC)"
    assert result[0]["shaves"] == 2
    assert result[0]["unique_users"] == 2


def test_aggregate_razor_formats_shavette_de():
    """Test shavette with DE blade format (should become Half DE)."""
    records = [
        {
            "author": "user1",
            "razor": {"matched": {"format": "Shavette"}},
            "blade": {"matched": {"format": "DE"}},
        },
    ]
    result = aggregate_razor_formats(records)
    assert len(result) == 1
    assert result[0]["format"] == "Shavette (Half DE)"
    assert result[0]["shaves"] == 1


def test_aggregate_razor_formats_shavette_unspecified():
    """Test shavette with no blade format."""
    records = [
        {
            "author": "user1",
            "razor": {"matched": {"format": "Shavette"}},
            "blade": {"matched": {}},  # No format
        },
    ]
    result = aggregate_razor_formats(records)
    assert len(result) == 1
    assert result[0]["format"] == "Shavette (Unspecified)"
    assert result[0]["shaves"] == 1


def test_aggregate_razor_formats_shavette_predefined():
    """Test shavette with predefined format (should use as-is)."""
    records = [
        {
            "author": "user1",
            "razor": {"matched": {"format": "Shavette (AC)"}},
            "blade": {"matched": {"format": "DE"}},  # Should be ignored
        },
    ]
    result = aggregate_razor_formats(records)
    assert len(result) == 1
    assert result[0]["format"] == "Shavette (AC)"
    assert result[0]["shaves"] == 1


def test_aggregate_razor_formats_half_de_detection():
    """Test Half DE detection logic."""
    records = [
        {
            "author": "user1",
            "razor": {"matched": {"format": "Half DE (multi-blade)"}},
            "blade": {"matched": {"format": "DE"}},
        },
        {
            "author": "user2",
            "razor": {"matched": {"format": "Half DE"}},
            "blade": {"matched": {"format": "DE"}},
        },
    ]
    result = aggregate_razor_formats(records)
    assert len(result) == 2
    formats = {r["format"] for r in result}
    assert "Half DE (multi-blade)" in formats
    assert "Half DE" in formats


def test_aggregate_razor_formats_blade_format_fallback():
    """Test blade format fallback when no razor format."""
    records = [
        {
            "author": "user1",
            "razor": {"matched": {}},  # No format
            "blade": {"matched": {"format": "GEM"}},
        },
    ]
    result = aggregate_razor_formats(records)
    assert len(result) == 1
    assert result[0]["format"] == "GEM"
    assert result[0]["shaves"] == 1


def test_aggregate_razor_formats_default_de():
    """Test default to DE when no formats available."""
    records = [
        {
            "author": "user1",
            "razor": {"matched": {}},  # No format
            "blade": {"matched": {}},  # No format
        },
    ]
    result = aggregate_razor_formats(records)
    assert len(result) == 1
    assert result[0]["format"] == "DE"
    assert result[0]["shaves"] == 1


def test_aggregate_razor_formats_no_razor_match():
    """Test handling when no razor match exists."""
    records = [
        {
            "author": "user1",
            "razor": {"original": "Unknown Razor", "matched": None},
            "blade": {"matched": {"format": "DE"}},
        },
    ]
    result = aggregate_razor_formats(records)
    assert len(result) == 0  # Should skip records with no razor match


def test_aggregate_razor_formats_complex_scenario():
    """Test complex scenario with multiple format types."""
    records = [
        # Regular DE razor
        {"author": "user1", "razor": {"matched": {"format": "DE"}}},
        # Shavette with AC blade
        {
            "author": "user2",
            "razor": {"matched": {"format": "Shavette"}},
            "blade": {"matched": {"format": "AC"}},
        },
        # Shavette with DE blade (should become Half DE)
        {
            "author": "user3",
            "razor": {"matched": {"format": "Shavette"}},
            "blade": {"matched": {"format": "DE"}},
        },
        # Straight razor
        {"author": "user4", "razor": {"matched": {"format": "Straight"}}},
        # Half DE razor
        {
            "author": "user5",
            "razor": {"matched": {"format": "Half DE"}},
            "blade": {"matched": {"format": "DE"}},
        },
    ]
    result = aggregate_razor_formats(records)
    assert len(result) == 5

    # Check all expected formats are present
    formats = [r["format"] for r in result]
    assert "DE" in formats
    assert "Shavette (AC)" in formats
    assert "Shavette (Half DE)" in formats
    assert "Straight" in formats
    assert "Half DE" in formats
