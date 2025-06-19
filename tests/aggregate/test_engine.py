"""Unit tests for the aggregate engine module."""

import pytest

from sotd.aggregate.aggregation_functions import calculate_basic_metrics, filter_matched_records
from sotd.aggregate.product_aggregators import (
    aggregate_blades,
    aggregate_brushes,
    aggregate_razors,
    aggregate_soaps,
)
from sotd.aggregate.user_aggregators import aggregate_users, aggregate_user_blade_usage
from sotd.aggregate.engine import (
    aggregate_brush_fibers,
    aggregate_brush_knot_sizes,
    aggregate_blackbird_plates,
    aggregate_christopher_bradley_plates,
    aggregate_game_changer_plates,
    aggregate_super_speed_tips,
    aggregate_straight_razor_specs,
    aggregate_razor_blade_combinations,
)


class TestFilterMatchedRecords:
    """Test the filter_matched_records function."""

    def test_empty_records(self):
        """Test with empty records list."""
        result = filter_matched_records([])
        assert result == []

    def test_invalid_records_type(self):
        """Test with invalid records type."""
        with pytest.raises(ValueError, match="Expected list of records"):
            filter_matched_records("invalid")  # type: ignore

    def test_no_matched_products(self):
        """Test with records that have no matched products."""
        records = [
            {
                "id": "test123",
                "author": "testuser",
                "created_utc": 1640995200,
                "body": "Test comment",
                "razor": {
                    "matched": {},  # Empty dict, not matched
                },
            }
        ]
        result = filter_matched_records(records)
        assert result == []

    def test_successfully_matched_razor(self):
        """Test with successfully matched razor."""
        records = [
            {
                "id": "test123",
                "author": "testuser",
                "created_utc": 1640995200,
                "body": "Test comment",
                "razor": {
                    "matched": {
                        "brand": "Test Brand",
                        "model": "Test Model",
                        "match_type": "exact",
                    }
                },
            }
        ]
        result = filter_matched_records(records)
        assert len(result) == 1
        assert result[0]["id"] == "test123"

    def test_successfully_matched_blade(self):
        """Test with successfully matched blade."""
        records = [
            {
                "id": "test123",
                "author": "testuser",
                "created_utc": 1640995200,
                "body": "Test comment",
                "blade": {
                    "matched": {
                        "brand": "Test Blade",
                        "match_type": "exact",
                    }
                },
            }
        ]
        result = filter_matched_records(records)
        assert len(result) == 1
        assert result[0]["id"] == "test123"

    def test_successfully_matched_soap(self):
        """Test with successfully matched soap."""
        records = [
            {
                "id": "test123",
                "author": "testuser",
                "created_utc": 1640995200,
                "body": "Test comment",
                "soap": {
                    "matched": {
                        "maker": "Test Maker",
                        "scent": "Test Scent",
                        "match_type": "exact",
                    }
                },
            }
        ]
        result = filter_matched_records(records)
        assert len(result) == 1
        assert result[0]["id"] == "test123"

    def test_successfully_matched_brush(self):
        """Test with successfully matched brush."""
        records = [
            {
                "id": "test123",
                "author": "testuser",
                "created_utc": 1640995200,
                "body": "Test comment",
                "brush": {
                    "matched": {
                        "brand": "Test Brush",
                        "model": "Test Model",
                        "handle_maker": "Test Handle",
                        "fiber": "Badger",
                        "knot_size_mm": "24",
                        "match_type": "exact",
                    }
                },
            }
        ]
        result = filter_matched_records(records)
        assert len(result) == 1
        assert result[0]["id"] == "test123"

    def test_invalid_match_type(self):
        """Test with invalid match_type."""
        records = [
            {
                "id": "test123",
                "author": "testuser",
                "created_utc": 1640995200,
                "body": "Test comment",
                "razor": {
                    "matched": {
                        "brand": "Test Brand",
                        "match_type": "invalid_type",
                    }
                },
            }
        ]
        # Now considered valid because matched is non-empty
        result = filter_matched_records(records)
        assert len(result) == 1
        assert result[0]["id"] == "test123"

    def test_mixed_valid_invalid_records(self):
        """Test with mix of valid and invalid records."""
        records = [
            {
                "id": "test123",
                "author": "testuser",
                "created_utc": 1640995200,
                "body": "Test comment",
                "razor": {
                    "matched": {
                        "brand": "Test Brand",
                        "match_type": "exact",
                    }
                },
            },
            {
                "id": "test456",
                "author": "testuser2",
                "created_utc": 1640995201,
                "body": "Test comment 2",
                "razor": {
                    "matched": {},  # Empty dict, not matched
                },
            },
        ]
        result = filter_matched_records(records)
        assert len(result) == 1
        assert result[0]["id"] == "test123"


class TestCalculateBasicMetrics:
    """Test the calculate_basic_metrics function."""

    def test_empty_records(self):
        """Test with empty records."""
        result = calculate_basic_metrics([])
        expected = {
            "total_shaves": 0,
            "unique_shavers": 0,
            "avg_shaves_per_user": 0.0,
        }
        assert result == expected

    def test_invalid_records_type(self):
        """Test with invalid records type."""
        with pytest.raises(ValueError, match="Expected list of records"):
            calculate_basic_metrics("invalid")  # type: ignore

    def test_single_user_single_shave(self):
        """Test with single user and single shave."""
        records = [
            {
                "id": "test123",
                "author": "testuser",
                "created_utc": 1640995200,
                "body": "Test comment",
            }
        ]
        result = calculate_basic_metrics(records)
        assert result["total_shaves"] == 1
        assert result["unique_shavers"] == 1
        assert result["avg_shaves_per_user"] == 1.0

    def test_single_user_multiple_shaves(self):
        """Test with single user and multiple shaves."""
        records = [
            {
                "id": "test123",
                "author": "testuser",
                "created_utc": 1640995200,
                "body": "Test comment 1",
            },
            {
                "id": "test456",
                "author": "testuser",
                "created_utc": 1640995201,
                "body": "Test comment 2",
            },
        ]
        result = calculate_basic_metrics(records)
        assert result["total_shaves"] == 2
        assert result["unique_shavers"] == 1
        assert result["avg_shaves_per_user"] == 2.0

    def test_multiple_users(self):
        """Test with multiple users."""
        records = [
            {
                "id": "test123",
                "author": "user1",
                "created_utc": 1640995200,
                "body": "Test comment 1",
            },
            {
                "id": "test456",
                "author": "user2",
                "created_utc": 1640995201,
                "body": "Test comment 2",
            },
            {
                "id": "test789",
                "author": "user1",
                "created_utc": 1640995202,
                "body": "Test comment 3",
            },
        ]
        result = calculate_basic_metrics(records)
        assert result["total_shaves"] == 3
        assert result["unique_shavers"] == 2
        assert result["avg_shaves_per_user"] == 1.5

    def test_invalid_records_filtered_out(self):
        """Test that invalid records are filtered out."""
        records = [
            {
                "id": "test123",
                "author": "user1",
                "created_utc": 1640995200,
                "body": "Test comment 1",
            },
            {
                "id": "test456",
                # Missing author
                "created_utc": 1640995201,
                "body": "Test comment 2",
            },
            {
                "id": "test789",
                "author": 123,  # Invalid type
                "created_utc": 1640995202,
                "body": "Test comment 3",
            },
        ]
        result = calculate_basic_metrics(records)
        assert result["total_shaves"] == 1
        assert result["unique_shavers"] == 1
        assert result["avg_shaves_per_user"] == 1.0


class TestAggregateRazors:
    """Test the aggregate_razors function."""

    def test_empty_records(self):
        """Test with empty records."""
        result = aggregate_razors([])
        assert result == []

    def test_invalid_records_type(self):
        """Test with invalid records type."""
        with pytest.raises(ValueError, match="Expected list of records"):
            aggregate_razors("invalid")  # type: ignore

    def test_no_razor_data(self):
        """Test with no razor data."""
        records = [
            {
                "id": "test123",
                "author": "testuser",
                "created_utc": 1640995200,
                "body": "Test comment",
                # No razor field
            }
        ]
        result = aggregate_razors(records)
        assert result == []

    def test_single_razor_single_user(self):
        """Test with single razor and single user."""
        records = [
            {
                "id": "test123",
                "author": "testuser",
                "created_utc": 1640995200,
                "body": "Test comment",
                "razor": {
                    "matched": {
                        "brand": "Test Brand",
                        "model": "Test Model",
                        "format": "DE",
                        "match_type": "exact",
                    }
                },
            }
        ]
        result = aggregate_razors(records)
        assert len(result) == 1
        assert result[0]["name"] == "Test Brand Test Model DE"
        assert result[0]["shaves"] == 1
        assert result[0]["unique_users"] == 1
        assert result[0]["avg_shaves_per_user"] == 1.0

    def test_single_razor_multiple_users(self):
        """Test with single razor and multiple users."""
        records = [
            {
                "id": "test123",
                "author": "user1",
                "created_utc": 1640995200,
                "body": "Test comment 1",
                "razor": {
                    "matched": {
                        "brand": "Test Brand",
                        "model": "Test Model",
                        "match_type": "exact",
                    }
                },
            },
            {
                "id": "test456",
                "author": "user2",
                "created_utc": 1640995201,
                "body": "Test comment 2",
                "razor": {
                    "matched": {
                        "brand": "Test Brand",
                        "model": "Test Model",
                        "match_type": "exact",
                    }
                },
            },
        ]
        result = aggregate_razors(records)
        assert len(result) == 1
        assert result[0]["name"] == "Test Brand Test Model"
        assert result[0]["shaves"] == 2
        assert result[0]["unique_users"] == 2
        assert result[0]["avg_shaves_per_user"] == 1.0

    def test_multiple_razors(self):
        """Test with multiple razors."""
        records = [
            {
                "id": "test123",
                "author": "user1",
                "created_utc": 1640995200,
                "body": "Test comment 1",
                "razor": {
                    "matched": {
                        "brand": "Brand A",
                        "model": "Model A",
                        "match_type": "exact",
                    }
                },
            },
            {
                "id": "test456",
                "author": "user2",
                "created_utc": 1640995201,
                "body": "Test comment 2",
                "razor": {
                    "matched": {
                        "brand": "Brand B",
                        "model": "Model B",
                        "match_type": "exact",
                    }
                },
            },
        ]
        result = aggregate_razors(records)
        assert len(result) == 2
        # Should be sorted by shaves (descending)
        assert result[0]["name"] == "Brand A Model A"
        assert result[1]["name"] == "Brand B Model B"

    def test_invalid_match_type_filtered_out(self):
        """Test that records with invalid match_type are filtered out."""
        records = [
            {
                "id": "test123",
                "author": "user1",
                "created_utc": 1640995200,
                "body": "Test comment 1",
                "razor": {
                    "matched": {
                        "brand": "Test Brand",
                        "model": "Test Model",
                        "match_type": "invalid_type",
                    }
                },
            }
        ]
        result = aggregate_razors(records)
        assert result == []

    def test_tiebreaker_unique_users(self):
        """Test that unique_users is used as a tie breaker when shaves are equal."""
        records = [
            # Razor A: 2 users, 4 shaves
            {
                "id": "1",
                "author": "user1",
                "razor": {"matched": {"brand": "A", "model": "X", "match_type": "exact"}},
            },
            {
                "id": "2",
                "author": "user1",
                "razor": {"matched": {"brand": "A", "model": "X", "match_type": "exact"}},
            },
            {
                "id": "3",
                "author": "user2",
                "razor": {"matched": {"brand": "A", "model": "X", "match_type": "exact"}},
            },
            {
                "id": "4",
                "author": "user2",
                "razor": {"matched": {"brand": "A", "model": "X", "match_type": "exact"}},
            },
            # Razor B: 4 users, 4 shaves
            {
                "id": "5",
                "author": "user3",
                "razor": {"matched": {"brand": "B", "model": "Y", "match_type": "exact"}},
            },
            {
                "id": "6",
                "author": "user4",
                "razor": {"matched": {"brand": "B", "model": "Y", "match_type": "exact"}},
            },
            {
                "id": "7",
                "author": "user5",
                "razor": {"matched": {"brand": "B", "model": "Y", "match_type": "exact"}},
            },
            {
                "id": "8",
                "author": "user6",
                "razor": {"matched": {"brand": "B", "model": "Y", "match_type": "exact"}},
            },
        ]
        result = aggregate_razors(records)
        assert result[0]["name"] == "B Y"  # More unique users
        assert result[1]["name"] == "A X"


