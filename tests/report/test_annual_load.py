#!/usr/bin/env python3
"""Tests for the annual report data loader."""

import json
from pathlib import Path

import pytest

from sotd.report import annual_load


class TestAnnualDataLoading:
    """Test annual aggregated data loading functionality."""

    def test_load_valid_annual_data(self, tmp_path: Path) -> None:
        """Test loading valid annual aggregated data."""
        # Create test annual data
        test_data = {
            "metadata": {
                "year": "2024",
                "total_shaves": 1200,
                "unique_shavers": 100,
                "included_months": ["2024-01", "2024-02", "2024-03"],
                "missing_months": [
                    "2024-04",
                    "2024-05",
                    "2024-06",
                    "2024-07",
                    "2024-08",
                    "2024-09",
                    "2024-10",
                    "2024-11",
                    "2024-12"]},
            "razors": [
                {"name": "Rockwell 6C", "shaves": 200, "unique_users": 80, "position": 1}, {"name": "Merkur 34C", "shaves": 150, "unique_users": 60, "position": 2}
            ],
            "blades": [
                {
                    "name": "Astra Superior Platinum",
                    "shaves": 250,
                    "unique_users": 90,
                    "position": 1}, {"name": "Feather Hi-Stainless", "shaves": 200, "unique_users": 85, "position": 2}
            ],
            "brushes": [
                {"name": "Simpson Chubby 2", "shaves": 100, "unique_users": 40, "position": 1}, {"name": "Omega 10049", "shaves": 80, "unique_users": 35, "position": 2}
            ],
            "soaps": [
                {
                    "name": "Barrister and Mann Seville",
                    "shaves": 120,
                    "unique_users": 50,
                    "position": 1}, {
                    "name": "Stirling Executive Man",
                    "shaves": 100,
                    "unique_users": 45,
                    "position": 2}
            ]}

        # Write test file
        file_path = tmp_path / "aggregated" / "annual" / "2024.json"
        file_path.parent.mkdir(parents=True)
        with open(file_path, "w") as f:
            json.dump(test_data, f, ensure_ascii=False)

        # Test loading
        metadata, data = annual_load.load_annual_data(file_path)

        assert metadata["year"] == "2024"
        assert metadata["total_shaves"] == 1200
        assert metadata["unique_shavers"] == 100
        assert len(metadata["included_months"]) == 3
        assert len(metadata["missing_months"]) == 9
        assert len(data["razors"]) == 2
        assert len(data["blades"]) == 2
        assert len(data["brushes"]) == 2
        assert len(data["soaps"]) == 2
        assert data["razors"][0]["name"] == "Rockwell 6C"

    def test_load_nonexistent_annual_file(self, tmp_path: Path) -> None:
        """Test loading nonexistent annual file."""
        file_path = tmp_path / "aggregated" / "annual" / "2024.json"

        with pytest.raises(FileNotFoundError):
            annual_load.load_annual_data(file_path)

    def test_load_invalid_json_annual_file(self, tmp_path: Path) -> None:
        """Test loading invalid JSON annual file."""
        file_path = tmp_path / "aggregated" / "annual" / "2024.json"
        file_path.parent.mkdir(parents=True)
        with open(file_path, "w") as f:
            f.write("invalid json content")

        with pytest.raises(json.JSONDecodeError):
            annual_load.load_annual_data(file_path)

    def test_load_missing_metadata_section(self, tmp_path: Path) -> None:
        """Test loading annual file missing metadata section."""
        test_data = {
            "razors": [],
            "blades": [],
            "brushes": [],
            "soaps": []}

        file_path = tmp_path / "aggregated" / "annual" / "2024.json"
        file_path.parent.mkdir(parents=True)
        with open(file_path, "w") as f:
            json.dump(test_data, f, ensure_ascii=False)

        with pytest.raises(KeyError, match="Missing 'metadata' section"):
            annual_load.load_annual_data(file_path)

    def test_load_missing_required_metadata_fields(self, tmp_path: Path) -> None:
        """Test loading annual file missing required metadata fields."""
        test_data = {
            "metadata": {
                "year": "2024",
                # Missing total_shaves, unique_shavers, included_months, missing_months
            },
            "razors": [],
            "blades": [],
            "brushes": [],
            "soaps": []}

        file_path = tmp_path / "aggregated" / "annual" / "2024.json"
        file_path.parent.mkdir(parents=True)
        with open(file_path, "w") as f:
            json.dump(test_data, f, ensure_ascii=False)

        with pytest.raises(KeyError, match="Missing required metadata field"):
            annual_load.load_annual_data(file_path)

    def test_load_missing_product_categories(self, tmp_path: Path) -> None:
        """Test loading annual file missing required product categories."""
        test_data = {
            "metadata": {
                "year": "2024",
                "total_shaves": 1200,
                "unique_shavers": 100,
                "included_months": ["2024-01"],
                "missing_months": [
                    "2024-02",
                    "2024-03",
                    "2024-04",
                    "2024-05",
                    "2024-06",
                    "2024-07",
                    "2024-08",
                    "2024-09",
                    "2024-10",
                    "2024-11",
                    "2024-12"]},
            "razors": [],
            # Missing blades, brushes, soaps
        }

        file_path = tmp_path / "aggregated" / "annual" / "2024.json"
        file_path.parent.mkdir(parents=True)
        with open(file_path, "w") as f:
            json.dump(test_data, f, ensure_ascii=False)

        with pytest.raises(KeyError, match="Missing required product category"):
            annual_load.load_annual_data(file_path)

    def test_load_with_debug(self, tmp_path: Path) -> None:
        """Test loading annual data with debug output."""
        test_data = {
            "metadata": {
                "year": "2024",
                "total_shaves": 1200,
                "unique_shavers": 100,
                "included_months": ["2024-01"],
                "missing_months": [
                    "2024-02",
                    "2024-03",
                    "2024-04",
                    "2024-05",
                    "2024-06",
                    "2024-07",
                    "2024-08",
                    "2024-09",
                    "2024-10",
                    "2024-11",
                    "2024-12"]},
            "razors": [],
            "blades": [],
            "brushes": [],
            "soaps": []}

        file_path = tmp_path / "aggregated" / "annual" / "2024.json"
        file_path.parent.mkdir(parents=True)
        with open(file_path, "w") as f:
            json.dump(test_data, f, ensure_ascii=False)

        # Should not raise any exceptions with debug=True
        metadata, data = annual_load.load_annual_data(file_path, debug=True)
        assert metadata["year"] == "2024"
        assert metadata["total_shaves"] == 1200


