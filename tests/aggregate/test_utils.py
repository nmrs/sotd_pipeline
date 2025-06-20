"""Tests for aggregate utility functions."""

import pytest

from sotd.aggregate.processor import validate_records, normalize_fields, check_data_quality
from sotd.aggregate.utils.metrics import (
    calculate_metadata,
    calculate_unique_soaps,
    calculate_unique_brands,
)


class TestMetrics:
    """Test metric calculation functions."""

    def test_calculate_metadata_basic(self):
        """Test basic metadata calculation."""
        records = [
            {"author": "user1"},
            {"author": "user2"},
            {"author": "user1"},
            {"author": "user3"},
        ]

        meta = calculate_metadata(records, "2025-01")

        assert meta["month"] == "2025-01"
        assert meta["total_shaves"] == 4
        assert meta["unique_shavers"] == 3
        assert meta["avg_shaves_per_user"] == 1.33  # Rounded to 2 decimal places
        assert meta["unique_soaps"] == 0  # No soap data in these records
        assert meta["unique_brands"] == 0  # No soap data in these records

    def test_calculate_metadata_empty(self):
        """Test metadata calculation with empty records."""
        meta = calculate_metadata([], "2025-01")

        assert meta["month"] == "2025-01"
        assert meta["total_shaves"] == 0
        assert meta["unique_shavers"] == 0
        assert meta["avg_shaves_per_user"] == 0.0
        assert meta["unique_soaps"] == 0
        assert meta["unique_brands"] == 0

    def test_calculate_metadata_single_user(self):
        """Test metadata calculation with single user."""
        records = [
            {"author": "user1"},
            {"author": "user1"},
            {"author": "user1"},
        ]

        meta = calculate_metadata(records, "2025-01")

        assert meta["total_shaves"] == 3
        assert meta["unique_shavers"] == 1
        assert meta["avg_shaves_per_user"] == 3.0
        assert meta["unique_soaps"] == 0
        assert meta["unique_brands"] == 0

    def test_calculate_unique_soaps_basic(self):
        """Test unique soaps calculation."""
        records = [
            {
                "author": "user1",
                "soap": {"matched": {"maker": "Declaration Grooming", "scent": "Sellout"}},
            },
            {
                "author": "user2",
                "soap": {"matched": {"maker": "Declaration Grooming", "scent": "Sellout"}},
            },
            {
                "author": "user1",
                "soap": {"matched": {"maker": "Stirling", "scent": "Executive Man"}},
            },
        ]

        unique_soaps = calculate_unique_soaps(records)
        assert unique_soaps == 2  # "Declaration Grooming - Sellout" and "Stirling - Executive Man"

    def test_calculate_unique_soaps_no_matches(self):
        """Test unique soaps calculation with no matched soaps."""
        records = [
            {"author": "user1", "soap": {"original": "Unknown Soap"}},
            {
                "author": "user2",
                "soap": {"matched": {"maker": "Declaration Grooming"}},
            },  # Missing scent
        ]

        unique_soaps = calculate_unique_soaps(records)
        assert unique_soaps == 0

    def test_calculate_unique_soaps_empty(self):
        """Test unique soaps calculation with empty records."""
        unique_soaps = calculate_unique_soaps([])
        assert unique_soaps == 0

    def test_calculate_unique_brands_basic(self):
        """Test unique brands calculation."""
        records = [
            {
                "author": "user1",
                "soap": {"matched": {"maker": "Declaration Grooming", "scent": "Sellout"}},
            },
            {
                "author": "user2",
                "soap": {"matched": {"maker": "Declaration Grooming", "scent": "Darkfall"}},
            },
            {
                "author": "user1",
                "soap": {"matched": {"maker": "Stirling", "scent": "Executive Man"}},
            },
        ]

        unique_brands = calculate_unique_brands(records)
        assert unique_brands == 2  # "Declaration Grooming" and "Stirling"

    def test_calculate_unique_brands_no_matches(self):
        """Test unique brands calculation with no matched soaps."""
        records = [
            {"author": "user1", "soap": {"original": "Unknown Soap"}},
            {"author": "user2", "soap": {"matched": {"scent": "Some Scent"}}},  # Missing maker
        ]

        unique_brands = calculate_unique_brands(records)
        assert unique_brands == 0

    def test_calculate_unique_brands_empty(self):
        """Test unique brands calculation with empty records."""
        unique_brands = calculate_unique_brands([])
        assert unique_brands == 0

    def test_calculate_metadata_with_soap_data(self):
        """Test metadata calculation with soap data."""
        records = [
            {
                "author": "user1",
                "soap": {"matched": {"maker": "Declaration Grooming", "scent": "Sellout"}},
            },
            {
                "author": "user2",
                "soap": {"matched": {"maker": "Declaration Grooming", "scent": "Darkfall"}},
            },
            {
                "author": "user1",
                "soap": {"matched": {"maker": "Stirling", "scent": "Executive Man"}},
            },
        ]

        meta = calculate_metadata(records, "2025-01")

        assert meta["month"] == "2025-01"
        assert meta["total_shaves"] == 3
        assert meta["unique_shavers"] == 2
        assert meta["avg_shaves_per_user"] == 1.5
        assert meta["unique_soaps"] == 3  # 3 unique soap names
        assert meta["unique_brands"] == 2  # 2 unique makers


class TestValidation:
    """Test data validation functions."""

    def test_validate_records_valid(self):
        """Test validation with valid records."""
        records = [
            {"author": "user1", "razor": {"matched": {"brand": "Gillette"}}},
            {"author": "user2", "blade": {"matched": {"brand": "Personna"}}},
        ]

        result = validate_records(records)
        assert result == records

    def test_validate_records_invalid_type(self):
        """Test validation with invalid record type."""
        with pytest.raises(ValueError, match="Records must be a list"):
            validate_records("not a list")  # type: ignore

    def test_validate_records_missing_author(self):
        """Test validation with missing author field."""
        records = [
            {"razor": {"matched": {"brand": "Gillette"}}},
        ]

        with pytest.raises(ValueError, match="Each record must have an 'author' field"):
            validate_records(records)

    def test_normalize_fields(self):
        """Test field normalization."""
        records = [
            {
                "author": "  user1  ",
                "razor": {"matched": {"brand": "  Gillette  ", "model": "Tech"}},
            },
            {
                "author": "user2",
                "blade": {"matched": {"brand": "Personna", "model": "  Lab Blue  "}},
            },
        ]

        result = normalize_fields(records)

        assert result[0]["author"] == "user1"
        assert result[0]["razor"]["matched"]["brand"] == "Gillette"
        assert result[1]["blade"]["matched"]["model"] == "Lab Blue"

    def test_check_data_quality_valid(self):
        """Test data quality check with valid data."""
        records = [
            {"author": "user1"},
            {"author": "user2"},
        ]

        # Should not raise
        check_data_quality(records)

    def test_check_data_quality_empty(self):
        """Test data quality check with empty data."""
        # Should not raise for empty data
        check_data_quality([])

    def test_check_data_quality_no_authors(self):
        """Test data quality check with no valid authors."""
        records = [
            {"author": ""},
            {"author": None},
        ]

        # Should raise an error when there are no valid authors
        with pytest.raises(ValueError, match="No valid authors found in records"):
            check_data_quality(records)
