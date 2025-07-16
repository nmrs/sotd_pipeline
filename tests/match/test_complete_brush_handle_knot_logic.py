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
        assert result["matched"] is not None
        assert result["matched"]["brand"] == "Declaration Grooming"
        assert result["matched"]["model"] == "B15"

        # Should have handle maker information (even if None for complete brushes)
        assert "handle_maker" in result["matched"]

    def test_complete_brush_runs_knot_maker_logic(self):
        """Test that complete brush should run knot maker logic."""
        matcher = BrushMatcher()

        # Test with a complete brush that should have knot maker detection
        result = matcher.match("C&H v21")

        # Should have matched as a complete brush
        assert result["matched"] is not None
        assert result["matched"]["brand"] == "Chisel & Hound"
        assert result["matched"]["model"] == "v21"

        # Should have knot maker information (even if None for complete brushes)
        assert "knot_maker" in result["matched"]

    def test_result_includes_three_part_structure(self):
        """Test that result should include three-part structure (brush, handle, knot)."""
        matcher = BrushMatcher()

        result = matcher.match("B15")

        # Should have the basic brush structure
        assert "original" in result
        assert "matched" in result
        assert "match_type" in result

        # The matched structure should include brush, handle, and knot fields
        if result["matched"]:
            matched = result["matched"]
            # Brush fields
            assert "brand" in matched
            assert "model" in matched
            assert "fiber" in matched

            # Handle fields
            assert "handle_maker" in matched

            # Knot fields
            assert "knot_maker" in matched
            assert "knot_size_mm" in matched

    def test_handle_maker_identified_correctly(self):
        """Test that handle maker should be identified correctly."""
        matcher = BrushMatcher()

        # For complete brushes, handle maker might be the same as the brand
        # or might be None depending on the implementation
        result = matcher.match("B15")

        if result["matched"]:
            handle_maker = result["matched"]["handle_maker"]
            # Handle maker should either be the brand name or None
            assert handle_maker is None or handle_maker == "Declaration Grooming"

    def test_knot_maker_identified_correctly(self):
        """Test that knot maker should be identified correctly."""
        matcher = BrushMatcher()

        # For complete brushes, knot maker might be the same as the brand
        # or might be None depending on the implementation
        result = matcher.match("C&H v21")

        if result["matched"]:
            knot_maker = result["matched"]["knot_maker"]
            # Knot maker should either be the brand name or None
            assert knot_maker is None or knot_maker == "Chisel & Hound"

    def test_complete_brush_with_delimiters(self):
        """Test complete brush detection with delimiters."""
        matcher = BrushMatcher()

        # Test a complete brush with a delimiter
        result = matcher.match("B15 w/ custom handle")

        # Should be treated as a handle/knot combo, not a complete brush
        assert result["matched"] is not None
        assert result["matched"]["brand"] is None  # Expect None for handle/knot combo
        # Knot should be Declaration Grooming B15
        assert result["matched"]["knot_maker"] == "Declaration Grooming"
        assert result["matched"].get("knot", {}).get("brand") == "Declaration Grooming"
        assert result["matched"].get("knot", {}).get("model") == "B15"

    def test_complete_brush_vs_handle_knot_combination(self):
        """Test that complete brushes are distinguished from handle/knot combinations."""
        matcher = BrushMatcher()

        # Complete brush (no delimiter or same maker)
        complete_result = matcher.match("B15")

        # Handle/knot combination (different makers)
        combo_result = matcher.match("Elite handle w/ Declaration knot")

        # Both should match but with different structures
        assert complete_result["matched"] is not None
        assert combo_result["matched"] is not None

        # Complete brush should have brand/model
        assert complete_result["matched"]["brand"] == "Declaration Grooming"
        assert complete_result["matched"]["model"] == "B15"

        # Handle/knot combo should have handle_maker and knot_maker (may be None if not determined)
        assert combo_result["matched"]["handle_maker"] == "Elite"
        assert combo_result["matched"]["knot_maker"] in (
            "Declaration Grooming (batch not specified)",
            None,
        )
        # For handle/knot combinations, brand is typically None since it's a combination
        assert combo_result["matched"]["brand"] is None
