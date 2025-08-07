"""
Integration tests for brush parallel data manager integration.

Tests that the brush parallel data manager is properly integrated
with the match phase processing.
"""

import pytest

from sotd.match.brush_parallel_data_manager import BrushParallelDataManager


class TestBrushParallelDataIntegration:
    """Test brush parallel data manager integration."""

    def test_parallel_data_manager_integration(self, tmp_path):
        """Test that parallel data manager creates correct directory structure."""
        manager = BrushParallelDataManager(base_path=tmp_path)
        manager.create_directories()

        # Verify directory structure
        assert (tmp_path / "matched").exists()
        assert (tmp_path / "matched").is_dir()
        assert (tmp_path / "matched_new").exists()
        assert (tmp_path / "matched_new").is_dir()

    def test_parallel_data_manager_save_load_cycle(self, tmp_path):
        """Test complete save/load cycle for both brush systems."""
        manager = BrushParallelDataManager(base_path=tmp_path)
        manager.create_directories()

        # Test data
        test_data = {
            "metadata": {"month": "2025-05", "record_count": 100, "brush_system": "current"},
            "data": [{"test": "record"}],
        }

        # Save to current system
        output_path = manager.save_data("2025-05", test_data, "current")
        assert output_path == tmp_path / "matched" / "2025-05.json"
        assert output_path.exists()

        # Load from current system
        loaded_data = manager.load_data("2025-05", "current")
        assert loaded_data == test_data

        # Save to new system
        test_data["metadata"]["brush_system"] = "new"
        output_path = manager.save_data("2025-05", test_data, "new")
        assert output_path == tmp_path / "matched_new" / "2025-05.json"
        assert output_path.exists()

        # Load from new system
        loaded_data = manager.load_data("2025-05", "new")
        assert loaded_data == test_data

    def test_parallel_data_manager_file_existence(self, tmp_path):
        """Test file existence checking for both brush systems."""
        manager = BrushParallelDataManager(base_path=tmp_path)
        manager.create_directories()

        # Files should not exist initially
        assert not manager.file_exists("2025-05", "current")
        assert not manager.file_exists("2025-05", "new")

        # Create files
        test_data = {"test": "data"}
        manager.save_data("2025-05", test_data, "current")
        manager.save_data("2025-05", test_data, "new")

        # Files should exist now
        assert manager.file_exists("2025-05", "current")
        assert manager.file_exists("2025-05", "new")

    def test_parallel_data_manager_metadata_extraction(self, tmp_path):
        """Test metadata extraction from saved files."""
        manager = BrushParallelDataManager(base_path=tmp_path)
        manager.create_directories()

        # Test data with metadata
        test_data = {
            "metadata": {
                "month": "2025-05",
                "record_count": 150,
                "brush_system": "current",
                "performance": {"total_time": 10.5},
            },
            "data": [],
        }

        # Save and extract metadata
        manager.save_data("2025-05", test_data, "current")
        metadata = manager.get_metadata("2025-05", "current")

        assert metadata["month"] == "2025-05"
        assert metadata["record_count"] == 150
        assert metadata["brush_system"] == "current"
        assert metadata["performance"]["total_time"] == 10.5

    def test_parallel_data_manager_month_listing(self, tmp_path):
        """Test listing available months for both brush systems."""
        manager = BrushParallelDataManager(base_path=tmp_path)
        manager.create_directories()

        # Create test files
        months = ["2025-01", "2025-02", "2025-03"]
        test_data = {"test": "data"}

        for month in months:
            manager.save_data(month, test_data, "current")
            manager.save_data(month, test_data, "new")

        # List available months
        current_months = manager.list_available_months("current")
        new_months = manager.list_available_months("new")

        assert set(current_months) == set(months)
        assert set(new_months) == set(months)
        assert current_months == sorted(months)
        assert new_months == sorted(months)

    def test_parallel_data_manager_invalid_system_handling(self, tmp_path):
        """Test handling of invalid brush system names."""
        manager = BrushParallelDataManager(base_path=tmp_path)

        # Test invalid system names
        with pytest.raises(ValueError, match="Invalid brush system"):
            manager.get_output_path("2025-05", "invalid")

        with pytest.raises(ValueError, match="Invalid brush system"):
            manager.save_data("2025-05", {"test": "data"}, "invalid")

        with pytest.raises(ValueError, match="Invalid brush system"):
            manager.load_data("2025-05", "invalid")

        with pytest.raises(ValueError, match="Invalid brush system"):
            manager.file_exists("2025-05", "invalid")

        with pytest.raises(ValueError, match="Invalid brush system"):
            manager.get_metadata("2025-05", "invalid")

        with pytest.raises(ValueError, match="Invalid brush system"):
            manager.list_available_months("invalid")

    def test_parallel_data_manager_file_not_found_handling(self, tmp_path):
        """Test handling of file not found scenarios."""
        manager = BrushParallelDataManager(base_path=tmp_path)
        manager.create_directories()

        # Test file not found scenarios
        with pytest.raises(FileNotFoundError):
            manager.load_data("2025-05", "current")

        with pytest.raises(FileNotFoundError):
            manager.get_metadata("2025-05", "current")
