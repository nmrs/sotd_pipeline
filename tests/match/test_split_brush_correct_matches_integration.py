"""
Integration tests for split brush correct matches functionality.

This module tests the complete flow from CatalogLoader loading the split_brush section
through to the BrushMatcher correctly matching split brushes from correct_matches.yaml.
"""

import pytest
from pathlib import Path
from typing import Dict, Any

from sotd.match.config import BrushMatcherConfig
from sotd.match.loaders import CatalogLoader
from sotd.match.brush_matcher import BrushMatcher
from sotd.match.correct_matches import CorrectMatchesChecker


class TestSplitBrushCorrectMatchesIntegration:
    """Test split brush correct matches integration end-to-end."""

    @pytest.fixture
    def split_brush_correct_matches(self) -> Dict[str, Any]:
        """Create test correct matches data with split_brush section."""
        return {
            "split_brush": {
                "jayaruh #441 w/ ap shave co g5c": {
                    "handle": "Jayaruh #441",
                    "knot": "AP Shave Co G5C",
                },
                "declaration b2 in mozingo handle": {
                    "handle": "Mozingo handle",
                    "knot": "Declaration B2",
                },
            },
            "handle": {
                "Jayaruh": {"#441": ["Jayaruh #441"]},
                "Unknown": {"Mozingo handle": ["Mozingo handle"]},
            },
            "knot": {
                "AP Shave Co": {"G5C": ["AP Shave Co G5C"]},
                "Declaration Grooming": {"B2": ["Declaration B2"]},
            },
            "brush": {"Simpson": {"Chubby 2": ["simpson chubby 2"]}},
        }

    @pytest.fixture
    def config(self) -> BrushMatcherConfig:
        """Create test configuration."""
        return BrushMatcherConfig.create_custom(
            catalog_path=Path("data/brushes.yaml"),
            handles_path=Path("data/handles.yaml"),
            knots_path=Path("data/knots.yaml"),
            correct_matches_path=Path("data/correct_matches.yaml"),
            debug=False,
        )

    def test_catalog_loader_includes_split_brush_section(
        self, config, split_brush_correct_matches, tmp_path
    ):
        """Test that CatalogLoader includes split_brush section when loading correct matches."""
        # Create a temporary correct_matches.yaml file
        import yaml
        correct_matches_file = tmp_path / "correct_matches.yaml"
        with open(correct_matches_file, 'w') as f:
            yaml.dump(split_brush_correct_matches, f)
        
        # Update config to use temporary file
        config.correct_matches_path = correct_matches_file
        
        # Load catalogs using CatalogLoader
        catalog_loader = CatalogLoader(config)
        catalogs = catalog_loader.load_all_catalogs()
        
        # Verify split_brush section is included
        correct_matches = catalogs.get("correct_matches", {})
        assert "split_brush" in correct_matches, "split_brush section should be included"
        
        split_brush_section = correct_matches["split_brush"]
        key = "jayaruh #441 w/ ap shave co g5c"
        assert key in split_brush_section, "split brush key should be present"
        assert split_brush_section[key]["handle"] == "Jayaruh #441"
        assert split_brush_section[key]["knot"] == "AP Shave Co G5C"

    def test_correct_matches_checker_case_insensitive_matching(
        self, config, split_brush_correct_matches
    ):
        """Test that CorrectMatchesChecker performs case-insensitive matching for split brushes."""
        checker = CorrectMatchesChecker(config, split_brush_correct_matches)
        
        # Test with mixed case input
        result = checker.check("Jayaruh #441 w/ AP Shave Co G5C")
        assert result is not None, "Should find match with mixed case"
        assert result.match_type == "split_brush_section"
        assert result.handle_component == "Jayaruh #441"
        assert result.knot_component == "AP Shave Co G5C"
        
        # Test with lowercase input
        result_lower = checker.check("jayaruh #441 w/ ap shave co g5c")
        assert result_lower is not None, "Should find match with lowercase"
        assert result_lower.match_type == "split_brush_section"
        assert result_lower.handle_component == "Jayaruh #441"
        assert result_lower.knot_component == "AP Shave Co G5C"
        
        # Test with uppercase input
        result_upper = checker.check("JAYARUH #441 W/ AP SHAVE CO G5C")
        assert result_upper is not None, "Should find match with uppercase"
        assert result_upper.match_type == "split_brush_section"
        assert result_upper.handle_component == "Jayaruh #441"
        assert result_upper.knot_component == "AP Shave Co G5C"

    def test_brush_matcher_split_brush_correct_match_priority(
        self, config, split_brush_correct_matches, tmp_path
    ):
        """Test that BrushMatcher prioritizes split brush correct matches over split detection."""
        # Create a temporary correct_matches.yaml file
        import yaml
        correct_matches_file = tmp_path / "correct_matches.yaml"
        with open(correct_matches_file, 'w') as f:
            yaml.dump(split_brush_correct_matches, f)
        
        # Update config to use temporary file
        config.correct_matches_path = correct_matches_file
        
        # Create brush matcher
        brush_matcher = BrushMatcher(config=config)
        
        # Test the specific case from the screenshot
        result = brush_matcher.match("Jayaruh #441 w/ AP Shave Co G5C")
        
        assert result is not None, "Should find a match"
        assert result.match_type == "exact", "Should be exact match from correct matches"
        pattern = "correct_matches_split_brush"
        assert result.pattern == pattern, "Should indicate split brush correct match"
        
        # Verify the matched data structure
        matched = result.matched
        assert matched["brand"] is None, "Split brushes have no top-level brand"
        assert matched["model"] is None, "Split brushes have no top-level model"
        
        # Verify handle component
        handle = matched["handle"]
        assert handle["brand"] == "Jayaruh"
        assert handle["model"] == "#441"
        assert handle["source_text"] == "Jayaruh #441"
        assert handle["_matched_by"] == "CorrectMatches"
        assert handle["_pattern"] == pattern
        
        # Verify knot component
        knot = matched["knot"]
        assert knot["brand"] == "AP Shave Co"  # Full brand name from knot section
        assert knot["model"] == "G5C"  # Model from knot section
        assert knot["source_text"] == "AP Shave Co G5C"
        assert knot["_matched_by"] == "CorrectMatches"
        assert knot["_pattern"] == pattern

    def test_brush_matcher_case_insensitive_matching(self, config, split_brush_correct_matches, tmp_path):
        """Test that BrushMatcher performs case-insensitive matching for split brushes."""
        # Create a temporary correct_matches.yaml file
        import yaml
        correct_matches_file = tmp_path / "correct_matches.yaml"
        with open(correct_matches_file, 'w') as f:
            yaml.dump(split_brush_correct_matches, f)
        
        # Update config to use temporary file
        config.correct_matches_path = correct_matches_file
        
        # Create brush matcher
        brush_matcher = BrushMatcher(config=config)
        
        # Test with different case variations
        test_cases = [
            "Jayaruh #441 w/ AP Shave Co G5C",  # Mixed case
            "jayaruh #441 w/ ap shave co g5c",  # Lowercase
            "JAYARUH #441 W/ AP SHAVE CO G5C",  # Uppercase
        ]
        
        for test_input in test_cases:
            result = brush_matcher.match(test_input)
            assert result is not None, f"Should find match for: {test_input}"
            assert result.match_type == "exact", f"Should be exact match for: {test_input}"
            assert result.pattern == "correct_matches_split_brush", f"Should be split brush correct match for: {test_input}"
            
            # Verify consistent results regardless of input case
            matched = result.matched
            assert matched["handle"]["brand"] == "Jayaruh"
            assert matched["handle"]["model"] == "#441"
            assert matched["knot"]["brand"] == "AP Shave Co"  # Full brand name
            assert matched["knot"]["model"] == "G5C"  # Model from knot section

    def test_split_brush_priority_over_other_matching(self, config, split_brush_correct_matches, tmp_path):
        """Test that split brush correct matches take priority over other matching strategies."""
        # Create a temporary correct_matches.yaml file
        import yaml
        correct_matches_file = tmp_path / "correct_matches.yaml"
        with open(correct_matches_file, 'w') as f:
            yaml.dump(split_brush_correct_matches, f)
        
        # Update config to use temporary file
        config.correct_matches_path = correct_matches_file
        
        # Create brush matcher
        brush_matcher = BrushMatcher(config=config)
        
        # Test that split brush correct match takes priority
        result = brush_matcher.match("Jayaruh #441 w/ AP Shave Co G5C")
        
        # Should be exact match from correct matches, not regex from split detection
        assert result.match_type == "exact", "Should prioritize correct matches over split detection"
        assert result.pattern == "correct_matches_split_brush", "Should use correct matches pattern"
        
        # Verify it's not using split detection logic
        handle = result.matched["handle"]
        knot = result.matched["knot"]
        assert handle["_matched_by"] == "CorrectMatches", "Should use correct matches, not HandleMatcher"
        assert knot["_matched_by"] == "CorrectMatches", "Should use correct matches, not BrushSplitter"

    def test_multiple_split_brush_entries(self, config, split_brush_correct_matches, tmp_path):
        """Test that multiple split brush entries work correctly."""
        # Create a temporary correct_matches.yaml file
        import yaml
        correct_matches_file = tmp_path / "correct_matches.yaml"
        with open(correct_matches_file, 'w') as f:
            yaml.dump(split_brush_correct_matches, f)
        
        # Update config to use temporary file
        config.correct_matches_path = correct_matches_file
        
        # Create brush matcher
        brush_matcher = BrushMatcher(config=config)
        
        # Test first entry
        result1 = brush_matcher.match("Jayaruh #441 w/ AP Shave Co G5C")
        assert result1 is not None
        assert result1.match_type == "exact"
        assert result1.matched["handle"]["brand"] == "Jayaruh"
        assert result1.matched["knot"]["brand"] == "AP Shave Co"  # Full brand name
        
        # Test second entry
        result2 = brush_matcher.match("Declaration B2 in Mozingo handle")
        assert result2 is not None
        assert result2.match_type == "exact"
        assert result2.matched["handle"]["brand"] == "Unknown"  # From handle section
        assert result2.matched["knot"]["brand"] == "Declaration Grooming"  # From knot section

    def test_split_brush_not_found_falls_back_to_split_detection(self, config, split_brush_correct_matches, tmp_path):
        """Test that when split brush is not in correct matches, it falls back to split detection."""
        # Create a temporary correct_matches.yaml file
        import yaml
        correct_matches_file = tmp_path / "correct_matches.yaml"
        with open(correct_matches_file, 'w') as f:
            yaml.dump(split_brush_correct_matches, f)
        
        # Update config to use temporary file
        config.correct_matches_path = correct_matches_file
        
        # Create brush matcher
        brush_matcher = BrushMatcher(config=config)
        
        # Test with a split brush that's not in correct matches
        result = brush_matcher.match("Some Other Handle w/ Some Other Knot")
        
        # Should fall back to split detection logic
        assert result is not None, "Should find a match via split detection"
        assert result.match_type == "regex", "Should use regex match from split detection"
        assert result.pattern == "split", "Should use split pattern from split detection" 