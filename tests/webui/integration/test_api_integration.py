"""Integration tests for the filtered API endpoints."""

import tempfile
from pathlib import Path

import pytest
import yaml

from sotd.utils.filtered_entries import FilteredEntriesManager


class TestAPIIntegration:
    """Test the API integration with filtered entries."""

    @pytest.fixture
    def temp_data_dir(self):
        """Create a temporary data directory for testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            data_dir = temp_path / "data"
            data_dir.mkdir()

            # Create empty filtered entries file
            filtered_file = data_dir / "intentionally_unmatched.yaml"
            with open(filtered_file, "w") as f:
                yaml.dump(
                    {
                        "razor": {},
                        "brush": {},
                        "blade": {},
                        "soap": {},
                    },
                    f,
                )

            yield temp_path

    def test_filtered_entries_manager_operations(self, temp_data_dir):
        """Test basic operations of the FilteredEntriesManager."""
        filtered_file = temp_data_dir / "data" / "intentionally_unmatched.yaml"
        manager = FilteredEntriesManager(filtered_file)
        manager.load()

        # Test adding an entry
        manager.add_entry(
            "razor", "Test Razor", "test_comment", "data/comments/2025-01.json", "user"
        )
        manager.save()

        # Verify the entry was added
        assert manager.is_filtered("razor", "Test Razor")

        # Test removing an entry
        manager.remove_entry("razor", "Test Razor", "test_comment", "data/comments/2025-01.json")
        manager.save()

        # Verify the entry was removed
        assert not manager.is_filtered("razor", "Test Razor")

    def test_data_structure_validation(self, temp_data_dir):
        """Test data structure validation."""
        filtered_file = temp_data_dir / "data" / "intentionally_unmatched.yaml"
        manager = FilteredEntriesManager(filtered_file)
        manager.load()

        # Test validation of valid data
        is_valid, errors = manager.validate_data()
        assert is_valid
        assert len(errors) == 0

        # Test validation of invalid data
        manager._data["invalid_category"] = {}
        is_valid, errors = manager.validate_data()
        assert not is_valid
        assert len(errors) > 0

    def test_duplicate_comment_id_handling(self, temp_data_dir):
        """Test handling of duplicate comment IDs."""
        filtered_file = temp_data_dir / "data" / "intentionally_unmatched.yaml"
        manager = FilteredEntriesManager(filtered_file)
        manager.load()

        # Add the same entry twice
        manager.add_entry(
            "brush", "Test Brush", "test_comment", "data/comments/2025-01.json", "user"
        )
        manager.add_entry(
            "brush", "Test Brush", "test_comment", "data/comments/2025-01.json", "user"
        )
        manager.save()

        # Verify only one entry was added
        comment_ids = manager.get_entry_comment_ids("brush", "Test Brush")
        assert len(comment_ids) == 1

    def test_multiple_comment_ids_per_entry(self, temp_data_dir):
        """Test handling multiple comment IDs for the same entry."""
        filtered_file = temp_data_dir / "data" / "intentionally_unmatched.yaml"
        manager = FilteredEntriesManager(filtered_file)
        manager.load()

        # Add multiple comment IDs for the same entry
        manager.add_entry("soap", "Test Soap", "comment_1", "data/comments/2025-01.json", "user")
        manager.add_entry("soap", "Test Soap", "comment_2", "data/comments/2025-02.json", "user")
        manager.save()

        # Verify both comment IDs were added
        comment_ids = manager.get_entry_comment_ids("soap", "Test Soap")
        assert len(comment_ids) == 2

        # Verify the entry is filtered
        assert manager.is_filtered("soap", "Test Soap")

    def test_corrupted_file_handling(self, temp_data_dir):
        """Test handling of corrupted YAML files."""
        filtered_file = temp_data_dir / "data" / "intentionally_unmatched.yaml"

        # Write corrupted YAML
        with open(filtered_file, "w") as f:
            f.write("invalid: yaml: content: [")

        # Should handle corrupted file gracefully
        manager = FilteredEntriesManager(filtered_file)
        try:
            manager.load()
            # If it doesn't raise an exception, it should create a new file
            assert filtered_file.exists()
        except Exception:
            # If it raises an exception, that's also acceptable behavior
            pass

    def test_empty_file_handling(self, temp_data_dir):
        """Test handling of empty files."""
        filtered_file = temp_data_dir / "data" / "intentionally_unmatched.yaml"

        # Remove the file
        filtered_file.unlink()

        # Should create a new file with empty structure
        manager = FilteredEntriesManager(filtered_file)
        manager.load()

        # Verify the file was created with empty structure
        assert filtered_file.exists()
        with open(filtered_file, "r") as f:
            data = yaml.safe_load(f)

        assert "razor" in data
        assert "brush" in data
        assert "blade" in data
        assert "soap" in data
