"""Unit tests for brush matcher dual component fallback logic."""

import pytest
from unittest.mock import Mock, patch

from sotd.match.brush_matcher import BrushMatcher
from sotd.match.types import create_match_result


class TestBrushMatcherDualComponentFallback:
    """Test dual component fallback logic in brush matcher."""

    @pytest.fixture
    def brush_matcher(self):
        """Create brush matcher with mocked components."""
        with patch("sotd.match.brush_matcher.CatalogLoader") as mock_loader:
            # Mock catalog data
            mock_loader.return_value.load_all_catalogs.return_value = {
                "brushes": {"known_brushes": {}, "other_brushes": {}},
                "knots": {"known_knots": {}, "other_knots": {}},
                "correct_matches": {},
            }

            matcher = BrushMatcher()

            # Mock handle matcher
            matcher.handle_matcher = Mock()

            # Mock knot matcher
            matcher.knot_matcher = Mock()

            # Mock strategies
            matcher.strategies = [Mock(), Mock()]

            return matcher

    def test_dual_component_detection_both_found(self, brush_matcher):
        """Test dual component detection when both handle and knot are found."""
        # Mock handle matcher to return a match
        handle_match = {
            "handle_maker": "Rad Dinosaur",
            "handle_model": "Creation",
            "_matched_by_section": "artisan_handles",
            "_pattern_used": "rad_dinosaur_pattern",
        }
        brush_matcher.handle_matcher.match_handle_maker.return_value = handle_match

        # Mock knot matcher to return a match
        knot_match = create_match_result(
            original="G5C",
            matched={
                "brand": "AP Shave Co",
                "model": "G5C",
                "fiber": "Synthetic",
                "knot_size_mm": 26.0,
                "source_text": "G5C",
                "_matched_by": "KnownKnotMatchingStrategy",
                "_pattern": "g5c_pattern",
            },
            match_type="regex",
            pattern="g5c_pattern",
        )
        brush_matcher.knot_matcher.match.return_value = knot_match

        # Test dual component detection
        result = brush_matcher._try_dual_component_match("Rad Dinosaur G5C")

        assert result is not None
        handle_result, knot_result = result
        assert handle_result == handle_match
        assert knot_result == knot_match

    def test_dual_component_detection_only_handle_found(self, brush_matcher):
        """Test dual component detection when only handle is found."""
        # Mock handle matcher to return a match
        handle_match = {
            "handle_maker": "Rad Dinosaur",
            "handle_model": "Creation",
            "_matched_by_section": "artisan_handles",
            "_pattern_used": "rad_dinosaur_pattern",
        }
        brush_matcher.handle_matcher.match_handle_maker.return_value = handle_match

        # Mock knot matcher to return None
        brush_matcher.knot_matcher.match.return_value = None

        # Test dual component detection
        result = brush_matcher._try_dual_component_match("Rad Dinosaur")

        assert result is None

    def test_dual_component_detection_only_knot_found(self, brush_matcher):
        """Test dual component detection when only knot is found."""
        # Mock handle matcher to return None
        brush_matcher.handle_matcher.match_handle_maker.return_value = None

        # Mock knot matcher to return a match
        knot_match = create_match_result(
            original="G5C",
            matched={
                "brand": "AP Shave Co",
                "model": "G5C",
                "fiber": "Synthetic",
                "knot_size_mm": 26.0,
                "source_text": "G5C",
                "_matched_by": "KnownKnotMatchingStrategy",
                "_pattern": "g5c_pattern",
            },
            match_type="regex",
            pattern="g5c_pattern",
        )
        brush_matcher.knot_matcher.match.return_value = knot_match

        # Test dual component detection
        result = brush_matcher._try_dual_component_match("G5C")

        assert result is None

    def test_dual_component_detection_neither_found(self, brush_matcher):
        """Test dual component detection when neither handle nor knot is found."""
        # Mock both matchers to return None
        brush_matcher.handle_matcher.match_handle_maker.return_value = None
        brush_matcher.knot_matcher.match.return_value = None

        # Test dual component detection
        result = brush_matcher._try_dual_component_match("Unknown Text")

        assert result is None

    def test_user_intent_detection_handle_primary(self, brush_matcher):
        """Test user intent detection when handle appears first."""
        value = "Rad Dinosaur G5C"
        handle_text = "Rad Dinosaur"
        knot_text = "G5C"

        intent = brush_matcher.detect_user_intent(value, handle_text, knot_text)

        assert intent == "handle_primary"

    def test_user_intent_detection_knot_primary(self, brush_matcher):
        """Test user intent detection when knot appears first."""
        value = "G5C Rad Dinosaur Creation"
        handle_text = "Rad Dinosaur"
        knot_text = "G5C"

        intent = brush_matcher.detect_user_intent(value, handle_text, knot_text)

        assert intent == "knot_primary"

    def test_user_intent_detection_identical_positions(self, brush_matcher):
        """Test user intent detection when components have identical positions."""
        value = "Rad Dinosaur"
        handle_text = "Rad Dinosaur"
        knot_text = "Rad Dinosaur"  # Same text

        intent = brush_matcher.detect_user_intent(value, handle_text, knot_text)

        # Should default to handle_primary when positions are identical
        assert intent == "handle_primary"

    def test_user_intent_detection_missing_text(self, brush_matcher):
        """Test user intent detection when one component text is missing."""
        value = "Rad Dinosaur G5C"
        handle_text = "Rad Dinosaur"
        knot_text = "Missing Text"  # Not in original string

        intent = brush_matcher.detect_user_intent(value, handle_text, knot_text)

        # Should default to handle_primary when knot text not found
        assert intent == "handle_primary"

    def test_validate_dual_component_match_valid(self, brush_matcher):
        """Test validation of a valid dual component match."""
        handle_match = {
            "handle_maker": "Rad Dinosaur",
            "handle_model": "Creation",
            "_matched_by_section": "artisan_handles",
            "_pattern_used": "rad_dinosaur_pattern",
        }

        knot_match = create_match_result(
            original="G5C",
            matched={
                "brand": "AP Shave Co",
                "model": "G5C",
                "fiber": "Synthetic",
                "knot_size_mm": 26.0,
                "source_text": "G5C",
                "_matched_by": "KnownKnotMatchingStrategy",
                "_pattern": "g5c_pattern",
            },
            match_type="regex",
            pattern="g5c_pattern",
        )

        is_valid = brush_matcher._validate_dual_component_match(handle_match, knot_match)

        assert is_valid is True

    def test_validate_dual_component_match_overlapping_components(self, brush_matcher):
        """Test validation when components overlap (shared words)."""
        handle_match = {
            "handle_maker": "Rad Dinosaur",
            "handle_model": "Creation",
            "_matched_by_section": "artisan_handles",
            "_pattern_used": "rad_dinosaur_pattern",
        }

        knot_match = create_match_result(
            original="Rad Dinosaur G5C",
            matched={
                "brand": "Rad Dinosaur",  # Same as handle maker
                "model": "G5C",
                "fiber": "Synthetic",
                "knot_size_mm": 26.0,
                "source_text": "Rad Dinosaur G5C",  # Overlaps with handle
                "_matched_by": "KnownKnotMatchingStrategy",
                "_pattern": "overlapping_pattern",
            },
            match_type="regex",
            pattern="overlapping_pattern",
        )

        is_valid = brush_matcher._validate_dual_component_match(handle_match, knot_match)

        # Same brand is now valid for makers that are both handle and knot makers
        assert is_valid is True

    def test_validate_dual_component_match_none_handle(self, brush_matcher):
        """Test validation when handle match is None."""
        handle_match = None

        knot_match = create_match_result(
            original="G5C",
            matched={
                "brand": "AP Shave Co",
                "model": "G5C",
                "fiber": "Synthetic",
                "knot_size_mm": 26.0,
                "source_text": "G5C",
                "_matched_by": "KnownKnotMatchingStrategy",
                "_pattern": "g5c_pattern",
            },
            match_type="regex",
            pattern="g5c_pattern",
        )

        is_valid = brush_matcher._validate_dual_component_match(handle_match, knot_match)

        assert is_valid is False

    def test_validate_dual_component_match_none_knot(self, brush_matcher):
        """Test validation when knot match is None."""
        handle_match = {
            "handle_maker": "Rad Dinosaur",
            "handle_model": "Creation",
            "_matched_by_section": "artisan_handles",
            "_pattern_used": "rad_dinosaur_pattern",
        }

        knot_match = None

        is_valid = brush_matcher._validate_dual_component_match(handle_match, knot_match)

        assert is_valid is False

    def test_create_dual_component_result_structure(self, brush_matcher):
        """Test creation of dual component result structure."""
        handle_match = {
            "handle_maker": "Rad Dinosaur",
            "handle_model": "Creation",
            "_matched_by_section": "artisan_handles",
            "_pattern_used": "rad_dinosaur_pattern",
        }

        knot_match = create_match_result(
            original="G5C",
            matched={
                "brand": "AP Shave Co",
                "model": "G5C",
                "fiber": "Synthetic",
                "knot_size_mm": 26.0,
                "source_text": "G5C",
                "_matched_by": "KnownKnotMatchingStrategy",
                "_pattern": "g5c_pattern",
            },
            match_type="regex",
            pattern="g5c_pattern",
        )

        value = "Rad Dinosaur G5C"
        user_intent = "handle_primary"

        result = brush_matcher.create_dual_component_result(
            handle_match, knot_match, value, user_intent
        )

        # Verify result structure
        assert result.original == value
        assert result.matched is not None
        assert result.matched["brand"] is None  # Composite brush
        assert result.matched["model"] is None  # Composite brush
        assert result.matched["user_intent"] == user_intent

        # Verify handle section
        assert result.matched["handle"]["brand"] == "Rad Dinosaur"
        assert result.matched["handle"]["model"] == "Creation"
        assert result.matched["handle"]["source_text"] == value
        assert result.matched["handle"]["_matched_by"] == "HandleMatcher"
        assert result.matched["handle"]["_pattern"] == "dual_component_fallback"

        # Verify knot section
        assert result.matched["knot"]["brand"] == "AP Shave Co"
        assert result.matched["knot"]["model"] == "G5C"
        assert result.matched["knot"]["fiber"] == "Synthetic"
        assert result.matched["knot"]["knot_size_mm"] == 26.0
        assert result.matched["knot"]["source_text"] == value
        assert result.matched["knot"]["_matched_by"] == "KnotMatcher"
        assert result.matched["knot"]["_pattern"] == "dual_component_fallback"

    def test_create_dual_component_result_knot_primary(self, brush_matcher):
        """Test creation of dual component result with knot primary intent."""
        handle_match = {
            "handle_maker": "Rad Dinosaur",
            "handle_model": "Creation",
            "_matched_by_section": "artisan_handles",
            "_pattern_used": "rad_dinosaur_pattern",
        }

        knot_match = create_match_result(
            original="G5C",
            matched={
                "brand": "AP Shave Co",
                "model": "G5C",
                "fiber": "Synthetic",
                "knot_size_mm": 26.0,
                "source_text": "G5C",
                "_matched_by": "KnownKnotMatchingStrategy",
                "_pattern": "g5c_pattern",
            },
            match_type="regex",
            pattern="g5c_pattern",
        )

        value = "G5C Rad Dinosaur Creation"
        user_intent = "knot_primary"

        result = brush_matcher.create_dual_component_result(
            handle_match, knot_match, value, user_intent
        )

        assert result.matched["user_intent"] == "knot_primary"

    def test_dual_component_detection_exception_handling(self, brush_matcher):
        """Test dual component detection handles exceptions gracefully."""
        # Mock handle matcher to raise exception
        brush_matcher.handle_matcher.match_handle_maker.side_effect = Exception(
            "Handle matcher error"
        )

        # Mock knot matcher to return a match
        knot_match = create_match_result(
            original="G5C",
            matched={
                "brand": "AP Shave Co",
                "model": "G5C",
                "fiber": "Synthetic",
                "knot_size_mm": 26.0,
                "source_text": "G5C",
                "_matched_by": "KnownKnotMatchingStrategy",
                "_pattern": "g5c_pattern",
            },
            match_type="regex",
            pattern="g5c_pattern",
        )
        brush_matcher.knot_matcher.match.return_value = knot_match

        # Test that exception is handled gracefully
        result = brush_matcher._try_dual_component_match("Rad Dinosaur G5C")

        assert result is None

    def test_dual_component_detection_knot_exception_handling(self, brush_matcher):
        """Test dual component detection handles knot matcher exceptions gracefully."""
        # Mock handle matcher to return a match
        handle_match = {
            "handle_maker": "Rad Dinosaur",
            "handle_model": "Creation",
            "_matched_by_section": "artisan_handles",
            "_pattern_used": "rad_dinosaur_pattern",
        }
        brush_matcher.handle_matcher.match_handle_maker.return_value = handle_match

        # Mock knot matcher to raise exception
        brush_matcher.knot_matcher.match.side_effect = Exception("Knot matcher error")

        # Test that exception is handled gracefully
        result = brush_matcher._try_dual_component_match("Rad Dinosaur G5C")

        assert result is None