class TestAggregateBlades:
    """Test the aggregate_blades function."""

    def test_empty_records(self):
        """Test with empty records."""
        result = aggregate_blades([])
        assert result == []

    def test_invalid_records_type(self):
        """Test with invalid records type."""
        with pytest.raises(ValueError, match="Expected list of records"):
            aggregate_blades("invalid")  # type: ignore

    def test_no_blade_data(self):
        """Test with no blade data."""
        records = [
            {
                "id": "test123",
                "author": "testuser",
                "created_utc": 1640995200,
                "body": "Test comment",
                # No blade field
            }
        ]
        result = aggregate_blades(records)
        assert result == []

    def test_single_blade_single_user(self):
        """Test with single blade and single user."""
        records = [
            {
                "id": "test123",
                "author": "testuser",
                "created_utc": 1640995200,
                "body": "Test comment",
                "blade": {
                    "matched": {
                        "brand": "Test Blade",
                        "match_type": "exact",
                    }
                },
            }
        ]
        result = aggregate_blades(records)
        assert len(result) == 1
        assert result[0]["name"] == "Test Blade"
        assert result[0]["shaves"] == 1
        assert result[0]["unique_users"] == 1
        assert result[0]["avg_shaves_per_user"] == 1.0

    def test_multiple_blades(self):
        """Test with multiple blades."""
        records = [
            {
                "id": "test123",
                "author": "user1",
                "created_utc": 1640995200,
                "body": "Test comment 1",
                "blade": {
                    "matched": {
                        "brand": "Blade A",
                        "match_type": "exact",
                    }
                },
            },
            {
                "id": "test456",
                "author": "user2",
                "created_utc": 1640995201,
                "body": "Test comment 2",
                "blade": {
                    "matched": {
                        "brand": "Blade B",
                        "match_type": "exact",
                    }
                },
            },
        ]
        result = aggregate_blades(records)
        assert len(result) == 2
        assert result[0]["name"] == "Blade A"
        assert result[1]["name"] == "Blade B"

    def test_tiebreaker_unique_users(self):
        records = [
            # Blade A: 2 users, 4 shaves
            {
                "id": "1",
                "author": "user1",
                "blade": {"matched": {"brand": "A", "match_type": "exact"}},
            },
            {
                "id": "2",
                "author": "user1",
                "blade": {"matched": {"brand": "A", "match_type": "exact"}},
            },
            {
                "id": "3",
                "author": "user2",
                "blade": {"matched": {"brand": "A", "match_type": "exact"}},
            },
            {
                "id": "4",
                "author": "user2",
                "blade": {"matched": {"brand": "A", "match_type": "exact"}},
            },
            # Blade B: 4 users, 4 shaves
            {
                "id": "5",
                "author": "user3",
                "blade": {"matched": {"brand": "B", "match_type": "exact"}},
            },
            {
                "id": "6",
                "author": "user4",
                "blade": {"matched": {"brand": "B", "match_type": "exact"}},
            },
            {
                "id": "7",
                "author": "user5",
                "blade": {"matched": {"brand": "B", "match_type": "exact"}},
            },
            {
                "id": "8",
                "author": "user6",
                "blade": {"matched": {"brand": "B", "match_type": "exact"}},
            },
        ]
        result = aggregate_blades(records)
        assert result[0]["name"] == "B"
        assert result[1]["name"] == "A"


class TestAggregateSoaps:
    """Test the aggregate_soaps function."""

    def test_empty_records(self):
        """Test with empty records."""
        result = aggregate_soaps([])
        assert result == []

    def test_invalid_records_type(self):
        """Test with invalid records type."""
        with pytest.raises(ValueError, match="Expected list of records"):
            aggregate_soaps("invalid")  # type: ignore

    def test_no_soap_data(self):
        """Test with no soap data."""
        records = [
            {
                "id": "test123",
                "author": "testuser",
                "created_utc": 1640995200,
                "body": "Test comment",
                # No soap field
            }
        ]
        result = aggregate_soaps(records)
        assert result == []

    def test_single_soap_single_user(self):
        """Test with single soap and single user."""
        records = [
            {
                "id": "test123",
                "author": "testuser",
                "created_utc": 1640995200,
                "body": "Test comment",
                "soap": {
                    "matched": {
                        "maker": "Test Maker",
                        "scent": "Test Scent",
                        "match_type": "exact",
                    }
                },
            }
        ]
        result = aggregate_soaps(records)
        assert len(result) == 1
        assert result[0]["name"] == "Test Maker Test Scent"
        assert result[0]["shaves"] == 1
        assert result[0]["unique_users"] == 1
        assert result[0]["avg_shaves_per_user"] == 1.0

    def test_multiple_soaps(self):
        """Test with multiple soaps."""
        records = [
            {
                "id": "test123",
                "author": "user1",
                "created_utc": 1640995200,
                "body": "Test comment 1",
                "soap": {
                    "matched": {
                        "maker": "Maker A",
                        "scent": "Scent A",
                        "match_type": "exact",
                    }
                },
            },
            {
                "id": "test456",
                "author": "user2",
                "created_utc": 1640995201,
                "body": "Test comment 2",
                "soap": {
                    "matched": {
                        "maker": "Maker B",
                        "scent": "Scent B",
                        "match_type": "exact",
                    }
                },
            },
        ]
        result = aggregate_soaps(records)
        assert len(result) == 2
        assert result[0]["name"] == "Maker A Scent A"
        assert result[1]["name"] == "Maker B Scent B"

    def test_tiebreaker_unique_users(self):
        records = [
            # Soap A: 2 users, 4 shaves
            {
                "id": "1",
                "author": "user1",
                "soap": {"matched": {"maker": "A", "scent": "X", "match_type": "exact"}},
            },
            {
                "id": "2",
                "author": "user1",
                "soap": {"matched": {"maker": "A", "scent": "X", "match_type": "exact"}},
            },
            {
                "id": "3",
                "author": "user2",
                "soap": {"matched": {"maker": "A", "scent": "X", "match_type": "exact"}},
            },
            {
                "id": "4",
                "author": "user2",
                "soap": {"matched": {"maker": "A", "scent": "X", "match_type": "exact"}},
            },
            # Soap B: 4 users, 4 shaves
            {
                "id": "5",
                "author": "user3",
                "soap": {"matched": {"maker": "B", "scent": "Y", "match_type": "exact"}},
            },
            {
                "id": "6",
                "author": "user4",
                "soap": {"matched": {"maker": "B", "scent": "Y", "match_type": "exact"}},
            },
            {
                "id": "7",
                "author": "user5",
                "soap": {"matched": {"maker": "B", "scent": "Y", "match_type": "exact"}},
            },
            {
                "id": "8",
                "author": "user6",
                "soap": {"matched": {"maker": "B", "scent": "Y", "match_type": "exact"}},
            },
        ]
        result = aggregate_soaps(records)
        assert result[0]["name"] == "B Y"
        assert result[1]["name"] == "A X"


class TestAggregateBrushes:
    """Test the aggregate_brushes function."""

    def test_empty_records(self):
        """Test with empty records."""
        result = aggregate_brushes([])
        assert result == []

    def test_invalid_records_type(self):
        """Test with invalid records type."""
        with pytest.raises(ValueError, match="Expected list of records"):
            aggregate_brushes("invalid")  # type: ignore

    def test_no_brush_data(self):
        """Test with no brush data."""
        records = [
            {
                "id": "test123",
                "author": "testuser",
                "created_utc": 1640995200,
                "body": "Test comment",
                # No brush field
            }
        ]
        result = aggregate_brushes(records)
        assert result == []

    def test_single_brush_single_user(self):
        """Test with single brush and single user."""
        records = [
            {
                "id": "test123",
                "author": "testuser",
                "created_utc": 1640995200,
                "body": "Test comment",
                "brush": {
                    "matched": {
                        "brand": "Test Brush",
                        "model": "Test Model",
                        "handle_maker": "Test Handle",
                        "fiber": "Badger",
                        "knot_size_mm": "24",
                        "match_type": "exact",
                    }
                },
            }
        ]
        result = aggregate_brushes(records)
        assert len(result) == 1
        assert result[0]["name"] == "Test Brush Test Model"
        assert result[0]["shaves"] == 1
        assert result[0]["unique_users"] == 1
        assert result[0]["avg_shaves_per_user"] == 1.0

    def test_multiple_brushes(self):
        """Test with multiple brushes."""
        records = [
            {
                "id": "test123",
                "author": "user1",
                "created_utc": 1640995200,
                "body": "Test comment 1",
                "brush": {
                    "matched": {
                        "brand": "Brush A",
                        "model": "Model A",
                        "handle_maker": "Handle A",
                        "match_type": "exact",
                    }
                },
            },
            {
                "id": "test456",
                "author": "user2",
                "created_utc": 1640995201,
                "body": "Test comment 2",
                "brush": {
                    "matched": {
                        "brand": "Brush B",
                        "model": "Model B",
                        "handle_maker": "Handle B",
                        "match_type": "exact",
                    }
                },
            },
        ]
        result = aggregate_brushes(records)
        assert len(result) == 2
        assert result[0]["name"] == "Brush A Model A"
        assert result[1]["name"] == "Brush B Model B"

    def test_tiebreaker_unique_users(self):
        records = [
            # Brush A: 2 users, 4 shaves
            {
                "id": "1",
                "author": "user1",
                "brush": {"matched": {"brand": "A", "model": "X", "match_type": "exact"}},
            },
            {
                "id": "2",
                "author": "user1",
                "brush": {"matched": {"brand": "A", "model": "X", "match_type": "exact"}},
            },
            {
                "id": "3",
                "author": "user2",
                "brush": {"matched": {"brand": "A", "model": "X", "match_type": "exact"}},
            },
            {
                "id": "4",
                "author": "user2",
                "brush": {"matched": {"brand": "A", "model": "X", "match_type": "exact"}},
            },
            # Brush B: 4 users, 4 shaves
            {
                "id": "5",
                "author": "user3",
                "brush": {"matched": {"brand": "B", "model": "Y", "match_type": "exact"}},
            },
            {
                "id": "6",
                "author": "user4",
                "brush": {"matched": {"brand": "B", "model": "Y", "match_type": "exact"}},
            },
            {
                "id": "7",
                "author": "user5",
                "brush": {"matched": {"brand": "B", "model": "Y", "match_type": "exact"}},
            },
            {
                "id": "8",
                "author": "user6",
                "brush": {"matched": {"brand": "B", "model": "Y", "match_type": "exact"}},
            },
        ]
        result = aggregate_brushes(records)
        assert result[0]["name"] == "B Y"
        assert result[1]["name"] == "A X"