class TestAnnualFilePathGeneration:
    """Test annual file path generation functionality."""

    def test_get_annual_file_path(self) -> None:
        """Test getting annual file path for a specific year."""
        base_dir = Path("/data")
        file_path = annual_load.get_annual_file_path(base_dir, "2024")
        expected_path = Path("/data/aggregated/annual/2024.json")
        assert file_path == expected_path

    def test_get_annual_file_path_with_string_year(self) -> None:
        """Test getting annual file path with string year input."""
        base_dir = Path("/data")
        file_path = annual_load.get_annual_file_path(base_dir, 2024)
        expected_path = Path("/data/aggregated/annual/2024.json")
        assert file_path == expected_path


class TestAnnualDataValidation:
    """Test annual data validation functionality."""

    def test_validate_annual_data_structure_valid(self) -> None:
        """Test validation of valid annual data structure."""
        test_data = {
            "metadata": {
                "year": "2024",
                "total_shaves": 1200,
                "unique_shavers": 100,
                "included_months": ["2024-01"],
                "missing_months": [
                    "2024-02",
                    "2024-03",
                    "2024-04",
                    "2024-05",
                    "2024-06",
                    "2024-07",
                    "2024-08",
                    "2024-09",
                    "2024-10",
                    "2024-11",
                    "2024-12"]},
            "razors": [],
            "blades": [],
            "brushes": [],
            "soaps": []}

        # Should not raise any exceptions
        annual_load.validate_annual_data_structure(test_data)

    def test_validate_annual_data_structure_invalid_root(self) -> None:
        """Test validation of invalid annual data structure (not dict)."""
        test_data = "not a dict"  # type: ignore

        with pytest.raises(ValueError, match="Annual data must be a dictionary"):
            annual_load.validate_annual_data_structure(test_data)  # type: ignore

    def test_validate_annual_data_structure_missing_metadata(self) -> None:
        """Test validation of annual data missing metadata."""
        test_data = {
            "razors": [],
            "blades": [],
            "brushes": [],
            "soaps": []}

        with pytest.raises(ValueError, match="Annual data must contain 'metadata' section"):
            annual_load.validate_annual_data_structure(test_data)

    def test_validate_annual_data_structure_missing_categories(self) -> None:
        """Test validation of annual data missing product categories."""
        test_data = {
            "metadata": {
                "year": "2024",
                "total_shaves": 1200,
                "unique_shavers": 100,
                "included_months": ["2024-01"],
                "missing_months": [
                    "2024-02",
                    "2024-03",
                    "2024-04",
                    "2024-05",
                    "2024-06",
                    "2024-07",
                    "2024-08",
                    "2024-09",
                    "2024-10",
                    "2024-11",
                    "2024-12"]},
            "razors": [],
            # Missing blades, brushes, soaps
        }

        with pytest.raises(
            ValueError, match="Annual data must contain all required product categories"
        ):
            annual_load.validate_annual_data_structure(test_data)

    def test_validate_annual_metadata_valid(self) -> None:
        """Test validation of valid annual metadata."""
        metadata = {
            "year": "2024",
            "total_shaves": 1200,
            "unique_shavers": 100,
            "included_months": ["2024-01"],
            "missing_months": [
                "2024-02",
                "2024-03",
                "2024-04",
                "2024-05",
                "2024-06",
                "2024-07",
                "2024-08",
                "2024-09",
                "2024-10",
                "2024-11",
                "2024-12"]}

        # Should not raise any exceptions
        annual_load.validate_annual_metadata(metadata)

    def test_validate_annual_metadata_missing_fields(self) -> None:
        """Test validation of annual metadata missing required fields."""
        metadata = {
            "year": "2024",
            # Missing total_shaves, unique_shavers, included_months, missing_months
        }

        with pytest.raises(ValueError, match="Annual metadata must contain 'total_shaves' field"):
            annual_load.validate_annual_metadata(metadata)

    def test_validate_annual_metadata_invalid_types(self) -> None:
        """Test validation of annual metadata with invalid field types."""
        metadata = {
            "year": "2024",
            "total_shaves": "not a number",
            "unique_shavers": 100,
            "included_months": ["2024-01"],
            "missing_months": [
                "2024-02",
                "2024-03",
                "2024-04",
                "2024-05",
                "2024-06",
                "2024-07",
                "2024-08",
                "2024-09",
                "2024-10",
                "2024-11",
                "2024-12"]}

        with pytest.raises(ValueError, match="Annual metadata 'total_shaves' must be a number"):
            annual_load.validate_annual_metadata(metadata)


