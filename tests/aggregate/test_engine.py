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
            filter_matched_records("invalid")

    def test_no_matched_products(self):
        """Test with records that have no matched products."""
        records = [
            {
                "id": "test123",
                "author": "testuser",
                "created_utc": 1640995200,
                "body": "Test comment",
                "razor": {
                    "matched": {
                        "brand": None,  # No brand, so not matched
                    }
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
                        "handle_maker": "Test Handle",
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
        result = filter_matched_records(records)
        assert result == []

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
                    "matched": {
                        "brand": None,  # Not matched
                    }
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
            calculate_basic_metrics("invalid")

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
            aggregate_razors("invalid")

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
        assert result[0]["razor_name"] == "Test Brand Test Model DE"
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
        assert result[0]["razor_name"] == "Test Brand Test Model"
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
        assert result[0]["razor_name"] == "Brand A Model A"
        assert result[1]["razor_name"] == "Brand B Model B"

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


class TestAggregateBlades:
    """Test the aggregate_blades function."""

    def test_empty_records(self):
        """Test with empty records."""
        result = aggregate_blades([])
        assert result == []

    def test_invalid_records_type(self):
        """Test with invalid records type."""
        with pytest.raises(ValueError, match="Expected list of records"):
            aggregate_blades("invalid")

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
        assert result[0]["blade_name"] == "Test Blade"
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
        assert result[0]["blade_name"] == "Blade A"
        assert result[1]["blade_name"] == "Blade B"


class TestAggregateSoaps:
    """Test the aggregate_soaps function."""

    def test_empty_records(self):
        """Test with empty records."""
        result = aggregate_soaps([])
        assert result == []

    def test_invalid_records_type(self):
        """Test with invalid records type."""
        with pytest.raises(ValueError, match="Expected list of records"):
            aggregate_soaps("invalid")

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
        assert result[0]["soap_name"] == "Test Maker Test Scent"
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
        assert result[0]["soap_name"] == "Maker A Scent A"
        assert result[1]["soap_name"] == "Maker B Scent B"


class TestAggregateBrushes:
    """Test the aggregate_brushes function."""

    def test_empty_records(self):
        """Test with empty records."""
        result = aggregate_brushes([])
        assert result == []

    def test_invalid_records_type(self):
        """Test with invalid records type."""
        with pytest.raises(ValueError, match="Expected list of records"):
            aggregate_brushes("invalid")

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
        assert result[0]["brush_name"] == "Test Handle Test Brush Badger 24mm"
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
                        "handle_maker": "Handle B",
                        "match_type": "exact",
                    }
                },
            },
        ]
        result = aggregate_brushes(records)
        assert len(result) == 2
        assert result[0]["brush_name"] == "Handle A Brush A"
        assert result[1]["brush_name"] == "Handle B Brush B"


class TestAggregateUsers:
    """Test the aggregate_users function."""

    def test_empty_records(self):
        """Test with empty records."""
        result = aggregate_users([])
        assert result == []

    def test_invalid_records_type(self):
        """Test with invalid records type."""
        with pytest.raises(ValueError, match="Expected list of records"):
            aggregate_users("invalid")

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
