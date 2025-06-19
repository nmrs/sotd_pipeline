"""Unit tests for the aggregate load module."""

import json
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from sotd.aggregate.load import (
    get_enriched_file_path,
    load_enriched_data,
    validate_enriched_record,
    validate_match_type,
)


class TestGetEnrichedFilePath:
    """Test the get_enriched_file_path function."""

    def test_valid_year_month(self):
        """Test with valid year and month."""
        base_dir = Path("/tmp")
        result = get_enriched_file_path(base_dir, 2025, 4)
        expected = Path("/tmp/enriched/2025-04.json")
        assert result == expected

    def test_single_digit_month(self):
        """Test with single digit month (should be zero-padded)."""
        base_dir = Path("/tmp")
        result = get_enriched_file_path(base_dir, 2025, 1)
        expected = Path("/tmp/enriched/2025-01.json")
        assert result == expected

    def test_double_digit_month(self):
        """Test with double digit month."""
        base_dir = Path("/tmp")
        result = get_enriched_file_path(base_dir, 2025, 12)
        expected = Path("/tmp/enriched/2025-12.json")
        assert result == expected


class TestValidateEnrichedRecord:
    """Test the validate_enriched_record function."""

    def test_valid_record(self):
        """Test with a valid enriched record."""
        record = {
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
        assert validate_enriched_record(record, 0) is True

    def test_missing_required_fields(self):
        """Test with missing required fields."""
        record = {
            "id": "test123",
            "author": "testuser",
            # Missing created_utc and body
        }
        assert validate_enriched_record(record, 0) is False

    def test_invalid_field_types(self):
        """Test with invalid field types."""
        record = {
            "id": 123,  # Should be string
            "author": "testuser",
            "created_utc": "invalid",  # Should be numeric
            "body": "Test comment",
        }
        assert validate_enriched_record(record, 0) is False

    def test_invalid_product_structure(self):
        """Test with invalid product structure."""
        record = {
            "id": "test123",
            "author": "testuser",
            "created_utc": 1640995200,
            "body": "Test comment",
            "razor": "invalid",  # Should be dict
        }
        assert validate_enriched_record(record, 0) is False

    def test_invalid_match_type(self):
        """Test with invalid match_type."""
        record = {
            "id": "test123",
            "author": "testuser",
            "created_utc": 1640995200,
            "body": "Test comment",
            "razor": {
                "matched": {
                    "brand": "Test Brand",
                    "match_type": "invalid_type",  # Invalid match_type
                }
            },
        }
        assert validate_enriched_record(record, 0) is False

    def test_valid_match_types(self):
        """Test with all valid match types."""
        valid_types = ["exact", "fuzzy", "manual", "unmatched"]
        for match_type in valid_types:
            record = {
                "id": "test123",
                "author": "testuser",
                "created_utc": 1640995200,
                "body": "Test comment",
                "razor": {
                    "matched": {
                        "brand": "Test Brand",
                        "match_type": match_type,
                    }
                },
            }
            assert validate_enriched_record(record, 0) is True


class TestValidateMatchType:
    """Test the validate_match_type function."""

    def test_valid_match_types(self):
        """Test with valid match types."""
        valid_types = ["exact", "fuzzy", "manual", "unmatched"]
        for match_type in valid_types:
            assert validate_match_type(match_type, "razor", 0) is True

    def test_invalid_match_type(self):
        """Test with invalid match type."""
        assert validate_match_type("invalid", "razor", 0) is False

    def test_non_string_match_type(self):
        """Test with non-string match type."""
        assert validate_match_type("invalid", "razor", 0) is False
        assert validate_match_type(123, "razor", 0) is False  # type: ignore
        assert validate_match_type(None, "razor", 0) is False  # type: ignore


class TestLoadEnrichedData:
    """Test the load_enriched_data function."""

    def test_load_valid_data(self):
        """Test loading valid enriched data."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            data = {
                "meta": {
                    "month": "2025-04",
                    "extracted_at": "2025-04-21T18:40:00Z",
                },
                "data": [
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
                ],
            }
            json.dump(data, f)
            f.flush()

            try:
                metadata, records = load_enriched_data(Path(f.name))
                assert metadata == data["meta"]
                assert len(records) == 1
                assert records[0]["id"] == "test123"
            finally:
                Path(f.name).unlink()

    def test_file_not_found(self):
        """Test with non-existent file."""
        with pytest.raises(FileNotFoundError):
            load_enriched_data(Path("/nonexistent/file.json"))

    def test_empty_file(self):
        """Test with empty file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write("")
            f.flush()

            try:
                with pytest.raises(ValueError, match="Enriched data file is empty"):
                    load_enriched_data(Path(f.name))
            finally:
                Path(f.name).unlink()

    def test_invalid_json(self):
        """Test with invalid JSON."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write('{"invalid": json}')
            f.flush()

            try:
                with pytest.raises(ValueError, match="Invalid JSON"):
                    load_enriched_data(Path(f.name))
            finally:
                Path(f.name).unlink()

    def test_missing_meta_section(self):
        """Test with missing meta section."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            data = {
                "data": [
                    {
                        "id": "test123",
                        "author": "testuser",
                        "created_utc": 1640995200,
                        "body": "Test comment",
                    }
                ],
            }
            json.dump(data, f)
            f.flush()

            try:
                with pytest.raises(ValueError, match="Missing 'meta' section"):
                    load_enriched_data(Path(f.name))
            finally:
                Path(f.name).unlink()

    def test_missing_data_section(self):
        """Test with missing data section."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            data = {
                "meta": {
                    "month": "2025-04",
                    "extracted_at": "2025-04-21T18:40:00Z",
                },
            }
            json.dump(data, f)
            f.flush()

            try:
                with pytest.raises(ValueError, match="Missing 'data' section"):
                    load_enriched_data(Path(f.name))
            finally:
                Path(f.name).unlink()

    def test_invalid_metadata(self):
        """Test with invalid metadata."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            data = {
                "meta": "invalid",  # Should be dict
                "data": [],
            }
            json.dump(data, f)
            f.flush()

            try:
                with pytest.raises(ValueError, match="Expected dict for 'meta'"):
                    load_enriched_data(Path(f.name))
            finally:
                Path(f.name).unlink()

    def test_invalid_data_structure(self):
        """Test with invalid data structure."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            data = {
                "meta": {
                    "month": "2025-04",
                    "extracted_at": "2025-04-21T18:40:00Z",
                },
                "data": "invalid",  # Should be list
            }
            json.dump(data, f)
            f.flush()

            try:
                with pytest.raises(ValueError, match="Expected list for 'data'"):
                    load_enriched_data(Path(f.name))
            finally:
                Path(f.name).unlink()

    def test_invalid_metadata_fields(self):
        """Test with invalid metadata fields."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            data = {
                "meta": {
                    # Missing required fields
                },
                "data": [],
            }
            json.dump(data, f)
            f.flush()

            try:
                with pytest.raises(ValueError, match="Missing required metadata field"):
                    load_enriched_data(Path(f.name))
            finally:
                Path(f.name).unlink()

    def test_invalid_month_format(self):
        """Test with invalid month format."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            data = {
                "meta": {
                    "month": "2025",  # Invalid format
                    "extracted_at": "2025-04-21T18:40:00Z",
                },
                "data": [],
            }
            json.dump(data, f)
            f.flush()

            try:
                with pytest.raises(ValueError, match="Invalid month format"):
                    load_enriched_data(Path(f.name))
            finally:
                Path(f.name).unlink()

    def test_data_quality_issues(self):
        """Test with data quality issues (more invalid than valid records)."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            data = {
                "meta": {
                    "month": "2025-04",
                    "extracted_at": "2025-04-21T18:40:00Z",
                },
                "data": [
                    # Valid record
                    {
                        "id": "test123",
                        "author": "testuser",
                        "created_utc": 1640995200,
                        "body": "Test comment",
                    },
                    # Invalid record (missing fields)
                    {"id": "test456"},
                    # Invalid record (missing fields)
                    {"author": "testuser2"},
                ],
            }
            json.dump(data, f)
            f.flush()

            try:
                with pytest.raises(ValueError, match="Data quality issue"):
                    load_enriched_data(Path(f.name))
            finally:
                Path(f.name).unlink()

    def test_no_valid_records(self):
        """Test with no valid records."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            data = {
                "meta": {
                    "month": "2025-04",
                    "extracted_at": "2025-04-21T18:40:00Z",
                },
                "data": [
                    {"id": "test123"},  # Invalid record
                    {"author": "testuser"},  # Invalid record
                ],
            }
            json.dump(data, f)
            f.flush()

            try:
                with pytest.raises(ValueError, match="No valid records found"):
                    load_enriched_data(Path(f.name))
            finally:
                Path(f.name).unlink()

    def test_some_invalid_records_ok(self):
        """Test with some invalid records (less than half)."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            data = {
                "meta": {
                    "month": "2025-04",
                    "extracted_at": "2025-04-21T18:40:00Z",
                },
                "data": [
                    # Valid records
                    {
                        "id": "test123",
                        "author": "testuser",
                        "created_utc": 1640995200,
                        "body": "Test comment",
                    },
                    {
                        "id": "test456",
                        "author": "testuser2",
                        "created_utc": 1640995201,
                        "body": "Test comment 2",
                    },
                    # Invalid record (less than half)
                    {"id": "test789"},
                ],
            }
            json.dump(data, f)
            f.flush()

            try:
                metadata, records = load_enriched_data(Path(f.name))
                assert len(records) == 2  # Only valid records returned
                assert records[0]["id"] == "test123"
                assert records[1]["id"] == "test456"
            finally:
                Path(f.name).unlink()

    @patch("sotd.aggregate.load.Path.stat")
    def test_file_access_error(self, mock_stat):
        """Test with file access error."""
        mock_stat.side_effect = OSError("Permission denied")

        with pytest.raises(OSError, match="Permission denied"):
            load_enriched_data(Path("/tmp/test.json"))

    def test_unicode_decode_error(self):
        """Test with Unicode decode error."""
        with tempfile.NamedTemporaryFile(mode="wb", suffix=".json", delete=False) as f:
            # Write invalid UTF-8 bytes
            f.write(b"\xff\xfe\xfd")
            f.flush()

            try:
                with pytest.raises(ValueError, match="Unicode decode error"):
                    load_enriched_data(Path(f.name))
            finally:
                Path(f.name).unlink()
