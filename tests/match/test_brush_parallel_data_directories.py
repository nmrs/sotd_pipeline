"""
Tests for parallel brush data directories.

This module tests the parallel data directory structure for Phase 2 Step 6
of the multi-strategy scoring system implementation.
"""

import pytest

from sotd.match.brush_parallel_data_manager import BrushParallelDataManager


class TestBrushParallelDataDirectories:
    """Test parallel brush data directories."""

    def test_directory_structure_creation(self, tmp_path):
        """Test that parallel data directories are created correctly."""
        manager = BrushParallelDataManager(base_path=tmp_path)

        # Create directories
        manager.create_directories()

        # Verify both directories exist
        assert manager.current_dir.exists()
        assert manager.new_dir.exists()

        # Verify directory names
        assert manager.current_dir.name == "matched"
        assert manager.new_dir.name == "matched_new"

    def test_directory_paths_correct(self, tmp_path):
        """Test that directory paths are correctly structured."""
        manager = BrushParallelDataManager(base_path=tmp_path)

        expected_current = tmp_path / "matched"
        expected_new = tmp_path / "matched_new"

        assert manager.current_dir == expected_current
        assert manager.new_dir == expected_new

    def test_output_paths_correct(self, tmp_path):
        """Test that output paths are correctly generated."""
        manager = BrushParallelDataManager(base_path=tmp_path)

        # Test current system path
        current_path = manager.get_output_path("2025-05", "current")
        expected_current_path = tmp_path / "matched" / "2025-05.json"
        assert current_path == expected_current_path

        # Test new system path
        new_path = manager.get_output_path("2025-05", "new")
        expected_new_path = tmp_path / "matched_new" / "2025-05.json"
        assert new_path == expected_new_path

    def test_data_save_load_cycle(self, tmp_path):
        """Test complete save and load cycle for both systems."""
        manager = BrushParallelDataManager(base_path=tmp_path)
        manager.create_directories()

        test_data = {
            "metadata": {"month": "2025-05", "brush_system": "current"},
            "data": [{"test": "data"}],
        }

        # Save to current system
        saved_path = manager.save_data("2025-05", test_data, "current")
        assert saved_path.exists()

        # Load from current system
        loaded_data = manager.load_data("2025-05", "current")
        assert loaded_data == test_data

        # Save to new system
        test_data["metadata"]["brush_system"] = "new"
        saved_path_new = manager.save_data("2025-05", test_data, "new")
        assert saved_path_new.exists()

        # Load from new system
        loaded_data_new = manager.load_data("2025-05", "new")
        assert loaded_data_new == test_data

    def test_file_existence_checking(self, tmp_path):
        """Test file existence checking for both systems."""
        manager = BrushParallelDataManager(base_path=tmp_path)
        manager.create_directories()

        # Initially no files exist
        assert not manager.file_exists("2025-05", "current")
        assert not manager.file_exists("2025-05", "new")

        # Create test file
        test_data = {"test": "data"}
        manager.save_data("2025-05", test_data, "current")

        # Check existence
        assert manager.file_exists("2025-05", "current")
        assert not manager.file_exists("2025-05", "new")

    def test_metadata_extraction(self, tmp_path):
        """Test metadata extraction from both systems."""
        manager = BrushParallelDataManager(base_path=tmp_path)
        manager.create_directories()

        test_data = {
            "metadata": {"month": "2025-05", "brush_system": "current", "record_count": 100},
            "data": [],
        }

        # Save data
        manager.save_data("2025-05", test_data, "current")

        # Extract metadata
        metadata = manager.get_metadata("2025-05", "current")
        assert metadata["month"] == "2025-05"
        assert metadata["brush_system"] == "current"
        assert metadata["record_count"] == 100

    def test_month_listing(self, tmp_path):
        """Test listing available months for both systems."""
        manager = BrushParallelDataManager(base_path=tmp_path)
        manager.create_directories()

        # Initially no months
        assert manager.list_available_months("current") == []
        assert manager.list_available_months("new") == []

        # Create some test files
        test_data = {"test": "data"}
        manager.save_data("2025-05", test_data, "current")
        manager.save_data("2025-06", test_data, "current")
        manager.save_data("2025-05", test_data, "new")

        # Check listings
        current_months = manager.list_available_months("current")
        new_months = manager.list_available_months("new")

        assert "2025-05" in current_months
        assert "2025-06" in current_months
        assert "2025-05" in new_months
        assert "2025-06" not in new_months

    def test_system_validation(self, tmp_path):
        """Test system name validation."""
        manager = BrushParallelDataManager(base_path=tmp_path)

        # Valid systems
        manager._validate_system_name("current")
        manager._validate_system_name("new")

        # Invalid system
        with pytest.raises(ValueError, match="Invalid brush system"):
            manager._validate_system_name("invalid")

    def test_directory_isolation(self, tmp_path):
        """Test that data is properly isolated between systems."""
        manager = BrushParallelDataManager(base_path=tmp_path)
        manager.create_directories()

        current_data = {"system": "current", "data": [1, 2, 3]}
        new_data = {"system": "new", "data": [4, 5, 6]}

        # Save to both systems
        manager.save_data("2025-05", current_data, "current")
        manager.save_data("2025-05", new_data, "new")

        # Load and verify isolation
        loaded_current = manager.load_data("2025-05", "current")
        loaded_new = manager.load_data("2025-05", "new")

        assert loaded_current["system"] == "current"
        assert loaded_new["system"] == "new"
        assert loaded_current != loaded_new
