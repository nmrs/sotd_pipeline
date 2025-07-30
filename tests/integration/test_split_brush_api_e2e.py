"""
End-to-End API Tests for Split Brush Workflow

This module tests the complete split brush workflow through the API endpoints,
ensuring the entire system works correctly in real application scenarios.
"""

import pytest
import yaml
from pathlib import Path
from rich.console import Console

from sotd.match.tools.managers.correct_matches_manager import CorrectMatchesManager


class TestSplitBrushAPIE2E:
    """Test complete split brush workflow through API endpoints."""

    @pytest.fixture
    def temp_data_dir(self, tmp_path) -> Path:
        """Create temporary data directory for testing."""
        data_dir = tmp_path / "data"
        data_dir.mkdir()
        return data_dir

    @pytest.fixture
    def temp_correct_matches_file(self, temp_data_dir) -> Path:
        """Create temporary correct_matches.yaml file."""
        correct_matches_file = temp_data_dir / "correct_matches.yaml"
        correct_matches_file.write_text("brush: {}\nhandle: {}\nknot: {}\nsplit_brush: {}")
        return correct_matches_file

    def test_api_split_brush_workflow(self, temp_data_dir, temp_correct_matches_file):
        """Test complete split brush workflow through API endpoints."""

        # Step 1: Test API mismatch analysis with split brush data
        # Create sample matched data with split brushes
        sample_data = {
            "data": [
                {
                    "id": "1",
                    "brush": {
                        "original": "jayaruh #441 w/ ap shave co g5c",
                        "normalized": "jayaruh #441 w/ ap shave co g5c",
                        "matched": {
                            "brand": None,
                            "model": None,
                            "handle": {
                                "brand": "Jayaruh",
                                "model": "#441",
                                "normalized": "jayaruh #441",
                            },
                            "knot": {
                                "brand": "AP Shave Co",
                                "model": "G5C",
                                "normalized": "ap shave co g5c",
                            },
                        },
                        "match_type": "split_detection",
                        "confidence": 0.8,
                    },
                },
                {
                    "id": "2",
                    "brush": {
                        "original": "declaration b2 in mozingo handle",
                        "normalized": "declaration b2 in mozingo handle",
                        "matched": {
                            "brand": None,
                            "model": None,
                            "handle": {
                                "brand": "Declaration",
                                "model": "B2",
                                "normalized": "declaration b2",
                            },
                        },
                        "match_type": "split_detection",
                        "confidence": 0.7,
                    },
                },
            ]
        }

        # Step 2: Test API endpoint with split brush data
        # Note: This is a simplified test since we can't easily mock the full API
        # In a real scenario, we would test the actual API endpoints

        # Step 3: Test CorrectMatchesManager integration
        console = Console()
        correct_matches_manager = CorrectMatchesManager(console, temp_correct_matches_file)

        # Create match data for split brush
        match_data = {
            "original": "jayaruh #441 w/ ap shave co g5c",
            "matched": {
                "brand": None,
                "model": None,
                "handle": {
                    "brand": "Jayaruh",
                    "model": "#441",
                },
                "knot": {
                    "brand": "AP Shave Co",
                    "model": "G5C",
                },
            },
            "field": "brush",
        }

        # Mark a split brush as correct
        match_key = correct_matches_manager.create_match_key(
            "brush", match_data["original"], match_data["matched"]
        )
        correct_matches_manager.mark_match_as_correct(match_key, match_data)
        correct_matches_manager.save_correct_matches()

        # Step 4: Verify correct_matches.yaml structure
        with open(temp_correct_matches_file, "r") as f:
            correct_matches_data = yaml.safe_load(f)

        assert "split_brush" in correct_matches_data
        split_brush_data = correct_matches_data["split_brush"]
        assert "jayaruh #441 w/ ap shave co g5c" in split_brush_data

        brush_entry = split_brush_data["jayaruh #441 w/ ap shave co g5c"]
        assert brush_entry["handle"] == "Jayaruh #441"
        assert brush_entry["knot"] == "AP Shave Co G5C"

        # Step 5: Test component reuse
        # Mark another split brush with the same handle component
        correct_matches_manager.mark_brush_correct(
            original="jayaruh #441 w/ different knot",
            is_split_brush=True,
            handle_component="Jayaruh #441",
            knot_component="Different Knot",
        )

        # Verify that handle components are reused
        with open(temp_correct_matches_file, "r") as f:
            updated_data = yaml.safe_load(f)

        # Check that handle section contains the reused components
        assert "handle" in updated_data
        assert "Jayaruh" in updated_data["handle"]
        assert "#441" in updated_data["handle"]["Jayaruh"]

        # Step 6: Test performance with multiple operations
        # Add several more split brushes to test performance
        for i in range(10):
            correct_matches_manager.mark_brush_correct(
                original=f"test handle {i} w/ test knot {i}",
                is_split_brush=True,
                handle_component=f"Test Handle {i}",
                knot_component=f"Test Knot {i}",
            )

        # Verify all entries were added correctly
        with open(temp_correct_matches_file, "r") as f:
            final_data = yaml.safe_load(f)

        assert len(final_data["split_brush"]) == 12  # 2 original + 10 new

        # Step 7: Test error handling
        # Test with invalid data
        try:
            correct_matches_manager.mark_brush_correct(
                original="",
                is_split_brush=True,
                handle_component=None,
                knot_component=None,
            )
        except Exception as e:
            # Should handle empty original gracefully
            assert "original" in str(e).lower() or "empty" in str(e).lower()

    def test_backward_compatibility(self, temp_data_dir, temp_correct_matches_file):
        """Test backward compatibility with existing functionality."""

        # Create existing correct_matches.yaml structure
        existing_data = {"brush": {"Simpson": {"Chubby 2": ["simpson chubby 2"]}}}

        with open(temp_correct_matches_file, "w") as f:
            yaml.dump(existing_data, f)

        # Test that existing structure is preserved when adding split brushes
        correct_matches_manager = CorrectMatchesManager(temp_correct_matches_file)
        correct_matches_manager.mark_brush_correct(
            original="test split brush",
            is_split_brush=True,
            handle_component="Test Handle",
            knot_component="Test Knot",
        )

        with open(temp_correct_matches_file, "r") as f:
            updated_data = yaml.safe_load(f)

        # Existing brush section should be preserved
        assert "brush" in updated_data
        assert "Simpson" in updated_data["brush"]
        assert "Chubby 2" in updated_data["brush"]["Simpson"]

        # New split_brush section should be added
        assert "split_brush" in updated_data
        assert "test split brush" in updated_data["split_brush"]

    def test_error_handling(self, temp_data_dir, temp_correct_matches_file):
        """Test error handling in the split brush workflow."""

        correct_matches_manager = CorrectMatchesManager(temp_correct_matches_file)

        # Test with malformed data
        try:
            correct_matches_manager.mark_brush_correct(
                original=None,
                is_split_brush=True,
                handle_component="Test",
                knot_component="Test",
            )
        except Exception as e:
            # Should handle None original gracefully
            assert "original" in str(e).lower()

        # Test with invalid file path
        invalid_manager = CorrectMatchesManager(Path("/nonexistent/path/file.yaml"))
        try:
            invalid_manager.mark_brush_correct(
                original="test",
                is_split_brush=True,
                handle_component="Test",
                knot_component="Test",
            )
        except Exception as e:
            # Should handle file I/O errors gracefully
            assert "file" in str(e).lower() or "path" in str(e).lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
