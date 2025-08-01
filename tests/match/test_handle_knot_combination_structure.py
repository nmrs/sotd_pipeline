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
            (
                "Unknown handle w/ Declaration B15",
                "Unknown",
                "Declaration Grooming",
            ),  # Split brush with Unknown handle and Declaration B15 knot
            ("Elite handle w/ Unknown knot", "Elite", None),
            ("Some handle w/ Some knot", "Some", None),  # "Some" is extracted as handle brand
        ],
    )
    def test_handle_knot_combo_structure(self, input_text, expected_handle, expected_knot):
        matcher = BrushMatcher()
        result = matcher.match(input_text)
        matched = result.matched
        if matched:
            # Check handle maker in nested structure
            if expected_handle:
                if matched.get("handle"):
                    assert matched["handle"].get("brand") == expected_handle
                else:
                    # Fallback for old structure
                    assert matched.get("handle_maker") == expected_handle
            else:
                if matched.get("handle"):
                    assert matched["handle"].get("brand") is None
                else:
                    # Fallback for old structure
                    assert matched.get("handle_maker") is None

            # Check knot brand in nested structure
            if expected_knot:
                if matched.get("knot"):
                    assert matched["knot"].get("brand") == expected_knot
                else:
                    # Fallback for old structure
                    assert matched.get("brand") == expected_knot
            else:
                if matched.get("knot"):
                    assert matched["knot"].get("brand") is None
                else:
                    # Fallback for old structure
                    assert matched.get("brand") is None