class TestAggregateUsers:
    """Test the aggregate_users function."""

    def test_empty_records(self):
        """Test with empty records."""
        result = aggregate_users([])
        assert result == []

    def test_invalid_records_type(self):
        """Test with invalid records type."""
        with pytest.raises(ValueError, match="Expected list of records"):
            aggregate_users("invalid")  # type: ignore

    def test_single_user_single_shave(self):
        """Test with single user and single shave."""
        records = [
            {
                "id": "test123",
                "author": "testuser",
                "created_utc": 1640995200,
                "body": "Test comment",
                "thread_title": "Monday SOTD Thread - May 20, 2025",
            }
        ]
        result = aggregate_users(records)
        assert len(result) == 1
        assert result[0]["user"] == "testuser"
        assert result[0]["shaves"] == 1
        assert result[0]["unique_days"] == 1
        assert result[0]["missed_days"] == 30  # May has 31 days, so 31-1=30 missed
        assert result[0]["avg_shaves_per_user"] == 1.0

    def test_single_user_multiple_shaves_same_day(self):
        """Test with single user and multiple shaves on same day."""
        records = [
            {
                "id": "test123",
                "author": "testuser",
                "created_utc": 1640995200,
                "body": "Test comment 1",
                "thread_title": "Monday SOTD Thread - May 20, 2025",
            },
            {
                "id": "test456",
                "author": "testuser",
                "created_utc": 1640995201,
                "body": "Test comment 2",
                "thread_title": "Monday SOTD Thread - May 20, 2025",
            },
        ]
        result = aggregate_users(records)
        assert len(result) == 1
        assert result[0]["user"] == "testuser"
        assert result[0]["shaves"] == 2
        assert result[0]["unique_days"] == 1  # Same day, so only 1 unique day
        assert result[0]["missed_days"] == 30  # May has 31 days, so 31-1=30 missed
        assert result[0]["avg_shaves_per_user"] == 1.0

    def test_single_user_multiple_shaves_different_days(self):
        """Test with single user and multiple shaves on different days."""
        records = [
            {
                "id": "test123",
                "author": "testuser",
                "created_utc": 1640995200,
                "body": "Test comment 1",
                "thread_title": "Monday SOTD Thread - May 20, 2025",
            },
            {
                "id": "test456",
                "author": "testuser",
                "created_utc": 1640995201,
                "body": "Test comment 2",
                "thread_title": "Tuesday SOTD Thread - May 21, 2025",
            },
        ]
        result = aggregate_users(records)
        assert len(result) == 1
        assert result[0]["user"] == "testuser"
        assert result[0]["shaves"] == 2
        assert result[0]["unique_days"] == 2  # Different days, so 2 unique days
        assert result[0]["missed_days"] == 29  # May has 31 days, so 31-2=29 missed
        assert result[0]["avg_shaves_per_user"] == 1.0

    def test_multiple_users(self):
        """Test with multiple users."""
        records = [
            {
                "id": "test123",
                "author": "user1",
                "created_utc": 1640995200,
                "body": "Test comment 1",
                "thread_title": "Monday SOTD Thread - May 20, 2025",
            },
            {
                "id": "test456",
                "author": "user2",
                "created_utc": 1640995201,
                "body": "Test comment 2",
                "thread_title": "Tuesday SOTD Thread - May 21, 2025",
            },
            {
                "id": "test789",
                "author": "user1",
                "created_utc": 1640995202,
                "body": "Test comment 3",
                "thread_title": "Wednesday SOTD Thread - May 22, 2025",
            },
        ]
        result = aggregate_users(records)
        assert len(result) == 2
        # Should be sorted by shaves (descending), then by missed days (ascending)
        assert result[0]["user"] == "user1"
        assert result[0]["shaves"] == 2
        assert result[0]["unique_days"] == 2
        assert result[0]["missed_days"] == 29
        assert result[1]["user"] == "user2"
        assert result[1]["shaves"] == 1
        assert result[1]["unique_days"] == 1
        assert result[1]["missed_days"] == 30

    def test_sorting_by_shaves_then_missed_days(self):
        """Test that sorting works correctly: shaves (descending), then missed days (ascending)."""
        records = [
            # User A: 2 shaves, 2 unique days (29 missed)
            {
                "id": "test1",
                "author": "userA",
                "created_utc": 1640995200,
                "body": "Test comment 1",
                "thread_title": "Monday SOTD Thread - May 20, 2025",
            },
            {
                "id": "test2",
                "author": "userA",
                "created_utc": 1640995201,
                "body": "Test comment 2",
                "thread_title": "Tuesday SOTD Thread - May 21, 2025",
            },
            # User B: 2 shaves, 1 unique day (30 missed) - should rank lower
            {
                "id": "test3",
                "author": "userB",
                "created_utc": 1640995202,
                "body": "Test comment 3",
                "thread_title": "Monday SOTD Thread - May 20, 2025",
            },
            {
                "id": "test4",
                "author": "userB",
                "created_utc": 1640995203,
                "body": "Test comment 4",
                "thread_title": "Monday SOTD Thread - May 20, 2025",
            },
        ]
        result = aggregate_users(records)
        assert len(result) == 2
        # User A should rank higher (same shaves, fewer missed days)
        assert result[0]["user"] == "userA"
        assert result[0]["shaves"] == 2
        assert result[0]["missed_days"] == 29
        assert result[1]["user"] == "userB"
        assert result[1]["shaves"] == 2
        assert result[1]["missed_days"] == 30

    def test_invalid_records_filtered_out(self):
        """Test that invalid records are filtered out."""
        records = [
            {
                "id": "test123",
                "author": "user1",
                "created_utc": 1640995200,
                "body": "Test comment 1",
                "thread_title": "Monday SOTD Thread - May 20, 2025",
            },
            {
                "id": "test456",
                # Missing author
                "created_utc": 1640995201,
                "body": "Test comment 2",
                "thread_title": "Tuesday SOTD Thread - May 21, 2025",
            },
            {
                "id": "test789",
                "author": 123,  # Invalid type
                "created_utc": 1640995202,
                "body": "Test comment 3",
                "thread_title": "Wednesday SOTD Thread - May 22, 2025",
            },
        ]
        result = aggregate_users(records)
        assert len(result) == 1
        assert result[0]["user"] == "user1"
        assert result[0]["shaves"] == 1
        assert result[0]["unique_days"] == 1
        assert result[0]["missed_days"] == 30

    def test_no_thread_title_fallback(self):
        """Test behavior when thread_title is missing or invalid."""
        records = [
            {
                "id": "test123",
                "author": "testuser",
                "created_utc": 1640995200,
                "body": "Test comment",
                # No thread_title
            }
        ]
        result = aggregate_users(records)
        assert len(result) == 1
        assert result[0]["user"] == "testuser"
        assert result[0]["shaves"] == 1
        assert result[0]["unique_days"] == 0  # No valid thread title to parse
        # Missed days will depend on current month when test runs

    def test_invalid_thread_title_fallback(self):
        """Test behavior when thread_title cannot be parsed."""
        records = [
            {
                "id": "test123",
                "author": "testuser",
                "created_utc": 1640995200,
                "body": "Test comment",
                "thread_title": "Invalid thread title without date",
            }
        ]
        result = aggregate_users(records)
        assert len(result) == 1
        assert result[0]["user"] == "testuser"
        assert result[0]["shaves"] == 1
        assert result[0]["unique_days"] == 0  # Invalid thread title, no date parsed
        # Missed days will depend on current month when test runs


class TestAggregateBrushFibers:
    """Test the aggregate_brush_fibers function."""

    def test_empty_records(self):
        result = aggregate_brush_fibers([])
        assert result == []

    def test_single_fiber_single_user(self):
        records = [
            {
                "id": "test1",
                "author": "user1",
                "brush": {
                    "matched": {
                        "brand": "Simpson",
                        "model": "Chubby 2",
                        "fiber": "Badger",
                        "match_type": "exact",
                    }
                },
            }
        ]
        result = aggregate_brush_fibers(records)
        assert len(result) == 1
        assert result[0]["fiber"] == "Badger"
        assert result[0]["shaves"] == 1
        assert result[0]["unique_users"] == 1
        assert result[0]["avg_shaves_per_user"] == 1.0

    def test_multiple_fibers_multiple_users(self):
        records = [
            {
                "id": "test1",
                "author": "user1",
                "brush": {
                    "matched": {
                        "brand": "Simpson",
                        "model": "Chubby 2",
                        "fiber": "Badger",
                        "match_type": "exact",
                    }
                },
            },
            {
                "id": "test2",
                "author": "user2",
                "brush": {
                    "matched": {
                        "brand": "Omega",
                        "model": "10048",
                        "fiber": "Boar",
                        "match_type": "exact",
                    }
                },
            },
            {
                "id": "test3",
                "author": "user1",
                "brush": {
                    "matched": {
                        "brand": "Simpson",
                        "model": "Chubby 2",
                        "fiber": "Badger",
                        "match_type": "exact",
                    }
                },
            },
        ]
        result = aggregate_brush_fibers(records)
        assert len(result) == 2
        fibers = {r["fiber"]: r for r in result}
        assert fibers["Badger"]["shaves"] == 2
        assert fibers["Badger"]["unique_users"] == 1
        assert fibers["Boar"]["shaves"] == 1
        assert fibers["Boar"]["unique_users"] == 1

    def test_tiebreaker_unique_users(self):
        records = [
            # Fiber A: 2 users, 4 shaves
            {
                "id": "1",
                "author": "user1",
                "brush": {
                    "matched": {"brand": "A", "model": "X", "fiber": "F1", "match_type": "exact"}
                },
            },
            {
                "id": "2",
                "author": "user1",
                "brush": {
                    "matched": {"brand": "A", "model": "X", "fiber": "F1", "match_type": "exact"}
                },
            },
            {
                "id": "3",
                "author": "user2",
                "brush": {
                    "matched": {"brand": "A", "model": "X", "fiber": "F1", "match_type": "exact"}
                },
            },
            {
                "id": "4",
                "author": "user2",
                "brush": {
                    "matched": {"brand": "A", "model": "X", "fiber": "F1", "match_type": "exact"}
                },
            },
            # Fiber B: 4 users, 4 shaves
            {
                "id": "5",
                "author": "user3",
                "brush": {
                    "matched": {"brand": "B", "model": "Y", "fiber": "F2", "match_type": "exact"}
                },
            },
            {
                "id": "6",
                "author": "user4",
                "brush": {
                    "matched": {"brand": "B", "model": "Y", "fiber": "F2", "match_type": "exact"}
                },
            },
            {
                "id": "7",
                "author": "user5",
                "brush": {
                    "matched": {"brand": "B", "model": "Y", "fiber": "F2", "match_type": "exact"}
                },
            },
            {
                "id": "8",
                "author": "user6",
                "brush": {
                    "matched": {"brand": "B", "model": "Y", "fiber": "F2", "match_type": "exact"}
                },
            },
        ]
        result = aggregate_brush_fibers(records)
        assert result[0]["fiber"] == "F2"
        assert result[1]["fiber"] == "F1"


