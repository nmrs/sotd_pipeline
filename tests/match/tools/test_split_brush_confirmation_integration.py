#!/usr/bin/env python3
"""Integration tests for split brush confirmation functionality."""

import tempfile
import yaml
from pathlib import Path
from rich.console import Console
import shutil

from sotd.match.tools.managers.correct_matches_manager import CorrectMatchesManager


class TestSplitBrushConfirmationIntegration:
    """Test split brush confirmation integration end-to-end."""

    def setup_method(self):
        """Set up test fixtures."""
        # Create a temporary directory for test files
        self.temp_dir = tempfile.mkdtemp()
        self.temp_correct_matches = Path(self.temp_dir) / "correct_matches.yaml"

    def teardown_method(self):
        """Clean up test fixtures."""
        # Clean up temporary files
        if self.temp_correct_matches.exists():
            self.temp_correct_matches.unlink()

        # Clean up backup file if it exists
        backup_file = self.temp_correct_matches.with_suffix(".yaml.backup")
        if backup_file.exists():
            backup_file.unlink()

        if self.temp_dir and Path(self.temp_dir).exists():
            # Use shutil.rmtree to remove directory and all contents
            shutil.rmtree(self.temp_dir)

    def test_split_brush_confirmation_in_identify_mismatches(self):
        """Test that split brush entries in correct_matches.yaml are properly recognized as confirmed."""
        # Create test data with split brush entry
        test_data = {
            "split_brush": {
                "jayaruh #441 w/ ap shave co g5c": {
                    "handle": "jayaruh #441",
                    "knot": "ap shave co g5c",
                }
            }
        }
        
        # Write test data to temporary file
        with open(self.temp_correct_matches, "w") as f:
            yaml.dump(test_data, f)

        # Create mismatch analyzer
        from sotd.match.tools.analyzers.mismatch_analyzer import MismatchAnalyzer

        analyzer = MismatchAnalyzer()
        analyzer._correct_matches_file = self.temp_correct_matches
        analyzer._load_correct_matches()

        # Test that the split brush is recognized as confirmed
        # Mock args
        class Args:
            def __init__(self):
                self.threshold = 3
                self.debug = False

        args = Args()
        
        result = analyzer.identify_mismatches(
            {
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
                                },
                                "knot": {
                                    "brand": "AP Shave Co",
                                    "model": "G5C",
                                },
                            },
                        },
                    }
                ]
            },
            "brush",
            args,
        )

        # Should be in exact_matches (confirmed)
        assert len(result["exact_matches"]) == 1
        exact_match = result["exact_matches"][0]
        assert exact_match["is_confirmed"] is True
        assert exact_match["is_split_brush"] is True

    def test_split_brush_confirmation_loading(self):
        """Test that split brush entries are properly loaded from correct_matches.yaml."""
        # Create test data with split brush entry
        test_data = {
            "split_brush": {
                "jayaruh #441 w/ ap shave co g5c": {
                    "handle": "jayaruh #441",
                    "knot": "ap shave co g5c",
                }
            }
        }
        
        # Write test data to temporary file
        with open(self.temp_correct_matches, "w") as f:
            yaml.dump(test_data, f)

        # Create mismatch analyzer
        from sotd.match.tools.analyzers.mismatch_analyzer import MismatchAnalyzer

        analyzer = MismatchAnalyzer()
        analyzer._correct_matches_file = self.temp_correct_matches
        analyzer._load_correct_matches()

        # Verify that the split brush entry is loaded
        assert len(analyzer._correct_matches) > 0
        # Should have at least one split brush entry
        split_brush_keys = [key for key in analyzer._correct_matches if "jayaruh" in key.lower()]
        assert len(split_brush_keys) > 0

    def test_split_brush_unconfirmed_scenario(self):
        """Test that unconfirmed split brushes are properly categorized."""
        # Create test data with split brush entry
        test_data = {
            "split_brush": {
                "jayaruh #441 w/ ap shave co g5c": {
                    "handle": "jayaruh #441",
                    "knot": "ap shave co g5c",
                }
            }
        }
        
        # Write test data to temporary file
        with open(self.temp_correct_matches, "w") as f:
            yaml.dump(test_data, f)

        # Create mismatch analyzer
        from sotd.match.tools.analyzers.mismatch_analyzer import MismatchAnalyzer

        analyzer = MismatchAnalyzer()
        analyzer._correct_matches_file = self.temp_correct_matches
        analyzer._load_correct_matches()

        # Test an unconfirmed split brush
        # Mock args
        class Args:
            def __init__(self):
                self.threshold = 3
                self.debug = False

        args = Args()
        
        result = analyzer.identify_mismatches(
            {
                "data": [
                    {
                        "id": "1",
                        "brush": {
                            "original": "unknown handle w/ unknown knot",
                            "normalized": "unknown handle w/ unknown knot",
                            "matched": {
                                "brand": None,
                                "model": None,
                                "handle": {
                                    "brand": "Unknown",
                                    "model": "Handle",
                                },
                                "knot": {
                                    "brand": "Unknown",
                                    "model": "Knot",
                                },
                            },
                        },
                    }
                ]
            },
            "brush",
            args,
        )

        # Should be in good_matches (unconfirmed)
        assert len(result["good_matches"]) == 1
        good_match = result["good_matches"][0]
        assert good_match["is_confirmed"] is False
        assert good_match["is_split_brush"] is True

    def test_split_brush_case_sensitivity_fix(self):
        """Test that split brush components are saved in lowercase for consistency."""
        console = Console()
        correct_matches_file = self.temp_correct_matches
        manager = CorrectMatchesManager(console, correct_matches_file)

        # Create match data with mixed case
        match_data = {
            "original": "Test Handle w/ Test Knot",
            "matched": {
                "brand": None,
                "model": None,
                "handle": {
                    "brand": "Test",
                    "model": "Handle",
                },
                "knot": {
                    "brand": "Test",
                    "model": "Knot",
                },
            },
            "field": "brush",
        }

        # Mark as correct and save
        match_key = manager.create_match_key("brush", match_data["original"], match_data["matched"])
        manager.mark_match_as_correct(match_key, match_data)
        manager.save_correct_matches()

        # Load the saved file and verify case sensitivity
        with open(correct_matches_file, "r") as f:
            saved_data = yaml.safe_load(f)

        assert "split_brush" in saved_data
        split_brush_data = saved_data["split_brush"]
        
        # Key should be lowercase
        expected_key = "test handle w/ test knot"
        assert expected_key in split_brush_data
        
        # Components should be lowercase
        brush_entry = split_brush_data[expected_key]
        assert brush_entry["handle"] == "test handle"
        assert brush_entry["knot"] == "test knot"

    def test_split_brush_overwriting_fix(self):
        """Test that marking a new split brush as correct doesn't overwrite existing entries."""
        console = Console()
        correct_matches_file = self.temp_correct_matches
        manager = CorrectMatchesManager(console, correct_matches_file)

        # First, create an existing split brush entry
        existing_data = {
            "split_brush": {
                "existing handle w/ existing knot": {
                    "handle": "existing handle",
                    "knot": "existing knot",
                }
            }
        }
        
        with open(correct_matches_file, "w") as f:
            yaml.dump(existing_data, f)

        # Load existing data
        manager.load_correct_matches()

        # Now add a new split brush entry
        new_match_data = {
            "original": "new handle w/ new knot",
            "matched": {
                "brand": None,
                "model": None,
                "handle": {
                    "brand": "New",
                    "model": "Handle",
                },
                "knot": {
                    "brand": "New",
                    "model": "Knot",
                },
            },
            "field": "brush",
        }

        # Mark as correct and save
        match_key = manager.create_match_key(
            "brush", new_match_data["original"], new_match_data["matched"]
        )
        manager.mark_match_as_correct(match_key, new_match_data)
        manager.save_correct_matches()

        # Load the saved file and verify both entries exist
        with open(correct_matches_file, "r") as f:
            saved_data = yaml.safe_load(f)

        assert "split_brush" in saved_data
        split_brush_data = saved_data["split_brush"]
        
        # Both entries should exist
        assert "existing handle w/ existing knot" in split_brush_data
        assert "new handle w/ new knot" in split_brush_data
        
        # Verify the content
        existing_entry = split_brush_data["existing handle w/ existing knot"]
        assert existing_entry["handle"] == "existing handle"
        assert existing_entry["knot"] == "existing knot"
        
        new_entry = split_brush_data["new handle w/ new knot"]
        assert new_entry["handle"] == "new handle"
        assert new_entry["knot"] == "new knot"

    def test_split_brush_loading_preserves_existing_entries(self):
        """Test that loading split brush entries preserves existing data structure."""
        console = Console()
        correct_matches_file = self.temp_correct_matches
        manager = CorrectMatchesManager(console, correct_matches_file)

        # Create existing data with split brush entries
        existing_data = {
            "split_brush": {
                "jayaruh #441 w/ ap shave co g5c": {
                    "handle": "jayaruh #441",
                    "knot": "ap shave co g5c",
                },
                "declaration b2 in mozingo handle": {
                    "handle": "declaration b2",
                    "knot": "mozingo handle",
                }
            }
        }
        
        with open(correct_matches_file, "w") as f:
            yaml.dump(existing_data, f)

        # Load the data
        manager.load_correct_matches()

        # Verify that both entries are loaded
        assert len(manager._correct_matches) >= 2
        
        # Check that the entries are properly loaded into the internal data structure
        jayaruh_keys = [
            key for key in manager._correct_matches if "jayaruh" in key.lower()
        ]
        declaration_keys = [
            key for key in manager._correct_matches if "declaration" in key.lower()
        ]
        
        assert len(jayaruh_keys) > 0
        assert len(declaration_keys) > 0

        # Save again to verify no data loss
        manager.save_correct_matches()

        # Load the saved file and verify both entries still exist
        with open(correct_matches_file, "r") as f:
            saved_data = yaml.safe_load(f)

        assert "split_brush" in saved_data
        split_brush_data = saved_data["split_brush"]
        
        assert "jayaruh #441 w/ ap shave co g5c" in split_brush_data
        assert "declaration b2 in mozingo handle" in split_brush_data
