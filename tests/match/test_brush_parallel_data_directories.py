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

        # Verify new directory exists
        assert manager.new_dir.exists()

        # Verify directory name
        assert manager.new_dir.name == "matched"

    def test_directory_paths_correct(self, tmp_path):
        """Test that directory paths are correctly structured."""
        manager = BrushParallelDataManager(base_path=tmp_path)

        expected_legacy = tmp_path / "matched_legacy"
        expected_new = tmp_path / "matched"

        assert manager.legacy_dir == expected_legacy
        assert manager.new_dir == expected_new

    def test_output_paths_correct(self, tmp_path):
        """Test that output paths are correctly generated."""
        manager = BrushParallelDataManager(base_path=tmp_path)

        # Test legacy system path
        legacy_path = manager.get_output_path("2025-05", "legacy")
        expected_legacy_path = tmp_path / "matched_legacy" / "2025-05.json"
        assert legacy_path == expected_legacy_path

        # Test new system path
        new_path = manager.get_output_path("2025-05", "new")
        expected_new_path = tmp_path / "matched" / "2025-05.json"
        assert new_path == expected_new_path

    def test_data_save_load_cycle(self, tmp_path):
        """Test complete save and load cycle for both systems."""
        manager = BrushParallelDataManager(base_path=tmp_path)
        manager.create_directories()

        test_data = {
            "metadata": {"month": "2025-05", "brush_system": "new"},
            "data": [{"test": "data"}],
        }

        # Save to new system
        saved_path = manager.save_data("2025-05", test_data, "new")
        assert saved_path.exists()

        # Load from new system
        loaded_data = manager.load_data("2025-05", "new")
        assert loaded_data == test_data

        # Save to new system
        test_data["metadata"]["brush_system"] = "new"
        saved_path_new = manager.save_data("2025-05", test_data, "new")
        assert saved_path_new.exists()

        # Load from new system
        loaded_data_new = manager.load_data("2025-05", "new")
        assert loaded_data_new == test_data

    def test_file_existence_checking(self, tmp_path):
        """Test file existence checking for new system."""
        manager = BrushParallelDataManager(base_path=tmp_path)
        manager.create_directories()

        # Initially no files exist
        assert not manager.file_exists("2025-05", "new")

        # Create test file
        test_data = {"test": "data"}
        manager.save_data("2025-05", test_data, "new")

        # Check existence
        assert manager.file_exists("2025-05", "new")

    def test_metadata_extraction(self, tmp_path):
        """Test metadata extraction from new system."""
        manager = BrushParallelDataManager(base_path=tmp_path)
        manager.create_directories()

        test_data = {
            "metadata": {"month": "2025-05", "brush_system": "new", "record_count": 100},
            "data": [],
        }

        # Save data
        manager.save_data("2025-05", test_data, "new")

        # Extract metadata
        metadata = manager.get_metadata("2025-05", "new")
        assert metadata["month"] == "2025-05"
        assert metadata["brush_system"] == "new"
        assert metadata["record_count"] == 100

    def test_month_listing(self, tmp_path):
        """Test listing available months for new system."""
        manager = BrushParallelDataManager(base_path=tmp_path)
        manager.create_directories()

        # Initially no months
        assert manager.list_available_months("new") == []

        # Create some test files
        test_data = {"test": "data"}
        manager.save_data("2025-05", test_data, "new")
        manager.save_data("2025-06", test_data, "new")

        # Check listings
        new_months = manager.list_available_months("new")

        assert "2025-05" in new_months
        assert "2025-06" in new_months

    def test_system_validation(self, tmp_path):
        """Test system name validation."""
        manager = BrushParallelDataManager(base_path=tmp_path)

        # Valid system
        manager._validate_system_name("new")

        # Invalid system
        with pytest.raises(ValueError, match="Invalid brush system"):
            manager._validate_system_name("invalid")

    def test_directory_isolation(self, tmp_path):
        """Test that data is properly isolated in new system."""
        manager = BrushParallelDataManager(base_path=tmp_path)
        manager.create_directories()

        test_data_1 = {"system": "new", "data": [1, 2, 3]}
        test_data_2 = {"system": "new", "data": [4, 5, 6]}

        # Save to different months
        manager.save_data("2025-05", test_data_1, "new")
        manager.save_data("2025-06", test_data_2, "new")

        # Load and verify isolation
        loaded_1 = manager.load_data("2025-05", "new")
        loaded_2 = manager.load_data("2025-06", "new")

        assert loaded_1["system"] == "new"
        assert loaded_2["system"] == "new"
        assert loaded_1 != loaded_2