class TestAggregateBrushKnotSizes:
    """Test the aggregate_brush_knot_sizes function."""

    def test_empty_records(self):
        result = aggregate_brush_knot_sizes([])
        assert result == []

    def test_single_knot_size_single_user(self):
        records = [
            {
                "id": "test1",
                "author": "user1",
                "brush": {
                    "matched": {
                        "brand": "Simpson",
                        "model": "Chubby 2",
                        "knot_size_mm": 28,
                        "match_type": "exact",
                    }
                },
            }
        ]
        result = aggregate_brush_knot_sizes(records)
        assert len(result) == 1
        assert result[0]["knot_size_mm"] == "28"
        assert result[0]["shaves"] == 1
        assert result[0]["unique_users"] == 1
        assert result[0]["avg_shaves_per_user"] == 1.0

    def test_multiple_knot_sizes_multiple_users(self):
        records = [
            {
                "id": "test1",
                "author": "user1",
                "brush": {
                    "matched": {
                        "brand": "Simpson",
                        "model": "Chubby 2",
                        "knot_size_mm": 28,
                        "match_type": "exact",
                    }
                },
            },
            {
                "id": "test2",
                "author": "user2",
                "brush": {
                    "matched": {
                        "brand": "Omega",
                        "model": "10048",
                        "knot_size_mm": 27,
                        "match_type": "exact",
                    }
                },
            },
            {
                "id": "test3",
                "author": "user1",
                "brush": {
                    "matched": {
                        "brand": "Simpson",
                        "model": "Chubby 2",
                        "knot_size_mm": 28,
                        "match_type": "exact",
                    }
                },
            },
        ]
        result = aggregate_brush_knot_sizes(records)
        assert len(result) == 2
        sizes = {r["knot_size_mm"]: r for r in result}
        assert sizes["28"]["shaves"] == 2
        assert sizes["28"]["unique_users"] == 1
        assert sizes["27"]["shaves"] == 1
        assert sizes["27"]["unique_users"] == 1

    def test_tiebreaker_unique_users(self):
        records = [
            # Knot A: 2 users, 4 shaves
            {
                "id": "1",
                "author": "user1",
                "brush": {
                    "matched": {
                        "brand": "A",
                        "model": "X",
                        "knot_size_mm": 24,
                        "match_type": "exact",
                    }
                },
            },
            {
                "id": "2",
                "author": "user1",
                "brush": {
                    "matched": {
                        "brand": "A",
                        "model": "X",
                        "knot_size_mm": 24,
                        "match_type": "exact",
                    }
                },
            },
            {
                "id": "3",
                "author": "user2",
                "brush": {
                    "matched": {
                        "brand": "A",
                        "model": "X",
                        "knot_size_mm": 24,
                        "match_type": "exact",
                    }
                },
            },
            {
                "id": "4",
                "author": "user2",
                "brush": {
                    "matched": {
                        "brand": "A",
                        "model": "X",
                        "knot_size_mm": 24,
                        "match_type": "exact",
                    }
                },
            },
            # Knot B: 4 users, 4 shaves
            {
                "id": "5",
                "author": "user3",
                "brush": {
                    "matched": {
                        "brand": "B",
                        "model": "Y",
                        "knot_size_mm": 26,
                        "match_type": "exact",
                    }
                },
            },
            {
                "id": "6",
                "author": "user4",
                "brush": {
                    "matched": {
                        "brand": "B",
                        "model": "Y",
                        "knot_size_mm": 26,
                        "match_type": "exact",
                    }
                },
            },
            {
                "id": "7",
                "author": "user5",
                "brush": {
                    "matched": {
                        "brand": "B",
                        "model": "Y",
                        "knot_size_mm": 26,
                        "match_type": "exact",
                    }
                },
            },
            {
                "id": "8",
                "author": "user6",
                "brush": {
                    "matched": {
                        "brand": "B",
                        "model": "Y",
                        "knot_size_mm": 26,
                        "match_type": "exact",
                    }
                },
            },
        ]
        result = aggregate_brush_knot_sizes(records)
        assert result[0]["knot_size_mm"] == "26"
        assert result[1]["knot_size_mm"] == "24"


class TestAggregateBlackbirdPlates:
    """Test the aggregate_blackbird_plates function."""

    def test_empty_records(self):
        """Test with empty records."""
        result = aggregate_blackbird_plates([])
        assert result == []

    def test_invalid_records_type(self):
        """Test with invalid records type."""
        with pytest.raises(ValueError, match="Expected list of records"):
            aggregate_blackbird_plates("invalid")  # type: ignore

    def test_no_blackbird_data(self):
        """Test with records that have no Blackland Blackbird razors."""
        records = [
            {
                "id": "test123",
                "author": "testuser",
                "razor": {
                    "matched": {
                        "brand": "RazoRock",
                        "model": "Game Changer",
                        "match_type": "exact",
                    }
                },
            }
        ]
        result = aggregate_blackbird_plates(records)
        assert result == []

    def test_blackbird_without_plate_data(self):
        """Test with Blackland Blackbird razors but no enriched plate data."""
        records = [
            {
                "id": "test123",
                "author": "testuser",
                "razor": {
                    "matched": {
                        "brand": "Blackland",
                        "model": "Blackbird",
                        "match_type": "exact",
                    }
                },
            }
        ]
        result = aggregate_blackbird_plates(records)
        assert result == []

    def test_single_plate_single_user(self):
        """Test with single Blackbird plate and single user."""
        records = [
            {
                "id": "test123",
                "author": "testuser",
                "razor": {
                    "matched": {
                        "brand": "Blackland",
                        "model": "Blackbird",
                        "match_type": "exact",
                    },
                    "enriched": {
                        "plate": "Standard",
                        "_enriched_by": "BlackbirdPlateEnricher",
                        "_extraction_source": "user_comment",
                    },
                },
            }
        ]
        result = aggregate_blackbird_plates(records)
        assert len(result) == 1
        assert result[0]["plate"] == "Standard"
        assert result[0]["shaves"] == 1
        assert result[0]["unique_users"] == 1
        assert result[0]["avg_shaves_per_user"] == 1.0

    def test_single_plate_multiple_users(self):
        """Test with single Blackbird plate and multiple users."""
        records = [
            {
                "id": "test123",
                "author": "user1",
                "razor": {
                    "matched": {
                        "brand": "Blackland",
                        "model": "Blackbird",
                        "match_type": "exact",
                    },
                    "enriched": {
                        "plate": "Standard",
                        "_enriched_by": "BlackbirdPlateEnricher",
                        "_extraction_source": "user_comment",
                    },
                },
            },
            {
                "id": "test456",
                "author": "user2",
                "razor": {
                    "matched": {
                        "brand": "Blackland",
                        "model": "Blackbird",
                        "match_type": "exact",
                    },
                    "enriched": {
                        "plate": "Standard",
                        "_enriched_by": "BlackbirdPlateEnricher",
                        "_extraction_source": "user_comment",
                    },
                },
            },
        ]
        result = aggregate_blackbird_plates(records)
        assert len(result) == 1
        assert result[0]["plate"] == "Standard"
        assert result[0]["shaves"] == 2
        assert result[0]["unique_users"] == 2
        assert result[0]["avg_shaves_per_user"] == 1.0

    def test_multiple_plates(self):
        """Test with multiple Blackbird plates."""
        records = [
            {
                "id": "test123",
                "author": "user1",
                "razor": {
                    "matched": {
                        "brand": "Blackland",
                        "model": "Blackbird",
                        "match_type": "exact",
                    },
                    "enriched": {
                        "plate": "Standard",
                        "_enriched_by": "BlackbirdPlateEnricher",
                        "_extraction_source": "user_comment",
                    },
                },
            },
            {
                "id": "test456",
                "author": "user2",
                "razor": {
                    "matched": {
                        "brand": "Blackland",
                        "model": "Blackbird",
                        "match_type": "exact",
                    },
                    "enriched": {
                        "plate": "Lite",
                        "_enriched_by": "BlackbirdPlateEnricher",
                        "_extraction_source": "user_comment",
                    },
                },
            },
            {
                "id": "test789",
                "author": "user3",
                "razor": {
                    "matched": {
                        "brand": "Blackland",
                        "model": "Blackbird",
                        "match_type": "exact",
                    },
                    "enriched": {
                        "plate": "OC",
                        "_enriched_by": "BlackbirdPlateEnricher",
                        "_extraction_source": "user_comment",
                    },
                },
            },
        ]
        result = aggregate_blackbird_plates(records)
        assert len(result) == 3

        # Check that results are sorted by shaves (descending)
        assert result[0]["shaves"] >= result[1]["shaves"]
        assert result[1]["shaves"] >= result[2]["shaves"]

        # Check all plates are present
        plates = [r["plate"] for r in result]
        assert "Standard" in plates
        assert "Lite" in plates
        assert "OC" in plates

    def test_blackbird_ti_model(self):
        """Test with Blackland Blackbird Ti model."""
        records = [
            {
                "id": "test123",
                "author": "testuser",
                "razor": {
                    "matched": {
                        "brand": "Blackland",
                        "model": "Blackbird Ti",
                        "match_type": "exact",
                    },
                    "enriched": {
                        "plate": "Standard",
                        "_enriched_by": "BlackbirdPlateEnricher",
                        "_extraction_source": "user_comment",
                    },
                },
            }
        ]
        result = aggregate_blackbird_plates(records)
        assert len(result) == 1
        assert result[0]["plate"] == "Standard"

    def test_mixed_razor_types(self):
        """Test with mix of Blackbird and other razors."""
        records = [
            {
                "id": "test123",
                "author": "user1",
                "razor": {
                    "matched": {
                        "brand": "Blackland",
                        "model": "Blackbird",
                        "match_type": "exact",
                    },
                    "enriched": {
                        "plate": "Standard",
                        "_enriched_by": "BlackbirdPlateEnricher",
                        "_extraction_source": "user_comment",
                    },
                },
            },
            {
                "id": "test456",
                "author": "user2",
                "razor": {
                    "matched": {
                        "brand": "RazoRock",
                        "model": "Game Changer",
                        "match_type": "exact",
                    },
                },
            },
        ]
        result = aggregate_blackbird_plates(records)
        assert len(result) == 1
        assert result[0]["plate"] == "Standard"
        assert result[0]["shaves"] == 1

    def test_tiebreaker_unique_users(self):
        """Test tiebreaker when shaves are equal."""
        records = [
            {
                "id": "test123",
                "author": "user1",
                "razor": {
                    "matched": {
                        "brand": "Blackland",
                        "model": "Blackbird",
                        "match_type": "exact",
                    },
                    "enriched": {
                        "plate": "Standard",
                        "_enriched_by": "BlackbirdPlateEnricher",
                        "_extraction_source": "user_comment",
                    },
                },
            },
            {
                "id": "test456",
                "author": "user2",
                "razor": {
                    "matched": {
                        "brand": "Blackland",
                        "model": "Blackbird",
                        "match_type": "exact",
                    },
                    "enriched": {
                        "plate": "Lite",
                        "_enriched_by": "BlackbirdPlateEnricher",
                        "_extraction_source": "user_comment",
                    },
                },
            },
            {
                "id": "test789",
                "author": "user1",
                "razor": {
                    "matched": {
                        "brand": "Blackland",
                        "model": "Blackbird",
                        "match_type": "exact",
                    },
                    "enriched": {
                        "plate": "Standard",
                        "_enriched_by": "BlackbirdPlateEnricher",
                        "_extraction_source": "user_comment",
                    },
                },
            },
        ]
        result = aggregate_blackbird_plates(records)
        assert len(result) == 2

        # Standard should be first (2 shaves, 1 unique user)
        # Lite should be second (1 shave, 1 unique user)
        assert result[0]["plate"] == "Standard"
        assert result[0]["shaves"] == 2
        assert result[0]["unique_users"] == 1
        assert result[1]["plate"] == "Lite"
        assert result[1]["shaves"] == 1
        assert result[1]["unique_users"] == 1


