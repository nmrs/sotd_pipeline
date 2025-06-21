"""
Unit tests for unified file I/O utilities.
"""

import json

import pytest
import yaml

from sotd.utils.file_io import (
    backup_file,
    ensure_directory_exists,
    get_file_size_mb,
    load_json_data,
    load_yaml_data,
    save_json_data,
    save_yaml_data,
)


class TestSaveJsonData:
    """Test JSON data saving functionality."""

    def test_save_json_data_success(self, tmp_path):
        """Test successful JSON data saving."""
        data = {"test": "value", "number": 42, "list": [1, 2, 3]}
        file_path = tmp_path / "test.json"

        save_json_data(data, file_path)

        assert file_path.exists()
        with file_path.open("r", encoding="utf-8") as f:
            loaded_data = json.load(f)

        assert loaded_data == data

    def test_save_json_data_creates_directory(self, tmp_path):
        """Test that save_json_data creates parent directories."""
        data = {"test": "value"}
        file_path = tmp_path / "subdir" / "nested" / "test.json"

        save_json_data(data, file_path)

        assert file_path.exists()
        assert file_path.parent.exists()

    def test_save_json_data_atomic_write(self, tmp_path):
        """Test that save_json_data uses atomic writes."""
        data = {"test": "value"}
        file_path = tmp_path / "test.json"

        # Create a file that should be replaced
        file_path.write_text("old content")

        save_json_data(data, file_path)

        # Verify the file was replaced atomically
        with file_path.open("r", encoding="utf-8") as f:
            loaded_data = json.load(f)

        assert loaded_data == data
        assert "old content" not in file_path.read_text()

    def test_save_json_data_custom_indent(self, tmp_path):
        """Test JSON saving with custom indentation."""
        data = {"test": "value"}
        file_path = tmp_path / "test.json"

        save_json_data(data, file_path, indent=4)

        content = file_path.read_text()
        # Check that indentation is 4 spaces
        assert '    "test"' in content

    def test_save_json_data_unicode(self, tmp_path):
        """Test JSON saving with unicode characters."""
        data = {"test": "café", "emoji": "🚀"}
        file_path = tmp_path / "test.json"

        save_json_data(data, file_path)

        with file_path.open("r", encoding="utf-8") as f:
            loaded_data = json.load(f)

        assert loaded_data == data

    def test_save_json_data_cleanup_on_error(self, tmp_path):
        """Test that temporary file is cleaned up on error."""
        data = {"test": "value"}
        file_path = tmp_path / "test.json"

        # Make the directory read-only to cause a write error
        tmp_path.chmod(0o444)

        with pytest.raises(OSError):
            save_json_data(data, file_path)

        # Check that no temporary file remains
        temp_files = list(tmp_path.glob("*.tmp"))
        assert len(temp_files) == 0


class TestLoadJsonData:
    """Test JSON data loading functionality."""

    def test_load_json_data_success(self, tmp_path):
        """Test successful JSON data loading."""
        data = {"test": "value", "number": 42}
        file_path = tmp_path / "test.json"

        with file_path.open("w", encoding="utf-8") as f:
            json.dump(data, f)

        loaded_data = load_json_data(file_path)
        assert loaded_data == data

    def test_load_json_data_file_not_found(self, tmp_path):
        """Test loading non-existent JSON file."""
        file_path = tmp_path / "nonexistent.json"

        with pytest.raises(FileNotFoundError):
            load_json_data(file_path)

    def test_load_json_data_invalid_json(self, tmp_path):
        """Test loading file with invalid JSON."""
        file_path = tmp_path / "invalid.json"
        file_path.write_text('{"invalid": json}')

        with pytest.raises(json.JSONDecodeError):
            load_json_data(file_path)

    def test_load_json_data_read_error(self, tmp_path):
        """Test loading file with read error."""
        file_path = tmp_path / "test.json"
        file_path.write_text('{"test": "value"}')

        # Make file unreadable
        file_path.chmod(0o000)

        with pytest.raises(OSError):
            load_json_data(file_path)