class TestAnnualDataIntegration:
    """Test annual data loading integration with existing patterns."""

    def test_load_annual_data_follows_existing_patterns(self, tmp_path: Path) -> None:
        """Test that annual data loading follows existing load patterns."""
        test_data = {
            "metadata": {
                "year": "2024",
                "total_shaves": 1200,
                "unique_shavers": 100,
                "included_months": ["2024-01"],
                "missing_months": [
                    "2024-02",
                    "2024-03",
                    "2024-04",
                    "2024-05",
                    "2024-06",
                    "2024-07",
                    "2024-08",
                    "2024-09",
                    "2024-10",
                    "2024-11",
                    "2024-12"]},
            "razors": [],
            "blades": [],
            "brushes": [],
            "soaps": []}

        file_path = tmp_path / "aggregated" / "annual" / "2024.json"
        file_path.parent.mkdir(parents=True)
        with open(file_path, "w") as f:
            json.dump(test_data, f, ensure_ascii=False)

        # Test that the function signature matches existing patterns
        metadata, data = annual_load.load_annual_data(file_path, debug=False)

        # Verify return types match existing patterns
        assert isinstance(metadata, dict)
        assert isinstance(data, dict)

        # Verify metadata structure follows existing patterns
        assert "year" in metadata
        assert "total_shaves" in metadata
        assert "unique_shavers" in metadata

    def test_annual_data_structure_consistency(self, tmp_path: Path) -> None:
        """Test that annual data structure is consistent with expected format."""
        test_data = {
            "metadata": {
                "year": "2024",
                "total_shaves": 1200,
                "unique_shavers": 100,
                "included_months": ["2024-01"],
                "missing_months": [
                    "2024-02",
                    "2024-03",
                    "2024-04",
                    "2024-05",
                    "2024-06",
                    "2024-07",
                    "2024-08",
                    "2024-09",
                    "2024-10",
                    "2024-11",
                    "2024-12"]},
            "razors": [
                {"name": "Rockwell 6C", "shaves": 200, "unique_users": 80, "position": 1}
            ],
            "blades": [
                {
                    "name": "Astra Superior Platinum",
                    "shaves": 250,
                    "unique_users": 90,
                    "position": 1}
            ],
            "brushes": [
                {"name": "Simpson Chubby 2", "shaves": 100, "unique_users": 40, "position": 1}
            ],
            "soaps": [
                {
                    "name": "Barrister and Mann Seville",
                    "shaves": 120,
                    "unique_users": 50,
                    "position": 1}
            ]}

        file_path = tmp_path / "aggregated" / "annual" / "2024.json"
        file_path.parent.mkdir(parents=True)
        with open(file_path, "w") as f:
            json.dump(test_data, f, ensure_ascii=False)

        metadata, data = annual_load.load_annual_data(file_path)

        # Verify product categories are lists of dictionaries
        for category in ["razors", "blades", "brushes", "soaps"]:
            assert isinstance(data[category], list)
            if data[category]:  # If not empty
                assert isinstance(data[category][0], dict)
                assert "name" in data[category][0]
                assert "shaves" in data[category][0]
                assert "unique_users" in data[category][0]
                assert "position" in data[category][0]


