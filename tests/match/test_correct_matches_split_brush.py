"""
Tests for split brush functionality in CorrectMatchesChecker.

This module tests the split brush lookup functionality that checks the split_brush
section first before proceeding with existing split detection logic.
"""

import pytest
from pathlib import Path
from typing import Dict, Any

from sotd.match.config import BrushMatcherConfig
from sotd.match.correct_matches import CorrectMatchesChecker


class TestCorrectMatchesCheckerSplitBrush:
    """Test split brush functionality in CorrectMatchesChecker."""

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

    @pytest.fixture
    def checker(self, config, split_brush_correct_matches) -> CorrectMatchesChecker:
        """Create CorrectMatchesChecker with test data."""
        return CorrectMatchesChecker(config, split_brush_correct_matches)

    def test_split_brush_exact_match(self, checker):
        """Test that split brush exact matches are found first."""
        result = checker.check("jayaruh #441 w/ ap shave co g5c")

        assert result is not None
        assert result.match_type == "split_brush_section"
        assert result.handle_component == "Jayaruh #441"
        assert result.knot_component == "AP Shave Co G5C"

    def test_split_brush_exact_match_case_insensitive(self, checker):
        """Test that split brush matches are case insensitive."""
        result = checker.check("jayaruh #441 w/ ap shave co g5c")

        assert result is not None
        assert result.match_type == "split_brush_section"
        assert result.handle_component == "Jayaruh #441"
        assert result.knot_component == "AP Shave Co G5C"

    def test_split_brush_not_found(self, checker):
        """Test that non-existent split brushes return None."""
        result = checker.check("Non-existent split brush")

        assert result is None

    def test_regular_brush_still_works(self, checker):
        """Test that regular brush matches still work."""
        result = checker.check("simpson chubby 2")

        assert result is not None
        assert result.match_type == "brush_section"
        assert result.brand == "Simpson"
        assert result.model == "Chubby 2"

    def test_split_brush_with_unknown_handle(self, checker):
        """Test split brush with handle that uses 'Unknown' brand."""
        result = checker.check("declaration b2 in mozingo handle")

        assert result is not None
        assert result.match_type == "split_brush_section"
        assert result.handle_component == "Mozingo handle"
        assert result.knot_component == "Declaration B2"

    def test_empty_input_returns_none(self, checker):
        """Test that empty input returns None."""
        result = checker.check("")
        assert result is None

        result = checker.check(None)
        assert result is None

    def test_no_correct_matches_returns_none(self, config):
        """Test that empty correct matches returns None."""
        checker = CorrectMatchesChecker(config, {})
        result = checker.check("Jayaruh #441 w/ AP Shave Co G5C")
        assert result is None

    def test_split_brush_priority_over_handle_knot(self, checker):
        """Test that split_brush section takes priority over handle/knot sections."""
        # Add a handle-only entry that could match the handle component
        checker.correct_matches["handle"]["Jayaruh"]["#441"].append(
            "jayaruh #441 w/ ap shave co g5c"
        )

        result = checker.check("jayaruh #441 w/ ap shave co g5c")

        # Should still match split_brush section, not handle section
        assert result is not None
        assert result.match_type == "split_brush_section"
        assert result.handle_component == "Jayaruh #441"
        assert result.knot_component == "AP Shave Co G5C"

    def test_split_brush_priority_over_brush(self, checker):
        """Test that split_brush section takes priority over brush section."""
        # Add a brush entry that could match the full string
        checker.correct_matches["brush"]["Jayaruh"] = {
            "Split Brush": ["jayaruh #441 w/ ap shave co g5c"]
        }

        result = checker.check("jayaruh #441 w/ ap shave co g5c")

        # Should still match split_brush section, not brush section
        assert result is not None
        assert result.match_type == "split_brush_section"
        assert result.handle_component == "Jayaruh #441"
        assert result.knot_component == "AP Shave Co G5C"