class TestSaveYamlData:
    """Test YAML data saving functionality."""

    def test_save_yaml_data_success(self, tmp_path):
        """Test successful YAML data saving."""
        data = {"test": "value", "number": 42, "list": [1, 2, 3]}
        file_path = tmp_path / "test.yaml"

        save_yaml_data(data, file_path)

        assert file_path.exists()
        with file_path.open("r", encoding="utf-8") as f:
            loaded_data = yaml.safe_load(f)

        assert loaded_data == data

    def test_save_yaml_data_creates_directory(self, tmp_path):
        """Test that save_yaml_data creates parent directories."""
        data = {"test": "value"}
        file_path = tmp_path / "subdir" / "nested" / "test.yaml"

        save_yaml_data(data, file_path)

        assert file_path.exists()
        assert file_path.parent.exists()

    def test_save_yaml_data_atomic_write(self, tmp_path):
        """Test that save_yaml_data uses atomic writes."""
        data = {"test": "value"}
        file_path = tmp_path / "test.yaml"

        # Create a file that should be replaced
        file_path.write_text("old content")

        save_yaml_data(data, file_path)

        # Verify the file was replaced atomically
        with file_path.open("r", encoding="utf-8") as f:
            loaded_data = yaml.safe_load(f)

        assert loaded_data == data
        assert "old content" not in file_path.read_text()

    def test_save_yaml_data_flow_style(self, tmp_path):
        """Test YAML saving with flow style."""
        data = {"test": "value"}
        file_path = tmp_path / "test.yaml"

        save_yaml_data(data, file_path, default_flow_style=True)

        content = file_path.read_text()
        # Flow style should produce inline format
        assert "{" in content and "}" in content

    def test_save_yaml_data_unicode(self, tmp_path):
        """Test YAML saving with unicode characters."""
        data = {"test": "café", "emoji": "🚀"}
        file_path = tmp_path / "test.yaml"

        save_yaml_data(data, file_path)

        with file_path.open("r", encoding="utf-8") as f:
            loaded_data = yaml.safe_load(f)

        assert loaded_data == data

    def test_save_yaml_data_cleanup_on_error(self, tmp_path):
        """Test that temporary file is cleaned up on error."""
        data = {"test": "value"}
        file_path = tmp_path / "test.yaml"

        # Make the directory read-only to cause a write error
        tmp_path.chmod(0o444)

        with pytest.raises(OSError):
            save_yaml_data(data, file_path)

        # Check that no temporary file remains
        temp_files = list(tmp_path.glob("*.tmp"))
        assert len(temp_files) == 0


class TestLoadYamlData:
    """Test YAML data loading functionality."""

    def test_load_yaml_data_success(self, tmp_path):
        """Test successful YAML data loading."""
        data = {"test": "value", "number": 42}
        file_path = tmp_path / "test.yaml"

        with file_path.open("w", encoding="utf-8") as f:
            yaml.dump(data, f)

        loaded_data = load_yaml_data(file_path)
        assert loaded_data == data

    def test_load_yaml_data_file_not_found(self, tmp_path):
        """Test loading non-existent YAML file."""
        file_path = tmp_path / "nonexistent.yaml"

        with pytest.raises(FileNotFoundError):
            load_yaml_data(file_path)

    def test_load_yaml_data_invalid_yaml(self, tmp_path):
        """Test loading file with invalid YAML."""
        file_path = tmp_path / "invalid.yaml"
        file_path.write_text("invalid: yaml: content: [")

        with pytest.raises(yaml.YAMLError):
            load_yaml_data(file_path)

    def test_load_yaml_data_empty_file(self, tmp_path):
        """Test loading empty YAML file."""
        file_path = tmp_path / "empty.yaml"
        file_path.write_text("")

        loaded_data = load_yaml_data(file_path)
        assert loaded_data == {}

    def test_load_yaml_data_read_error(self, tmp_path):
        """Test loading file with read error."""
        file_path = tmp_path / "test.yaml"
        file_path.write_text("test: value")

        # Make file unreadable
        file_path.chmod(0o000)

        with pytest.raises(OSError):
            load_yaml_data(file_path)


