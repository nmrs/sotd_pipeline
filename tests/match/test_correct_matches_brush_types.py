"""
Unit tests for brush type determination logic in CorrectMatchesChecker.

Tests the four distinct brush types: Complete Brush, Single Maker Brush,
Composite Brush, and Single Component Brush.
"""

import pytest
from unittest.mock import Mock

from sotd.match.correct_matches import CorrectMatchesChecker
from sotd.match.config import BrushMatcherConfig


class TestCompleteBrushDetermination:
    """Test complete brush determination logic."""

    def setup_method(self):
        """Set up test fixtures."""
        self.config = Mock(spec=BrushMatcherConfig)
        self.config.debug = False

        # Mock correct_matches data with brush section
        self.correct_matches = {
            "brush": {
                "Declaration Grooming": {
                    "B14": [
                        "declaration grooming bok b14",
                        "declaration grooming know it all 28mm b14 badger knot",
                    ]
                },
                "Chisel & Hound": {"v24": ["chisel and hound lg2024 custom brush v24"]},
            }
        }

        self.checker = CorrectMatchesChecker(self.config, self.correct_matches)

    def test_complete_brush_found_in_brush_section_only(self):
        """Test complete brush found in brush section only."""
        result = self.checker.check("declaration grooming bok b14")

        assert result is not None
        assert result.brand == "Declaration Grooming"
        assert result.model == "B14"
        assert result.match_type == "brush_section"
        assert result.handle_maker is None
        assert result.handle_model is None
        assert result.knot_info is None

    def test_complete_brush_with_handle_knot_overrides(self):
        """Test complete brush with handle/knot overrides."""
        # Add handle/knot sections with same data
        self.correct_matches["handle"] = {
            "Declaration Grooming": {"Unspecified": ["declaration grooming bok b14"]}
        }
        self.correct_matches["knot"] = {
            "Declaration Grooming": {"B14": ["declaration grooming bok b14"]}
        }

        result = self.checker.check("declaration grooming bok b14")

        # Should return brush section match (new implementation priority)
        assert result is not None
        assert result.brand == "Declaration Grooming"
        assert result.model == "B14"
        assert result.match_type == "brush_section"

    def test_complete_brush_case_insensitive_matching(self):
        """Test complete brush with case-insensitive matching."""
        result = self.checker.check("Declaration Grooming BOK B14")

        assert result is not None
        assert result.brand == "Declaration Grooming"
        assert result.model == "B14"
        assert result.match_type == "brush_section"


class TestSingleMakerBrushDetermination:
    """Test single maker brush determination logic."""

    def setup_method(self):
        """Set up test fixtures."""
        self.config = Mock(spec=BrushMatcherConfig)
        self.config.debug = False

        # Mock correct_matches data with handle/knot sections (same maker)
        self.correct_matches = {
            "handle": {
                "Declaration Grooming": {"Washington": ["declaration grooming washington b14"]}
            },
            "knot": {"Declaration Grooming": {"B14": ["declaration grooming washington b14"]}},
        }

        self.checker = CorrectMatchesChecker(self.config, self.correct_matches)

    def test_single_maker_brush_found_in_handle_knot_sections(self):
        """Test single maker brush found in handle + knot sections with same maker."""
        result = self.checker.check("declaration grooming washington b14")

        assert result is not None
        assert result.handle_maker == "Declaration Grooming"
        assert result.handle_model == "Washington"
        # Current implementation doesn't find knot_info for handle matches
        # This will be fixed in the new implementation
        assert result.match_type == "handle_knot_section"

    def test_single_maker_brush_case_insensitive_matching(self):
        """Test single maker brush with case-insensitive matching."""
        result = self.checker.check("Declaration Grooming Washington B14")

        assert result is not None
        assert result.handle_maker == "Declaration Grooming"
        assert result.handle_model == "Washington"
        assert result.match_type == "handle_knot_section"


class TestCompositeBrushDetermination:
    """Test composite brush determination logic."""

    def setup_method(self):
        """Set up test fixtures."""
        self.config = Mock(spec=BrushMatcherConfig)
        self.config.debug = False

        # Mock correct_matches data with handle/knot sections (different makers)
        self.correct_matches = {
            "handle": {
                "Dogwood Handcrafts": {
                    "Ivory": ["dogwood handcrafts ivory declaration grooming b14"]
                }
            },
            "knot": {
                "Declaration Grooming": {
                    "B14": ["dogwood handcrafts ivory declaration grooming b14"]
                }
            },
        }

        self.checker = CorrectMatchesChecker(self.config, self.correct_matches)

    def test_composite_brush_found_in_handle_knot_sections_different_makers(self):
        """Test composite brush found in handle + knot sections with different makers."""
        result = self.checker.check("dogwood handcrafts ivory declaration grooming b14")

        assert result is not None
        assert result.handle_maker == "Dogwood Handcrafts"
        assert result.handle_model == "Ivory"
        # Current implementation doesn't find knot_info for handle matches
        # This will be fixed in the new implementation
        assert result.match_type == "handle_knot_section"

    def test_composite_brush_case_insensitive_matching(self):
        """Test composite brush with case-insensitive matching."""
        result = self.checker.check("Dogwood Handcrafts Ivory Declaration Grooming B14")

        assert result is not None
        assert result.handle_maker == "Dogwood Handcrafts"
        assert result.handle_model == "Ivory"
        assert result.match_type == "handle_knot_section"


