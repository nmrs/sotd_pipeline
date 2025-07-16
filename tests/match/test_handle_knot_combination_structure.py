import pytest
from sotd.match.brush_matcher import BrushMatcher


class TestHandleKnotCombinationStructure:
    """Test that handle/knot combination results have the correct structure and required fields."""

    @pytest.mark.parametrize(
        "input_text,expected_handle,expected_knot",
        [
            ("Elite handle w/ Declaration B10", "Elite", "Declaration Grooming"),
            ("Wolf Whiskers w/ Omega knot", "Wolf Whiskers", "Omega"),
            ("DG B15 w/ C&H Zebra", "Chisel & Hound", "Declaration Grooming"),
            ("Unknown handle w/ Declaration B15", None, "Declaration Grooming"),
            ("Elite handle w/ Unknown knot", "Elite", None),
            ("Some handle w/ Some knot", None, None),
        ],
    )
    def test_handle_knot_combo_structure(self, input_text, expected_handle, expected_knot):
        matcher = BrushMatcher()
        result = matcher.match(input_text)
        matched = result.get("matched")
        assert matched is not None, f"No match for: {input_text}"
        # For combos, brand/model should be None
        assert matched["brand"] is None
        assert matched["model"] is None
        # Required top-level fields
        for field in [
            "fiber",
            "knot_size_mm",
            "handle_maker",
            "knot_maker",
            "fiber_strategy",
            "_matched_by_strategy",
            "_pattern_used",
            "handle",
            "knot",
        ]:
            assert field in matched, f"Missing field {field} in result for: {input_text}"
        # handle_maker and knot_maker should match expected (or None)
        assert matched["handle_maker"] in (expected_handle, None)
        assert matched["knot_maker"] in (expected_knot, None)
        # handle and knot subsections should be dicts or None
        assert isinstance(matched["handle"], (dict, type(None)))
        assert isinstance(matched["knot"], (dict, type(None)))
        # If handle is present, should have brand and model keys
        if matched["handle"]:
            assert "brand" in matched["handle"]
            assert "model" in matched["handle"]
            assert "source_text" in matched["handle"]
        # If knot is present, should have brand, model, fiber, knot_size_mm, source_text
        if matched["knot"]:
            for kfield in ["brand", "model", "fiber", "knot_size_mm", "source_text"]:
                assert kfield in matched["knot"], f"Missing {kfield} in knot for: {input_text}"
