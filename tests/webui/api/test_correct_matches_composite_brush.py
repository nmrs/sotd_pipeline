#!/usr/bin/env python3
"""Tests for correct-matches endpoint with composite brush logic."""

import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add the webui directory to the Python path
webui_dir = Path(__file__).parent.parent
if str(webui_dir) not in sys.path:
    sys.path.insert(0, str(webui_dir))

from webui.api.analysis import get_correct_matches  # noqa: E402


class TestCorrectMatchesCompositeBrush:
    """Test cases for correct-matches endpoint with composite brush logic."""

    @patch("webui.api.analysis.project_root")
    @patch("builtins.open")
    @patch("yaml.safe_load")
    def test_get_correct_matches_brush_combines_all_sections(
        self, mock_yaml_load, mock_open, mock_project_root
    ):
        """Test that get_correct_matches for brush field combines data from brush, handle, and knot sections."""

        # Mock YAML data with brush, handle, and knot sections
        mock_yaml_data = {
            "brush": {"AP Shave Co": {"G5C": ["ap shave co g5c 24mm"]}},
            "handle": {"AP Shave Co": {"Unspecified": ["ap shave co. - lemon drop 26mm tgn boar"]}},
            "knot": {"The Golden Nib": {"Boar": ["ap shave co. - lemon drop 26mm tgn boar"]}},
        }

        mock_yaml_load.return_value = mock_yaml_data

        # Mock file operations
        mock_file = MagicMock()
        mock_open.return_value.__enter__.return_value = mock_file

        # Mock file exists check
        with patch("pathlib.Path.exists", return_value=True):
            # Call the async function
            import asyncio

            result = asyncio.run(get_correct_matches("brush"))

            # Verify the result combines all sections
            assert result.field == "brush"
            assert result.total_entries == 3  # 1 from brush + 1 from handle + 1 from knot

            # Verify the entries contain data from all sections
            entries = result.entries

            # Should have brush section
            assert "brush" in entries
            assert "AP Shave Co" in entries["brush"]
            assert "G5C" in entries["brush"]["AP Shave Co"]
            assert "ap shave co g5c 24mm" in entries["brush"]["AP Shave Co"]["G5C"]

            # Should have handle section
            assert "handle" in entries
            assert "AP Shave Co" in entries["handle"]
            assert "Unspecified" in entries["handle"]["AP Shave Co"]
            handle_text = "ap shave co. - lemon drop 26mm tgn boar"
            assert handle_text in entries["handle"]["AP Shave Co"]["Unspecified"]

            # Should have knot section
            assert "knot" in entries
            assert "The Golden Nib" in entries["knot"]
            assert "Boar" in entries["knot"]["The Golden Nib"]
            knot_text = "ap shave co. - lemon drop 26mm tgn boar"
            assert knot_text in entries["knot"]["The Golden Nib"]["Boar"]

    @patch("webui.api.analysis.project_root")
    @patch("builtins.open")
    @patch("yaml.safe_load")
    def test_get_correct_matches_brush_preserves_existing_brush_logic(
        self, mock_yaml_load, mock_open, mock_project_root
    ):
        """Test that existing brush section logic is preserved when combining sections."""
        # Mock project root
        mock_project_root = Path("/fake/project/root")

        # Mock YAML data with only brush section (existing behavior)
        mock_yaml_data = {
            "brush": {"AP Shave Co": {"G5C": ["ap shave co g5c 24mm", "ap shave co g5c 26mm"]}}
        }

        mock_yaml_load.return_value = mock_yaml_data

        # Mock file operations
        mock_file = MagicMock()
        mock_open.return_value.__enter__.return_value = mock_file

        # Mock file exists check
        with patch("pathlib.Path.exists", return_value=True):
            # Call the async function
            import asyncio

            result = asyncio.run(get_correct_matches("brush"))

            # Verify the result works as before for brush-only data
            assert result.field == "brush"
            assert result.total_entries == 2  # 2 entries in the brush section

            # Verify the entries contain only brush section data
            entries = result.entries
            assert "brush" in entries
            assert "handle" not in entries
            assert "knot" not in entries

    @patch("webui.api.analysis.project_root")
    @patch("builtins.open")
    @patch("yaml.safe_load")
    def test_get_correct_matches_brush_handles_empty_sections(
        self, mock_yaml_load, mock_open, mock_project_root
    ):
        """Test that empty sections are handled gracefully."""
        # Mock project root
        mock_project_root = Path("/fake/project/root")

        # Mock YAML data with empty sections
        mock_yaml_data = {"brush": {}, "handle": {}, "knot": {}}

        mock_yaml_load.return_value = mock_yaml_data

        # Mock file operations
        mock_file = MagicMock()
        mock_open.return_value.__enter__.return_value = mock_file

        # Mock file exists check
        with patch("pathlib.Path.exists", return_value=True):
            # Call the async function
            import asyncio

            result = asyncio.run(get_correct_matches("brush"))

            # Verify the result handles empty sections
            assert result.field == "brush"
            assert result.total_entries == 0

            # Verify the entries contain all sections even when empty
            entries = result.entries
            assert "brush" in entries
            assert "handle" in entries
            assert "knot" in entries

    @patch("webui.api.analysis.project_root")
    @patch("builtins.open")
    @patch("yaml.safe_load")
    def test_get_correct_matches_brush_handles_missing_sections(
        self, mock_yaml_load, mock_open, mock_project_root
    ):
        """Test that missing sections are handled gracefully."""
        # Mock project root
        mock_project_root = Path("/fake/project/root")

        # Mock YAML data with only brush section (missing handle/knot)
        mock_yaml_data = {
            "brush": {"AP Shave Co": {"G5C": ["ap shave co g5c 24mm"]}}
            # Note: no handle or knot sections
        }

        mock_yaml_load.return_value = mock_yaml_data

        # Mock file operations
        mock_file = MagicMock()
        mock_open.return_value.__enter__.return_value = mock_file

        # Mock file exists check
        with patch("pathlib.Path.exists", return_value=True):
            # Call the function
            result = get_correct_matches("brush")

            # Verify the result handles missing sections
            assert result.field == "brush"
            assert result.total_entries == 1  # Only brush section entries

            # Verify the entries contain available sections
            entries = result.entries
            assert "brush" in entries
            assert "handle" not in entries
            assert "knot" not in entries

    @patch("webui.api.analysis.project_root")
    @patch("builtins.open")
    @patch("yaml.safe_load")
    def test_get_correct_matches_non_brush_fields_unaffected(
        self, mock_yaml_load, mock_open, mock_project_root
    ):
        """Test that non-brush fields are not affected by the composite brush logic."""
        # Mock project root
        mock_project_root = Path("/fake/project/root")

        # Mock YAML data with multiple fields
        mock_yaml_data = {
            "razor": {"Koraat": {"Moarteen": ["koraat moarteen"]}},
            "brush": {"AP Shave Co": {"G5C": ["ap shave co g5c 24mm"]}},
            "handle": {"AP Shave Co": {"Unspecified": ["ap shave co. - lemon drop 26mm tgn boar"]}},
            "knot": {"The Golden Nib": {"Boar": ["ap shave co. - lemon drop 26mm tgn boar"]}},
        }

        mock_yaml_load.return_value = mock_yaml_data

        # Mock file operations
        mock_file = MagicMock()
        mock_open.return_value.__enter__.return_value = mock_file

        # Mock file exists check
        with patch("pathlib.Path.exists", return_value=True):
            # Test razor field (should not be affected)
            result = get_correct_matches("razor")

            # Verify razor field is not affected
            assert result.field == "razor"
            assert result.total_entries == 1  # Only razor section entries

            # Verify the entries contain only razor section data
            entries = result.entries
            assert "razor" in entries
            assert "brush" not in entries
            assert "handle" not in entries
            assert "knot" not in entries

    @patch("webui.api.analysis.project_root")
    @patch("builtins.open")
    @patch("yaml.safe_load")
    def test_get_correct_matches_brush_composite_brush_confirmation_logic(
        self, mock_yaml_load, mock_open, mock_project_root
    ):
        """Test that the combined data enables composite brush confirmation logic."""
        # Mock project root
        mock_project_root = Path("/fake/project/root")

        # Mock YAML data with composite brush components
        mock_yaml_data = {
            "brush": {"AP Shave Co": {"G5C": ["ap shave co g5c 24mm"]}},
            "handle": {"AP Shave Co": {"Unspecified": ["ap shave co. - lemon drop 26mm tgn boar"]}},
            "knot": {"The Golden Nib": {"Boar": ["ap shave co. - lemon drop 26mm tgn boar"]}},
        }

        mock_yaml_load.return_value = mock_yaml_data

        # Mock file operations
        mock_file = MagicMock()
        mock_open.return_value.__enter__.return_value = mock_file

        # Mock file exists check
        with patch("pathlib.Path.exists", return_value=True):
            # Call the function
            result = get_correct_matches("brush")

            # Verify the result provides data needed for composite brush confirmation
            assert result.field == "brush"

            # The frontend should now be able to determine that:
            # "ap shave co. - lemon drop 26mm tgn boar" is confirmed because:
            # 1. Its handle component "AP Shave Co - Unspecified" exists in handle section
            # 2. Its knot component "The Golden Nib - Boar" exists in knot section

            entries = result.entries

            # Verify handle component data is available
            assert "handle" in entries
            handle_entries = entries["handle"]["AP Shave Co"]["Unspecified"]
            assert "ap shave co. - lemon drop 26mm tgn boar" in handle_entries

            # Verify knot component data is available
            assert "knot" in entries
            knot_entries = entries["knot"]["The Golden Nib"]["Boar"]
            assert "ap shave co. - lemon drop 26mm tgn boar" in knot_entries

            # This enables the frontend to implement the logic:
            # is_confirmed = handle_confirmed AND knot_confirmed
            # where handle_confirmed = handle_source_text in handle_section
            # and knot_confirmed = knot_source_text in knot_section
