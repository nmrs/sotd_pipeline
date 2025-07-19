"""Simple error handling tests for the filtered workflow."""

import tempfile
from pathlib import Path

import pytest
import yaml

from sotd.utils.filtered_entries import FilteredEntriesManager


class TestErrorHandlingSimple:
    """Test basic error handling scenarios."""

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

    def test_corrupted_yaml_handling(self, temp_data_dir):
        """Test handling of corrupted YAML files."""
        filtered_file = temp_data_dir / "data" / "intentionally_unmatched.yaml"

        # Write corrupted YAML
        with open(filtered_file, "w") as f:
            f.write("invalid: yaml: content: [")

        # Should handle corrupted data gracefully
        manager = FilteredEntriesManager(filtered_file)
        try:
            manager.load()
            # If it doesn't raise an exception, it should create a new file
            assert filtered_file.exists()
        except ValueError as e:
            # Should provide a clear error message about invalid YAML
            assert "Invalid YAML" in str(e)

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

    def test_data_validation(self, temp_data_dir):
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

    def test_malformed_data_handling(self, temp_data_dir):
        """Test handling of malformed data structures."""
        filtered_file = temp_data_dir / "data" / "intentionally_unmatched.yaml"

        # Create malformed data structure
        malformed_data = {
            "razor": {
                "Test Razor": {
                    "added_date": "2025-01-27",
                    # Missing comment_ids field
                }
            }
        }

        with open(filtered_file, "w") as f:
            yaml.dump(malformed_data, f)

        manager = FilteredEntriesManager(filtered_file)
        try:
            manager.load()
            # Should handle malformed data gracefully
            is_valid, errors = manager.validate_data()
            assert not is_valid
            assert len(errors) > 0
        except Exception as e:
            # Should provide clear error message
            assert "malformed" in str(e).lower() or "invalid" in str(e).lower()
