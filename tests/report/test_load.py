#!/usr/bin/env python3
"""Tests for the report load module."""

import json
from pathlib import Path

import pytest

from sotd.report import load


class TestLoadAggregatedData:
    """Test aggregated data loading functionality."""

    def test_load_valid_aggregated_data(self, tmp_path: Path) -> None:
        """Test loading valid aggregated data."""
        # Create test data
        test_data = {
            "meta": {
                "month": "2025-01",
                "total_shaves": 1000,
                "unique_shavers": 50,
            },
            "data": {
                "razors": [
                    {"name": "Razor 1", "shaves": 100, "unique_users": 20},
                    {"name": "Razor 2", "shaves": 80, "unique_users": 15},
                ]
            },
        }

        # Write test file
        file_path = tmp_path / "aggregated" / "2025-01.json"
        file_path.parent.mkdir(parents=True)
        with open(file_path, "w") as f:
            json.dump(test_data, f)

        # Test loading
        metadata, data = load.load_aggregated_data(file_path)

        assert metadata["month"] == "2025-01"
        assert metadata["total_shaves"] == 1000
        assert metadata["unique_shavers"] == 50
        assert len(data["razors"]) == 2
        assert data["razors"][0]["name"] == "Razor 1"

    def test_load_nonexistent_file(self, tmp_path: Path) -> None:
        """Test loading nonexistent file."""
        file_path = tmp_path / "nonexistent.json"

        with pytest.raises(FileNotFoundError):
            load.load_aggregated_data(file_path)

    def test_load_invalid_json(self, tmp_path: Path) -> None:
        """Test loading invalid JSON file."""
        file_path = tmp_path / "invalid.json"
        with open(file_path, "w") as f:
            f.write("invalid json content")

        with pytest.raises(json.JSONDecodeError):
            load.load_aggregated_data(file_path)

    def test_load_missing_meta_section(self, tmp_path: Path) -> None:
        """Test loading file missing meta section."""
        test_data = {"data": {"razors": []}}

        file_path = tmp_path / "missing_meta.json"
        with open(file_path, "w") as f:
            json.dump(test_data, f)

        with pytest.raises(KeyError, match="Missing 'meta' section"):
            load.load_aggregated_data(file_path)

    def test_load_missing_data_section(self, tmp_path: Path) -> None:
        """Test loading file missing data section."""
        test_data = {
            "meta": {
                "month": "2025-01",
                "total_shaves": 1000,
                "unique_shavers": 50,
            }
        }

        file_path = tmp_path / "missing_data.json"
        with open(file_path, "w") as f:
            json.dump(test_data, f)

        with pytest.raises(KeyError, match="Missing 'data' section"):
            load.load_aggregated_data(file_path)

    def test_load_missing_required_meta_fields(self, tmp_path: Path) -> None:
        """Test loading file missing required metadata fields."""
        test_data = {
            "meta": {
                "month": "2025-01",
                # Missing total_shaves and unique_shavers
            },
            "data": {"razors": []},
        }

        file_path = tmp_path / "missing_fields.json"
        with open(file_path, "w") as f:
            json.dump(test_data, f)

        with pytest.raises(KeyError, match="Missing required metadata field"):
            load.load_aggregated_data(file_path)

    def test_load_with_debug(self, tmp_path: Path) -> None:
        """Test loading with debug output."""
        test_data = {
            "meta": {
                "month": "2025-01",
                "total_shaves": 1000,
                "unique_shavers": 50,
            },
            "data": {"razors": []},
        }

        file_path = tmp_path / "debug_test.json"
        with open(file_path, "w") as f:
            json.dump(test_data, f)

        # Should not raise any exceptions with debug=True
        metadata, data = load.load_aggregated_data(file_path, debug=True)
        assert metadata["month"] == "2025-01"


class TestHistoricalDataLoading:
    """Test historical data loading functionality."""

    def test_load_historical_data_exists(self, tmp_path: Path) -> None:
        """Test loading historical data that exists."""
        # Create test data
        test_data = {
            "meta": {
                "month": "2024-12",
                "total_shaves": 900,
                "unique_shavers": 45,
            },
            "data": {
                "razors": [
                    {"name": "Razor 1", "shaves": 90, "unique_users": 18},
                ]
            },
        }

        # Write test file
        file_path = tmp_path / "aggregated" / "2024-12.json"
        file_path.parent.mkdir(parents=True)
        with open(file_path, "w") as f:
            json.dump(test_data, f)

        # Test loading
        result = load.load_historical_data(tmp_path, 2024, 12)
        assert result is not None
        metadata, data = result
        assert metadata["month"] == "2024-12"
        assert len(data["razors"]) == 1

    def test_load_historical_data_not_exists(self, tmp_path: Path) -> None:
        """Test loading historical data that doesn't exist."""
        result = load.load_historical_data(tmp_path, 2024, 12)
        assert result is None

    def test_load_historical_data_with_debug(self, tmp_path: Path) -> None:
        """Test loading historical data with debug output."""
        # Should not raise any exceptions with debug=True
        result = load.load_historical_data(tmp_path, 2024, 12, debug=True)
        assert result is None

    def test_load_historical_data_corrupted_file(self, tmp_path: Path) -> None:
        """Test loading corrupted historical data file."""
        # Create corrupted file
        file_path = tmp_path / "aggregated" / "2024-12.json"
        file_path.parent.mkdir(parents=True)
        with open(file_path, "w") as f:
            f.write("invalid json")

        # Should return None for corrupted files
        result = load.load_historical_data(tmp_path, 2024, 12)
        assert result is None


