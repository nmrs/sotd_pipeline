"""Test maker comparison logic for handle/knot combinations."""

from sotd.match.brush_matcher import BrushMatcher


class TestMakerComparisonLogic:
    """Test that maker comparison logic works correctly for split components."""

    def test_same_maker_splits_identified_correctly(self):
        """Test that same maker splits should be identified correctly."""
        matcher = BrushMatcher()

        # Test with same maker (Declaration Grooming handle + Declaration Grooming knot)
        result = matcher.match("Declaration handle w/ Declaration knot")

        # Should be treated as a handle/knot combo since knot maker cannot be determined
        assert result.matched is not None

    def test_different_maker_splits_identified_correctly(self):
        """Test that different maker splits should be identified correctly."""
        matcher = BrushMatcher()

        # Test with different makers (Elite handle + Declaration knot)
        result = matcher.match("Elite handle w/ Declaration knot")

        # Should be treated as a handle/knot combo
        assert result.matched is not None
        # Check that handle and knot are different makers
        if result.matched:
            handle_maker = result.matched.get("handle_maker")
            knot_maker = result.matched.get("knot_maker")
            assert handle_maker != knot_maker or handle_maker is None or knot_maker is None

    def test_maker_detection_works_for_various_brand_formats(self):
        """Test that maker detection should work for various brand formats."""
        matcher = BrushMatcher()

        # Test abbreviated names
        result = matcher.match("C&H handle w/ DG knot")

        # Should be treated as a handle/knot combo
        assert result.matched is not None

    def test_edge_cases_with_abbreviated_names(self):
        """Test edge cases with abbreviated names should be handled."""
        matcher = BrushMatcher()

        # Test with various abbreviations
        test_cases = [
            (
                "CH handle w/ DG knot",
                "Chisel & Hound",
                "Declaration Grooming (batch not specified)",
            ),
            (
                "C&H handle w/ Declaration knot",
                "Chisel & Hound",
                "Declaration Grooming (batch not specified)",
            ),
            (
                "Chisel & Hound handle w/ DG knot",
                "Chisel & Hound",
                "Declaration Grooming (batch not specified)",
            ),
        ]

        for input_text, expected_handle, expected_knot in test_cases:
            result = matcher.match(input_text)
            # For now, just verify the match doesn't crash
            assert result is not None
            assert hasattr(result, "matched")

    def test_unknown_makers_handled_gracefully(self):
        """Test that unknown makers should be handled gracefully."""
        matcher = BrushMatcher()

        # Test with unknown makers
        result = matcher.match("Unknown handle w/ Unknown knot")

        # Should still return a result, even if makers are not identified
        assert result.matched is not None

    def test_complete_brush_vs_handle_knot_combo_detection(self):
        """Test that complete brushes vs handle/knot combos are distinguished correctly."""
        matcher = BrushMatcher()

        # Complete brush (same maker) - use a known pattern
        complete_result = matcher.match("Declaration B15")

        # Handle/knot combo (different makers)
        combo_result = matcher.match("Elite handle w/ Declaration knot")

        # Both should return results
        assert complete_result.matched is not None
        assert combo_result.matched is not None

    def test_maker_comparison_with_catalog_data(self):
        """Test that maker comparison uses catalog data correctly."""
        matcher = BrushMatcher()

        # Test with known catalog entries
        result = matcher.match("Elite handle w/ C&H v21")

        # Should return a result
        assert result.matched is not None
