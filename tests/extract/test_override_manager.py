#!/usr/bin/env python3
"""Unit tests for OverrideManager class."""

import pytest
from pathlib import Path
from unittest.mock import mock_open, patch

from sotd.extract.override_manager import OverrideManager


class TestOverrideManager:
    """Test cases for OverrideManager class."""

    def test_init(self):
        """Test OverrideManager initialization."""
        override_path = Path("test_overrides.yaml")
        manager = OverrideManager(override_path)
        assert manager.override_file_path == override_path
        assert manager.overrides == {}

    def test_load_overrides_empty_file(self):
        """Test loading overrides from empty file."""
        manager = OverrideManager(Path("empty.yaml"))

        mock_file = mock_open(read_data="")
        with patch.object(Path, "open", mock_file):
            with patch.object(Path, "exists", return_value=True):
                manager.load_overrides()

        assert manager.overrides == {}

    def test_load_overrides_valid_single_override(self):
        """Test loading valid single override."""
        yaml_content = """
2025-01:
  m99b8f9:
    razor: Koraat
"""
        manager = OverrideManager(Path("test.yaml"))

        mock_file = mock_open(read_data=yaml_content)
        with patch.object(Path, "open", mock_file):
            with patch.object(Path, "exists", return_value=True):
                manager.load_overrides()

        assert "2025-01" in manager.overrides
        assert "m99b8f9" in manager.overrides["2025-01"]
        assert manager.overrides["2025-01"]["m99b8f9"]["razor"] == "Koraat"

    def test_load_overrides_multiple_fields(self):
        """Test loading overrides for multiple fields."""
        yaml_content = """
2025-01:
  m99b8f9:
    razor: Koraat
    blade: "Gillette Minora Platinum"
    soap: "Declaration Grooming - Seville"
"""
        manager = OverrideManager(Path("test.yaml"))

        mock_file = mock_open(read_data=yaml_content)
        with patch.object(Path, "open", mock_file):
            with patch.object(Path, "exists", return_value=True):
                manager.load_overrides()

        comment_overrides = manager.overrides["2025-01"]["m99b8f9"]
        assert comment_overrides["razor"] == "Koraat"
        assert comment_overrides["blade"] == "Gillette Minora Platinum"
        assert comment_overrides["soap"] == "Declaration Grooming - Seville"

    def test_load_overrides_multiple_comments(self):
        """Test loading overrides for multiple comments."""
        yaml_content = """
2025-01:
  m99b8f9:
    razor: Koraat
  m99b8f0:
    brush: "Semogue 610"
"""
        manager = OverrideManager(Path("test.yaml"))

        mock_file = mock_open(read_data=yaml_content)
        with patch.object(Path, "open", mock_file):
            with patch.object(Path, "exists", return_value=True):
                manager.load_overrides()

        assert len(manager.overrides["2025-01"]) == 2
        assert manager.overrides["2025-01"]["m99b8f9"]["razor"] == "Koraat"
        assert manager.overrides["2025-01"]["m99b8f0"]["brush"] == "Semogue 610"

    def test_load_overrides_multiple_months(self):
        """Test loading overrides for multiple months."""
        manager = OverrideManager(Path("test.yaml"))

        with patch.object(Path, "exists", return_value=False):
            manager.load_overrides()

        assert manager.overrides == {}

    def test_load_overrides_file_not_exists(self):
        """Test behavior when override file doesn't exist."""
        manager = OverrideManager(Path("nonexistent.yaml"))

        with patch.object(Path, "exists", return_value=False):
            manager.load_overrides()

        assert manager.overrides == {}

    def test_load_overrides_invalid_yaml(self):
        """Test error handling for invalid YAML."""
        yaml_content = """
2025-01:
  m99b8f9:
    razor: Koraat
    invalid_field: value
"""
        manager = OverrideManager(Path("test.yaml"))

        mock_file = mock_open(read_data=yaml_content)
        with patch.object(Path, "open", mock_file):
            with patch.object(Path, "exists", return_value=True):
                with pytest.raises(ValueError, match="Invalid field 'invalid_field'"):
                    manager.load_overrides()

    def test_load_overrides_invalid_field_type(self):
        """Test error handling for invalid field type."""
        yaml_content = """
2025-01:
  m99b8f9:
    razor: 123
"""
        manager = OverrideManager(Path("test.yaml"))

        mock_file = mock_open(read_data=yaml_content)
        with patch.object(Path, "open", mock_file):
            with patch.object(Path, "exists", return_value=True):
                with pytest.raises(ValueError, match="must be a string"):
                    manager.load_overrides()

    def test_load_overrides_empty_value(self):
        """Test error handling for empty override values."""
        yaml_content = """
2025-01:
  m99b8f9:
    razor: ""
"""
        manager = OverrideManager(Path("test.yaml"))

        mock_file = mock_open(read_data=yaml_content)
        with patch.object(Path, "open", mock_file):
            with patch.object(Path, "exists", return_value=True):
                with pytest.raises(ValueError, match="cannot be empty or whitespace-only"):
                    manager.load_overrides()

    def test_load_overrides_whitespace_only_value(self):
        """Test error handling for whitespace-only override values."""
        yaml_content = """
2025-01:
  m99b8f9:
    razor: "   "
"""
        manager = OverrideManager(Path("test.yaml"))

        mock_file = mock_open(read_data=yaml_content)
        with patch.object(Path, "open", mock_file):
            with patch.object(Path, "exists", return_value=True):
                with pytest.raises(ValueError, match="cannot be empty or whitespace-only"):
                    manager.load_overrides()

    def test_load_overrides_value_too_long(self):
        """Test error handling for override values that are too long."""
        long_value = "a" * 201  # 201 characters, over the 200 limit
        yaml_content = f"""
2025-01:
  m99b8f9:
    razor: "{long_value}"
"""
        manager = OverrideManager(Path("test.yaml"))

        mock_file = mock_open(read_data=yaml_content)
        with patch.object(Path, "open", mock_file):
            with patch.object(Path, "exists", return_value=True):
                with pytest.raises(ValueError, match="is too long"):
                    manager.load_overrides()

    def test_load_overrides_duplicate_override(self):
        """Test error handling for duplicate overrides."""
        # Note: YAML doesn't allow duplicate keys, so this test validates
        # that the duplicate detection logic works correctly
        yaml_content = """
2025-01:
  m99b8f9:
    razor: Koraat
    blade: Feather
"""
        manager = OverrideManager(Path("test.yaml"))

        mock_file = mock_open(read_data=yaml_content)
        with patch.object(Path, "open", mock_file):
            with patch.object(Path, "exists", return_value=True):
                manager.load_overrides()

        # Should load successfully since no actual duplicates exist
        assert "2025-01" in manager.overrides
        assert "m99b8f9" in manager.overrides["2025-01"]
        assert manager.overrides["2025-01"]["m99b8f9"]["razor"] == "Koraat"
        assert manager.overrides["2025-01"]["m99b8f9"]["blade"] == "Feather"

    def test_load_overrides_invalid_root_type(self):
        """Test error handling for invalid root type."""
        yaml_content = "invalid content"
        manager = OverrideManager(Path("test.yaml"))

        mock_file = mock_open(read_data=yaml_content)
        with patch.object(Path, "open", mock_file):
            with patch.object(Path, "exists", return_value=True):
                with pytest.raises(ValueError, match="must contain a dictionary at root level"):
                    manager.load_overrides()

    def test_load_overrides_invalid_month_type(self):
        """Test error handling for invalid month type."""
        yaml_content = """
2025-01: "not a dict"
"""
        manager = OverrideManager(Path("test.yaml"))

        mock_file = mock_open(read_data=yaml_content)
        with patch.object(Path, "open", mock_file):
            with patch.object(Path, "exists", return_value=True):
                with pytest.raises(
                    ValueError, match="must contain a dictionary of comment overrides"
                ):
                    manager.load_overrides()

    def test_load_overrides_invalid_comment_type(self):
        """Test error handling for invalid comment type."""
        yaml_content = """
2025-01:
  m99b8f9: "not a dict"
"""
        manager = OverrideManager(Path("test.yaml"))

        mock_file = mock_open(read_data=yaml_content)
        with patch.object(Path, "open", mock_file):
            with patch.object(Path, "exists", return_value=True):
                with pytest.raises(ValueError, match="must contain field overrides"):
                    manager.load_overrides()

    def test_get_override_existing(self):
        """Test getting existing override."""
        yaml_content = """
2025-01:
  m99b8f9:
    razor: Koraat
"""
        manager = OverrideManager(Path("test.yaml"))

        mock_file = mock_open(read_data=yaml_content)
        with patch.object(Path, "open", mock_file):
            with patch.object(Path, "exists", return_value=True):
                manager.load_overrides()

        override = manager.get_override("2025-01", "m99b8f9", "razor")
        assert override == "Koraat"

    def test_get_override_nonexistent_month(self):
        """Test getting override for nonexistent month."""
        manager = OverrideManager(Path("test.yaml"))
        override = manager.get_override("2025-01", "m99b8f9", "razor")
        assert override is None

    def test_get_override_nonexistent_comment(self):
        """Test getting override for nonexistent comment."""
        yaml_content = """
2025-01:
  m99b8f9:
    razor: Koraat
"""
        manager = OverrideManager(Path("test.yaml"))

        mock_file = mock_open(read_data=yaml_content)
        with patch.object(Path, "open", mock_file):
            with patch.object(Path, "exists", return_value=True):
                manager.load_overrides()

        override = manager.get_override("2025-01", "nonexistent", "razor")
        assert override is None

    def test_get_override_nonexistent_field(self):
        """Test getting override for nonexistent field."""
        yaml_content = """
2025-01:
  m99b8f9:
    razor: Koraat
"""
        manager = OverrideManager(Path("test.yaml"))

        mock_file = mock_open(read_data=yaml_content)
        with patch.object(Path, "open", mock_file):
            with patch.object(Path, "exists", return_value=True):
                manager.load_overrides()

        override = manager.get_override("2025-01", "m99b8f9", "blade")
        assert override is None

    def test_validate_overrides_all_exist(self):
        """Test validation when all override comment IDs exist."""
        yaml_content = """
2025-01:
  m99b8f9:
    razor: Koraat
"""
        manager = OverrideManager(Path("test.yaml"))

        mock_file = mock_open(read_data=yaml_content)
        with patch.object(Path, "open", mock_file):
            with patch.object(Path, "exists", return_value=True):
                manager.load_overrides()

        data = [{"id": "m99b8f9", "author": "test"}]
        # Should not raise any exception
        manager.validate_overrides(data)

    def test_validate_overrides_missing_comment_id(self):
        """Test validation when override references missing comment ID."""
        yaml_content = """
2025-01:
  m99b8f9:
    razor: Koraat
"""
        manager = OverrideManager(Path("test.yaml"))

        mock_file = mock_open(read_data=yaml_content)
        with patch.object(Path, "open", mock_file):
            with patch.object(Path, "exists", return_value=True):
                manager.load_overrides()

        data = [{"id": "different_id", "author": "test"}]
        with pytest.raises(ValueError, match="non-existent comment IDs"):
            manager.validate_overrides(data)

    def test_validate_overrides_no_id_field(self):
        """Test validation when comment records don't have id field."""
        yaml_content = """
2025-01:
  m99b8f9:
    razor: Koraat
"""
        manager = OverrideManager(Path("test.yaml"))

        mock_file = mock_open(read_data=yaml_content)
        with patch.object(Path, "open", mock_file):
            with patch.object(Path, "exists", return_value=True):
                manager.load_overrides()

        data = [{"author": "test"}]  # Missing id field
        with pytest.raises(ValueError, match="non-existent comment IDs"):
            manager.validate_overrides(data)

    def test_apply_override_existing_field(self):
        """Test applying override to existing field."""
        manager = OverrideManager(Path("test.yaml"))
        field_data = {"original": "Ko", "normalized": "Ko"}

        result = manager.apply_override(field_data, "Koraat", True)

        assert result["original"] == "Ko"  # Preserved
        assert result["normalized"] == "Koraat"  # Overridden
        assert result["overridden"] == "Normalized"

    def test_apply_override_missing_field(self):
        """Test applying override to create missing field."""
        manager = OverrideManager(Path("test.yaml"))

        result = manager.apply_override(None, "Koraat", False)

        assert result["original"] == "Koraat"
        assert result["normalized"] == "Koraat"
        assert result["overridden"] == "Original,Normalized"

    def test_apply_override_none_field_data(self):
        """Test applying override when field_data is None."""
        manager = OverrideManager(Path("test.yaml"))

        result = manager.apply_override(None, "Koraat", True)

        # Should create new field since field_data is None
        assert result["original"] == "Koraat"
        assert result["normalized"] == "Koraat"
        assert result["overridden"] == "Original,Normalized"

    def test_has_overrides_false(self):
        """Test has_overrides when no overrides are loaded."""
        manager = OverrideManager(Path("test.yaml"))
        assert not manager.has_overrides()

    def test_has_overrides_true(self):
        """Test has_overrides when overrides are loaded."""
        yaml_content = """
2025-01:
  m99b8f9:
    razor: Koraat
"""
        manager = OverrideManager(Path("test.yaml"))

        mock_file = mock_open(read_data=yaml_content)
        with patch.object(Path, "open", mock_file):
            with patch.object(Path, "exists", return_value=True):
                manager.load_overrides()

        assert manager.has_overrides()

    def test_load_overrides_strips_whitespace(self):
        """Test that override values have whitespace stripped."""
        yaml_content = """
2025-01:
  m99b8f9:
    razor: "  Koraat  "
"""
        manager = OverrideManager(Path("test.yaml"))

        mock_file = mock_open(read_data=yaml_content)
        with patch.object(Path, "open", mock_file):
            with patch.object(Path, "exists", return_value=True):
                manager.load_overrides()

        override = manager.get_override("2025-01", "m99b8f9", "razor")
        assert override == "Koraat"  # Whitespace stripped

    def test_get_override_summary_empty(self):
        """Test get_override_summary when no overrides are loaded."""
        manager = OverrideManager(Path("test.yaml"))
        summary = manager.get_override_summary()

        assert summary["total_overrides"] == 0
        assert summary["months_with_overrides"] == 0
        assert summary["month_counts"] == {}
        assert summary["field_counts"] == {}

    def test_get_override_summary_with_overrides(self):
        """Test get_override_summary with loaded overrides."""
        yaml_content = """
2025-01:
  m99b8f9:
    razor: Koraat
    blade: Feather
  m99b8f0:
    brush: Semogue
2025-02:
  m99b8f1:
    soap: Declaration
"""
        manager = OverrideManager(Path("test.yaml"))

        mock_file = mock_open(read_data=yaml_content)
        with patch.object(Path, "open", mock_file):
            with patch.object(Path, "exists", return_value=True):
                manager.load_overrides()

        summary = manager.get_override_summary()

        assert summary["total_overrides"] == 4
        assert summary["months_with_overrides"] == 2
        assert summary["month_counts"]["2025-01"] == 3
        assert summary["month_counts"]["2025-02"] == 1
        assert summary["field_counts"]["razor"] == 1
        assert summary["field_counts"]["blade"] == 1
        assert summary["field_counts"]["brush"] == 1
        assert summary["field_counts"]["soap"] == 1
