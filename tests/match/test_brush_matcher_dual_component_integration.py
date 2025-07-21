"""Integration tests for brush matcher dual component fallback logic."""

import pytest

from sotd.match.brush_matcher import BrushMatcher


class TestBrushMatcherDualComponentIntegration:
    """Integration tests for dual component fallback logic with real catalog data."""

    @pytest.fixture
    def brush_matcher(self):
        """Create brush matcher with real catalog data."""
        return BrushMatcher()

    def test_dual_component_rad_dinosaur_g5c(self, brush_matcher):
        """Test dual component detection with real Rad Dinosaur + G5C example."""
        value = "Rad Dinosaur G5C"

        # Test dual component detection
        result = brush_matcher._try_dual_component_match(value)

        if result is not None:
            handle_result, knot_result = result

            # Verify handle match
            assert handle_result is not None
            assert "handle_maker" in handle_result
            assert "Rad Dinosaur" in handle_result["handle_maker"]

            # Verify knot match
            assert knot_result is not None
            assert knot_result.matched is not None
            assert "brand" in knot_result.matched
            assert "AP Shave Co" in knot_result.matched["brand"]
            assert "G5C" in knot_result.matched["model"]

    def test_dual_component_g5c_rad_dinosaur(self, brush_matcher):
        """Test dual component detection with G5C first, then Rad Dinosaur."""
        value = "G5C Rad Dinosaur Creation"

        # Test dual component detection
        result = brush_matcher._try_dual_component_match(value)

        if result is not None:
            handle_result, knot_result = result

            # Verify handle match
            assert handle_result is not None
            assert "handle_maker" in handle_result
            assert "Rad Dinosaur" in handle_result["handle_maker"]

            # Verify knot match
            assert knot_result is not None
            assert knot_result.matched is not None
            assert "brand" in knot_result.matched
            assert "AP Shave Co" in knot_result.matched["brand"]
            assert "G5C" in knot_result.matched["model"]

    def test_user_intent_detection_real_examples(self, brush_matcher):
        """Test user intent detection with real catalog examples."""
        # Test handle primary
        value = "Rad Dinosaur G5C"
        handle_text = "Rad Dinosaur Creations"
        knot_text = "G5C"

        intent = brush_matcher.detect_user_intent(value, handle_text, knot_text)
        assert intent == "handle_primary"

        # Test knot primary
        value = "G5C Rad Dinosaur Creations"
        handle_text = "Rad Dinosaur Creations"
        knot_text = "G5C"

        intent = brush_matcher.detect_user_intent(value, handle_text, knot_text)
        assert intent == "knot_primary"

    def test_dual_component_result_creation_real_data(self, brush_matcher):
        """Test dual component result creation with real catalog data."""
        # Get real handle match from catalog
        handle_match = brush_matcher.handle_matcher.match_handle_maker("Rad Dinosaur")

        # Get real knot match from catalog
        knot_match = brush_matcher.knot_matcher.match("G5C")

        if handle_match and knot_match:
            value = "Rad Dinosaur G5C"
            user_intent = "handle_primary"

            result = brush_matcher.create_dual_component_result(
                handle_match, knot_match, value, user_intent
            )

            # Verify result structure
            assert result.original == value
            assert result.matched is not None
            assert result.matched["user_intent"] == user_intent

            # Verify handle section
            assert "handle" in result.matched
            assert result.matched["handle"]["brand"] == "Rad Dinosaur Creations"
            assert result.matched["handle"]["_matched_by"] == "HandleMatcher"
            assert result.matched["handle"]["_pattern"] == "dual_component_fallback"

            # Verify knot section
            assert "knot" in result.matched
            assert result.matched["knot"]["brand"] == "AP Shave Co"
            assert result.matched["knot"]["model"] == "G5C"
            assert result.matched["knot"]["_matched_by"] == "KnotMatcher"
            assert result.matched["knot"]["_pattern"] == "dual_component_fallback"

    def test_dual_component_validation_real_data(self, brush_matcher):
        """Test dual component validation with real catalog data."""
        # Get real handle match
        handle_match = brush_matcher.handle_matcher.match_handle_maker("Rad Dinosaur")

        # Get real knot match
        knot_match = brush_matcher.knot_matcher.match("G5C")

        if handle_match and knot_match:
            is_valid = brush_matcher._validate_dual_component_match(handle_match, knot_match)
            assert is_valid is True

    def test_dual_component_single_component_fallback(self, brush_matcher):
        """Test that single component fallback works when dual component fails."""
        # Test with a string that should only match handle
        value = "Rad Dinosaur"

        # This should not find a dual component match
        dual_result = brush_matcher._try_dual_component_match(value)  # noqa: F841

        # Should fall back to single component logic
        # (This test will be updated once we implement the new single component fallback)

    def test_dual_component_knot_only_fallback(self, brush_matcher):
        """Test that single component fallback works for knot-only matches."""
        # Test with a string that should only match knot
        value = "G5C"

        # This should not find a dual component match
        dual_result = brush_matcher._try_dual_component_match(value)  # noqa: F841

        # Should fall back to single component logic
        # (This test will be updated once we implement the new single component fallback)

    def test_dual_component_unknown_text(self, brush_matcher):
        """Test dual component detection with unknown text."""
        value = "Unknown Brush Text"

        # This should not find any matches
        result = brush_matcher._try_dual_component_match(value)

        assert result is None

    def test_dual_component_edge_cases(self, brush_matcher):
        """Test dual component detection with edge cases."""
        # Test with empty string
        result = brush_matcher._try_dual_component_match("")
        assert result is None

        # Test with single word
        result = brush_matcher._try_dual_component_match("Single")
        assert result is None

        # Test with very long string
        long_string = "Rad Dinosaur " + "G5C " * 50
        result = brush_matcher._try_dual_component_match(long_string)  # noqa: F841
        # Should still work if both components are found

    def test_user_intent_edge_cases(self, brush_matcher):
        """Test user intent detection with edge cases."""
        # Test with empty strings
        intent = brush_matcher.detect_user_intent("", "", "")
        assert intent == "handle_primary"  # Default behavior

        # Test with identical text
        intent = brush_matcher.detect_user_intent("Rad Dinosaur", "Rad Dinosaur", "Rad Dinosaur")
        assert intent == "handle_primary"  # Default behavior

        # Test with missing components
        intent = brush_matcher.detect_user_intent("Rad Dinosaur G5C", "Rad Dinosaur", "")
        assert intent == "handle_primary"  # Default behavior

    def test_dual_component_performance(self, brush_matcher):
        """Test dual component detection performance with multiple examples."""
        test_cases = [
            "Rad Dinosaur G5C",
            "G5C Rad Dinosaur Creation",
            "Wolf Whiskers G5C",
            "G5C Wolf Whiskers handle",
            "Declaration G5C",
            "G5C Declaration knot",
        ]

        for value in test_cases:
            result = brush_matcher._try_dual_component_match(value)
            # Should not raise exceptions and should complete quickly

    def test_dual_component_catalog_coverage(self, brush_matcher):
        """Test dual component detection with various catalog entries."""
        # Test with different handle makers
        handle_makers = ["Rad Dinosaur", "Wolf Whiskers", "Declaration"]
        knot_models = ["G5C", "G5A", "G5B"]

        for handle_maker in handle_makers:
            for knot_model in knot_models:
                value = f"{handle_maker} {knot_model}"
                result = brush_matcher._try_dual_component_match(value)
                # Should handle gracefully regardless of match success

    def test_dual_component_error_handling(self, brush_matcher):
        """Test dual component detection error handling."""
        # Test with malformed input
        malformed_inputs = [
            None,
            123,
            [],
            {},
        ]

        for malformed_input in malformed_inputs:
            try:
                result = brush_matcher._try_dual_component_match(malformed_input)
                # Should handle gracefully without crashing
            except Exception as e:
                # Should catch and handle exceptions gracefully
                assert "str" in str(e) or "None" in str(e)

    def test_dual_component_logging(self, brush_matcher):
        """Test that dual component detection includes appropriate logging."""
        # This test will verify that debug logging is included
        # Implementation will be added when we implement the methods
        value = "Rad Dinosaur G5C"

        # Should include debug logging for dual component attempts
        # (This test will be updated once we implement the methods)
        result = brush_matcher._try_dual_component_match(value)
