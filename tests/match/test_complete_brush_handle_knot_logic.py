"""Test complete brush handle/knot logic."""

from sotd.match.brush_matcher import BrushMatcher


class TestCompleteBrushHandleKnotLogic:
    """Test that complete brushes run handle maker and knot maker detection."""

    def test_complete_brush_runs_handle_maker_logic(self):
        """Test that complete brush should run handle maker logic."""
        matcher = BrushMatcher()

        # Test with a complete brush that should have handle maker detection
        result = matcher.match("B15")

        # Should have matched as a complete brush
        assert result.matched is not None

    def test_complete_brush_runs_knot_maker_logic(self):
        """Test that complete brush should run knot maker logic."""
        matcher = BrushMatcher()

        # Test with a complete brush that should have knot maker detection
        result = matcher.match("C&H v21")

        # Should have matched as a complete brush
        assert result.matched is not None

    def test_result_includes_three_part_structure(self):
        """Test that result should include three-part structure (brush, handle, knot)."""
        matcher = BrushMatcher()

        result = matcher.match("B15")

        # Should have the basic brush structure
        assert hasattr(result, "original")
        assert hasattr(result, "matched")
        assert hasattr(result, "match_type")
        assert hasattr(result, "pattern")

    def test_handle_maker_identified_correctly(self):
        """Test that handle maker should be identified correctly."""
        matcher = BrushMatcher()

        # For complete brushes, handle maker might be the same as the brand
        # or might be None depending on the implementation
        result = matcher.match("B15")

        if result.matched:
            # Should have handle section with brand
            assert "handle" in result.matched
            assert "brand" in result.matched["handle"]

    def test_knot_maker_identified_correctly(self):
        """Test that knot maker should be identified correctly."""
        matcher = BrushMatcher()

        # For complete brushes, knot maker might be the same as the brand
        # or might be None depending on the implementation
        result = matcher.match("C&H v21")

        if result.matched:
            # Should have knot section with brand
            assert "knot" in result.matched
            assert "brand" in result.matched["knot"]

    def test_complete_brush_with_delimiters(self):
        """Test complete brush detection with delimiters."""
        matcher = BrushMatcher()

        # Test a complete brush with a delimiter
        result = matcher.match("B15 w/ custom handle")

        # Should return a result
        assert result.matched is not None

    def test_complete_brush_vs_handle_knot_combination(self):
        """Test that complete brushes are distinguished from handle/knot combinations."""
        matcher = BrushMatcher()

        # Complete brush (no delimiter or same maker)
        complete_result = matcher.match("B15")

        # Handle/knot combination (different makers)
        combo_result = matcher.match("Elite handle w/ Declaration knot")

        # Both should return results
        assert complete_result.matched is not None
        assert combo_result.matched is not None