class TestGetFileSizeMb:
    """Test file size calculation functionality."""

    def test_get_file_size_mb_existing_file(self, tmp_path):
        """Test getting size of existing file."""
        file_path = tmp_path / "test.txt"
        content = "x" * (1024 * 1024)  # 1MB
        file_path.write_text(content)

        size_mb = get_file_size_mb(file_path)
        assert size_mb == 1.0

    def test_get_file_size_mb_nonexistent_file(self, tmp_path):
        """Test getting size of non-existent file."""
        file_path = tmp_path / "nonexistent.txt"

        size_mb = get_file_size_mb(file_path)
        assert size_mb == 0.0

    def test_get_file_size_mb_small_file(self, tmp_path):
        """Test getting size of small file."""
        file_path = tmp_path / "small.txt"
        file_path.write_text("hello")

        size_mb = get_file_size_mb(file_path)
        assert size_mb > 0.0
        assert size_mb < 0.001  # Should be very small


class TestEnsureDirectoryExists:
    """Test directory creation functionality."""

    def test_ensure_directory_exists_new_directory(self, tmp_path):
        """Test creating new directory."""
        new_dir = tmp_path / "new_directory"

        ensure_directory_exists(new_dir)

        assert new_dir.exists()
        assert new_dir.is_dir()

    def test_ensure_directory_exists_existing_directory(self, tmp_path):
        """Test with existing directory."""
        existing_dir = tmp_path / "existing"
        existing_dir.mkdir()

        ensure_directory_exists(existing_dir)

        assert existing_dir.exists()
        assert existing_dir.is_dir()

    def test_ensure_directory_exists_nested_directories(self, tmp_path):
        """Test creating nested directories."""
        nested_dir = tmp_path / "level1" / "level2" / "level3"

        ensure_directory_exists(nested_dir)

        assert nested_dir.exists()
        assert nested_dir.is_dir()
        assert (tmp_path / "level1").exists()
        assert (tmp_path / "level1" / "level2").exists()


class TestBackupFile:
    """Test file backup functionality."""

    def test_backup_file_existing_file(self, tmp_path):
        """Test backing up existing file."""
        original_file = tmp_path / "test.txt"
        original_file.write_text("original content")

        backup_path = backup_file(original_file)

        assert backup_path is not None
        assert backup_path.exists()
        assert backup_path.read_text() == "original content"
        assert original_file.exists()  # Original should still exist

    def test_backup_file_nonexistent_file(self, tmp_path):
        """Test backing up non-existent file."""
        nonexistent_file = tmp_path / "nonexistent.txt"

        backup_path = backup_file(nonexistent_file)

        assert backup_path is None

    def test_backup_file_custom_suffix(self, tmp_path):
        """Test backup with custom suffix."""
        original_file = tmp_path / "test.txt"
        original_file.write_text("original content")

        backup_path = backup_file(original_file, backup_suffix=".custom")

        assert backup_path is not None
        assert backup_path.suffix == ".custom"
        assert backup_path.read_text() == "original content"

    def test_backup_file_error_handling(self, tmp_path):
        """Test backup error handling."""
        original_file = tmp_path / "test.txt"
        original_file.write_text("original content")

        # Create a backup file that already exists to cause a copy error
        backup_path = original_file.with_suffix(original_file.suffix + ".backup")
        backup_path.write_text("existing backup")

        # Make the backup file read-only to cause copy error
        backup_path.chmod(0o444)

        # Try to backup the original file - should fail due to read-only backup
        result = backup_file(original_file)

        # Should return None on error
        assert result is None
