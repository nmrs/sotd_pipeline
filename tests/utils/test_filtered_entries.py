"""Tests for filtered entries utilities."""

import pytest
import yaml

from sotd.utils.filtered_entries import (
    FilteredEntriesManager,
    load_filtered_entries,
    save_filtered_entries,
)


class TestFilteredEntriesManager:
    """Test the FilteredEntriesManager class."""

    def test_init(self, tmp_path):
        """Test manager initialization."""
        file_path = tmp_path / "test_filtered.yaml"
        manager = FilteredEntriesManager(file_path)

        assert manager.file_path == file_path
        assert manager._data == {}

    def test_load_empty_file(self, tmp_path):
        """Test loading when file doesn't exist."""
        file_path = tmp_path / "test_filtered.yaml"
        manager = FilteredEntriesManager(file_path)

        result = manager.load()

        expected = {
            "razor": {},
            "brush": {},
            "blade": {},
            "soap": {},
        }
        assert result == expected
        assert manager._data == expected
        assert file_path.exists()

    def test_load_populated_file(self, tmp_path):
        """Test loading populated YAML file."""
        file_path = tmp_path / "test_filtered.yaml"

        # Create test data
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

        with open(file_path, "w", encoding="utf-8") as f:
            yaml.dump(test_data, f)

        manager = FilteredEntriesManager(file_path)
        result = manager.load()

        assert result == test_data
        assert manager._data == test_data

    def test_load_missing_categories(self, tmp_path):
        """Test loading file with missing categories."""
        file_path = tmp_path / "test_filtered.yaml"

        # Create test data missing some categories
        test_data = {"razor": {"Test Razor": {"added_date": "2025-01-27", "comment_ids": []}}}

        with open(file_path, "w", encoding="utf-8") as f:
            yaml.dump(test_data, f)

        manager = FilteredEntriesManager(file_path)
        result = manager.load()

        # Should have all categories
        assert "razor" in result
        assert "brush" in result
        assert "blade" in result
        assert "soap" in result
        assert result["razor"] == test_data["razor"]
        assert result["brush"] == {}
        assert result["blade"] == {}
        assert result["soap"] == {}

    def test_load_corrupted_yaml(self, tmp_path):
        """Test loading corrupted YAML file."""
        file_path = tmp_path / "test_filtered.yaml"

        # Write invalid YAML
        with open(file_path, "w", encoding="utf-8") as f:
            f.write("invalid: yaml: content: [")

        manager = FilteredEntriesManager(file_path)

        with pytest.raises(ValueError, match="Invalid YAML format"):
            manager.load()

    def test_save(self, tmp_path):
        """Test saving data to YAML file."""
        file_path = tmp_path / "test_filtered.yaml"
        manager = FilteredEntriesManager(file_path)

        # Set test data
        manager._data = {
            "razor": {
                "Test Razor": {
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

        manager.save()

        assert file_path.exists()

        # Verify saved content
        with open(file_path, "r", encoding="utf-8") as f:
            saved_data = yaml.safe_load(f)

        assert saved_data == manager._data

    def test_add_entry_new(self, tmp_path):
        """Test adding a new entry."""
        file_path = tmp_path / "test_filtered.yaml"
        manager = FilteredEntriesManager(file_path)
        manager.load()

        manager.add_entry(
            category="razor",
            entry_name="Test Razor",
            comment_id="abc123",
            file_path="data/comments/2025-01.json",
            source="user",
        )

        assert manager.is_filtered("razor", "Test Razor")
        comment_ids = manager.get_entry_comment_ids("razor", "Test Razor")
        assert len(comment_ids) == 1
        assert comment_ids[0]["id"] == "abc123"
        assert comment_ids[0]["file"] == "data/comments/2025-01.json"
        assert comment_ids[0]["source"] == "user"

    def test_add_entry_existing(self, tmp_path):
        """Test adding to existing entry."""
        file_path = tmp_path / "test_filtered.yaml"
        manager = FilteredEntriesManager(file_path)
        manager.load()

        # Add first comment
        manager.add_entry(
            category="razor",
            entry_name="Test Razor",
            comment_id="abc123",
            file_path="data/comments/2025-01.json",
        )

        # Add second comment
        manager.add_entry(
            category="razor",
            entry_name="Test Razor",
            comment_id="def456",
            file_path="data/comments/2025-01.json",
        )

        comment_ids = manager.get_entry_comment_ids("razor", "Test Razor")
        assert len(comment_ids) == 2
        assert any(c["id"] == "abc123" for c in comment_ids)
        assert any(c["id"] == "def456" for c in comment_ids)

    def test_add_entry_duplicate(self, tmp_path):
        """Test adding duplicate comment_id."""
        file_path = tmp_path / "test_filtered.yaml"
        manager = FilteredEntriesManager(file_path)
        manager.load()

        # Add comment
        manager.add_entry(
            category="razor",
            entry_name="Test Razor",
            comment_id="abc123",
            file_path="data/comments/2025-01.json",
        )

        # Add same comment again
        manager.add_entry(
            category="razor",
            entry_name="Test Razor",
            comment_id="abc123",
            file_path="data/comments/2025-01.json",
        )

        comment_ids = manager.get_entry_comment_ids("razor", "Test Razor")
        assert len(comment_ids) == 1  # Should not duplicate

    def test_remove_entry(self, tmp_path):
        """Test removing an entry."""
        file_path = tmp_path / "test_filtered.yaml"
        manager = FilteredEntriesManager(file_path)
        manager.load()

        # Add entry
        manager.add_entry(
            category="razor",
            entry_name="Test Razor",
            comment_id="abc123",
            file_path="data/comments/2025-01.json",
        )

        # Remove entry
        result = manager.remove_entry(
            category="razor",
            entry_name="Test Razor",
            comment_id="abc123",
            file_path="data/comments/2025-01.json",
        )

        assert result is True
        assert not manager.is_filtered("razor", "Test Razor")
        assert manager.get_entry_comment_ids("razor", "Test Razor") == []

    def test_remove_entry_nonexistent(self, tmp_path):
        """Test removing non-existent entry."""
        file_path = tmp_path / "test_filtered.yaml"
        manager = FilteredEntriesManager(file_path)
        manager.load()

        result = manager.remove_entry(
            category="razor",
            entry_name="Test Razor",
            comment_id="abc123",
            file_path="data/comments/2025-01.json",
        )

        assert result is False

    def test_is_filtered(self, tmp_path):
        """Test checking if entry is filtered."""
        file_path = tmp_path / "test_filtered.yaml"
        manager = FilteredEntriesManager(file_path)
        manager.load()

        # Initially not filtered
        assert not manager.is_filtered("razor", "Test Razor")

        # Add entry
        manager.add_entry(
            category="razor",
            entry_name="Test Razor",
            comment_id="abc123",
            file_path="data/comments/2025-01.json",
        )

        # Now filtered
        assert manager.is_filtered("razor", "Test Razor")

    def test_get_filtered_entries_all(self, tmp_path):
        """Test getting all filtered entries."""
        file_path = tmp_path / "test_filtered.yaml"
        manager = FilteredEntriesManager(file_path)
        manager.load()

        # Add entries
        manager.add_entry("razor", "Test Razor", "abc123", "data/comments/2025-01.json")
        manager.add_entry("brush", "Test Brush", "def456", "data/comments/2025-01.json")

        result = manager.get_filtered_entries()

        assert "razor" in result
        assert "brush" in result
        assert "Test Razor" in result["razor"]
        assert "Test Brush" in result["brush"]

    def test_get_filtered_entries_category(self, tmp_path):
        """Test getting filtered entries for specific category."""
        file_path = tmp_path / "test_filtered.yaml"
        manager = FilteredEntriesManager(file_path)
        manager.load()

        # Add entries
        manager.add_entry("razor", "Test Razor", "abc123", "data/comments/2025-01.json")
        manager.add_entry("brush", "Test Brush", "def456", "data/comments/2025-01.json")

        result = manager.get_filtered_entries("razor")

        assert "razor" in result
        assert "brush" not in result
        assert "Test Razor" in result["razor"]

    def test_get_entry_comment_ids(self, tmp_path):
        """Test getting comment IDs for an entry."""
        file_path = tmp_path / "test_filtered.yaml"
        manager = FilteredEntriesManager(file_path)
        manager.load()

        # Add entry
        manager.add_entry(
            category="razor",
            entry_name="Test Razor",
            comment_id="abc123",
            file_path="data/comments/2025-01.json",
        )

        comment_ids = manager.get_entry_comment_ids("razor", "Test Razor")

        assert len(comment_ids) == 1
        assert comment_ids[0]["id"] == "abc123"
        assert comment_ids[0]["file"] == "data/comments/2025-01.json"

    def test_get_entry_comment_ids_nonexistent(self, tmp_path):
        """Test getting comment IDs for non-existent entry."""
        file_path = tmp_path / "test_filtered.yaml"
        manager = FilteredEntriesManager(file_path)
        manager.load()

        comment_ids = manager.get_entry_comment_ids("razor", "Test Razor")

        assert comment_ids == []

    def test_validate_data_valid(self, tmp_path):
        """Test validation with valid data."""
        file_path = tmp_path / "test_filtered.yaml"
        manager = FilteredEntriesManager(file_path)
        manager.load()

        # Add valid entry
        manager.add_entry(
            category="razor",
            entry_name="Test Razor",
            comment_id="abc123",
            file_path="data/comments/2025-01.json",
        )

        is_valid, errors = manager.validate_data()

        assert is_valid is True
        assert errors == []

    def test_validate_data_invalid_category(self, tmp_path):
        """Test validation with invalid category."""
        file_path = tmp_path / "test_filtered.yaml"
        manager = FilteredEntriesManager(file_path)
        manager.load()

        # Add invalid category
        manager._data["invalid_category"] = {}

        is_valid, errors = manager.validate_data()

        assert is_valid is False
        assert any("Invalid category: invalid_category" in error for error in errors)

    def test_validate_data_missing_fields(self, tmp_path):
        """Test validation with missing required fields."""
        file_path = tmp_path / "test_filtered.yaml"
        manager = FilteredEntriesManager(file_path)
        manager.load()

        # Add entry with missing fields
        manager._data["razor"]["Test Razor"] = {
            "added_date": "2025-01-27",
            "comment_ids": [{"id": "abc123"}],  # Missing file and source
        }

        is_valid, errors = manager.validate_data()

        assert is_valid is False
        assert any("Missing fields" in error for error in errors)


class TestUtilityFunctions:
    """Test utility functions."""

    def test_load_filtered_entries(self, tmp_path):
        """Test load_filtered_entries function."""
        file_path = tmp_path / "test_filtered.yaml"

        # Create test data
        test_data = {
            "razor": {"Test Razor": {"added_date": "2025-01-27", "comment_ids": []}},
            "brush": {},
            "blade": {},
            "soap": {},
        }

        with open(file_path, "w", encoding="utf-8") as f:
            yaml.dump(test_data, f)

        manager = load_filtered_entries(file_path)

        assert isinstance(manager, FilteredEntriesManager)
        assert manager.file_path == file_path
        assert manager._data == test_data

    def test_save_filtered_entries(self, tmp_path):
        """Test save_filtered_entries function."""
        file_path = tmp_path / "test_filtered.yaml"
        manager = FilteredEntriesManager(file_path)
        manager.load()

        # Add test data
        manager.add_entry(
            category="razor",
            entry_name="Test Razor",
            comment_id="abc123",
            file_path="data/comments/2025-01.json",
        )

        save_filtered_entries(manager)

        assert file_path.exists()

        # Verify saved content
        with open(file_path, "r", encoding="utf-8") as f:
            saved_data = yaml.safe_load(f)

        assert "razor" in saved_data
        assert "Test Razor" in saved_data["razor"]
