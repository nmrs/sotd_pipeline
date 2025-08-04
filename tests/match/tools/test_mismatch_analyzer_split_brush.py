#!/usr/bin/env python3
"""Tests for split brush detection functionality in MismatchAnalyzer."""

import tempfile
from pathlib import Path

from sotd.match.tools.analyzers.mismatch_analyzer import MismatchAnalyzer


class TestMismatchAnalyzerSplitBrush:
    """Test cases for split brush detection in MismatchAnalyzer."""

    def setup_method(self):
        """Set up test fixtures."""
        # Create a temporary directory for test files
        self.temp_dir = tempfile.mkdtemp()
        self.temp_correct_matches = Path(self.temp_dir) / "correct_matches.yaml"

        # Create a minimal test correct_matches.yaml file
        test_content = """razor:
  Test Brand:
    Test Model:
      - Test Original
"""
        self.temp_correct_matches.write_text(test_content)

        # Create analyzer first
        self.analyzer = MismatchAnalyzer()

        # Then patch the instance attribute
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

    def test_is_split_brush_basic_split_brush(self):
        """Test detection of basic split brush with both handle and knot."""
        field_data = {
            "brand": None,
            "model": None,
            "handle": {"brand": "Jayaruh", "model": "#441"},
            "knot": {"brand": "AP Shave Co", "model": "G5C"},
        }

        assert self.analyzer._is_split_brush(field_data) is True

    def test_is_split_brush_handle_only(self):
        """Test detection of handle-only split brush."""
        field_data = {
            "brand": None,
            "model": None,
            "handle": {"brand": "Jayaruh", "model": "#441"},
            # No knot section
        }

        assert self.analyzer._is_split_brush(field_data) is True

    def test_is_split_brush_knot_only(self):
        """Test detection of knot-only split brush."""
        field_data = {
            "brand": None,
            "model": None,
            # No handle section
            "knot": {"brand": "AP Shave Co", "model": "G5C"},
        }

        assert self.analyzer._is_split_brush(field_data) is True

    def test_is_split_brush_not_split_brush(self):
        """Test that regular brush is not detected as split brush."""
        field_data = {
            "brand": "Simpson",
            "model": "Chubby 2",
            # No handle or knot sections
        }

        assert self.analyzer._is_split_brush(field_data) is False

    def test_is_split_brush_brand_not_null(self):
        """Test that brush with brand is not detected as split brush."""
        field_data = {
            "brand": "Simpson",  # Not null
            "model": None,
            "handle": {"brand": "Jayaruh", "model": "#441"},
            "knot": {"brand": "AP Shave Co", "model": "G5C"},
        }

        assert self.analyzer._is_split_brush(field_data) is False

    def test_is_split_brush_model_not_null(self):
        """Test that brush with model is not detected as split brush."""
        field_data = {
            "brand": None,
            "model": "Chubby 2",  # Not null
            "handle": {"brand": "Jayaruh", "model": "#441"},
            "knot": {"brand": "AP Shave Co", "model": "G5C"},
        }

        assert self.analyzer._is_split_brush(field_data) is False

    def test_is_split_brush_no_handle_or_knot(self):
        """Test that brush without handle or knot is not detected as split brush."""
        field_data = {
            "brand": None,
            "model": None,
            # No handle or knot sections
        }

        assert self.analyzer._is_split_brush(field_data) is False

    def test_is_split_brush_invalid_input(self):
        """Test handling of invalid input."""
        assert self.analyzer._is_split_brush(None) is False  # type: ignore
        assert self.analyzer._is_split_brush("not a dict") is False  # type: ignore
        assert self.analyzer._is_split_brush([]) is False  # type: ignore

    def test_extract_split_brush_components_basic(self):
        """Test extraction of components from basic split brush."""
        field_data = {
            "brand": None,
            "model": None,
            "handle": {"brand": "Jayaruh", "model": "#441"},
            "knot": {"brand": "AP Shave Co", "model": "G5C"},
        }

        handle_component, knot_component = self.analyzer._extract_split_brush_components(field_data)

        assert handle_component == "Jayaruh #441"
        assert knot_component == "AP Shave Co G5C"

    def test_extract_split_brush_components_handle_only(self):
        """Test extraction of components from handle-only split brush."""
        field_data = {
            "brand": None,
            "model": None,
            "handle": {"brand": "Jayaruh", "model": "#441"},
            # No knot section
        }

        handle_component, knot_component = self.analyzer._extract_split_brush_components(field_data)

        assert handle_component == "Jayaruh #441"
        assert knot_component is None

    def test_extract_split_brush_components_knot_only(self):
        """Test extraction of components from knot-only split brush."""
        field_data = {
            "brand": None,
            "model": None,
            # No handle section
            "knot": {"brand": "AP Shave Co", "model": "G5C"},
        }

        handle_component, knot_component = self.analyzer._extract_split_brush_components(field_data)

        assert handle_component is None
        assert knot_component == "AP Shave Co G5C"

    def test_extract_split_brush_components_string_components(self):
        """Test extraction when components are strings instead of dicts."""
        field_data = {
            "brand": None,
            "model": None,
            "handle": "Jayaruh #441",
            "knot": "AP Shave Co G5C",
        }

        handle_component, knot_component = self.analyzer._extract_split_brush_components(field_data)

        assert handle_component == "Jayaruh #441"
        assert knot_component == "AP Shave Co G5C"

    def test_extract_split_brush_components_empty_brands_models(self):
        """Test extraction with empty brand/model fields."""
        field_data = {
            "brand": None,
            "model": None,
            "handle": {"brand": "", "model": "#441"},
            "knot": {"brand": "AP Shave Co", "model": ""},
        }

        handle_component, knot_component = self.analyzer._extract_split_brush_components(field_data)

        assert handle_component == "#441"  # Empty brand is stripped
        assert knot_component == "AP Shave Co"  # Empty model is stripped

    def test_extract_split_brush_components_not_split_brush(self):
        """Test extraction from non-split brush returns None values."""
        field_data = {
            "brand": "Simpson",
            "model": "Chubby 2",
        }

        handle_component, knot_component = self.analyzer._extract_split_brush_components(field_data)

        assert handle_component is None
        assert knot_component is None

    def test_identify_mismatches_with_split_brush(self):
        """Test that identify_mismatches includes split brush fields."""
        # Create test data with a split brush
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

        # Test mismatch identification
        mismatches = self.analyzer.identify_mismatches(test_data, "brush", args)

        # Should have the split brush in good_matches (since it's a good quality match)
        assert len(mismatches["good_matches"]) == 1

        split_brush_item = mismatches["good_matches"][0]
        assert split_brush_item["is_split_brush"] is True
        assert split_brush_item["handle_component"] == "Jayaruh #441"
        assert split_brush_item["knot_component"] == "AP Shave Co G5C"

    def test_identify_mismatches_with_regular_brush(self):
        """Test that identify_mismatches handles regular brushes correctly."""
        # Create test data with a regular brush
        test_data = {
            "data": [
                {
                    "id": "1",
                    "brush": {
                        "original": "Simpson Chubby 2",
                        "normalized": "Simpson Chubby 2",
                        "matched": {
                            "brand": "Simpson",
                            "model": "Chubby 2",
                        },
                        "pattern": "simpson_pattern",
                        "match_type": "regex",
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

        # Test mismatch identification
        mismatches = self.analyzer.identify_mismatches(test_data, "brush", args)

        # Should have the regular brush in good_matches
        assert len(mismatches["good_matches"]) == 1

        regular_brush_item = mismatches["good_matches"][0]
        assert regular_brush_item["is_split_brush"] is False
        assert regular_brush_item["handle_component"] is None
        assert regular_brush_item["knot_component"] is None

    def test_is_split_brush_confirmed(self):
        """Test that split brush confirmation logic works correctly.
        
        A split brush is only considered confirmed if ALL its components 
        (both handle and knot) are present in correct_matches.yaml.
        Partial confirmation is not allowed.
        """
        # Set up correct matches with handle and knot components
        self.analyzer._correct_matches = {"handle:alpha outlaw", "knot:silver stf++"}

        # Test data for "Alpha Outlaw Silver STF++"
        matched = {
            "brand": None,
            "model": None,
            "handle": {"brand": "Alpha", "model": "Outlaw", "source_text": "Alpha Outlaw"},
            "knot": {"brand": "Mühle", "model": "STF", "source_text": "Silver STF++"},
        }

        # Should be confirmed since both handle and knot are in correct_matches
        assert self.analyzer._is_split_brush_confirmed(matched) is True

        # Test with missing handle component
        matched_no_handle = {
            "brand": None,
            "model": None,
            "knot": {"brand": "Mühle", "model": "STF", "source_text": "Silver STF++"},
        }
        assert self.analyzer._is_split_brush_confirmed(matched_no_handle) is False

        # Test with missing knot component
        matched_no_knot = {
            "brand": None,
            "model": None,
            "handle": {"brand": "Alpha", "model": "Outlaw", "source_text": "Alpha Outlaw"},
        }
        assert self.analyzer._is_split_brush_confirmed(matched_no_knot) is False

        # Test with only handle confirmed
        self.analyzer._correct_matches = {"handle:alpha outlaw"}
        assert self.analyzer._is_split_brush_confirmed(matched) is False

        # Test with only knot confirmed
        self.analyzer._correct_matches = {"knot:silver stf++"}
        assert self.analyzer._is_split_brush_confirmed(matched) is False
