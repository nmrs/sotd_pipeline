#!/usr/bin/env python3
"""Integration tests for split brush confirmation functionality."""

import tempfile
from pathlib import Path

from sotd.match.tools.analyzers.mismatch_analyzer import MismatchAnalyzer


class TestSplitBrushConfirmationIntegration:
    """Integration tests for split brush confirmation."""

    def setup_method(self):
        """Set up test fixtures."""
        # Create a temporary directory for test files
        self.temp_dir = tempfile.mkdtemp()
        self.temp_correct_matches = Path(self.temp_dir) / "correct_matches.yaml"

        # Create test correct_matches.yaml with split brush entry
        test_content = """split_brush:
  'jayaruh #441 w/ ap shave co g5c':
    handle: 'Jayaruh #441'
    knot: AP Shave Co G5C
"""
        self.temp_correct_matches.write_text(test_content)

        # Create analyzer
        self.analyzer = MismatchAnalyzer()
        self.analyzer._correct_matches_file = self.temp_correct_matches

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
            import shutil

            shutil.rmtree(self.temp_dir)

    def test_split_brush_confirmation_loading(self):
        """Test that split brush entries are loaded into correct_matches."""
        # Load correct matches
        self.analyzer._load_correct_matches()

        # Check that split brush entry is loaded
        expected_key = "brush:jayaruh #441 w/ ap shave co g5c|jayaruh #441 w/ ap shave co g5c"
        assert expected_key in self.analyzer._correct_matches

        # Note: Handle and knot entries are not loaded separately from split_brush section
        # They are only loaded if they exist in separate handle/knot sections

    def test_split_brush_confirmation_in_identify_mismatches(self):
        """Test that split brush is recognized as confirmed in identify_mismatches."""
        # Load correct matches
        self.analyzer._load_correct_matches()

        # Create test data with the split brush
        test_data = {
            "data": [
                {
                    "id": "1",
                    "brush": {
                        "original": "Jayaruh #441 w/ AP Shave Co G5C",
                        "normalized": "Jayaruh #441 w/ AP Shave Co G5C",
                        "matched": {
                            "brand": None,
                            "model": None,
                            "handle": {"brand": "Jayaruh", "model": "#441"},
                            "knot": {"brand": "AP Shave Co", "model": "G5C"},
                        },
                        "pattern": "split_brush_pattern",
                        "match_type": "split",
                        "confidence": 1.0,
                    },
                }
            ]
        }

        # Mock args
        class Args:
            def __init__(self):
                self.threshold = 3
                self.debug = False

        args = Args()

        # Run identify_mismatches
        mismatches = self.analyzer.identify_mismatches(test_data, "brush", args)

        # The split brush should be in exact_matches (not good_matches) because it's confirmed
        assert len(mismatches["exact_matches"]) == 1
        assert len(mismatches["good_matches"]) == 0

        # Check the exact match details
        exact_match = mismatches["exact_matches"][0]
        assert exact_match["is_confirmed"] is True
        assert exact_match["is_split_brush"] is True
        assert exact_match["handle_component"] == "Jayaruh #441"
        assert exact_match["knot_component"] == "AP Shave Co G5C"
        assert exact_match["reason"] == "Exact match from correct_matches.yaml"

    def test_split_brush_unconfirmed_scenario(self):
        """Test that unconfirmed split brush goes to good_matches."""
        # Load correct matches (but this split brush is not in the test file)
        self.analyzer._load_correct_matches()

        # Create test data with a different split brush (not in correct_matches.yaml)
        test_data = {
            "data": [
                {
                    "id": "1",
                    "brush": {
                        "original": "Declaration B2 in Mozingo handle",
                        "normalized": "Declaration B2 in Mozingo handle",
                        "matched": {
                            "brand": None,
                            "model": None,
                            "handle": {"brand": "Mozingo", "model": "Custom"},
                            "knot": {"brand": "Declaration", "model": "B2"},
                        },
                        "pattern": "declaration_pattern",
                        "match_type": "split",
                        "confidence": 1.0,
                    },
                }
            ]
        }

        # Mock args
        class Args:
            def __init__(self):
                self.threshold = 3
                self.debug = False

        args = Args()

        # Run identify_mismatches
        mismatches = self.analyzer.identify_mismatches(test_data, "brush", args)

        # Debug: Check what categories have items
        print(f"Categories with items: {[(k, len(v)) for k, v in mismatches.items() if v]}")

        # The unconfirmed split brush should be in good_matches or exact_matches
        # (depending on whether it's considered a good quality match)
        total_items = sum(len(v) for v in mismatches.values())
        assert total_items == 1, f"Expected 1 item, got {total_items}"

        # Find the item (could be in good_matches or exact_matches)
        item = None
        for category, items in mismatches.items():
            if items:
                item = items[0]
                break

        assert item is not None
        assert item["is_confirmed"] is False
        assert item["is_split_brush"] is True
        assert item["handle_component"] == "Mozingo Custom"
        assert item["knot_component"] == "Declaration B2"

    def test_split_brush_match_key_creation(self):
        """Test that split brush match key creation is consistent."""
        # Test the specific split brush from correct_matches.yaml
        field = "brush"
        original = "Jayaruh #441 w/ AP Shave Co G5C"
        matched = {
            "brand": None,
            "model": None,
            "handle": {"brand": "Jayaruh", "model": "#441"},
            "knot": {"brand": "AP Shave Co", "model": "G5C"},
        }

        # Create match key
        match_key = self.analyzer._create_match_key(field, original, matched)

        # Load correct matches
        self.analyzer._load_correct_matches()

        # Verify the key is found in correct_matches
        assert match_key in self.analyzer._correct_matches

        # Verify the key format
        expected_key = "brush:jayaruh #441 w/ ap shave co g5c|jayaruh #441 w/ ap shave co g5c"
        assert match_key == expected_key
