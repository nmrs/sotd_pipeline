#!/usr/bin/env python3
"""Tests for YAML utilities."""

from pathlib import Path
from unittest.mock import patch

import pytest

from webui.api.utils.yaml_utils import (
    load_yaml_file,
    save_yaml_file,
    validate_required_fields,
    validate_yaml_structure,
)


class TestLoadYamlFile:
    """Test load_yaml_file function."""

    def test_load_valid_yaml_file(self, tmp_path):
        """Test loading a valid YAML file."""
        yaml_content = """
        test_key: test_value
        nested:
          key: value
        """
        yaml_file = tmp_path / "test.yaml"
        yaml_file.write_text(yaml_content)

        result = load_yaml_file(yaml_file)

        assert result == {"test_key": "test_value", "nested": {"key": "value"}}

    def test_load_nonexistent_file(self, tmp_path):
        """Test loading a file that doesn't exist."""
        nonexistent_file = tmp_path / "nonexistent.yaml"

        with pytest.raises(FileNotFoundError, match="YAML file not found"):
            load_yaml_file(nonexistent_file)

    def test_load_malformed_yaml(self, tmp_path):
        """Test loading a malformed YAML file."""
        malformed_content = """
        test_key: test_value
        nested:
          - invalid: yaml: structure
        """
        yaml_file = tmp_path / "malformed.yaml"
        yaml_file.write_text(malformed_content)

        with pytest.raises(Exception):  # yaml.YAMLError
            load_yaml_file(yaml_file)

    def test_load_empty_file(self, tmp_path):
        """Test loading an empty YAML file."""
        yaml_file = tmp_path / "empty.yaml"
        yaml_file.write_text("")

        result = load_yaml_file(yaml_file)

        assert result is None  # yaml.safe_load returns None for empty files


class TestSaveYamlFile:
    """Test save_yaml_file function."""

    def test_save_valid_data(self, tmp_path):
        """Test saving valid data to YAML file."""
        test_data = {"test_key": "test_value", "nested": {"key": "value"}}
        yaml_file = tmp_path / "test.yaml"

        save_yaml_file(test_data, yaml_file)

        assert yaml_file.exists()
        loaded_data = load_yaml_file(yaml_file)
        assert loaded_data == test_data

    def test_save_atomic_write(self, tmp_path):
        """Test that save uses atomic write (temp file then move)."""
        test_data = {"key": "value"}
        yaml_file = tmp_path / "test.yaml"

        # Mock the replace method to verify atomic write
        with patch.object(Path, "replace") as mock_replace:
            save_yaml_file(test_data, yaml_file)
            mock_replace.assert_called_once()

    def test_save_cleanup_temp_file_on_error(self, tmp_path):
        """Test that temp file is cleaned up on error."""
        test_data = {"key": "value"}
        yaml_file = tmp_path / "test.yaml"

        # Mock yaml.dump to raise an error
        with patch("yaml.dump", side_effect=Exception("YAML error")):
            with pytest.raises(Exception):
                save_yaml_file(test_data, yaml_file)

            # Verify temp file was cleaned up
            temp_file = yaml_file.with_suffix(".tmp")
            assert not temp_file.exists()

    def test_save_unicode_data(self, tmp_path):
        """Test saving data with unicode characters."""
        test_data = {"key": "value", "unicode": "café", "emoji": "🚀"}
        yaml_file = tmp_path / "test.yaml"

        save_yaml_file(test_data, yaml_file)

        loaded_data = load_yaml_file(yaml_file)
        assert loaded_data == test_data


class TestValidateYamlStructure:
    """Test validate_yaml_structure function."""

    def test_validate_valid_dict(self):
        """Test validation of valid dictionary."""
        data = {"key": "value"}
        result = validate_yaml_structure(data, dict)
        assert result is True

    def test_validate_valid_list(self):
        """Test validation of valid list."""
        data = ["item1", "item2"]
        result = validate_yaml_structure(data, list)
        assert result is True

    def test_validate_wrong_type(self):
        """Test validation with wrong type."""
        data = "not a dict"
        result = validate_yaml_structure(data, dict)
        assert result is False

    def test_validate_empty_dict(self):
        """Test validation of empty dictionary."""
        data = {}
        result = validate_yaml_structure(data, dict)
        assert result is False  # Empty dict is considered invalid

    def test_validate_none(self):
        """Test validation of None."""
        result = validate_yaml_structure(None, dict)
        assert result is False


class TestValidateRequiredFields:
    """Test validate_required_fields function."""

    def test_validate_all_fields_present(self):
        """Test validation when all required fields are present."""
        data = {"field1": "value1", "field2": "value2", "field3": "value3"}
        required_fields = ["field1", "field2"]
        result = validate_required_fields(data, required_fields)
        assert result is True

    def test_validate_missing_fields(self):
        """Test validation when required fields are missing."""
        data = {"field1": "value1", "field3": "value3"}
        required_fields = ["field1", "field2", "field4"]
        result = validate_required_fields(data, required_fields)
        assert result is False

    def test_validate_empty_required_fields(self):
        """Test validation with empty required fields list."""
        data = {"field1": "value1"}
        required_fields = []
        result = validate_required_fields(data, required_fields)
        assert result is True

    def test_validate_empty_data(self):
        """Test validation with empty data."""
        data = {}
        required_fields = ["field1"]
        result = validate_required_fields(data, required_fields)
        assert result is False

    def test_validate_none_data(self):
        """Test validation with None data."""
        required_fields = ["field1"]
        result = validate_required_fields(None, required_fields)  # type: ignore
        assert result is False
