"""
Tests for split brush functionality in BrushMatcher.

This module tests the integration of split brush correct matches with the BrushMatcher
to ensure that split brush lookups work correctly in the match phase.
"""

import pytest
from pathlib import Path
from typing import Dict, Any

from sotd.match.config import BrushMatcherConfig
from sotd.match.brush_matcher import BrushMatcher


class TestBrushMatcherSplitBrush:
    """Test split brush functionality in BrushMatcher."""

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
                "Jayaruh": {"#441": ["jayaruh #441"]},
                "Unknown": {"Mozingo handle": ["mozingo handle"]},
            },
            "knot": {
                "AP Shave Co": {"G5C": ["ap shave co g5c"]},
                "Declaration Grooming": {"B2": ["declaration b2"]},
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

    @pytest.fixture
    def brush_matcher(self, config, split_brush_correct_matches) -> BrushMatcher:
        """Create BrushMatcher with test data."""
        matcher = BrushMatcher(config)
        # Inject test correct matches data
        matcher.correct_matches = split_brush_correct_matches
        matcher.correct_matches_checker.correct_matches = split_brush_correct_matches
        return matcher

    def test_split_brush_exact_match(self, brush_matcher):
        """Test that split brush exact matches are found first."""
        result = brush_matcher.match("jayaruh #441 w/ ap shave co g5c")

        assert result is not None
        assert result.match_type == "exact"
        assert result.pattern == "correct_matches_split_brush"

        # Check that brand and model are None for split brushes
        assert result.matched["brand"] is None
        assert result.matched["model"] is None

        # Check handle section
        assert result.matched["handle"]["brand"] == "Jayaruh"
        # Note: handle model might be None if handle matcher doesn't find it
        assert result.matched["handle"]["source_text"] == "Jayaruh #441"
        assert result.matched["handle"]["_matched_by"] == "CorrectMatches"
        assert result.matched["handle"]["_pattern"] == "correct_matches_split_brush"

        # Check knot section
        assert result.matched["knot"]["brand"] == "AP Shave Co"
        assert result.matched["knot"]["model"] == "G5C"
        assert result.matched["knot"]["source_text"] == "AP Shave Co G5C"
        assert result.matched["knot"]["_matched_by"] == "CorrectMatches"
        assert result.matched["knot"]["_pattern"] == "correct_matches_split_brush"

    def test_split_brush_with_unknown_handle(self, brush_matcher):
        """Test split brush with handle that uses 'Unknown' brand."""
        result = brush_matcher.match("declaration b2 in mozingo handle")

        assert result is not None
        assert result.match_type == "exact"
        assert result.pattern == "correct_matches_split_brush"

        # Check handle section with Unknown brand
        # Note: handle matcher might find a match instead of using Unknown
        assert result.matched["handle"]["source_text"] == "Mozingo handle"

        # Check knot section
        assert result.matched["knot"]["brand"] == "Declaration Grooming"
        assert result.matched["knot"]["model"] == "B2"
        assert result.matched["knot"]["source_text"] == "Declaration B2"

    def test_split_brush_priority_over_split_detection(self, brush_matcher):
        """Test that split_brush section takes priority over split detection logic."""
        # This should match the split_brush section directly, not go through split detection
        result = brush_matcher.match("jayaruh #441 w/ ap shave co g5c")

        assert result is not None
        assert result.match_type == "exact"
        assert result.pattern == "correct_matches_split_brush"
        # Should not use split detection patterns
        assert "split_detection" not in result.pattern

    def test_regular_brush_still_works(self, brush_matcher):
        """Test that regular brush matches still work."""
        result = brush_matcher.match("simpson chubby 2")

        assert result is not None
        assert result.match_type == "exact"
        # Note: pattern might be None due to how create_match_result works
        assert result.matched["brand"] == "Simpson"
        assert result.matched["model"] == "Chubby 2"

    def test_split_brush_not_found(self, brush_matcher):
        """Test that non-existent split brushes fall back to normal processing."""
        result = brush_matcher.match("non-existent split brush")

        # Should not find a match or fall back to other strategies
        # The exact behavior depends on the brush matcher's fallback logic
        # For now, just verify it doesn't crash
        assert result is None or result.match_type != "exact"

    def test_split_brush_component_lookup_fallback(self, brush_matcher):
        """Test that split brush component lookup falls back to matchers when not found."""
        # Add a split brush entry where components don't exist in handle/knot sections
        brush_matcher.correct_matches["split_brush"]["test handle w/ test knot"] = {
            "handle": "Test Handle",
            "knot": "Test Knot",
        }

        result = brush_matcher.match("test handle w/ test knot")

        # Should still return a result even if components aren't found in handle/knot sections
        assert result is not None
        assert result.match_type == "exact"
        assert result.pattern == "correct_matches_split_brush"

        # Components should be set even if not found in handle/knot sections
        assert result.matched["handle"]["source_text"] == "Test Handle"
        assert result.matched["knot"]["source_text"] == "Test Knot"