class TestAggregateChristopherBradleyPlates:
    """Test the aggregate_christopher_bradley_plates function."""

    def test_empty_records(self):
        """Test with empty records."""
        result = aggregate_christopher_bradley_plates([])
        assert result == []

    def test_invalid_records_type(self):
        """Test with invalid records type."""
        with pytest.raises(ValueError, match="Expected list of records"):
            aggregate_christopher_bradley_plates("invalid")  # type: ignore

    def test_no_christopher_bradley_data(self):
        """Test with records that have no Karve Christopher Bradley razors."""
        records = [
            {
                "id": "test123",
                "author": "testuser",
                "razor": {
                    "matched": {
                        "brand": "RazoRock",
                        "model": "Game Changer",
                        "match_type": "exact",
                    }
                },
            }
        ]
        result = aggregate_christopher_bradley_plates(records)
        assert result == []

    def test_christopher_bradley_without_plate_data(self):
        """Test with Karve Christopher Bradley razors but no enriched plate data."""
        records = [
            {
                "id": "test123",
                "author": "testuser",
                "razor": {
                    "matched": {
                        "brand": "Karve",
                        "model": "Christopher Bradley",
                        "match_type": "exact",
                    }
                },
            }
        ]
        result = aggregate_christopher_bradley_plates(records)
        assert result == []

    def test_single_plate_single_user(self):
        """Test with single Christopher Bradley plate and single user."""
        records = [
            {
                "id": "test123",
                "author": "testuser",
                "razor": {
                    "matched": {
                        "brand": "Karve",
                        "model": "Christopher Bradley",
                        "match_type": "exact",
                    },
                    "enriched": {
                        "plate_level": "C",
                        "plate_type": "SB",
                        "_enriched_by": "ChristopherBradleyEnricher",
                        "_extraction_source": "user_comment",
                    },
                },
            }
        ]
        result = aggregate_christopher_bradley_plates(records)
        assert len(result) == 1
        assert result[0]["plate"] == "C SB"
        assert result[0]["shaves"] == 1
        assert result[0]["unique_users"] == 1
        assert result[0]["avg_shaves_per_user"] == 1.0

    def test_single_plate_multiple_users(self):
        """Test with single Christopher Bradley plate and multiple users."""
        records = [
            {
                "id": "test123",
                "author": "user1",
                "razor": {
                    "matched": {
                        "brand": "Karve",
                        "model": "Christopher Bradley",
                        "match_type": "exact",
                    },
                    "enriched": {
                        "plate_level": "D",
                        "plate_type": "OC",
                        "_enriched_by": "ChristopherBradleyEnricher",
                        "_extraction_source": "user_comment",
                    },
                },
            },
            {
                "id": "test456",
                "author": "user2",
                "razor": {
                    "matched": {
                        "brand": "Karve",
                        "model": "Christopher Bradley",
                        "match_type": "exact",
                    },
                    "enriched": {
                        "plate_level": "D",
                        "plate_type": "OC",
                        "_enriched_by": "ChristopherBradleyEnricher",
                        "_extraction_source": "user_comment",
                    },
                },
            },
        ]
        result = aggregate_christopher_bradley_plates(records)
        assert len(result) == 1
        assert result[0]["plate"] == "D OC"
        assert result[0]["shaves"] == 2
        assert result[0]["unique_users"] == 2
        assert result[0]["avg_shaves_per_user"] == 1.0

    def test_multiple_plates(self):
        """Test with multiple Christopher Bradley plates."""
        records = [
            {
                "id": "test123",
                "author": "user1",
                "razor": {
                    "matched": {
                        "brand": "Karve",
                        "model": "Christopher Bradley",
                        "match_type": "exact",
                    },
                    "enriched": {
                        "plate_level": "AA",
                        "plate_type": "SB",
                        "_enriched_by": "ChristopherBradleyEnricher",
                        "_extraction_source": "user_comment",
                    },
                },
            },
            {
                "id": "test456",
                "author": "user2",
                "razor": {
                    "matched": {
                        "brand": "Karve",
                        "model": "Christopher Bradley",
                        "match_type": "exact",
                    },
                    "enriched": {
                        "plate_level": "B",
                        "plate_type": "SB",
                        "_enriched_by": "ChristopherBradleyEnricher",
                        "_extraction_source": "user_comment",
                    },
                },
            },
            {
                "id": "test789",
                "author": "user3",
                "razor": {
                    "matched": {
                        "brand": "Karve",
                        "model": "Christopher Bradley",
                        "match_type": "exact",
                    },
                    "enriched": {
                        "plate_level": "F",
                        "plate_type": "OC",
                        "_enriched_by": "ChristopherBradleyEnricher",
                        "_extraction_source": "user_comment",
                    },
                },
            },
        ]
        result = aggregate_christopher_bradley_plates(records)
        assert len(result) == 3

        # Check that results are sorted by shaves (descending)
        assert result[0]["shaves"] >= result[1]["shaves"]
        assert result[1]["shaves"] >= result[2]["shaves"]

        # Check all plates are present
        plates = [r["plate"] for r in result]
        assert "AA SB" in plates
        assert "B SB" in plates
        assert "F OC" in plates

    def test_default_plate_type(self):
        """Test that plate type defaults to SB when not specified."""
        records = [
            {
                "id": "test123",
                "author": "testuser",
                "razor": {
                    "matched": {
                        "brand": "Karve",
                        "model": "Christopher Bradley",
                        "match_type": "exact",
                    },
                    "enriched": {
                        "plate_level": "E",
                        "_enriched_by": "ChristopherBradleyEnricher",
                        "_extraction_source": "user_comment",
                    },
                },
            }
        ]
        result = aggregate_christopher_bradley_plates(records)
        assert len(result) == 1
        assert result[0]["plate"] == "E SB"

    def test_mixed_razor_types(self):
        """Test with mix of Christopher Bradley and other razors."""
        records = [
            {
                "id": "test123",
                "author": "user1",
                "razor": {
                    "matched": {
                        "brand": "Karve",
                        "model": "Christopher Bradley",
                        "match_type": "exact",
                    },
                    "enriched": {
                        "plate_level": "G",
                        "plate_type": "SB",
                        "_enriched_by": "ChristopherBradleyEnricher",
                        "_extraction_source": "user_comment",
                    },
                },
            },
            {
                "id": "test456",
                "author": "user2",
                "razor": {
                    "matched": {
                        "brand": "RazoRock",
                        "model": "Game Changer",
                        "match_type": "exact",
                    },
                },
            },
        ]
        result = aggregate_christopher_bradley_plates(records)
        assert len(result) == 1
        assert result[0]["plate"] == "G SB"
        assert result[0]["shaves"] == 1

    def test_tiebreaker_unique_users(self):
        """Test tiebreaker when shaves are equal."""
        records = [
            {
                "id": "test123",
                "author": "user1",
                "razor": {
                    "matched": {
                        "brand": "Karve",
                        "model": "Christopher Bradley",
                        "match_type": "exact",
                    },
                    "enriched": {
                        "plate_level": "A",
                        "plate_type": "SB",
                        "_enriched_by": "ChristopherBradleyEnricher",
                        "_extraction_source": "user_comment",
                    },
                },
            },
            {
                "id": "test456",
                "author": "user2",
                "razor": {
                    "matched": {
                        "brand": "Karve",
                        "model": "Christopher Bradley",
                        "match_type": "exact",
                    },
                    "enriched": {
                        "plate_level": "C",
                        "plate_type": "OC",
                        "_enriched_by": "ChristopherBradleyEnricher",
                        "_extraction_source": "user_comment",
                    },
                },
            },
            {
                "id": "test789",
                "author": "user1",
                "razor": {
                    "matched": {
                        "brand": "Karve",
                        "model": "Christopher Bradley",
                        "match_type": "exact",
                    },
                    "enriched": {
                        "plate_level": "A",
                        "plate_type": "SB",
                        "_enriched_by": "ChristopherBradleyEnricher",
                        "_extraction_source": "user_comment",
                    },
                },
            },
        ]
        result = aggregate_christopher_bradley_plates(records)
        assert len(result) == 2

        # A SB should be first (2 shaves, 1 unique user)
        # C OC should be second (1 shave, 1 unique user)
        assert result[0]["plate"] == "A SB"
        assert result[0]["shaves"] == 2
        assert result[0]["unique_users"] == 1
        assert result[1]["plate"] == "C OC"
        assert result[1]["shaves"] == 1
        assert result[1]["unique_users"] == 1


class TestAggregateGameChangerPlates:
    """Test the aggregate_game_changer_plates function."""

    def test_empty_records(self):
        """Test with empty records."""
        result = aggregate_game_changer_plates([])
        assert result == []

    def test_invalid_records_type(self):
        """Test with invalid records type."""
        with pytest.raises(ValueError, match="Expected list of records"):
            aggregate_game_changer_plates("invalid")  # type: ignore

    def test_no_game_changer_data(self):
        """Test with records that have no RazoRock Game Changer razors."""
        records = [
            {
                "id": "test123",
                "author": "testuser",
                "razor": {
                    "matched": {
                        "brand": "Blackland",
                        "model": "Blackbird",
                        "match_type": "exact",
                    }
                },
            }
        ]
        result = aggregate_game_changer_plates(records)
        assert result == []

    def test_game_changer_without_plate_data(self):
        """Test with RazoRock Game Changer razors but no enriched plate data."""
        records = [
            {
                "id": "test123",
                "author": "testuser",
                "razor": {
                    "matched": {
                        "brand": "RazoRock",
                        "model": "Game Changer",
                        "match_type": "exact",
                    }
                },
            }
        ]
        result = aggregate_game_changer_plates(records)
        assert result == []

    def test_single_gap_single_user(self):
        """Test with single Game Changer gap and single user."""
        records = [
            {
                "id": "test123",
                "author": "testuser",
                "razor": {
                    "matched": {
                        "brand": "RazoRock",
                        "model": "Game Changer",
                        "match_type": "exact",
                    },
                    "enriched": {
                        "gap": ".68",
                        "_enriched_by": "GameChangerEnricher",
                        "_extraction_source": "user_comment",
                    },
                },
            }
        ]
        result = aggregate_game_changer_plates(records)
        assert len(result) == 1
        assert result[0]["plate"] == "Gap .68"
        assert result[0]["shaves"] == 1
        assert result[0]["unique_users"] == 1
        assert result[0]["avg_shaves_per_user"] == 1.0

    def test_single_variant_single_user(self):
        """Test with single Game Changer variant and single user."""
        records = [
            {
                "id": "test123",
                "author": "testuser",
                "razor": {
                    "matched": {
                        "brand": "RazoRock",
                        "model": "Game Changer",
                        "match_type": "exact",
                    },
                    "enriched": {
                        "variant": "OC",
                        "_enriched_by": "GameChangerEnricher",
                        "_extraction_source": "user_comment",
                    },
                },
            }
        ]
        result = aggregate_game_changer_plates(records)
        assert len(result) == 1
        assert result[0]["plate"] == "OC"
        assert result[0]["shaves"] == 1
        assert result[0]["unique_users"] == 1
        assert result[0]["avg_shaves_per_user"] == 1.0

    def test_gap_and_variant_single_user(self):
        """Test with both gap and variant for single user."""
        records = [
            {
                "id": "test123",
                "author": "testuser",
                "razor": {
                    "matched": {
                        "brand": "RazoRock",
                        "model": "Game Changer",
                        "match_type": "exact",
                    },
                    "enriched": {
                        "gap": ".84",
                        "variant": "JAWS",
                        "_enriched_by": "GameChangerEnricher",
                        "_extraction_source": "user_comment",
                    },
                },
            }
        ]
        result = aggregate_game_changer_plates(records)
        assert len(result) == 1
        assert result[0]["plate"] == "Gap .84 JAWS"
        assert result[0]["shaves"] == 1
        assert result[0]["unique_users"] == 1
        assert result[0]["avg_shaves_per_user"] == 1.0

    def test_single_plate_multiple_users(self):
        """Test with single Game Changer plate and multiple users."""
        records = [
            {
                "id": "test123",
                "author": "user1",
                "razor": {
                    "matched": {
                        "brand": "RazoRock",
                        "model": "Game Changer",
                        "match_type": "exact",
                    },
                    "enriched": {
                        "gap": ".76",
                        "_enriched_by": "GameChangerEnricher",
                        "_extraction_source": "user_comment",
                    },
                },
            },
            {
                "id": "test456",
                "author": "user2",
                "razor": {
                    "matched": {
                        "brand": "RazoRock",
                        "model": "Game Changer",
                        "match_type": "exact",
                    },
                    "enriched": {
                        "gap": ".76",
                        "_enriched_by": "GameChangerEnricher",
                        "_extraction_source": "user_comment",
                    },
                },
            },
        ]
        result = aggregate_game_changer_plates(records)
        assert len(result) == 1
        assert result[0]["plate"] == "Gap .76"
        assert result[0]["shaves"] == 2
        assert result[0]["unique_users"] == 2
        assert result[0]["avg_shaves_per_user"] == 1.0

    def test_multiple_plates(self):
        """Test with multiple Game Changer plates."""
        records = [
            {
                "id": "test123",
                "author": "user1",
                "razor": {
                    "matched": {
                        "brand": "RazoRock",
                        "model": "Game Changer",
                        "match_type": "exact",
                    },
                    "enriched": {
                        "gap": ".68",
                        "_enriched_by": "GameChangerEnricher",
                        "_extraction_source": "user_comment",
                    },
                },
            },
            {
                "id": "test456",
                "author": "user2",
                "razor": {
                    "matched": {
                        "brand": "RazoRock",
                        "model": "Game Changer",
                        "match_type": "exact",
                    },
                    "enriched": {
                        "gap": ".84",
                        "_enriched_by": "GameChangerEnricher",
                        "_extraction_source": "user_comment",
                    },
                },
            },
            {
                "id": "test789",
                "author": "user3",
                "razor": {
                    "matched": {
                        "brand": "RazoRock",
                        "model": "Game Changer",
                        "match_type": "exact",
                    },
                    "enriched": {
                        "variant": "OC",
                        "_enriched_by": "GameChangerEnricher",
                        "_extraction_source": "user_comment",
                    },
                },
            },
        ]
        result = aggregate_game_changer_plates(records)
        assert len(result) == 3

        # Check that results are sorted by shaves (descending)
        assert result[0]["shaves"] >= result[1]["shaves"]
        assert result[1]["shaves"] >= result[2]["shaves"]

        # Check all plates are present
        plates = [r["plate"] for r in result]
        assert "Gap .68" in plates
        assert "Gap .84" in plates
        assert "OC" in plates

    def test_game_changer_68_model(self):
        """Test with RazoRock Game Changer .68 model."""
        records = [
            {
                "id": "test123",
                "author": "testuser",
                "razor": {
                    "matched": {
                        "brand": "RazoRock",
                        "model": "Game Changer .68",
                        "match_type": "exact",
                    },
                    "enriched": {
                        "gap": ".68",
                        "_enriched_by": "GameChangerEnricher",
                        "_extraction_source": "user_comment",
                    },
                },
            }
        ]
        result = aggregate_game_changer_plates(records)
        assert len(result) == 1
        assert result[0]["plate"] == "Gap .68"

    def test_mixed_razor_types(self):
        """Test with mix of Game Changer and other razors."""
        records = [
            {
                "id": "test123",
                "author": "user1",
                "razor": {
                    "matched": {
                        "brand": "RazoRock",
                        "model": "Game Changer",
                        "match_type": "exact",
                    },
                    "enriched": {
                        "gap": "1.05",
                        "_enriched_by": "GameChangerEnricher",
                        "_extraction_source": "user_comment",
                    },
                },
            },
            {
                "id": "test456",
                "author": "user2",
                "razor": {
                    "matched": {
                        "brand": "Blackland",
                        "model": "Blackbird",
                        "match_type": "exact",
                    },
                },
            },
        ]
        result = aggregate_game_changer_plates(records)
        assert len(result) == 1
        assert result[0]["plate"] == "Gap 1.05"
        assert result[0]["shaves"] == 1

    def test_tiebreaker_unique_users(self):
        """Test tiebreaker when shaves are equal."""
        records = [
            {
                "id": "test123",
                "author": "user1",
                "razor": {
                    "matched": {
                        "brand": "RazoRock",
                        "model": "Game Changer",
                        "match_type": "exact",
                    },
                    "enriched": {
                        "gap": ".76",
                        "_enriched_by": "GameChangerEnricher",
                        "_extraction_source": "user_comment",
                    },
                },
            },
            {
                "id": "test456",
                "author": "user2",
                "razor": {
                    "matched": {
                        "brand": "RazoRock",
                        "model": "Game Changer",
                        "match_type": "exact",
                    },
                    "enriched": {
                        "variant": "JAWS",
                        "_enriched_by": "GameChangerEnricher",
                        "_extraction_source": "user_comment",
                    },
                },
            },
            {
                "id": "test789",
                "author": "user1",
                "razor": {
                    "matched": {
                        "brand": "RazoRock",
                        "model": "Game Changer",
                        "match_type": "exact",
                    },
                    "enriched": {
                        "gap": ".76",
                        "_enriched_by": "GameChangerEnricher",
                        "_extraction_source": "user_comment",
                    },
                },
            },
        ]
        result = aggregate_game_changer_plates(records)
        assert len(result) == 2

        # Gap .76 should be first (2 shaves, 1 unique user)
        # JAWS should be second (1 shave, 1 unique user)
        assert result[0]["plate"] == "Gap .76"
        assert result[0]["shaves"] == 2
        assert result[0]["unique_users"] == 1
        assert result[1]["plate"] == "JAWS"
        assert result[1]["shaves"] == 1
        assert result[1]["unique_users"] == 1


