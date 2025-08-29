#!/usr/bin/env python3
"""Tests for refactored brush_splits module using YAML utilities."""

from unittest.mock import patch

import pytest


class TestBrushSplitsYAMLRefactor:
    """Test that brush_splits module uses YAML utilities correctly."""

    def test_load_validated_splits_uses_yaml_utils(self, tmp_path):
        """Test that load_validated_splits uses the new YAML utilities."""
        # Create test YAML data
        test_data = {
            "splits": [
                {
                    "original": "Test Brush",
                    "handle": "Test Handle",
                    "knot": "Test Knot",
                    "validated": True,
                    "should_not_split": False,
                }
            ]
        }

        yaml_file = tmp_path / "brush_splits.yaml"
        # Create the file so the method doesn't return early
        yaml_file.touch()

        # Mock the YAML utilities
        with patch("webui.api.utils.yaml_utils.load_yaml_file") as mock_load:
            mock_load.return_value = test_data

            # Import the refactored module
            from webui.api.brush_splits import BrushSplitValidator

            validator = BrushSplitValidator()
            validator.yaml_path = yaml_file

            # Call the method
            validator.load_validated_splits()

            # Verify the YAML utility was called
            mock_load.assert_called_once_with(yaml_file)

    def test_save_validated_splits_uses_yaml_utils(self, tmp_path):
        """Test that save_validated_splits uses the new YAML utilities."""
        from webui.api.brush_splits import BrushSplit, BrushSplitValidator

        # Create test splits
        test_splits = [
            BrushSplit(
                original="Test Brush",
                handle="Test Handle",
                knot="Test Knot",
                validated=True,
                should_not_split=False,
            )
        ]

        yaml_file = tmp_path / "brush_splits.yaml"

        # Mock the YAML utilities
        with patch("webui.api.utils.yaml_utils.save_yaml_file") as mock_save:
            validator = BrushSplitValidator()
            validator.yaml_path = yaml_file

            # Call the method
            result = validator.save_validated_splits(test_splits)

            # Verify the YAML utility was called with correct data
            assert result is True
            mock_save.assert_called_once()

            # Check that the data structure is correct
            call_args = mock_save.call_args
            assert call_args[0][1] == yaml_file  # file_path
            data = call_args[0][0]  # data
            assert "splits" in data
            assert len(data["splits"]) == 1

    def test_load_validated_splits_handles_missing_file(self, tmp_path):
        """Test that load_validated_splits handles missing file gracefully."""
        yaml_file = tmp_path / "nonexistent.yaml"
        yaml_file.touch()  # Create the file so the method doesn't return early

        with patch("webui.api.utils.yaml_utils.load_yaml_file") as mock_load:
            mock_load.side_effect = FileNotFoundError("YAML file not found")

            from webui.api.brush_splits import BrushSplitValidator, ProcessingError

            validator = BrushSplitValidator()
            validator.yaml_path = yaml_file

            # Should raise ProcessingError
            with pytest.raises(ProcessingError, match="Failed to load validated splits"):
                validator.load_validated_splits()

            # Verify the YAML utility was called
            mock_load.assert_called_once_with(yaml_file)

    def test_load_validated_splits_handles_corrupted_data(self, tmp_path):
        """Test that load_validated_splits handles corrupted YAML data."""
        yaml_file = tmp_path / "corrupted.yaml"
        yaml_file.touch()  # Create the file

        with patch("webui.api.utils.yaml_utils.load_yaml_file") as mock_load:
            mock_load.return_value = "not a dict"  # Invalid data

            from webui.api.brush_splits import BrushSplitValidator, DataCorruptionError

            validator = BrushSplitValidator()
            validator.yaml_path = yaml_file

            # Should raise DataCorruptionError
            with pytest.raises(DataCorruptionError):
                validator.load_validated_splits()

    def test_save_validated_splits_handles_io_error(self, tmp_path):
        """Test that save_validated_splits handles I/O errors gracefully."""
        from webui.api.brush_splits import BrushSplit, BrushSplitValidator

        test_splits = [
            BrushSplit(
                original="Test Brush", handle="Test Handle", knot="Test Knot", validated=True
            )
        ]

        yaml_file = tmp_path / "brush_splits.yaml"

        with patch("webui.api.utils.yaml_utils.save_yaml_file") as mock_save:
            mock_save.side_effect = OSError("I/O error")

            validator = BrushSplitValidator()
            validator.yaml_path = yaml_file

            # Should return False on error
            result = validator.save_validated_splits(test_splits)
            assert result is False

    def test_yaml_utils_integration(self, tmp_path):
        """Test full integration with YAML utilities."""
        from webui.api.brush_splits import BrushSplit, BrushSplitValidator

        # Create test data
        test_splits = [
            BrushSplit(
                original="Test Brush 1",
                handle="Test Handle",
                knot="Test Knot",
                validated=True,
                should_not_split=False,
            ),
            BrushSplit(
                original="Test Brush 2",
                handle=None,
                knot="Test Brush 2",
                validated=True,
                should_not_split=True,
            ),
        ]

        yaml_file = tmp_path / "brush_splits.yaml"

        # Test save
        validator = BrushSplitValidator()
        validator.yaml_path = yaml_file

        result = validator.save_validated_splits(test_splits)
        assert result is True
        assert yaml_file.exists()

        # Test load
        validator.validated_splits.clear()
        validator.load_validated_splits()

        assert len(validator.validated_splits) == 2
        assert "Test Brush 1" in validator.validated_splits
        assert "Test Brush 2" in validator.validated_splits
