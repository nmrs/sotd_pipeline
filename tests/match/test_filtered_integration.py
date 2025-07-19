"""Tests for filtered entries integration in match phase."""

import pytest
import tempfile
import shutil
from pathlib import Path
import yaml

from sotd.match.match import match_record, add_filtered_entry, _get_filtered_entries_manager


@pytest.fixture
def temp_data_dir():
    """Create temporary data directory with test filtered entries."""
    temp_dir = tempfile.mkdtemp()
    data_dir = Path(temp_dir) / "data"
    data_dir.mkdir()

    # Create test filtered entries file
    filtered_file = data_dir / "intentionally_unmatched.yaml"
    test_data = {
        "razor": {
            "Hot Wheels Play Razor": {
                "added_date": "2025-01-27",
                "comment_ids": [
                    {"file": "data/comments/2025-01.json", "id": "abc123", "source": "user"}
                ],
            }
        },
        "brush": {},
        "blade": {},
        "soap": {},
    }

    with open(filtered_file, "w", encoding="utf-8") as f:
        yaml.dump(test_data, f)

    yield temp_dir

    # Cleanup
    shutil.rmtree(temp_dir)


class TestFilteredEntriesIntegration:
    """Test filtered entries integration in match phase."""

    def test_filtered_razor_is_skipped(self, temp_data_dir, monkeypatch):
        """Test that filtered razors are skipped during matching."""
        # Mock the filtered entries file path
        from sotd.match.match import _filtered_entries_manager

        monkeypatch.setattr("sotd.match.match._filtered_entries_manager", None)

        # Mock the Path constructor to return our test file
        original_path = Path

        def mock_path(path_str):
            if "intentionally_unmatched.yaml" in str(path_str):
                return Path(temp_data_dir) / "data" / "intentionally_unmatched.yaml"
            return original_path(path_str)

        monkeypatch.setattr("sotd.match.match.Path", mock_path)

        # Test record with filtered razor
        record = {
            "razor": "Hot Wheels Play Razor",
            "blade": "Feather",
            "brush": "Simpson Chubby 2",
            "soap": "Declaration Grooming",
        }

        result = match_record(record)

        # Razor should be marked as intentionally unmatched
        assert result["razor"]["original"] == "Hot Wheels Play Razor"
        assert result["razor"]["matched"] is None
        assert result["razor"]["match_type"] == "intentionally_unmatched"
        assert result["razor"]["pattern"] is None

        # Other fields should be processed normally
        assert "blade" in result
        assert "brush" in result
        assert "soap" in result

    def test_non_filtered_entries_processed_normally(self, temp_data_dir, monkeypatch):
        """Test that non-filtered entries are processed normally."""
        # Mock the filtered entries file path
        from sotd.match.match import _filtered_entries_manager

        monkeypatch.setattr("sotd.match.match._filtered_entries_manager", None)

        # Mock the Path constructor to return our test file
        original_path = Path

        def mock_path(path_str):
            if "intentionally_unmatched.yaml" in str(path_str):
                return Path(temp_data_dir) / "data" / "intentionally_unmatched.yaml"
            return original_path(path_str)

        monkeypatch.setattr("sotd.match.match.Path", mock_path)

        # Test record with non-filtered entries
        record = {
            "razor": "Merkur 34C",
            "blade": "Feather",
            "brush": "Simpson Chubby 2",
            "soap": "Declaration Grooming",
        }

        result = match_record(record)

        # All entries should be processed normally (not marked as intentionally unmatched)
        assert result["razor"]["original"] == "Merkur 34C"
        assert result["razor"]["match_type"] != "intentionally_unmatched"

        assert result["blade"]["original"] == "Feather"
        assert result["blade"]["match_type"] != "intentionally_unmatched"

        assert result["brush"]["original"] == "Simpson Chubby 2"
        assert result["brush"]["match_type"] != "intentionally_unmatched"

        assert result["soap"]["original"] == "Declaration Grooming"
        assert result["soap"]["match_type"] != "intentionally_unmatched"

    def test_add_filtered_entry_function(self, temp_data_dir, monkeypatch):
        """Test the add_filtered_entry function."""
        # Mock the filtered entries file path
        from sotd.match.match import _filtered_entries_manager

        monkeypatch.setattr("sotd.match.match._filtered_entries_manager", None)

        # Mock the Path constructor to return our test file
        original_path = Path

        def mock_path(path_str):
            if "intentionally_unmatched.yaml" in str(path_str):
                return Path(temp_data_dir) / "data" / "intentionally_unmatched.yaml"
            return original_path(path_str)

        monkeypatch.setattr("sotd.match.match.Path", mock_path)

        # Add a new filtered entry
        add_filtered_entry(
            category="razor",
            entry_name="Test Razor",
            comment_id="def456",
            file_path="data/comments/2025-01.json",
            source="pipeline",
        )

        # Verify the entry was added
        manager = _get_filtered_entries_manager()
        assert manager.is_filtered("razor", "Test Razor")

        # Check that the entry appears in the file
        filtered_file = Path(temp_data_dir) / "data" / "intentionally_unmatched.yaml"
        with open(filtered_file, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        assert "Test Razor" in data["razor"]
        assert data["razor"]["Test Razor"]["comment_ids"][0]["id"] == "def456"
        assert data["razor"]["Test Razor"]["comment_ids"][0]["source"] == "pipeline"

    def test_filtered_entries_manager_initialization(self, temp_data_dir, monkeypatch):
        """Test that filtered entries manager initializes correctly."""
        # Mock the filtered entries file path
        from sotd.match.match import _filtered_entries_manager

        monkeypatch.setattr("sotd.match.match._filtered_entries_manager", None)

        # Mock the Path constructor to return our test file
        original_path = Path

        def mock_path(path_str):
            if "intentionally_unmatched.yaml" in str(path_str):
                return Path(temp_data_dir) / "data" / "intentionally_unmatched.yaml"
            return original_path(path_str)

        monkeypatch.setattr("sotd.match.match.Path", mock_path)

        # Get the manager
        manager = _get_filtered_entries_manager()

        # Verify it loaded the test data
        assert manager.is_filtered("razor", "Hot Wheels Play Razor")
        assert not manager.is_filtered("razor", "Merkur 34C")

    def test_filtered_entries_manager_caching(self, temp_data_dir, monkeypatch):
        """Test that filtered entries manager is cached."""
        # Mock the filtered entries file path
        from sotd.match.match import _filtered_entries_manager

        monkeypatch.setattr("sotd.match.match._filtered_entries_manager", None)

        # Mock the Path constructor to return our test file
        original_path = Path

        def mock_path(path_str):
            if "intentionally_unmatched.yaml" in str(path_str):
                return Path(temp_data_dir) / "data" / "intentionally_unmatched.yaml"
            return original_path(path_str)

        monkeypatch.setattr("sotd.match.match.Path", mock_path)

        # Get the manager twice
        manager1 = _get_filtered_entries_manager()
        manager2 = _get_filtered_entries_manager()

        # Should be the same object (cached)
        assert manager1 is manager2

    def test_filtered_entries_with_missing_file(self, monkeypatch):
        """Test that filtered entries work when file doesn't exist."""
        # Mock the filtered entries file path
        from sotd.match.match import _filtered_entries_manager

        monkeypatch.setattr("sotd.match.match._filtered_entries_manager", None)

        # Mock the file path to non-existent file
        temp_dir = tempfile.mkdtemp()
        filtered_file = Path(temp_dir) / "data" / "intentionally_unmatched.yaml"

        # Mock the Path constructor to return our test file
        original_path = Path

        def mock_path(path_str):
            if "intentionally_unmatched.yaml" in str(path_str):
                return filtered_file
            return original_path(path_str)

        monkeypatch.setattr("sotd.match.match.Path", mock_path)

        try:
            # Get the manager (should create empty file)
            manager = _get_filtered_entries_manager()

            # Should not be filtered since file was empty
            assert not manager.is_filtered("razor", "Test Razor")

            # File should have been created
            assert filtered_file.exists()

        finally:
            shutil.rmtree(temp_dir)

    def test_match_record_preserves_original_data(self, temp_data_dir, monkeypatch):
        """Test that match_record preserves original data structure."""
        # Mock the filtered entries file path
        from sotd.match.match import _filtered_entries_manager

        monkeypatch.setattr("sotd.match.match._filtered_entries_manager", None)

        # Mock the Path constructor to return our test file
        original_path = Path

        def mock_path(path_str):
            if "intentionally_unmatched.yaml" in str(path_str):
                return Path(temp_data_dir) / "data" / "intentionally_unmatched.yaml"
            return original_path(path_str)

        monkeypatch.setattr("sotd.match.match.Path", mock_path)

        # Test record
        original_record = {
            "razor": "Hot Wheels Play Razor",
            "blade": "Feather",
            "brush": "Simpson Chubby 2",
            "soap": "Declaration Grooming",
            "id": "test123",
            "author": "test_user",
        }

        result = match_record(original_record)

        # Should preserve all original fields
        assert result["id"] == "test123"
        assert result["author"] == "test_user"

        # Should process all product fields
        assert "razor" in result
        assert "blade" in result
        assert "brush" in result
        assert "soap" in result