class TestAggregateSuperSpeedTips:
    """Test the aggregate_super_speed_tips function."""

    def test_empty_records(self):
        """Test with empty records."""
        result = aggregate_super_speed_tips([])
        assert result == []

    def test_invalid_records_type(self):
        """Test with invalid records type."""
        with pytest.raises(ValueError, match="Expected list of records"):
            aggregate_super_speed_tips("invalid")  # type: ignore

    def test_no_super_speed_data(self):
        """Test with records that don't contain Super Speed razors."""
        records = [
            {
                "id": "test123",
                "author": "testuser",
                "razor": {
                    "matched": {
                        "brand": "Blackland",
                        "model": "Blackbird",
                        "match_type": "exact",
                    },
                },
            }
        ]
        result = aggregate_super_speed_tips(records)
        assert result == []

    def test_super_speed_without_tip_data(self):
        """Test with Super Speed razors that don't have tip data."""
        records = [
            {
                "id": "test123",
                "author": "testuser",
                "razor": {
                    "matched": {
                        "brand": "Gillette",
                        "model": "Super Speed",
                        "match_type": "exact",
                    },
                    "enriched": {},
                },
            }
        ]
        result = aggregate_super_speed_tips(records)
        assert result == []

    def test_single_tip_single_user(self):
        """Test with single tip type and single user."""
        records = [
            {
                "id": "test123",
                "author": "testuser",
                "razor": {
                    "matched": {
                        "brand": "Gillette",
                        "model": "Super Speed",
                        "match_type": "exact",
                    },
                    "enriched": {
                        "super_speed_tip": "Red",
                        "_enriched_by": "SuperSpeedTipEnricher",
                        "_extraction_source": "user_comment",
                    },
                },
            }
        ]
        result = aggregate_super_speed_tips(records)
        assert len(result) == 1
        assert result[0]["tip"] == "Red"
        assert result[0]["shaves"] == 1
        assert result[0]["unique_users"] == 1
        assert result[0]["avg_shaves_per_user"] == 1.0

    def test_single_tip_multiple_users(self):
        """Test with single tip type and multiple users."""
        records = [
            {
                "id": "test123",
                "author": "user1",
                "razor": {
                    "matched": {
                        "brand": "Gillette",
                        "model": "Super Speed",
                        "match_type": "exact",
                    },
                    "enriched": {
                        "super_speed_tip": "Blue",
                        "_enriched_by": "SuperSpeedTipEnricher",
                        "_extraction_source": "user_comment",
                    },
                },
            },
            {
                "id": "test456",
                "author": "user2",
                "razor": {
                    "matched": {
                        "brand": "Gillette",
                        "model": "Super Speed",
                        "match_type": "exact",
                    },
                    "enriched": {
                        "super_speed_tip": "Blue",
                        "_enriched_by": "SuperSpeedTipEnricher",
                        "_extraction_source": "user_comment",
                    },
                },
            },
        ]
        result = aggregate_super_speed_tips(records)
        assert len(result) == 1
        assert result[0]["tip"] == "Blue"
        assert result[0]["shaves"] == 2
        assert result[0]["unique_users"] == 2
        assert result[0]["avg_shaves_per_user"] == 1.0

    def test_multiple_tips(self):
        """Test with multiple tip types."""
        records = [
            {
                "id": "test123",
                "author": "user1",
                "razor": {
                    "matched": {
                        "brand": "Gillette",
                        "model": "Super Speed",
                        "match_type": "exact",
                    },
                    "enriched": {
                        "super_speed_tip": "Red",
                        "_enriched_by": "SuperSpeedTipEnricher",
                        "_extraction_source": "user_comment",
                    },
                },
            },
            {
                "id": "test456",
                "author": "user2",
                "razor": {
                    "matched": {
                        "brand": "Gillette",
                        "model": "Super Speed",
                        "match_type": "exact",
                    },
                    "enriched": {
                        "super_speed_tip": "Black",
                        "_enriched_by": "SuperSpeedTipEnricher",
                        "_extraction_source": "user_comment",
                    },
                },
            },
            {
                "id": "test789",
                "author": "user3",
                "razor": {
                    "matched": {
                        "brand": "Gillette",
                        "model": "Super Speed",
                        "match_type": "exact",
                    },
                    "enriched": {
                        "super_speed_tip": "Flare",
                        "_enriched_by": "SuperSpeedTipEnricher",
                        "_extraction_source": "user_comment",
                    },
                },
            },
        ]
        result = aggregate_super_speed_tips(records)
        assert len(result) == 3

        # Check that results are sorted by shaves (descending)
        assert result[0]["shaves"] >= result[1]["shaves"]
        assert result[1]["shaves"] >= result[2]["shaves"]

        # Check all tips are present
        tips = [r["tip"] for r in result]
        assert "Red" in tips
        assert "Black" in tips
        assert "Flare" in tips

    def test_mixed_razor_types(self):
        """Test with mix of Super Speed and other razors."""
        records = [
            {
                "id": "test123",
                "author": "user1",
                "razor": {
                    "matched": {
                        "brand": "Gillette",
                        "model": "Super Speed",
                        "match_type": "exact",
                    },
                    "enriched": {
                        "super_speed_tip": "Red",
                        "_enriched_by": "SuperSpeedTipEnricher",
                        "_extraction_source": "user_comment",
                    },
                },
            },
            {
                "id": "test456",
                "author": "user2",
                "razor": {
                    "matched": {
                        "brand": "Blackland",
                        "model": "Blackbird",
                        "match_type": "exact",
                    },
                },
            },
        ]
        result = aggregate_super_speed_tips(records)
        assert len(result) == 1
        assert result[0]["tip"] == "Red"
        assert result[0]["shaves"] == 1

    def test_tiebreaker_unique_users(self):
        """Test tiebreaker when shaves are equal."""
        records = [
            {
                "id": "test123",
                "author": "user1",
                "razor": {
                    "matched": {
                        "brand": "Gillette",
                        "model": "Super Speed",
                        "match_type": "exact",
                    },
                    "enriched": {
                        "super_speed_tip": "Blue",
                        "_enriched_by": "SuperSpeedTipEnricher",
                        "_extraction_source": "user_comment",
                    },
                },
            },
            {
                "id": "test456",
                "author": "user2",
                "razor": {
                    "matched": {
                        "brand": "Gillette",
                        "model": "Super Speed",
                        "match_type": "exact",
                    },
                    "enriched": {
                        "super_speed_tip": "Black",
                        "_enriched_by": "SuperSpeedTipEnricher",
                        "_extraction_source": "user_comment",
                    },
                },
            },
            {
                "id": "test789",
                "author": "user1",
                "razor": {
                    "matched": {
                        "brand": "Gillette",
                        "model": "Super Speed",
                        "match_type": "exact",
                    },
                    "enriched": {
                        "super_speed_tip": "Blue",
                        "_enriched_by": "SuperSpeedTipEnricher",
                        "_extraction_source": "user_comment",
                    },
                },
            },
        ]
        result = aggregate_super_speed_tips(records)
        assert len(result) == 2

        # Blue should be first (2 shaves, 1 unique user)
        # Black should be second (1 shave, 1 unique user)
        assert result[0]["tip"] == "Blue"
        assert result[0]["shaves"] == 2
        assert result[0]["unique_users"] == 1
        assert result[1]["tip"] == "Black"
        assert result[1]["shaves"] == 1
        assert result[1]["unique_users"] == 1


