"""Unit tests for the aggregate engine module."""

import pytest

from sotd.aggregate.engine import (
    aggregate_blades,
    aggregate_brushes,
    aggregate_razors,
    aggregate_soaps,
    aggregate_users,
    calculate_basic_metrics,
    filter_matched_records,
    aggregate_brush_fibers,
    aggregate_brush_knot_sizes,
    aggregate_blackbird_plates,
    aggregate_christopher_bradley_plates,
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
            }
        ]
        result = aggregate_users(records)
        assert len(result) == 1
        assert result[0]["user"] == "testuser"
        assert result[0]["shaves"] == 1

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
        result = aggregate_users(records)
        assert len(result) == 1
        assert result[0]["user"] == "testuser"
        assert result[0]["shaves"] == 2

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
        result = aggregate_users(records)
        assert len(result) == 2
        # Should be sorted by shaves (descending)
        assert result[0]["user"] == "user1"
        assert result[0]["shaves"] == 2
        assert result[1]["user"] == "user2"
        assert result[1]["shaves"] == 1

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
        result = aggregate_users(records)
        assert len(result) == 1
        assert result[0]["user"] == "user1"
        assert result[0]["shaves"] == 1


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
