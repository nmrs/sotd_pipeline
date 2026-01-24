"""Tests for core product aggregators."""

from sotd.aggregate.aggregators.core import (
    aggregate_blades,
    aggregate_brushes,
    aggregate_razors,
    aggregate_soaps,
)


class TestRazorAggregator:
    """Test razor aggregation logic."""

    def test_aggregate_razors_basic(self):
        """Test basic razor aggregation."""
        records = [
            {
                "author": "user1",
                "razor": {"matched": {"brand": "Gillette", "model": "Tech", "format": "DE"}},
            },
            {
                "author": "user2",
                "razor": {"matched": {"brand": "Gillette", "model": "Tech", "format": "DE"}},
            },
            {
                "author": "user1",
                "razor": {"matched": {"brand": "Fatip", "model": "Grande", "format": "DE"}},
            },
        ]

        result = aggregate_razors(records)

        assert len(result) == 2
        assert result[0]["name"] == "Gillette Tech"
        assert result[0]["brand"] == "Gillette"
        assert result[0]["model"] == "Tech"
        assert result[0]["shaves"] == 2
        assert result[0]["unique_users"] == 2
        assert result[0]["rank"] == 1
        assert result[1]["name"] == "Fatip Grande"
        assert result[1]["brand"] == "Fatip"
        assert result[1]["model"] == "Grande"
        assert result[1]["shaves"] == 1
        assert result[1]["unique_users"] == 1
        assert result[1]["rank"] == 2

    def test_aggregate_razors_no_matches(self):
        """Test razor aggregation with no matched razors."""
        records = [
            {"author": "user1", "razor": {"original": "Unknown Razor"}},
            {"author": "user2", "razor": {"original": "Another Unknown"}},
        ]

        result = aggregate_razors(records)

        assert result == []

    def test_aggregate_razors_empty_records(self):
        """Test razor aggregation with empty records."""
        result = aggregate_razors([])
        assert result == []


class TestBladeAggregator:
    """Test blade aggregation logic."""

    def test_aggregate_blades_basic(self):
        """Test basic blade aggregation."""
        records = [
            {
                "author": "user1",
                "blade": {"matched": {"brand": "Gillette", "model": "Minora", "format": "DE"}},
            },
            {
                "author": "user2",
                "blade": {"matched": {"brand": "Gillette", "model": "Minora", "format": "DE"}},
            },
            {
                "author": "user1",
                "blade": {"matched": {"brand": "Personna", "model": "Lab Blue", "format": "DE"}},
            },
        ]

        result = aggregate_blades(records)

        assert len(result) == 2
        assert result[0]["name"] == "Gillette Minora"
        assert result[0]["brand"] == "Gillette"
        assert result[0]["model"] == "Minora"
        assert result[0]["shaves"] == 2
        assert result[0]["unique_users"] == 2
        assert result[0]["rank"] == 1
        assert result[1]["name"] == "Personna Lab Blue"
        assert result[1]["brand"] == "Personna"
        assert result[1]["model"] == "Lab Blue"
        assert result[1]["shaves"] == 1
        assert result[1]["unique_users"] == 1
        assert result[1]["rank"] == 2

    def test_aggregate_blades_no_matches(self):
        """Test blade aggregation with no matched blades."""
        records = [
            {"author": "user1", "blade": {"original": "Unknown Blade"}},
            {"author": "user2", "blade": {"original": "Another Unknown"}},
        ]

        result = aggregate_blades(records)

        assert result == []


class TestBrushAggregator:
    """Test brush aggregation logic."""

    def test_aggregate_brushes_basic(self):
        """Test basic brush aggregation."""
        records = [
            {
                "author": "user1",
                "brush": {
                    "matched": {
                        "brand": "Semogue",
                        "model": "610",
                        "handle": {"brand": "Semogue", "model": "610"},
                        "knot": {
                            "brand": "Semogue",
                            "model": "610",
                            "fiber": "Boar",
                            "knot_size_mm": 21,
                        },
                    }
                },
            },
            {
                "author": "user2",
                "brush": {
                    "matched": {
                        "brand": "Semogue",
                        "model": "610",
                        "handle": {"brand": "Semogue", "model": "610"},
                        "knot": {
                            "brand": "Semogue",
                            "model": "610",
                            "fiber": "Boar",
                            "knot_size_mm": 21,
                        },
                    }
                },
            },
            {
                "author": "user1",
                "brush": {
                    "matched": {
                        "brand": "AP Shave Co",
                        "model": "MiG",
                        "handle": {"brand": "AP Shave Co", "model": "MiG"},
                        "knot": {
                            "brand": "AP Shave Co",
                            "model": "MiG",
                            "fiber": "Synthetic",
                            "knot_size_mm": 24,
                        },
                    }
                },
            },
        ]

        result = aggregate_brushes(records)

        assert len(result) == 2
        assert result[0]["name"] == "Semogue 610"
        assert result[0]["brand"] == "Semogue"
        assert result[0]["model"] == "610"
        assert result[0]["shaves"] == 2
        assert result[0]["unique_users"] == 2
        assert result[0]["rank"] == 1
        assert result[1]["name"] == "AP Shave Co MiG"
        assert result[1]["brand"] == "AP Shave Co"
        assert result[1]["model"] == "MiG"
        assert result[1]["shaves"] == 1
        assert result[1]["unique_users"] == 1
        assert result[1]["rank"] == 2

    def test_aggregate_brushes_no_matches(self):
        """Test brush aggregation with no matched brushes."""
        records = [
            {"author": "user1", "brush": {"original": "Unknown Brush"}},
            {"author": "user2", "brush": {"original": "Another Unknown"}},
        ]

        result = aggregate_brushes(records)

        assert result == []


class TestSoapAggregator:
    """Test soap aggregation logic."""

    def test_aggregate_soaps_basic(self):
        """Test basic soap aggregation."""
        records = [
            {
                "author": "user1",
                "soap": {"matched": {"brand": "Grooming Dept", "scent": "Laundry II"}},
            },
            {
                "author": "user2",
                "soap": {"matched": {"brand": "Grooming Dept", "scent": "Laundry II"}},
            },
            {
                "author": "user1",
                "soap": {"matched": {"brand": "Declaration Grooming", "scent": "Persephone"}},
            },
        ]

        result = aggregate_soaps(records)

        assert len(result) == 2
        assert result[0]["name"] == "Grooming Dept - Laundry II"
        assert result[0]["brand"] == "Grooming Dept"
        assert result[0]["scent"] == "Laundry II"
        assert "model" not in result[0]  # Soaps have scent, not model
        assert result[0]["shaves"] == 2
        assert result[0]["unique_users"] == 2
        assert result[0]["rank"] == 1
        assert result[1]["name"] == "Declaration Grooming - Persephone"
        assert result[1]["brand"] == "Declaration Grooming"
        assert result[1]["scent"] == "Persephone"
        assert "model" not in result[1]  # Soaps have scent, not model
        assert result[1]["shaves"] == 1
        assert result[1]["unique_users"] == 1
        assert result[1]["rank"] == 2

    def test_aggregate_soaps_no_matches(self):
        """Test soap aggregation with no matched soaps."""
        records = [
            {"author": "user1", "soap": {"original": "Unknown Soap"}},
            {"author": "user2", "soap": {"original": "Another Unknown"}},
        ]

        result = aggregate_soaps(records)

        assert result == []