class TestAggregateStraightRazorSpecs:
    """Test the aggregate_straight_razor_specs function."""

    def test_empty_records(self):
        """Test with empty records."""
        result = aggregate_straight_razor_specs([])
        assert result == []

    def test_invalid_records_type(self):
        """Test with invalid records type."""
        with pytest.raises(ValueError, match="Expected list of records"):
            aggregate_straight_razor_specs("invalid")  # type: ignore

    def test_no_straight_razor_data(self):
        """Test with records that don't contain straight razors."""
        records = [
            {
                "id": "test123",
                "author": "testuser",
                "razor": {
                    "matched": {
                        "brand": "Blackland",
                        "model": "Blackbird",
                        "format": "DE",
                        "match_type": "exact",
                    },
                },
            }
        ]
        result = aggregate_straight_razor_specs(records)
        assert result == []

    def test_straight_razor_without_spec_data(self):
        """Test with straight razors that don't have specification data."""
        records = [
            {
                "id": "test123",
                "author": "testuser",
                "razor": {
                    "matched": {
                        "brand": "Dovo",
                        "model": "Classic",
                        "format": "Straight",
                        "match_type": "exact",
                    },
                    "enriched": {},
                },
            }
        ]
        result = aggregate_straight_razor_specs(records)
        assert result == []

    def test_single_spec_single_user(self):
        """Test with single specification and single user."""
        records = [
            {
                "id": "test123",
                "author": "testuser",
                "razor": {
                    "matched": {
                        "brand": "Dovo",
                        "model": "Classic",
                        "format": "Straight",
                        "match_type": "exact",
                    },
                    "enriched": {
                        "grind": "full_hollow",
                        "width": "6/8",
                        "point": "round",
                        "_enriched_by": "StraightRazorEnricher",
                        "_extraction_source": "user_comment",
                    },
                },
            }
        ]
        result = aggregate_straight_razor_specs(records)
        assert len(result) == 1
        assert result[0]["specs"] == "Grind: full_hollow | Width: 6/8 | Point: round"
        assert result[0]["shaves"] == 1
        assert result[0]["unique_users"] == 1
        assert result[0]["avg_shaves_per_user"] == 1.0

    def test_single_spec_multiple_users(self):
        """Test with single specification and multiple users."""
        records = [
            {
                "id": "test123",
                "author": "user1",
                "razor": {
                    "matched": {
                        "brand": "Dovo",
                        "model": "Classic",
                        "format": "Straight",
                        "match_type": "exact",
                    },
                    "enriched": {
                        "grind": "wedge",
                        "width": "7/8",
                        "_enriched_by": "StraightRazorEnricher",
                        "_extraction_source": "user_comment",
                    },
                },
            },
            {
                "id": "test456",
                "author": "user2",
                "razor": {
                    "matched": {
                        "brand": "Thiers-Issard",
                        "model": "Classic",
                        "format": "Straight",
                        "match_type": "exact",
                    },
                    "enriched": {
                        "grind": "wedge",
                        "width": "7/8",
                        "_enriched_by": "StraightRazorEnricher",
                        "_extraction_source": "user_comment",
                    },
                },
            },
        ]
        result = aggregate_straight_razor_specs(records)
        assert len(result) == 1
        assert result[0]["specs"] == "Grind: wedge | Width: 7/8"
        assert result[0]["shaves"] == 2
        assert result[0]["unique_users"] == 2
        assert result[0]["avg_shaves_per_user"] == 1.0

    def test_multiple_specs(self):
        """Test with multiple specifications."""
        records = [
            {
                "id": "test123",
                "author": "user1",
                "razor": {
                    "matched": {
                        "brand": "Dovo",
                        "model": "Classic",
                        "format": "Straight",
                        "match_type": "exact",
                    },
                    "enriched": {
                        "grind": "full_hollow",
                        "width": "6/8",
                        "point": "round",
                        "_enriched_by": "StraightRazorEnricher",
                        "_extraction_source": "user_comment",
                    },
                },
            },
            {
                "id": "test456",
                "author": "user2",
                "razor": {
                    "matched": {
                        "brand": "Thiers-Issard",
                        "model": "Classic",
                        "format": "Straight",
                        "match_type": "exact",
                    },
                    "enriched": {
                        "grind": "half_hollow",
                        "width": "5/8",
                        "point": "square",
                        "_enriched_by": "StraightRazorEnricher",
                        "_extraction_source": "user_comment",
                    },
                },
            },
            {
                "id": "test789",
                "author": "user3",
                "razor": {
                    "matched": {
                        "brand": "Boker",
                        "model": "Classic",
                        "format": "Straight",
                        "match_type": "exact",
                    },
                    "enriched": {
                        "grind": "wedge",
                        "width": "8/8",
                        "_enriched_by": "StraightRazorEnricher",
                        "_extraction_source": "user_comment",
                    },
                },
            },
        ]
        result = aggregate_straight_razor_specs(records)
        assert len(result) == 3

        # Check that results are sorted by shaves (descending)
        assert result[0]["shaves"] >= result[1]["shaves"]
        assert result[1]["shaves"] >= result[2]["shaves"]

        # Check all specs are present
        specs_list = [r["specs"] for r in result]
        assert "Grind: full_hollow | Width: 6/8 | Point: round" in specs_list
        assert "Grind: half_hollow | Width: 5/8 | Point: square" in specs_list
        assert "Grind: wedge | Width: 8/8" in specs_list

    def test_partial_specs(self):
        """Test with partial specifications (only some fields present)."""
        records = [
            {
                "id": "test123",
                "author": "user1",
                "razor": {
                    "matched": {
                        "brand": "Dovo",
                        "model": "Classic",
                        "format": "Straight",
                        "match_type": "exact",
                    },
                    "enriched": {
                        "grind": "full_hollow",
                        "_enriched_by": "StraightRazorEnricher",
                        "_extraction_source": "user_comment",
                    },
                },
            },
            {
                "id": "test456",
                "author": "user2",
                "razor": {
                    "matched": {
                        "brand": "Thiers-Issard",
                        "model": "Classic",
                        "format": "Straight",
                        "match_type": "exact",
                    },
                    "enriched": {
                        "width": "6/8",
                        "point": "round",
                        "_enriched_by": "StraightRazorEnricher",
                        "_extraction_source": "user_comment",
                    },
                },
            },
        ]
        result = aggregate_straight_razor_specs(records)
        assert len(result) == 2

        # Check partial specs are handled correctly
        specs_list = [r["specs"] for r in result]
        assert "Grind: full_hollow" in specs_list
        assert "Width: 6/8 | Point: round" in specs_list

    def test_mixed_razor_types(self):
        """Test with mix of straight razors and other razors."""
        records = [
            {
                "id": "test123",
                "author": "user1",
                "razor": {
                    "matched": {
                        "brand": "Dovo",
                        "model": "Classic",
                        "format": "Straight",
                        "match_type": "exact",
                    },
                    "enriched": {
                        "grind": "full_hollow",
                        "width": "6/8",
                        "point": "round",
                        "_enriched_by": "StraightRazorEnricher",
                        "_extraction_source": "user_comment",
                    },
                },
            },
            {
                "id": "test456",
                "author": "user2",
                "razor": {
                    "matched": {
                        "brand": "Blackland",
                        "model": "Blackbird",
                        "format": "DE",
                        "match_type": "exact",
                    },
                },
            },
        ]
        result = aggregate_straight_razor_specs(records)
        assert len(result) == 1
        assert result[0]["specs"] == "Grind: full_hollow | Width: 6/8 | Point: round"
        assert result[0]["shaves"] == 1

    def test_tiebreaker_unique_users(self):
        """Test tiebreaker when shaves are equal."""
        records = [
            {
                "id": "test123",
                "author": "user1",
                "razor": {
                    "matched": {
                        "brand": "Dovo",
                        "model": "Classic",
                        "format": "Straight",
                        "match_type": "exact",
                    },
                    "enriched": {
                        "grind": "full_hollow",
                        "width": "6/8",
                        "_enriched_by": "StraightRazorEnricher",
                        "_extraction_source": "user_comment",
                    },
                },
            },
            {
                "id": "test456",
                "author": "user2",
                "razor": {
                    "matched": {
                        "brand": "Thiers-Issard",
                        "model": "Classic",
                        "format": "Straight",
                        "match_type": "exact",
                    },
                    "enriched": {
                        "grind": "half_hollow",
                        "width": "5/8",
                        "_enriched_by": "StraightRazorEnricher",
                        "_extraction_source": "user_comment",
                    },
                },
            },
            {
                "id": "test789",
                "author": "user1",
                "razor": {
                    "matched": {
                        "brand": "Boker",
                        "model": "Classic",
                        "format": "Straight",
                        "match_type": "exact",
                    },
                    "enriched": {
                        "grind": "full_hollow",
                        "width": "6/8",
                        "_enriched_by": "StraightRazorEnricher",
                        "_extraction_source": "user_comment",
                    },
                },
            },
        ]
        result = aggregate_straight_razor_specs(records)
        assert len(result) == 2

        # Full hollow 6/8 should be first (2 shaves, 1 unique user)
        # Half hollow 5/8 should be second (1 shave, 1 unique user)
        assert result[0]["specs"] == "Grind: full_hollow | Width: 6/8"
        assert result[0]["shaves"] == 2
        assert result[0]["unique_users"] == 1
        assert result[1]["specs"] == "Grind: half_hollow | Width: 5/8"
        assert result[1]["shaves"] == 1
        assert result[1]["unique_users"] == 1


