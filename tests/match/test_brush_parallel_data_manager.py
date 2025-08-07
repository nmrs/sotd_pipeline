"""
Unit tests for brush parallel data manager.

Tests the parallel data directory structure for brush system comparison.
"""

import pytest
from pathlib import Path
import json

from sotd.match.brush_parallel_data_manager import BrushParallelDataManager


class TestBrushParallelDataManager:
    """Test brush parallel data manager."""

    def test_init_default_paths(self):
        """Test initialization with default paths."""
        manager = BrushParallelDataManager()

        assert manager.base_path == Path("data")
        assert manager.current_dir == Path("data/matched")
        assert manager.new_dir == Path("data/matched_new")

    def test_init_custom_paths(self):
        """Test initialization with custom paths."""
        custom_base = Path("/custom/data")
        manager = BrushParallelDataManager(base_path=custom_base)

        assert manager.base_path == custom_base
        assert manager.current_dir == custom_base / "matched"
        assert manager.new_dir == custom_base / "matched_new"

    def test_create_directories(self, tmp_path):
        """Test directory creation."""
        manager = BrushParallelDataManager(base_path=tmp_path)

        # Directories should not exist initially
        assert not manager.current_dir.exists()
        assert not manager.new_dir.exists()

        # Create directories
        manager.create_directories()

        # Directories should exist after creation
        assert manager.current_dir.exists()
        assert manager.new_dir.exists()
        assert manager.current_dir.is_dir()
        assert manager.new_dir.is_dir()

    def test_get_output_path_current_system(self):
        """Test getting output path for current brush system."""
        manager = BrushParallelDataManager()

        path = manager.get_output_path("2025-05", "current")
        assert path == Path("data/matched/2025-05.json")

    def test_get_output_path_new_system(self):
        """Test getting output path for new brush system."""
        manager = BrushParallelDataManager()

        path = manager.get_output_path("2025-05", "new")
        assert path == Path("data/matched_new/2025-05.json")

    def test_get_output_path_invalid_system(self):
        """Test getting output path for invalid brush system."""
        manager = BrushParallelDataManager()

        with pytest.raises(ValueError, match="Invalid brush system"):
            manager.get_output_path("2025-05", "invalid")

    def test_save_data_current_system(self, tmp_path):
        """Test saving data for current brush system."""
        manager = BrushParallelDataManager(base_path=tmp_path)
        manager.create_directories()

        data = {"test": "data", "month": "2025-05"}
        output_path = manager.save_data("2025-05", data, "current")

        assert output_path == tmp_path / "matched" / "2025-05.json"
        assert output_path.exists()

        # Verify data was saved correctly
        with open(output_path) as f:
            saved_data = json.load(f)
        assert saved_data == data

    def test_save_data_new_system(self, tmp_path):
        """Test saving data for new brush system."""
        manager = BrushParallelDataManager(base_path=tmp_path)
        manager.create_directories()

        data = {"test": "data", "month": "2025-05"}
        output_path = manager.save_data("2025-05", data, "new")

        assert output_path == tmp_path / "matched_new" / "2025-05.json"
        assert output_path.exists()

        # Verify data was saved correctly
        with open(output_path) as f:
            saved_data = json.load(f)
        assert saved_data == data

    def test_load_data_current_system(self, tmp_path):
        """Test loading data for current brush system."""
        manager = BrushParallelDataManager(base_path=tmp_path)
        manager.create_directories()

        data = {"test": "data", "month": "2025-05"}
        file_path = tmp_path / "matched" / "2025-05.json"

        # Save test data
        with open(file_path, "w") as f:
            json.dump(data, f)

        # Load data
        loaded_data = manager.load_data("2025-05", "current")
        assert loaded_data == data

    def test_load_data_new_system(self, tmp_path):
        """Test loading data for new brush system."""
        manager = BrushParallelDataManager(base_path=tmp_path)
        manager.create_directories()

        data = {"test": "data", "month": "2025-05"}
        file_path = tmp_path / "matched_new" / "2025-05.json"

        # Save test data
        with open(file_path, "w") as f:
            json.dump(data, f)

        # Load data
        loaded_data = manager.load_data("2025-05", "new")
        assert loaded_data == data

    def test_load_data_file_not_found(self, tmp_path):
        """Test loading data when file doesn't exist."""
        manager = BrushParallelDataManager(base_path=tmp_path)
        manager.create_directories()

        with pytest.raises(FileNotFoundError):
            manager.load_data("2025-05", "current")

    def test_file_exists_current_system(self, tmp_path):
        """Test checking if file exists for current brush system."""
        manager = BrushParallelDataManager(base_path=tmp_path)
        manager.create_directories()

        # File should not exist initially
        assert not manager.file_exists("2025-05", "current")

        # Create file
        file_path = tmp_path / "matched" / "2025-05.json"
        with open(file_path, "w") as f:
            json.dump({"test": "data"}, f)

        # File should exist now
        assert manager.file_exists("2025-05", "current")

    def test_file_exists_new_system(self, tmp_path):
        """Test checking if file exists for new brush system."""
        manager = BrushParallelDataManager(base_path=tmp_path)
        manager.create_directories()

        # File should not exist initially
        assert not manager.file_exists("2025-05", "new")

        # Create file
        file_path = tmp_path / "matched_new" / "2025-05.json"
        with open(file_path, "w") as f:
            json.dump({"test": "data"}, f)

        # File should exist now
        assert manager.file_exists("2025-05", "new")

    def test_get_metadata_current_system(self, tmp_path):
        """Test getting metadata for current brush system."""
        manager = BrushParallelDataManager(base_path=tmp_path)
        manager.create_directories()

        data = {
            "metadata": {"month": "2025-05", "record_count": 100, "brush_system": "current"},
            "data": [],
        }
        file_path = tmp_path / "matched" / "2025-05.json"

        with open(file_path, "w") as f:
            json.dump(data, f)

        metadata = manager.get_metadata("2025-05", "current")
        assert metadata == data["metadata"]

    def test_get_metadata_new_system(self, tmp_path):
        """Test getting metadata for new brush system."""
        manager = BrushParallelDataManager(base_path=tmp_path)
        manager.create_directories()

        data = {
            "metadata": {"month": "2025-05", "record_count": 100, "brush_system": "new"},
            "data": [],
        }
        file_path = tmp_path / "matched_new" / "2025-05.json"

        with open(file_path, "w") as f:
            json.dump(data, f)

        metadata = manager.get_metadata("2025-05", "new")
        assert metadata == data["metadata"]

    def test_get_metadata_file_not_found(self, tmp_path):
        """Test getting metadata when file doesn't exist."""
        manager = BrushParallelDataManager(base_path=tmp_path)
        manager.create_directories()

        with pytest.raises(FileNotFoundError):
            manager.get_metadata("2025-05", "current")

    def test_list_available_months_current_system(self, tmp_path):
        """Test listing available months for current brush system."""
        manager = BrushParallelDataManager(base_path=tmp_path)
        manager.create_directories()

        # Create some test files
        months = ["2025-01", "2025-02", "2025-03"]
        for month in months:
            file_path = tmp_path / "matched" / f"{month}.json"
            with open(file_path, "w") as f:
                json.dump({"month": month}, f)

        available_months = manager.list_available_months("current")
        assert set(available_months) == set(months)

    def test_list_available_months_new_system(self, tmp_path):
        """Test listing available months for new brush system."""
        manager = BrushParallelDataManager(base_path=tmp_path)
        manager.create_directories()

        # Create some test files
        months = ["2025-01", "2025-02", "2025-03"]
        for month in months:
            file_path = tmp_path / "matched_new" / f"{month}.json"
            with open(file_path, "w") as f:
                json.dump({"month": month}, f)

        available_months = manager.list_available_months("new")
        assert set(available_months) == set(months)

    def test_list_available_months_empty_directory(self, tmp_path):
        """Test listing available months for empty directory."""
        manager = BrushParallelDataManager(base_path=tmp_path)
        manager.create_directories()

        available_months = manager.list_available_months("current")
        assert available_months == []

    def test_validate_system_name_valid(self):
        """Test validation of valid system names."""
        manager = BrushParallelDataManager()

        # Should not raise exception
        manager._validate_system_name("current")
        manager._validate_system_name("new")

    def test_validate_system_name_invalid(self):
        """Test validation of invalid system names."""
        manager = BrushParallelDataManager()

        with pytest.raises(ValueError, match="Invalid brush system"):
            manager._validate_system_name("invalid")

        with pytest.raises(ValueError, match="Invalid brush system"):
            manager._validate_system_name("old")

        with pytest.raises(ValueError, match="Invalid brush system"):
            manager._validate_system_name("")
