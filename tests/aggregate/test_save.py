"""Unit tests for the aggregate save module."""

import json
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from sotd.aggregate.save import (
    get_aggregated_file_path,
    load_aggregated_data,
    save_aggregated_data,
    validate_aggregated_data,
)


class TestGetAggregatedFilePath:
    """Test the get_aggregated_file_path function."""

    def test_valid_year_month(self):
        """Test with valid year and month."""
        base_dir = Path("/data")
        path = get_aggregated_file_path(base_dir, 2025, 1)
        assert path == Path("/data/aggregated/2025-01.json")

    def test_single_digit_month(self):
        """Test with single digit month."""
        base_dir = Path("/data")
        path = get_aggregated_file_path(base_dir, 2025, 5)
        assert path == Path("/data/aggregated/2025-05.json")

    def test_double_digit_month(self):
        """Test with double digit month."""
        base_dir = Path("/data")
        path = get_aggregated_file_path(base_dir, 2025, 12)
        assert path == Path("/data/aggregated/2025-12.json")


class TestSaveAggregatedData:
    """Test the save_aggregated_data function."""

    def test_successful_save(self):
        """Test successful save of aggregated data."""
        results = {
            "year": 2025,
            "month": 1,
            "status": "success",
            "basic_metrics": {
                "total_shaves": 100,
                "unique_shavers": 50,
                "avg_shaves_per_user": 2.0,
            },
            "aggregations": {
                "razors": [{"name": "Test Razor", "shaves": 50}],
                "blades": [{"name": "Test Blade", "shaves": 30}],
                "soaps": [{"name": "Test Soap", "shaves": 40}],
                "brushes": [{"name": "Test Brush", "shaves": 25}],
                "users": [{"name": "Test User", "shaves": 10}],
                "razor_manufacturers": [],
                "blade_manufacturers": [],
                "soap_makers": [],
                "brush_knot_makers": [],
                "brush_handle_makers": [],
                "brush_fibers": [],
                "brush_knot_sizes": [],
                "blackbird_plates": [],
                "christopher_bradley_plates": [],
                "game_changer_plates": [],
                "super_speed_tips": [],
                "straight_razor_specs": [],
                "razor_blade_combinations": [],
                "user_blade_usage": [],
            },
            "summary": {
                "total_records": 100,
                "matched_records": 95,
                "razor_count": 1,
                "blade_count": 1,
                "soap_count": 1,
                "brush_count": 1,
                "user_count": 1,
            },
        }

        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "test_output.json"
            save_aggregated_data(results, output_path, force=False, debug=False)

            # Verify file was created
            assert output_path.exists()

            # Load and verify content
            with output_path.open("r") as f:
                content = json.load(f)

            # Check structure
            assert "meta" in content
            assert "data" in content

            # Check metadata
            meta = content["meta"]
            assert meta["month"] == "2025-01"
            assert "aggregated_at" in meta
            assert meta["total_shaves"] == 100
            assert meta["unique_shavers"] == 50
            assert meta["avg_shaves_per_user"] == 2.0
            assert "categories" in meta
            assert "summary" in meta

            # Check data
            data = content["data"]
            assert "razors" in data
            assert "blades" in data
            assert "soaps" in data
            assert "brushes" in data
            assert "users" in data

    def test_failed_aggregation_save(self):
        """Test saving failed aggregation results."""
        results = {
            "year": 2025,
            "month": 1,
            "status": "error",
            "error": "Test error message",
            "reason": "test_reason",
        }

        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "test_output.json"
            save_aggregated_data(results, output_path, force=False, debug=False)

            # Verify file was created
            assert output_path.exists()

            # Load and verify content
            with output_path.open("r") as f:
                content = json.load(f)

            # Check structure
            assert "meta" in content
            assert "data" in content

            # Check metadata for failed aggregation
            meta = content["meta"]
            assert meta["month"] == "2025-01"
            assert "aggregated_at" in meta
            assert meta["status"] == "error"
            assert meta["error"] == "Test error message"
            assert meta["reason"] == "test_reason"

            # Check data should be empty
            data = content["data"]
            assert data == {}

    def test_force_overwrite(self):
        """Test force overwrite functionality."""
        results = {
            "year": 2025,
            "month": 1,
            "status": "success",
            "basic_metrics": {
                "total_shaves": 100,
                "unique_shavers": 50,
                "avg_shaves_per_user": 2.0,
            },
            "aggregations": {
                "razors": [],
                "blades": [],
                "soaps": [],
                "brushes": [],
                "users": [],
                "razor_manufacturers": [],
                "blade_manufacturers": [],
                "soap_makers": [],
                "brush_knot_makers": [],
                "brush_handle_makers": [],
                "brush_fibers": [],
                "brush_knot_sizes": [],
                "blackbird_plates": [],
                "christopher_bradley_plates": [],
                "game_changer_plates": [],
                "super_speed_tips": [],
                "straight_razor_specs": [],
                "razor_blade_combinations": [],
                "user_blade_usage": [],
            },
            "summary": {
                "total_records": 100,
                "matched_records": 95,
                "razor_count": 0,
                "blade_count": 0,
                "soap_count": 0,
                "brush_count": 0,
                "user_count": 0,
            },
        }

        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "test_output.json"

            # Create initial file
            output_path.write_text('{"test": "initial"}')

            # Save with force=True
            save_aggregated_data(results, output_path, force=True, debug=False)

            # Verify file was overwritten
            assert output_path.exists()

            # Load and verify content was overwritten
            with output_path.open("r") as f:
                content = json.load(f)

            assert "meta" in content
            assert "data" in content
            assert content["meta"]["month"] == "2025-01"

    def test_file_exists_error(self):
        """Test error when file exists and force=False."""
        results = {
            "year": 2025,
            "month": 1,
            "status": "success",
            "basic_metrics": {
                "total_shaves": 100,
                "unique_shavers": 50,
                "avg_shaves_per_user": 2.0,
            },
            "aggregations": {
                "razors": [],
                "blades": [],
                "soaps": [],
                "brushes": [],
                "users": [],
                "razor_manufacturers": [],
                "blade_manufacturers": [],
                "soap_makers": [],
                "brush_knot_makers": [],
                "brush_handle_makers": [],
                "brush_fibers": [],
                "brush_knot_sizes": [],
                "blackbird_plates": [],
                "christopher_bradley_plates": [],
                "game_changer_plates": [],
                "super_speed_tips": [],
                "straight_razor_specs": [],
                "razor_blade_combinations": [],
                "user_blade_usage": [],
            },
            "summary": {
                "total_records": 100,
                "matched_records": 95,
                "razor_count": 0,
                "blade_count": 0,
                "soap_count": 0,
                "brush_count": 0,
                "user_count": 0,
            },
        }

        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "test_output.json"

            # Create initial file
            output_path.write_text('{"test": "initial"}')

            # Try to save without force
            with pytest.raises(FileExistsError, match="Aggregated file already exists"):
                save_aggregated_data(results, output_path, force=False, debug=False)

    def test_directory_creation(self):
        """Test that output directory is created if it doesn't exist."""
        results = {
            "year": 2025,
            "month": 1,
            "status": "success",
            "basic_metrics": {
                "total_shaves": 100,
                "unique_shavers": 50,
                "avg_shaves_per_user": 2.0,
            },
            "aggregations": {
                "razors": [],
                "blades": [],
                "soaps": [],
                "brushes": [],
                "users": [],
                "razor_manufacturers": [],
                "blade_manufacturers": [],
                "soap_makers": [],
                "brush_knot_makers": [],
                "brush_handle_makers": [],
                "brush_fibers": [],
                "brush_knot_sizes": [],
                "blackbird_plates": [],
                "christopher_bradley_plates": [],
                "game_changer_plates": [],
                "super_speed_tips": [],
                "straight_razor_specs": [],
                "razor_blade_combinations": [],
                "user_blade_usage": [],
            },
            "summary": {
                "total_records": 100,
                "matched_records": 95,
                "razor_count": 0,
                "blade_count": 0,
                "soap_count": 0,
                "brush_count": 0,
                "user_count": 0,
            },
        }

        with tempfile.TemporaryDirectory() as temp_dir:
            # Create path with non-existent subdirectories
            output_path = Path(temp_dir) / "aggregated" / "subdir" / "test_output.json"

            # Save should create the directory structure
            save_aggregated_data(results, output_path, force=False, debug=False)

            # Verify file and directory were created
            assert output_path.exists()
            assert output_path.parent.exists()

    def test_write_error(self):
        """Test handling of write errors."""
        results = {
            "year": 2025,
            "month": 1,
            "status": "success",
            "basic_metrics": {
                "total_shaves": 100,
                "unique_shavers": 50,
                "avg_shaves_per_user": 2.0,
            },
            "aggregations": {
                "razors": [],
                "blades": [],
                "soaps": [],
                "brushes": [],
                "users": [],
                "razor_manufacturers": [],
                "blade_manufacturers": [],
                "soap_makers": [],
                "brush_knot_makers": [],
                "brush_handle_makers": [],
                "brush_fibers": [],
                "brush_knot_sizes": [],
                "blackbird_plates": [],
                "christopher_bradley_plates": [],
                "game_changer_plates": [],
                "super_speed_tips": [],
                "straight_razor_specs": [],
                "razor_blade_combinations": [],
                "user_blade_usage": [],
            },
            "summary": {
                "total_records": 100,
                "matched_records": 95,
                "razor_count": 0,
                "blade_count": 0,
                "soap_count": 0,
                "brush_count": 0,
                "user_count": 0,
            },
        }

        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "test_output.json"

            # Patch Path.open to raise an OSError
            with patch.object(Path, "open", side_effect=OSError("Write error")):
                with pytest.raises(OSError, match="Failed to write aggregated file"):
                    save_aggregated_data(results, output_path, force=False, debug=False)