class TestAggregateRazorBladeCombinations:
    """Test the aggregate_razor_blade_combinations function."""

    def test_empty_records(self):
        """Test with empty records."""
        result = aggregate_razor_blade_combinations([])
        assert result == []

    def test_invalid_records_type(self):
        """Test with invalid records type."""
        with pytest.raises(ValueError, match="Expected list of records"):
            aggregate_razor_blade_combinations("invalid")  # type: ignore

    def test_no_razor_blade_data(self):
        """Test with records that have no razor or blade data."""
        records = [
            {
                "id": "test123",
                "author": "testuser",
                "created_utc": 1640995200,
                "body": "Test comment",
            }
        ]
        result = aggregate_razor_blade_combinations(records)
        assert result == []

    def test_missing_razor_data(self):
        """Test with records that have blade but no razor data."""
        records = [
            {
                "id": "test123",
                "author": "testuser",
                "created_utc": 1640995200,
                "body": "Test comment",
                "blade": {
                    "matched": {
                        "brand": "Feather",
                        "model": "Hi-Stainless",
                        "match_type": "exact",
                    }
                },
            }
        ]
        result = aggregate_razor_blade_combinations(records)
        assert result == []

    def test_missing_blade_data(self):
        """Test with records that have razor but no blade data."""
        records = [
            {
                "id": "test123",
                "author": "testuser",
                "created_utc": 1640995200,
                "body": "Test comment",
                "razor": {
                    "matched": {
                        "brand": "Blackland",
                        "model": "Blackbird",
                        "match_type": "exact",
                    }
                },
            }
        ]
        result = aggregate_razor_blade_combinations(records)
        assert result == []

    def test_single_combination_single_user(self):
        """Test with single razor-blade combination and single user."""
        records = [
            {
                "id": "test123",
                "author": "user1",
                "razor": {
                    "matched": {
                        "brand": "Blackland",
                        "model": "Blackbird",
                        "match_type": "exact",
                    }
                },
                "blade": {
                    "matched": {
                        "brand": "Feather",
                        "model": "Hi-Stainless",
                        "match_type": "exact",
                    }
                },
            }
        ]
        result = aggregate_razor_blade_combinations(records)
        assert len(result) == 1
        assert result[0]["combination"] == "Blackland Blackbird + Feather Hi-Stainless"
        assert result[0]["shaves"] == 1
        assert result[0]["unique_users"] == 1
        assert result[0]["avg_shaves_per_user"] == 1.0

    def test_single_combination_multiple_users(self):
        """Test with single razor-blade combination and multiple users."""
        records = [
            {
                "id": "test123",
                "author": "user1",
                "razor": {
                    "matched": {
                        "brand": "Blackland",
                        "model": "Blackbird",
                        "match_type": "exact",
                    }
                },
                "blade": {
                    "matched": {
                        "brand": "Feather",
                        "model": "Hi-Stainless",
                        "match_type": "exact",
                    }
                },
            },
            {
                "id": "test456",
                "author": "user2",
                "razor": {
                    "matched": {
                        "brand": "Blackland",
                        "model": "Blackbird",
                        "match_type": "exact",
                    }
                },
                "blade": {
                    "matched": {
                        "brand": "Feather",
                        "model": "Hi-Stainless",
                        "match_type": "exact",
                    }
                },
            },
        ]
        result = aggregate_razor_blade_combinations(records)
        assert len(result) == 1
        assert result[0]["combination"] == "Blackland Blackbird + Feather Hi-Stainless"
        assert result[0]["shaves"] == 2
        assert result[0]["unique_users"] == 2
        assert result[0]["avg_shaves_per_user"] == 1.0

    def test_multiple_combinations(self):
        """Test with multiple razor-blade combinations."""
        records = [
            {
                "id": "test123",
                "author": "user1",
                "razor": {
                    "matched": {
                        "brand": "Blackland",
                        "model": "Blackbird",
                        "match_type": "exact",
                    }
                },
                "blade": {
                    "matched": {
                        "brand": "Feather",
                        "model": "Hi-Stainless",
                        "match_type": "exact",
                    }
                },
            },
            {
                "id": "test456",
                "author": "user2",
                "razor": {
                    "matched": {
                        "brand": "Karve",
                        "model": "Christopher Bradley",
                        "match_type": "exact",
                    }
                },
                "blade": {
                    "matched": {
                        "brand": "Astra",
                        "model": "Superior Platinum",
                        "match_type": "exact",
                    }
                },
            },
            {
                "id": "test789",
                "author": "user3",
                "razor": {
                    "matched": {
                        "brand": "Blackland",
                        "model": "Blackbird",
                        "match_type": "exact",
                    }
                },
                "blade": {
                    "matched": {
                        "brand": "Feather",
                        "model": "Hi-Stainless",
                        "match_type": "exact",
                    }
                },
            },
        ]
        result = aggregate_razor_blade_combinations(records)
        assert len(result) == 2

        # Check that results are sorted by shaves (descending)
        assert result[0]["shaves"] >= result[1]["shaves"]

        # Check all combinations are present
        combinations_list = [r["combination"] for r in result]
        assert "Blackland Blackbird + Feather Hi-Stainless" in combinations_list
        assert "Karve Christopher Bradley + Astra Superior Platinum" in combinations_list

        # Blackland + Feather should be first (2 shaves)
        assert result[0]["combination"] == "Blackland Blackbird + Feather Hi-Stainless"
        assert result[0]["shaves"] == 2
        assert result[0]["unique_users"] == 2

        # Karve + Astra should be second (1 shave)
        assert result[1]["combination"] == "Karve Christopher Bradley + Astra Superior Platinum"
        assert result[1]["shaves"] == 1
        assert result[1]["unique_users"] == 1

    def test_tiebreaker_unique_users(self):
        """Test tiebreaker when shaves are equal."""
        records = [
            {
                "id": "test123",
                "author": "user1",
                "razor": {
                    "matched": {
                        "brand": "Blackland",
                        "model": "Blackbird",
                        "match_type": "exact",
                    }
                },
                "blade": {
                    "matched": {
                        "brand": "Feather",
                        "model": "Hi-Stainless",
                        "match_type": "exact",
                    }
                },
            },
            {
                "id": "test456",
                "author": "user2",
                "razor": {
                    "matched": {
                        "brand": "Karve",
                        "model": "Christopher Bradley",
                        "match_type": "exact",
                    }
                },
                "blade": {
                    "matched": {
                        "brand": "Astra",
                        "model": "Superior Platinum",
                        "match_type": "exact",
                    }
                },
            },
            {
                "id": "test789",
                "author": "user1",
                "razor": {
                    "matched": {
                        "brand": "Blackland",
                        "model": "Blackbird",
                        "match_type": "exact",
                    }
                },
                "blade": {
                    "matched": {
                        "brand": "Feather",
                        "model": "Hi-Stainless",
                        "match_type": "exact",
                    }
                },
            },
        ]
        result = aggregate_razor_blade_combinations(records)
        assert len(result) == 2

        # Blackland + Feather should be first (2 shaves, 1 unique user)
        # Karve + Astra should be second (1 shave, 1 unique user)
        assert result[0]["combination"] == "Blackland Blackbird + Feather Hi-Stainless"
        assert result[0]["shaves"] == 2
        assert result[0]["unique_users"] == 1
        assert result[1]["combination"] == "Karve Christopher Bradley + Astra Superior Platinum"
        assert result[1]["shaves"] == 1
        assert result[1]["unique_users"] == 1


class TestAggregateUserBladeUsage:
    """Test the aggregate_user_blade_usage function."""

    def test_empty_records(self):
        """Test with empty records."""
        result = aggregate_user_blade_usage([])
        assert result == []

    def test_invalid_records_type(self):
        """Test with invalid records type."""
        with pytest.raises(ValueError, match="Expected list of records"):
            aggregate_user_blade_usage("invalid")  # type: ignore

    def test_no_blade_data(self):
        """Test with records that have no blade data."""
        records = [
            {
                "id": "test123",
                "author": "testuser",
                "created_utc": 1640995200,
                "body": "Test comment",
            }
        ]
        result = aggregate_user_blade_usage(records)
        assert result == []

    def test_blade_without_use_count(self):
        """Test with records that have blade but no use count data."""
        records = [
            {
                "id": "test123",
                "author": "testuser",
                "created_utc": 1640995200,
                "body": "Test comment",
                "blade": {
                    "matched": {
                        "brand": "Feather",
                        "model": "Hi-Stainless",
                        "match_type": "exact",
                    }
                },
            }
        ]
        result = aggregate_user_blade_usage(records)
        assert result == []

    def test_single_user_single_blade(self):
        """Test with single user and single blade usage."""
        records = [
            {
                "id": "test123",
                "author": "user1",
                "blade": {
                    "matched": {
                        "brand": "Feather",
                        "model": "Hi-Stainless",
                        "match_type": "exact",
                    },
                    "enriched": {
                        "use_count": 3,
                        "_enriched_by": "BladeEnricher",
                        "_extraction_source": "user_comment",
                    },
                },
            }
        ]
        result = aggregate_user_blade_usage(records)
        assert len(result) == 1
        assert result[0]["user"] == "user1"
        assert result[0]["blade"] == "Feather Hi-Stainless"
        assert result[0]["avg_use_count"] == 3.0
        assert result[0]["shaves"] == 1
        assert result[0]["max_use_count"] == 3

    def test_single_user_multiple_blades(self):
        """Test with single user and multiple blade usages."""
        records = [
            {
                "id": "test123",
                "author": "user1",
                "blade": {
                    "matched": {
                        "brand": "Feather",
                        "model": "Hi-Stainless",
                        "match_type": "exact",
                    },
                    "enriched": {
                        "use_count": 3,
                        "_enriched_by": "BladeEnricher",
                        "_extraction_source": "user_comment",
                    },
                },
            },
            {
                "id": "test456",
                "author": "user1",
                "blade": {
                    "matched": {
                        "brand": "Astra",
                        "model": "Superior Platinum",
                        "match_type": "exact",
                    },
                    "enriched": {
                        "use_count": 5,
                        "_enriched_by": "BladeEnricher",
                        "_extraction_source": "user_comment",
                    },
                },
            },
        ]
        result = aggregate_user_blade_usage(records)
        assert len(result) == 2

        # Check that results are sorted by avg_use_count (descending)
        assert result[0]["avg_use_count"] >= result[1]["avg_use_count"]

        # Astra should be first (5 uses)
        assert result[0]["blade"] == "Astra Superior Platinum"
        assert result[0]["avg_use_count"] == 5.0
        assert result[0]["shaves"] == 1
        assert result[0]["max_use_count"] == 5

        # Feather should be second (3 uses)
        assert result[1]["blade"] == "Feather Hi-Stainless"
        assert result[1]["avg_use_count"] == 3.0
        assert result[1]["shaves"] == 1
        assert result[1]["max_use_count"] == 3

    def test_multiple_users_same_blade(self):
        """Test with multiple users using the same blade."""
        records = [
            {
                "id": "test123",
                "author": "user1",
                "blade": {
                    "matched": {
                        "brand": "Feather",
                        "model": "Hi-Stainless",
                        "match_type": "exact",
                    },
                    "enriched": {
                        "use_count": 3,
                        "_enriched_by": "BladeEnricher",
                        "_extraction_source": "user_comment",
                    },
                },
            },
            {
                "id": "test456",
                "author": "user2",
                "blade": {
                    "matched": {
                        "brand": "Feather",
                        "model": "Hi-Stainless",
                        "match_type": "exact",
                    },
                    "enriched": {
                        "use_count": 7,
                        "_enriched_by": "BladeEnricher",
                        "_extraction_source": "user_comment",
                    },
                },
            },
        ]
        result = aggregate_user_blade_usage(records)
        assert len(result) == 2

        # Check that results are sorted by avg_use_count (descending)
        assert result[0]["avg_use_count"] >= result[1]["avg_use_count"]

        # user2 should be first (7 uses)
        assert result[0]["user"] == "user2"
        assert result[0]["blade"] == "Feather Hi-Stainless"
        assert result[0]["avg_use_count"] == 7.0
        assert result[0]["shaves"] == 1
        assert result[0]["max_use_count"] == 7

        # user1 should be second (3 uses)
        assert result[1]["user"] == "user1"
        assert result[1]["blade"] == "Feather Hi-Stainless"
        assert result[1]["avg_use_count"] == 3.0
        assert result[1]["shaves"] == 1
        assert result[1]["max_use_count"] == 3

    def test_user_multiple_shaves_same_blade(self):
        """Test with user having multiple shaves with same blade and use count."""
        records = [
            {
                "id": "test123",
                "author": "user1",
                "blade": {
                    "matched": {
                        "brand": "Feather",
                        "model": "Hi-Stainless",
                        "match_type": "exact",
                    },
                    "enriched": {
                        "use_count": 3,
                        "_enriched_by": "BladeEnricher",
                        "_extraction_source": "user_comment",
                    },
                },
            },
            {
                "id": "test456",
                "author": "user1",
                "blade": {
                    "matched": {
                        "brand": "Feather",
                        "model": "Hi-Stainless",
                        "match_type": "exact",
                    },
                    "enriched": {
                        "use_count": 5,
                        "_enriched_by": "BladeEnricher",
                        "_extraction_source": "user_comment",
                    },
                },
            },
        ]
        result = aggregate_user_blade_usage(records)
        assert len(result) == 1

        # Average should be (3 + 5) / 2 = 4.0
        assert result[0]["user"] == "user1"
        assert result[0]["blade"] == "Feather Hi-Stainless"
        assert result[0]["avg_use_count"] == 4.0
        assert result[0]["shaves"] == 2
        assert result[0]["max_use_count"] == 5

    def test_tiebreaker_shaves(self):
        """Test tiebreaker when avg_use_count is equal."""
        records = [
            {
                "id": "test123",
                "author": "user1",
                "blade": {
                    "matched": {
                        "brand": "Feather",
                        "model": "Hi-Stainless",
                        "match_type": "exact",
                    },
                    "enriched": {
                        "use_count": 5,
                        "_enriched_by": "BladeEnricher",
                        "_extraction_source": "user_comment",
                    },
                },
            },
            {
                "id": "test456",
                "author": "user2",
                "blade": {
                    "matched": {
                        "brand": "Astra",
                        "model": "Superior Platinum",
                        "match_type": "exact",
                    },
                    "enriched": {
                        "use_count": 5,
                        "_enriched_by": "BladeEnricher",
                        "_extraction_source": "user_comment",
                    },
                },
            },
            {
                "id": "test789",
                "author": "user1",
                "blade": {
                    "matched": {
                        "brand": "Feather",
                        "model": "Hi-Stainless",
                        "match_type": "exact",
                    },
                    "enriched": {
                        "use_count": 5,
                        "_enriched_by": "BladeEnricher",
                        "_extraction_source": "user_comment",
                    },
                },
            },
        ]
        result = aggregate_user_blade_usage(records)
        assert len(result) == 2

        # user1 + Feather should be first (avg 5.0, 2 shaves)
        # user2 + Astra should be second (avg 5.0, 1 shave)
        assert result[0]["user"] == "user1"
        assert result[0]["blade"] == "Feather Hi-Stainless"
        assert result[0]["avg_use_count"] == 5.0
        assert result[0]["shaves"] == 2
        assert result[1]["user"] == "user2"
        assert result[1]["blade"] == "Astra Superior Platinum"
        assert result[1]["avg_use_count"] == 5.0
        assert result[1]["shaves"] == 1
