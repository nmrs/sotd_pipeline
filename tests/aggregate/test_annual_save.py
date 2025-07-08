"""
Tests for annual data saving functionality.

This module tests the annual data saving functionality, including file format,
metadata structure, error handling, and integration with existing save patterns.
"""

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from sotd.aggregate.annual_engine import save_annual_data


class TestSaveAnnualData:
    """Test the save_annual_data function."""

    def test_save_annual_data_creates_directory_structure(self, tmp_path):
        """Test that save_annual_data creates the necessary directory structure."""
        data_dir = tmp_path / "data"
        aggregated_dir = data_dir / "aggregated"
        annual_dir = aggregated_dir / "annual"

        # Ensure directories don't exist initially
        assert not annual_dir.exists()

        # Sample annual data
        annual_data = {
            "metadata": {
                "year": "2024",
                "total_shaves": 1200,
                "unique_shavers": 300,
                "included_months": ["2024-01", "2024-02", "2024-03"],
                "missing_months": ["2024-04", "2024-05"],
            },
            "razors": [{"name": "Razor A", "shaves": 100, "unique_users": 50, "position": 1}],
            "blades": [{"name": "Blade A", "shaves": 150, "unique_users": 75, "position": 1}],
            "brushes": [{"name": "Brush A", "shaves": 80, "unique_users": 40, "position": 1}],
            "soaps": [{"name": "Soap A", "shaves": 200, "unique_users": 100, "position": 1}],
        }

        save_annual_data(annual_data, "2024", data_dir)

        # Verify directory structure was created
        assert annual_dir.exists()
        assert annual_dir.is_dir()

    def test_save_annual_data_creates_correct_file(self, tmp_path):
        """Test that save_annual_data creates the correct file with proper naming."""
        data_dir = tmp_path / "data"
        annual_file = data_dir / "aggregated" / "annual" / "2024.json"

        # Sample annual data
        annual_data = {
            "metadata": {
                "year": "2024",
                "total_shaves": 1200,
                "unique_shavers": 300,
                "included_months": ["2024-01", "2024-02"],
                "missing_months": [],
            },
            "razors": [],
            "blades": [],
            "brushes": [],
            "soaps": [],
        }

        save_annual_data(annual_data, "2024", data_dir)

        # Verify file was created
        assert annual_file.exists()
        assert annual_file.is_file()

    def test_save_annual_data_file_content_structure(self, tmp_path):
        """Test that saved file has correct content structure."""
        data_dir = tmp_path / "data"
        annual_file = data_dir / "aggregated" / "annual" / "2024.json"

        # Sample annual data
        annual_data = {
            "metadata": {
                "year": "2024",
                "total_shaves": 1200,
                "unique_shavers": 300,
                "included_months": ["2024-01", "2024-02"],
                "missing_months": [],
            },
            "razors": [{"name": "Razor A", "shaves": 100, "unique_users": 50, "position": 1}],
            "blades": [{"name": "Blade A", "shaves": 150, "unique_users": 75, "position": 1}],
            "brushes": [{"name": "Brush A", "shaves": 80, "unique_users": 40, "position": 1}],
            "soaps": [{"name": "Soap A", "shaves": 200, "unique_users": 100, "position": 1}],
        }

        save_annual_data(annual_data, "2024", data_dir)

        # Load and verify file content
        with open(annual_file, "r") as f:
            loaded_data = json.load(f)

        # Verify structure
        assert "metadata" in loaded_data
        assert "razors" in loaded_data
        assert "blades" in loaded_data
        assert "brushes" in loaded_data
        assert "soaps" in loaded_data

        # Verify metadata
        metadata = loaded_data["metadata"]
        assert metadata["year"] == "2024"
        assert metadata["total_shaves"] == 1200
        assert metadata["unique_shavers"] == 300
        assert metadata["included_months"] == ["2024-01", "2024-02"]
        assert metadata["missing_months"] == []

        # Verify data categories
        assert len(loaded_data["razors"]) == 1
        assert loaded_data["razors"][0]["name"] == "Razor A"
        assert len(loaded_data["blades"]) == 1
        assert loaded_data["blades"][0]["name"] == "Blade A"
        assert len(loaded_data["brushes"]) == 1
        assert loaded_data["brushes"][0]["name"] == "Brush A"
        assert len(loaded_data["soaps"]) == 1
        assert loaded_data["soaps"][0]["name"] == "Soap A"

    def test_save_annual_data_preserves_data_integrity(self, tmp_path):
        """Test that save_annual_data preserves all data without modification."""
        data_dir = tmp_path / "data"
        annual_file = data_dir / "aggregated" / "annual" / "2024.json"

        # Complex annual data with various data types
        annual_data = {
            "metadata": {
                "year": "2024",
                "total_shaves": 1200,
                "unique_shavers": 300,
                "included_months": ["2024-01", "2024-02", "2024-03"],
                "missing_months": ["2024-04", "2024-05"],
            },
            "razors": [
                {"name": "Razor A", "shaves": 100, "unique_users": 50, "position": 1},
                {"name": "Razor B", "shaves": 80, "unique_users": 40, "position": 2},
            ],
            "blades": [
                {"name": "Blade A", "shaves": 150, "unique_users": 75, "position": 1},
                {"name": "Blade B", "shaves": 120, "unique_users": 60, "position": 2},
            ],
            "brushes": [
                {"name": "Brush A", "shaves": 80, "unique_users": 40, "position": 1},
                {"name": "Brush B", "shaves": 60, "unique_users": 30, "position": 2},
            ],
            "soaps": [
                {"name": "Soap A", "shaves": 200, "unique_users": 100, "position": 1},
                {"name": "Soap B", "shaves": 180, "unique_users": 90, "position": 2},
            ],
        }

        save_annual_data(annual_data, "2024", data_dir)

        # Load and verify data integrity
        with open(annual_file, "r") as f:
            loaded_data = json.load(f)

        # Verify exact data preservation
        assert loaded_data == annual_data

    def test_save_annual_data_empty_data(self, tmp_path):
        """Test saving annual data with empty product categories."""
        data_dir = tmp_path / "data"
        annual_file = data_dir / "aggregated" / "annual" / "2024.json"

        # Annual data with empty categories
        annual_data = {
            "metadata": {
                "year": "2024",
                "total_shaves": 0,
                "unique_shavers": 0,
                "included_months": [],
                "missing_months": ["2024-01", "2024-02", "2024-03"],
            },
            "razors": [],
            "blades": [],
            "brushes": [],
            "soaps": [],
        }

        save_annual_data(annual_data, "2024", data_dir)

        # Verify file was created and contains empty data
        assert annual_file.exists()
        with open(annual_file, "r") as f:
            loaded_data = json.load(f)

        assert loaded_data["metadata"]["total_shaves"] == 0
        assert loaded_data["metadata"]["unique_shavers"] == 0
        assert len(loaded_data["razors"]) == 0
        assert len(loaded_data["blades"]) == 0
        assert len(loaded_data["brushes"]) == 0
        assert len(loaded_data["soaps"]) == 0

    def test_save_annual_data_overwrites_existing_file(self, tmp_path):
        """Test that save_annual_data overwrites existing files."""
        data_dir = tmp_path / "data"
        annual_file = data_dir / "aggregated" / "annual" / "2024.json"

        # Create initial file with different data
        annual_file.parent.mkdir(parents=True, exist_ok=True)
        initial_data = {
            "metadata": {"year": "2024", "total_shaves": 0, "unique_shavers": 0},
            "razors": [],
            "blades": [],
            "brushes": [],
            "soaps": [],
        }
        with open(annual_file, "w") as f:
            json.dump(initial_data, f, ensure_ascii=False)

        # New data to save
        new_data = {
            "metadata": {
                "year": "2024",
                "total_shaves": 1200,
                "unique_shavers": 300,
                "included_months": ["2024-01"],
                "missing_months": [],
            },
            "razors": [{"name": "New Razor", "shaves": 100, "unique_users": 50, "position": 1}],
            "blades": [],
            "brushes": [],
            "soaps": [],
        }

        save_annual_data(new_data, "2024", data_dir)

        # Verify file was overwritten with new data
        with open(annual_file, "r") as f:
            loaded_data = json.load(f)

        assert loaded_data == new_data
        assert loaded_data["metadata"]["total_shaves"] == 1200
        assert len(loaded_data["razors"]) == 1
        assert loaded_data["razors"][0]["name"] == "New Razor"

    @patch("sotd.utils.file_io.save_json_data")
    def test_save_annual_data_uses_unified_file_io(self, mock_save_json, tmp_path):
        """Test that save_annual_data uses the unified file I/O utilities."""
        data_dir = tmp_path / "data"
        annual_file = data_dir / "aggregated" / "annual" / "2024.json"

        # Sample annual data
        annual_data = {
            "metadata": {
                "year": "2024",
                "total_shaves": 1200,
                "unique_shavers": 300,
                "included_months": ["2024-01"],
                "missing_months": [],
            },
            "razors": [],
            "blades": [],
            "brushes": [],
            "soaps": [],
        }

        save_annual_data(annual_data, "2024", data_dir)

        # Verify save_json_data was called with correct parameters
        mock_save_json.assert_called_once_with(annual_data, annual_file, indent=2)

    def test_save_annual_data_handles_large_datasets(self, tmp_path):
        """Test that save_annual_data handles large datasets efficiently."""
        data_dir = tmp_path / "data"
        annual_file = data_dir / "aggregated" / "annual" / "2024.json"

        # Create large dataset
        large_razors = [
            {"name": f"Razor {i}", "shaves": i * 10, "unique_users": i * 5, "position": i}
            for i in range(1, 1001)
        ]

        annual_data = {
            "metadata": {
                "year": "2024",
                "total_shaves": 5005000,  # Sum of 1 to 1000 * 10
                "unique_shavers": 2502500,  # Sum of 1 to 1000 * 5
                "included_months": ["2024-01", "2024-02"],
                "missing_months": [],
            },
            "razors": large_razors,
            "blades": [],
            "brushes": [],
            "soaps": [],
        }

        # Should not raise any exceptions
        save_annual_data(annual_data, "2024", data_dir)

        # Verify file was created and contains all data
        assert annual_file.exists()
        with open(annual_file, "r") as f:
            loaded_data = json.load(f)

        assert len(loaded_data["razors"]) == 1000
        assert loaded_data["razors"][0]["name"] == "Razor 1"
        assert loaded_data["razors"][999]["name"] == "Razor 1000"

    def test_save_annual_data_validates_year_format(self, tmp_path):
        """Test that save_annual_data validates year format."""
        annual_data = {
            "metadata": {"year": "2024", "total_shaves": 100, "unique_shavers": 50},
            "razors": [],
            "blades": [],
            "brushes": [],
            "soaps": [],
        }

        # Test invalid year formats
        invalid_years = ["202", "20245", "abc", "20-24", ""]

        for invalid_year in invalid_years:
            with pytest.raises(ValueError, match="Year must be in YYYY format"):
                save_annual_data(annual_data, invalid_year, Path("/tmp"))

    def test_save_annual_data_validates_data_structure(self, tmp_path):
        """Test that save_annual_data validates data structure."""
        # Test missing required fields
        invalid_data_structures = [
            {},  # Empty dict
            {"metadata": {}},  # Missing data categories
            {"razors": [], "blades": []},  # Missing metadata
            {"metadata": {"year": "2024"}, "razors": []},  # Incomplete metadata
        ]

        for invalid_data in invalid_data_structures:
            with pytest.raises(ValueError, match="Invalid annual data structure"):
                save_annual_data(invalid_data, "2024", Path("/tmp"))

    def test_save_annual_data_handles_file_system_errors(self, tmp_path):
        """Test that save_annual_data handles file system errors gracefully."""
        annual_data = {
            "metadata": {
                "year": "2024",
                "total_shaves": 1200,
                "unique_shavers": 300,
                "included_months": ["2024-01"],
                "missing_months": [],
            },
            "razors": [],
            "blades": [],
            "brushes": [],
            "soaps": [],
        }

        # Test with non-existent parent directory (should create it)
        non_existent_dir = tmp_path / "non_existent" / "data"
        save_annual_data(annual_data, "2024", non_existent_dir)

        # Verify file was created in the new directory structure
        annual_file = non_existent_dir / "aggregated" / "annual" / "2024.json"
        assert annual_file.exists()

    @patch("sotd.utils.file_io.save_json_data")
    def test_save_annual_data_handles_io_errors(self, mock_save_json, tmp_path):
        """Test that save_annual_data handles I/O errors from save_json_data."""
        annual_data = {
            "metadata": {
                "year": "2024",
                "total_shaves": 1200,
                "unique_shavers": 300,
                "included_months": ["2024-01"],
                "missing_months": [],
            },
            "razors": [],
            "blades": [],
            "brushes": [],
            "soaps": [],
        }

        # Mock save_json_data to raise an exception
        mock_save_json.side_effect = OSError("Disk full")

        with pytest.raises(OSError, match="Disk full"):
            save_annual_data(annual_data, "2024", Path("/tmp"))

    def test_save_annual_data_json_serialization(self, tmp_path):
        """Test that save_annual_data properly handles JSON serialization."""
        data_dir = tmp_path / "data"
        annual_file = data_dir / "aggregated" / "annual" / "2024.json"

        # Data with various JSON-serializable types
        annual_data = {
            "metadata": {
                "year": "2024",
                "total_shaves": 1200,
                "unique_shavers": 300,
                "included_months": ["2024-01", "2024-02"],
                "missing_months": [],
                "extra_info": {
                    "processing_time": 1.5,
                    "is_complete": True,
                    "null_value": None,
                },
            },
            "razors": [
                {
                    "name": "Razor A",
                    "shaves": 100,
                    "unique_users": 50,
                    "position": 1,
                    "extra_data": {"rating": 4.5, "verified": True},
                }
            ],
            "blades": [],
            "brushes": [],
            "soaps": [],
        }

        save_annual_data(annual_data, "2024", data_dir)

        # Verify file can be loaded and contains all data types
        with open(annual_file, "r") as f:
            loaded_data = json.load(f)

        assert loaded_data["metadata"]["extra_info"]["processing_time"] == 1.5
        assert loaded_data["metadata"]["extra_info"]["is_complete"] is True
        assert loaded_data["metadata"]["extra_info"]["null_value"] is None
        assert loaded_data["razors"][0]["extra_data"]["rating"] == 4.5
        assert loaded_data["razors"][0]["extra_data"]["verified"] is True

    def test_save_annual_data_integration_with_existing_patterns(self, tmp_path):
        """Test that save_annual_data integrates well with existing save patterns."""
        data_dir = tmp_path / "data"

        # Create monthly aggregated data first (simulating existing pattern)
        monthly_dir = data_dir / "aggregated"
        monthly_dir.mkdir(parents=True, exist_ok=True)
        monthly_file = monthly_dir / "2024-01.json"
        monthly_data = {
            "meta": {"month": "2024-01", "total_shaves": 100, "unique_shavers": 50},
            "data": {"razors": [{"name": "Razor A", "shaves": 50, "unique_users": 25}]},
        }
        with open(monthly_file, "w") as f:
            json.dump(monthly_data, f, ensure_ascii=False)

        # Now save annual data (should not interfere with monthly data)
        annual_data = {
            "metadata": {
                "year": "2024",
                "total_shaves": 1200,
                "unique_shavers": 300,
                "included_months": ["2024-01"],
                "missing_months": [],
            },
            "razors": [{"name": "Annual Razor", "shaves": 100, "unique_users": 50, "position": 1}],
            "blades": [],
            "brushes": [],
            "soaps": [],
        }

        save_annual_data(annual_data, "2024", data_dir)

        # Verify both files exist and don't interfere
        assert monthly_file.exists()
        annual_file = data_dir / "aggregated" / "annual" / "2024.json"
        assert annual_file.exists()

        # Verify monthly data is unchanged
        with open(monthly_file, "r") as f:
            loaded_monthly = json.load(f)
        assert loaded_monthly == monthly_data

        # Verify annual data is correct
        with open(annual_file, "r") as f:
            loaded_annual = json.load(f)
        assert loaded_annual == annual_data
