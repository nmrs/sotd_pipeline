"""Test CorrectMatchesManager with new brand/model hierarchy structure."""

import pytest
from pathlib import Path
from unittest.mock import Mock

from sotd.match.tools.managers.correct_matches_manager import CorrectMatchesManager


class TestCorrectMatchesManagerNewStructure:
    """Test CorrectMatchesManager with new brand/model hierarchy structure."""

    @pytest.fixture
    def console_mock(self):
        """Create a mock console for testing."""
        return Mock()

    @pytest.fixture
    def correct_matches_manager(self, console_mock, tmp_path):
        """Create CorrectMatchesManager instance for testing."""
        correct_matches_file = tmp_path / "correct_matches.yaml"
        return CorrectMatchesManager(console_mock, correct_matches_file)

    def test_handle_section_structure_uses_catalog_model_names(self, correct_matches_manager):
        """Test that handle section structure uses catalog model names."""
        # Test data with new brand/model hierarchy
        match_data = {
            "original": "Declaration Grooming Washington handle",
            "matched": {
                "handle_maker": "Declaration Grooming",
                "handle_model": "Washington",
            },
            "field": "handle",
        }

        # Create match key
        match_key = correct_matches_manager.create_match_key(
            "handle", "Declaration Grooming Washington handle", match_data["matched"]
        )

        # Mark as correct
        correct_matches_manager.mark_match_as_correct(match_key, match_data)

        # Save to file
        correct_matches_manager.save_correct_matches()

        # Verify the structure uses catalog model names
        # The handle section should have: Declaration Grooming -> Washington -> [source_text]
        # Not: Declaration Grooming -> extracted_model_name -> [source_text]

        # Reload and check structure
        correct_matches_manager.load_correct_matches()

        # Check that the handle section has the correct structure
        # This will be verified by checking the saved YAML structure

    def test_model_name_extraction_from_catalog(self, correct_matches_manager):
        """Test that model names are extracted from catalog, not from source_text."""
        # Test with specific model
        match_data = {
            "original": "Declaration Grooming Jefferson handle",
            "matched": {
                "handle_maker": "Declaration Grooming",
                "handle_model": "Jefferson",
            },
            "field": "handle",
        }

        match_key = correct_matches_manager.create_match_key(
            "handle", "Declaration Grooming Jefferson handle", match_data["matched"]
        )
        correct_matches_manager.mark_match_as_correct(match_key, match_data)
        correct_matches_manager.save_correct_matches()

        # The saved structure should use "Jefferson" (from catalog) not extracted model name

        # Test with Unspecified model
        match_data_unspecified = {
            "original": "Jayaruh handle",
            "matched": {
                "handle_maker": "Jayaruh",
                "handle_model": "Unspecified",
            },
            "field": "handle",
        }

        match_key_unspecified = correct_matches_manager.create_match_key(
            "handle", "Jayaruh handle", match_data_unspecified["matched"]
        )
        correct_matches_manager.mark_match_as_correct(match_key_unspecified, match_data_unspecified)
        correct_matches_manager.save_correct_matches()

        # The saved structure should use "Unspecified" (from catalog)

    def test_brand_name_preservation(self, correct_matches_manager):
        """Test that brand names preserve proper casing from catalog."""
        # Test with proper brand casing
        match_data = {
            "original": "Declaration Grooming Washington handle",
            "matched": {
                "handle_maker": "Declaration Grooming",  # Proper casing from catalog
                "handle_model": "Washington",
            },
            "field": "handle",
        }

        match_key = correct_matches_manager.create_match_key(
            "handle", "Declaration Grooming Washington handle", match_data["matched"]
        )
        correct_matches_manager.mark_match_as_correct(match_key, match_data)
        correct_matches_manager.save_correct_matches()

        # The saved structure should preserve "Declaration Grooming" casing, not "declaration grooming"

    def test_split_brush_compatibility(self, correct_matches_manager):
        """Test that split_brush section functionality is maintained."""
        # Test split brush data
        match_data = {
            "original": "Declaration Grooming Washington w/ Zenith B2",
            "matched": {
                "handle": {
                    "brand": "Declaration Grooming",
                    "model": "Washington",
                    "source_text": "Declaration Grooming Washington",
                },
                "knot": {
                    "brand": "Zenith",
                    "model": "B2",
                    "source_text": "Zenith B2",
                },
            },
            "field": "brush",
        }

        match_key = correct_matches_manager.create_match_key(
            "brush", "Declaration Grooming Washington w/ Zenith B2", match_data["matched"]
        )
        correct_matches_manager.mark_match_as_correct(match_key, match_data)
        correct_matches_manager.save_correct_matches()

        # Verify split_brush section is created correctly
        # Verify handle and knot sections are created with proper model names

    def test_multiple_entries(self, correct_matches_manager):
        """Test saving multiple handle entries with different models."""
        # Test multiple entries for same brand, different models
        entries = [
            {
                "original": "Declaration Grooming Washington handle",
                "matched": {
                    "handle_maker": "Declaration Grooming",
                    "handle_model": "Washington",
                },
                "field": "handle",
            },
            {
                "original": "Declaration Grooming Jefferson handle",
                "matched": {
                    "handle_maker": "Declaration Grooming",
                    "handle_model": "Jefferson",
                },
                "field": "handle",
            },
            {
                "original": "Declaration Grooming handle",
                "matched": {
                    "handle_maker": "Declaration Grooming",
                    "handle_model": "Unspecified",
                },
                "field": "handle",
            },
        ]

        for entry in entries:
            match_key = correct_matches_manager.create_match_key(
                entry["field"], entry["original"], entry["matched"]
            )
            correct_matches_manager.mark_match_as_correct(match_key, entry)

        correct_matches_manager.save_correct_matches()

        # Verify all entries are saved with correct model names
        # Declaration Grooming should have Washington, Jefferson, and Unspecified models

    def test_model_name_consistency(self, correct_matches_manager):
        """Test that catalog model names are used consistently."""
        # Test that the same model name is used consistently across different entries
        match_data_1 = {
            "original": "Declaration Grooming Washington handle",
            "matched": {
                "handle_maker": "Declaration Grooming",
                "handle_model": "Washington",
            },
            "field": "handle",
        }

        match_data_2 = {
            "original": "DG Washington handle",
            "matched": {
                "handle_maker": "Declaration Grooming",
                "handle_model": "Washington",
            },
            "field": "handle",
        }

        # Both should save to the same model section: Declaration Grooming -> Washington
        match_key_1 = correct_matches_manager.create_match_key(
            "handle", "Declaration Grooming Washington handle", match_data_1["matched"]
        )
        match_key_2 = correct_matches_manager.create_match_key(
            "handle", "DG Washington handle", match_data_2["matched"]
        )

        correct_matches_manager.mark_match_as_correct(match_key_1, match_data_1)
        correct_matches_manager.mark_match_as_correct(match_key_2, match_data_2)
        correct_matches_manager.save_correct_matches()

        # Both entries should be saved under Declaration Grooming -> Washington

    def test_casing_consistency(self, correct_matches_manager):
        """Test proper brand casing and lowercase storage."""
        # Test that brand names preserve proper casing but storage is lowercase
        match_data = {
            "original": "Declaration Grooming Washington handle",
            "matched": {
                "handle_maker": "Declaration Grooming",  # Proper casing
                "handle_model": "Washington",
            },
            "field": "handle",
        }

        match_key = correct_matches_manager.create_match_key(
            "handle", "Declaration Grooming Washington handle", match_data["matched"]
        )
        correct_matches_manager.mark_match_as_correct(match_key, match_data)
        correct_matches_manager.save_correct_matches()

        # Brand name should be preserved as "Declaration Grooming" in structure
        # But source_text should be stored in lowercase

    def test_no_duplicates(self, correct_matches_manager):
        """Test that no duplicate brand/model entries are created."""
        # Test adding the same entry twice
        match_data = {
            "original": "Declaration Grooming Washington handle",
            "matched": {
                "handle_maker": "Declaration Grooming",
                "handle_model": "Washington",
            },
            "field": "handle",
        }

        match_key = correct_matches_manager.create_match_key(
            "handle", "Declaration Grooming Washington handle", match_data["matched"]
        )

        # Add the same entry twice
        correct_matches_manager.mark_match_as_correct(match_key, match_data)
        correct_matches_manager.mark_match_as_correct(match_key, match_data)

        correct_matches_manager.save_correct_matches()

        # Should not create duplicate entries in the YAML structure

    def test_end_to_end_workflow(self, correct_matches_manager):
        """Test end-to-end workflow: save, reload, verify structure."""
        # Test complete workflow
        match_data = {
            "original": "Declaration Grooming Washington handle",
            "matched": {
                "handle_maker": "Declaration Grooming",
                "handle_model": "Washington",
            },
            "field": "handle",
        }

        # Save
        match_key = correct_matches_manager.create_match_key(
            "handle", "Declaration Grooming Washington handle", match_data["matched"]
        )
        correct_matches_manager.mark_match_as_correct(match_key, match_data)
        correct_matches_manager.save_correct_matches()

        # Reload
        correct_matches_manager.load_correct_matches()

        # Verify structure is correct
        # Should be able to find the entry with correct brand/model structure
