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
        yaml_content = """
2025-01:
  m99b8f9:
    razor: Koraat
2025-02:
  m99b8f0:
    blade: "Feather"
"""
        manager = OverrideManager(Path("test.yaml"))
        
        mock_file = mock_open(read_data=yaml_content)
        with patch.object(Path, "open", mock_file):
            with patch.object(Path, "exists", return_value=True):
                manager.load_overrides()
        
        assert "2025-01" in manager.overrides
        assert "2025-02" in manager.overrides
        assert manager.overrides["2025-01"]["m99b8f9"]["razor"] == "Koraat"
        assert manager.overrides["2025-02"]["m99b8f0"]["blade"] == "Feather"

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
                with pytest.raises(ValueError, match="must be a non-empty string"):
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
                with pytest.raises(ValueError, match="must be a non-empty string"):
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
                with pytest.raises(ValueError, match="must be a non-empty string"):
                    manager.load_overrides()

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
                with pytest.raises(ValueError, match="must contain a dictionary of comment overrides"):
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