class TestLoadAggregatedData:
    """Test the load_aggregated_data function."""

    def test_load_valid_data(self):
        """Test loading valid aggregated data."""
        test_data = {
            "meta": {
                "month": "2025-01",
                "aggregated_at": "2025-01-21T18:40:00Z",
                "total_shaves": 100,
                "unique_shavers": 50,
                "avg_shaves_per_user": 2.0,
                "categories": ["razors", "blades", "soaps", "brushes", "users"],
            },
            "data": {
                "razors": [{"name": "Test Razor", "shaves": 50}],
                "blades": [{"name": "Test Blade", "shaves": 30}],
                "soaps": [{"name": "Test Soap", "shaves": 40}],
                "brushes": [{"name": "Test Brush", "shaves": 25}],
                "users": [{"name": "Test User", "shaves": 10}],
            },
        }

        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "test_data.json"
            with file_path.open("w") as f:
                json.dump(test_data, f)

            # Load the data
            loaded_data = load_aggregated_data(file_path, debug=False)

            # Verify structure
            assert "meta" in loaded_data
            assert "data" in loaded_data

            # Verify metadata
            meta = loaded_data["meta"]
            assert meta["month"] == "2025-01"
            assert meta["total_shaves"] == 100
            assert meta["unique_shavers"] == 50

            # Verify data
            data = loaded_data["data"]
            assert "razors" in data
            assert "blades" in data
            assert "soaps" in data
            assert "brushes" in data
            assert "users" in data

    def test_file_not_found(self):
        """Test error when file doesn't exist."""
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "nonexistent.json"

            with pytest.raises(FileNotFoundError, match="Aggregated data file not found"):
                load_aggregated_data(file_path, debug=False)

    def test_invalid_json(self):
        """Test error when file contains invalid JSON."""
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "invalid.json"
            file_path.write_text('{"invalid": json}')

            with pytest.raises(ValueError, match="Invalid JSON"):
                load_aggregated_data(file_path, debug=False)

    def test_missing_meta_section(self):
        """Test error when meta section is missing."""
        test_data = {
            "data": {
                "razors": [],
                "blades": [],
                "soaps": [],
                "brushes": [],
                "users": [],
            }
        }

        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "test_data.json"
            with file_path.open("w") as f:
                json.dump(test_data, f)

            with pytest.raises(ValueError, match="Missing 'meta' section"):
                load_aggregated_data(file_path, debug=False)

    def test_missing_data_section(self):
        """Test error when data section is missing."""
        test_data = {
            "meta": {
                "month": "2025-01",
                "aggregated_at": "2025-01-21T18:40:00Z",
            }
        }

        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "test_data.json"
            with file_path.open("w") as f:
                json.dump(test_data, f)

            with pytest.raises(ValueError, match="Missing 'data' section"):
                load_aggregated_data(file_path, debug=False)

    def test_invalid_meta_type(self):
        """Test error when meta is not a dict."""
        test_data = {
            "meta": "not a dict",
            "data": {
                "razors": [],
                "blades": [],
                "soaps": [],
                "brushes": [],
                "users": [],
            },
        }

        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "test_data.json"
            with file_path.open("w") as f:
                json.dump(test_data, f)

            with pytest.raises(ValueError, match="Expected dict for 'meta'"):
                load_aggregated_data(file_path, debug=False)

    def test_invalid_data_type(self):
        """Test error when data is not a dict."""
        test_data = {
            "meta": {
                "month": "2025-01",
                "aggregated_at": "2025-01-21T18:40:00Z",
            },
            "data": "not a dict",
        }

        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "test_data.json"
            with file_path.open("w") as f:
                json.dump(test_data, f)

            with pytest.raises(ValueError, match="Expected dict for 'data'"):
                load_aggregated_data(file_path, debug=False)


