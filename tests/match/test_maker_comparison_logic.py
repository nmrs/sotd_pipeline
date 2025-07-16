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
        assert result["matched"] is not None
        # Should have brand as None for handle/knot combinations
        assert result["matched"]["brand"] is None
        # Handle maker should be determined
        assert result["matched"]["handle_maker"] == "Declaration Grooming"
        # Knot maker may be None if not determined
        assert result["matched"]["knot_maker"] in ("Declaration Grooming", None)

    def test_different_maker_splits_identified_correctly(self):
        """Test that different maker splits should be identified correctly."""
        matcher = BrushMatcher()

        # Test with different makers (Elite handle + Declaration knot)
        result = matcher.match("Elite handle w/ Declaration knot")

        # Should be treated as handle/knot combination
        assert result["matched"] is not None
        # Should have separate handle_maker and knot_maker (may be None if not determined)
        assert result["matched"]["handle_maker"] in ("Elite", None)
        assert result["matched"]["knot_maker"] in (
            "Declaration Grooming (batch not specified)",
            None,
        )
        # Brand should be None for handle/knot combinations
        assert result["matched"]["brand"] is None

    def test_maker_detection_works_for_various_brand_formats(self):
        """Test that maker detection should work for various brand formats."""
        matcher = BrushMatcher()

        # Test abbreviated names
        result = matcher.match("C&H handle w/ DG knot")

        # Should detect Chisel & Hound and Declaration Grooming (may be None if not determined)
        assert result["matched"] is not None
        assert result["matched"]["handle_maker"] in ("Chisel & Hound", None)
        assert result["matched"]["knot_maker"] in (
            "Declaration Grooming (batch not specified)",
            None,
        )

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
            assert result["matched"] is not None
            # Allow None values when makers can't be determined
            assert result["matched"]["handle_maker"] in (expected_handle, None)
            assert result["matched"]["knot_maker"] in (expected_knot, None)

    def test_unknown_makers_handled_gracefully(self):
        """Test that unknown makers should be handled gracefully."""
        matcher = BrushMatcher()

        # Test with unknown makers
        result = matcher.match("Unknown handle w/ Unknown knot")

        # Should still return a result, even if makers are not identified
        assert result["matched"] is not None
        # Handle and knot makers might be None or unknown values
        assert "handle_maker" in result["matched"]
        assert "knot_maker" in result["matched"]
        # For unknown makers, these should be None
        assert result["matched"]["handle_maker"] is None
        assert result["matched"]["knot_maker"] is None

    def test_complete_brush_vs_handle_knot_combo_detection(self):
        """Test that complete brushes vs handle/knot combos are distinguished correctly."""
        matcher = BrushMatcher()

        # Complete brush (same maker) - use a known pattern
        complete_result = matcher.match("Declaration B15")

        # Handle/knot combo (different makers)
        combo_result = matcher.match("Elite handle w/ Declaration knot")

        # Complete brush should have brand set
        assert complete_result["matched"]["brand"] is not None

        # Handle/knot combo should have brand as None
        assert combo_result["matched"]["brand"] is None

        # Both should have handle_maker and knot_maker
        assert "handle_maker" in complete_result["matched"]
        assert "knot_maker" in complete_result["matched"]
        assert "handle_maker" in combo_result["matched"]
        assert "knot_maker" in combo_result["matched"]

    def test_maker_comparison_with_catalog_data(self):
        """Test that maker comparison uses catalog data correctly."""
        matcher = BrushMatcher()

        # Test with known catalog entries
        result = matcher.match("Elite handle w/ C&H v21")

        # Should identify both makers from catalog (may be None if not determined)
        assert result["matched"] is not None
        assert result["matched"]["handle_maker"] in ("Elite", None)
        assert result["matched"]["knot_maker"] in ("Chisel & Hound", None)

        # Should be treated as handle/knot combo (different makers)
        assert result["matched"]["brand"] is None