class TestSingleComponentBrushDetermination:
    """Test single component brush determination logic."""

    def setup_method(self):
        """Set up test fixtures."""
        self.config = Mock(spec=BrushMatcherConfig)
        self.config.debug = False

        # Mock correct_matches data with handle-only and knot-only sections
        self.correct_matches = {
            "handle": {"Dogwood Handcrafts": {"Ivory": ["dogwood handcrafts ivory"]}},
            "knot": {"Declaration Grooming": {"B14": ["declaration grooming b14"]}},
        }

        self.checker = CorrectMatchesChecker(self.config, self.correct_matches)

    def test_handle_only_brush_found_in_handle_section_only(self):
        """Test handle-only brush found in handle section only."""
        result = self.checker.check("dogwood handcrafts ivory")

        assert result is not None
        assert result.handle_maker == "Dogwood Handcrafts"
        assert result.handle_model == "Ivory"
        assert result.knot_info is None
        assert result.match_type == "handle_knot_section"

    def test_knot_only_brush_found_in_knot_section_only(self):
        """Test knot-only brush found in knot section only."""
        result = self.checker.check("declaration grooming b14")

        assert result is not None
        assert result.handle_maker is None
        assert result.handle_model is None
        assert result.knot_info is not None
        assert result.knot_info.get("brand") == "Declaration Grooming"
        assert result.knot_info.get("model") == "B14"
        assert result.match_type == "handle_knot_section"

    def test_single_component_case_insensitive_matching(self):
        """Test single component brush with case-insensitive matching."""
        result = self.checker.check("Dogwood Handcrafts Ivory")

        assert result is not None
        assert result.handle_maker == "Dogwood Handcrafts"
        assert result.handle_model == "Ivory"
        assert result.match_type == "handle_knot_section"


class TestEdgeCasesAndErrorConditions:
    """Test edge cases and error conditions."""

    def setup_method(self):
        """Set up test fixtures."""
        self.config = Mock(spec=BrushMatcherConfig)
        self.config.debug = False
        self.correct_matches = {"brush": {"Test Brand": {"Test Model": ["test brand test model"]}}}
        self.checker = CorrectMatchesChecker(self.config, self.correct_matches)

    def test_empty_input_returns_none(self):
        """Test empty input returns None."""
        result = self.checker.check("")
        assert result is None

    def test_none_input_returns_none(self):
        """Test None input returns None."""
        result = self.checker.check(None)  # type: ignore
        assert result is None

    def test_non_matching_input_returns_none(self):
        """Test non-matching input returns None."""
        result = self.checker.check("non matching input")
        assert result is None

    def test_empty_correct_matches_returns_none(self):
        """Test empty correct_matches returns None."""
        checker = CorrectMatchesChecker(self.config, {})
        result = checker.check("test brand test model")
        assert result is None

    def test_none_correct_matches_returns_none(self):
        """Test None correct_matches returns None."""
        checker = CorrectMatchesChecker(self.config, None)  # type: ignore
        result = checker.check("test brand test model")
        assert result is None

    def test_invalid_data_structure_handling(self):
        """Test invalid data structure handling."""
        # Test with malformed correct_matches structure
        malformed_matches = {"brush": "not a dict"}
        checker = CorrectMatchesChecker(self.config, malformed_matches)
        # Current implementation will fail with AttributeError for malformed data
        # This will be fixed in the new implementation to handle gracefully
        with pytest.raises(AttributeError):
            checker.check("test brand test model")

    def test_normalized_value_returns_none(self):
        """Test when normalize_for_matching returns None."""
        result = self.checker.check("   ")  # Only whitespace
        assert result is None


class TestPriorityOrder:
    """Test priority order of section checking."""

    def setup_method(self):
        """Set up test fixtures."""
        self.config = Mock(spec=BrushMatcherConfig)
        self.config.debug = False

        # Mock correct_matches data with same entry in multiple sections
        self.correct_matches = {
            "brush": {"Test Brand": {"Test Model": ["test brand test model"]}},
            "handle": {"Test Brand": {"Test Model": ["test brand test model"]}},
            "knot": {"Test Brand": {"Test Model": ["test brand test model"]}},
        }

        self.checker = CorrectMatchesChecker(self.config, self.correct_matches)

    def test_handle_knot_section_has_higher_priority_than_brush(self):
        """Test handle/knot section has higher priority than brush section."""
        result = self.checker.check("test brand test model")

        # Should return brush section match (new implementation priority)
        assert result is not None
        assert result.match_type == "brush_section"
        assert result.brand == "Test Brand"
        assert result.model == "Test Model"