class TestValidateAggregatedData:
    """Test the validate_aggregated_data function."""

    def test_valid_data(self):
        """Test validation of valid aggregated data."""
        data = {
            "meta": {
                "month": "2025-01",
                "aggregated_at": "2025-01-21T18:40:00Z",
                "total_shaves": 100,
                "unique_shavers": 50,
            },
            "data": {
                "razors": [],
                "blades": [],
                "soaps": [],
                "brushes": [],
                "users": [],
            },
        }

        assert validate_aggregated_data(data, debug=False) is True

    def test_not_dict(self):
        """Test validation with non-dict data."""
        data = {"invalid": True}  # Use a dict with wrong structure
        assert validate_aggregated_data(data, debug=False) is False

    def test_missing_meta(self):
        """Test validation with missing meta section."""
        data = {
            "data": {
                "razors": [],
                "blades": [],
                "soaps": [],
                "brushes": [],
                "users": [],
            }
        }
        assert validate_aggregated_data(data, debug=False) is False

    def test_missing_data(self):
        """Test validation with missing data section."""
        data = {
            "meta": {
                "month": "2025-01",
                "aggregated_at": "2025-01-21T18:40:00Z",
            }
        }
        assert validate_aggregated_data(data, debug=False) is False

    def test_meta_not_dict(self):
        """Test validation with meta not being a dict."""
        data = {
            "meta": "not a dict",
            "data": {
                "razors": [],
                "blades": [],
                "soaps": [],
                "brushes": [],
                "users": [],
            },
        }
        assert validate_aggregated_data(data, debug=False) is False

    def test_data_not_dict(self):
        """Test validation with data not being a dict."""
        data = {
            "meta": {
                "month": "2025-01",
                "aggregated_at": "2025-01-21T18:40:00Z",
            },
            "data": "not a dict",
        }
        assert validate_aggregated_data(data, debug=False) is False

    def test_missing_required_meta_fields(self):
        """Test validation with missing required metadata fields."""
        data = {
            "meta": {
                "total_shaves": 100,
                "unique_shavers": 50,
                # Missing month and aggregated_at
            },
            "data": {
                "razors": [],
                "blades": [],
                "soaps": [],
                "brushes": [],
                "users": [],
            },
        }
        assert validate_aggregated_data(data, debug=False) is False

    def test_invalid_month_format(self):
        """Test validation with invalid month format."""
        data = {
            "meta": {
                "month": "invalid-format",
                "aggregated_at": "2025-01-21T18:40:00Z",
            },
            "data": {
                "razors": [],
                "blades": [],
                "soaps": [],
                "brushes": [],
                "users": [],
            },
        }
        assert validate_aggregated_data(data, debug=False) is False

    def test_debug_output(self):
        """Test that debug output is provided when debug=True."""
        data = {"invalid": True}  # Use a dict with wrong structure

        # Capture print output
        with patch("builtins.print") as mock_print:
            result = validate_aggregated_data(data, debug=True)
            assert result is False
            mock_print.assert_called()