class TestAnnualDataErrorHandling:
    """Test annual data loading error handling."""

    def test_load_corrupted_annual_file(self, tmp_path: Path) -> None:
        """Test loading corrupted annual file."""
        file_path = tmp_path / "aggregated" / "annual" / "2024.json"
        file_path.parent.mkdir(parents=True)

        # Create a file that exists but has invalid JSON
        with open(file_path, "w") as f:
            f.write(
                '{"metadata": {"year": "2024", "total_shaves": 1200, "unique_shavers": 100, '
                '"included_months": ["2024-01"], "missing_months": ["2024-02"]}, '
                '"razors": [], "blades": [], "brushes": [], "soaps": []'  # Missing closing brace
            )

        with pytest.raises(json.JSONDecodeError):
            annual_load.load_annual_data(file_path)

    def test_load_annual_file_with_extra_fields(self, tmp_path: Path) -> None:
        """Test loading annual file with extra fields (should be allowed)."""
        test_data = {
            "metadata": {
                "year": "2024",
                "total_shaves": 1200,
                "unique_shavers": 100,
                "included_months": ["2024-01"],
                "missing_months": [
                    "2024-02",
                    "2024-03",
                    "2024-04",
                    "2024-05",
                    "2024-06",
                    "2024-07",
                    "2024-08",
                    "2024-09",
                    "2024-10",
                    "2024-11",
                    "2024-12"],
                "extra_field": "should be allowed"},
            "razors": [],
            "blades": [],
            "brushes": [],
            "soaps": [],
            "extra_category": []}

        file_path = tmp_path / "aggregated" / "annual" / "2024.json"
        file_path.parent.mkdir(parents=True)
        with open(file_path, "w") as f:
            json.dump(test_data, f, ensure_ascii=False)

        # Should not raise any exceptions
        metadata, data = annual_load.load_annual_data(file_path)
        assert metadata["year"] == "2024"
        assert "extra_field" in metadata
        assert "extra_category" in data


class TestAnnualDataPerformance:
    """Test annual data loading performance characteristics."""

    def test_load_large_annual_dataset(self, tmp_path: Path) -> None:
        """Test loading large annual dataset (performance test)."""
        # Create large dataset with many products
        large_razors = [
            {"name": f"Razor {i}, rank: 1", "shaves": 100 + i, "unique_users": 50 + i, "position": i}
            for i in range(1, 101)
        ]
        large_blades = [
            {"name": f"Blade {i}, rank: 1", "shaves": 200 + i, "unique_users": 100 + i, "position": i}
            for i in range(1, 101)
        ]
        large_brushes = [
            {"name": f"Brush {i}, rank: 1", "shaves": 50 + i, "unique_users": 25 + i, "position": i}
            for i in range(1, 101)
        ]
        large_soaps = [
            {"name": f"Soap {i}, rank: 1", "shaves": 75 + i, "unique_users": 40 + i, "position": i}
            for i in range(1, 101)
        ]

        test_data = {
            "metadata": {
                "year": "2024",
                "total_shaves": 50000,
                "unique_shavers": 1000,
                "included_months": [f"2024-{i:02d}" for i in range(1, 13)],
                "missing_months": []},
            "razors": large_razors,
            "blades": large_blades,
            "brushes": large_brushes,
            "soaps": large_soaps}

        file_path = tmp_path / "aggregated" / "annual" / "2024.json"
        file_path.parent.mkdir(parents=True)
        with open(file_path, "w") as f:
            json.dump(test_data, f, ensure_ascii=False)

        # Test loading performance
        metadata, data = annual_load.load_annual_data(file_path)

        assert metadata["year"] == "2024"
        assert metadata["total_shaves"] == 50000
        assert len(data["razors"]) == 100
        assert len(data["blades"]) == 100
        assert len(data["brushes"]) == 100
        assert len(data["soaps"]) == 100