class TestComparisonPeriods:
    """Test comparison period calculation functionality."""

    def test_get_comparison_periods_basic(self) -> None:
        """Test getting comparison periods for a basic case."""
        periods = load.get_comparison_periods(2025, 3)
        assert len(periods) == 3

        # Previous month (February 2025)
        assert periods[0] == (2025, 2, "previous month")

        # Previous year same month (March 2024)
        assert periods[1] == (2024, 3, "previous year")

        # 5 years ago same month (March 2020)
        assert periods[2] == (2020, 3, "5 years ago")

    def test_get_comparison_periods_january(self) -> None:
        """Test getting comparison periods for January (month rollover)."""
        periods = load.get_comparison_periods(2025, 1)
        assert len(periods) == 3

        # Previous month (December 2024)
        assert periods[0] == (2024, 12, "previous month")

        # Previous year same month (January 2024)
        assert periods[1] == (2024, 1, "previous year")

        # 5 years ago same month (January 2020)
        assert periods[2] == (2020, 1, "5 years ago")

    def test_get_comparison_periods_december(self) -> None:
        """Test getting comparison periods for December."""
        periods = load.get_comparison_periods(2025, 12)
        assert len(periods) == 3

        # Previous month (November 2025)
        assert periods[0] == (2025, 11, "previous month")

        # Previous year same month (December 2024)
        assert periods[1] == (2024, 12, "previous year")

        # 5 years ago same month (December 2020)
        assert periods[2] == (2020, 12, "5 years ago")


class TestComparisonDataLoading:
    """Test comparison data loading functionality."""

    def test_load_comparison_data_all_periods_exist(self, tmp_path: Path) -> None:
        """Test loading comparison data when all periods exist."""
        # Create test data for multiple periods
        periods_data = {
            "2025-02": {
                "meta": {"month": "2025-02", "total_shaves": 950, "unique_shavers": 48},
                "data": {"razors": [{"name": "Razor 1", "shaves": 85, "unique_users": 17}]},
            },
            "2024-03": {
                "meta": {"month": "2024-03", "total_shaves": 800, "unique_shavers": 40},
                "data": {"razors": [{"name": "Razor 1", "shaves": 70, "unique_users": 15}]},
            },
            "2020-03": {
                "meta": {"month": "2020-03", "total_shaves": 600, "unique_shavers": 30},
                "data": {"razors": [{"name": "Razor 1", "shaves": 50, "unique_users": 12}]},
            },
        }

        # Write test files
        aggregated_dir = tmp_path / "aggregated"
        aggregated_dir.mkdir(parents=True)

        for period, data in periods_data.items():
            file_path = aggregated_dir / f"{period}.json"
            with open(file_path, "w") as f:
                json.dump(data, f)

        # Test loading comparison data
        comparison_data = load.load_comparison_data(tmp_path, 2025, 3)

        assert len(comparison_data) == 3
        assert "previous month" in comparison_data
        assert "previous year" in comparison_data
        assert "5 years ago" in comparison_data

        # Check that data is loaded correctly
        prev_month_meta, prev_month_data = comparison_data["previous month"]
        assert prev_month_meta["month"] == "2025-02"

    def test_load_comparison_data_some_periods_exist(self, tmp_path: Path) -> None:
        """Test loading comparison data when only some periods exist."""
        # Create test data for only one period
        test_data = {
            "meta": {"month": "2024-03", "total_shaves": 800, "unique_shavers": 40},
            "data": {"razors": [{"name": "Razor 1", "shaves": 70, "unique_users": 15}]},
        }

        # Write test file for previous year only
        file_path = tmp_path / "aggregated" / "2024-03.json"
        file_path.parent.mkdir(parents=True)
        with open(file_path, "w") as f:
            json.dump(test_data, f)

        # Test loading comparison data
        comparison_data = load.load_comparison_data(tmp_path, 2025, 3)

        assert len(comparison_data) == 1
        assert "previous year" in comparison_data
        assert "previous month" not in comparison_data
        assert "5 years ago" not in comparison_data

    def test_load_comparison_data_no_periods_exist(self, tmp_path: Path) -> None:
        """Test loading comparison data when no periods exist."""
        comparison_data = load.load_comparison_data(tmp_path, 2025, 3)
        assert len(comparison_data) == 0

    def test_load_comparison_data_with_debug(self, tmp_path: Path) -> None:
        """Test loading comparison data with debug output."""
        # Should not raise any exceptions with debug=True
        comparison_data = load.load_comparison_data(tmp_path, 2025, 3, debug=True)
        assert len(comparison_data) == 0


class TestFilePathGeneration:
    """Test file path generation functionality."""

    def test_get_aggregated_file_path(self) -> None:
        """Test aggregated file path generation."""
        base_dir = Path("/test/data")
        path = load.get_aggregated_file_path(base_dir, 2025, 3)
        assert path == Path("/test/data/aggregated/2025-03.json")

    def test_get_aggregated_file_path_single_digit_month(self) -> None:
        """Test aggregated file path generation with single digit month."""
        base_dir = Path("/test/data")
        path = load.get_aggregated_file_path(base_dir, 2025, 1)
        assert path == Path("/test/data/aggregated/2025-01.json")

    def test_get_historical_file_path(self) -> None:
        """Test historical file path generation."""
        base_dir = Path("/test/data")
        path = load.get_historical_file_path(base_dir, 2024, 12)
        assert path == Path("/test/data/aggregated/2024-12.json")
