from sotd.match.brush_matching_strategies.other_knot_strategy import OtherKnotMatchingStrategy
import pytest


class TestOtherKnotMatchingStrategy:
    """Test the OtherKnotMatchingStrategy with knots.yaml data."""

    def setup_method(self):
        """Set up test data from knots.yaml structure."""
        self.catalog_data = {
            "AP Shave Co": {
                "default": "Synthetic",
                "patterns": [
                    r"A\.? ?P\.? ?\s*shave\s*(co)?",
                    r"\bap\b",
                    r"\bapsc\b",
                ],
            },
            "Alpha": {
                "default": "Synthetic",
                "patterns": ["alpha"],
            },
            "Chisel & Hound": {
                "default": "Badger",
                "knot_size_mm": 26,
                "patterns": [
                    r"chis.*hou",
                    r"chis.*fou",
                    r"\bc(?:\&|and|\+)h\b",
                    r"\bch\b",
                    r"broomstick",
                    r"season.*witch",
                ],
            },
        }
        self.strategy = OtherKnotMatchingStrategy(self.catalog_data)

    def test_other_knot_brand_match(self):
        """Test that other knot makers match correctly."""
        result = self.strategy.match("AP Shave Co")
        assert result.matched is not None
        assert result.matched["brand"] == "AP Shave Co"
        assert result.matched["model"] == "Synthetic"  # Now uses fiber as model
        assert result.matched["fiber"] == "Synthetic"
        assert result.matched["knot_size_mm"] is None
        assert result.match_type == "regex"

    def test_other_knot_with_default_fiber(self):
        """Test that knots use default fiber when specified."""
        result = self.strategy.match("Alpha")
        assert result.matched is not None
        assert result.matched["brand"] == "Alpha"
        assert result.matched["model"] == "Synthetic"  # Now uses fiber as model
        assert result.matched["fiber"] == "Synthetic"

    def test_other_knot_with_knot_size(self):
        """Test that knots with knot_size_mm use it."""
        result = self.strategy.match("Chisel & Hound")
        assert result.matched is not None
        assert result.matched["brand"] == "Chisel & Hound"
        assert result.matched["model"] == "Badger"  # Now uses fiber as model
        assert result.matched["fiber"] == "Badger"
        assert result.matched["knot_size_mm"] == 26

    def test_other_knot_pattern_matching(self):
        """Test that patterns match correctly."""
        result = self.strategy.match("APSC")
        assert result.matched is not None
        assert result.matched["brand"] == "AP Shave Co"
        assert result.matched["model"] == "Synthetic"  # Now uses fiber as model
        assert result.matched["fiber"] == "Synthetic"

    def test_other_knot_case_insensitive(self):
        """Test that matching is case insensitive."""
        result = self.strategy.match("alpha")
        assert result.matched is not None
        assert result.matched["brand"] == "Alpha"
        assert result.matched["model"] == "Synthetic"  # Now uses fiber as model
        assert result.matched["fiber"] == "Synthetic"

    def test_no_match_for_unknown_brand(self):
        """Test that unknown brands return no match."""
        result = self.strategy.match("UnknownBrand")
        assert result.matched is None
        assert result.match_type is None  # match_type is only included when there's a match

    def test_empty_input_handling(self):
        """Test that empty input is handled gracefully."""
        result = self.strategy.match("")
        assert result.matched is None

    def test_none_input_handling(self):
        """Test that None input is handled gracefully."""
        result = self.strategy.match("None")
        assert result.matched is None

    def test_enhanced_regex_error_reporting(self):
        """Test that malformed regex patterns produce detailed error messages."""
        malformed_catalog = {
            "Test Brand": {
                "default": "Synthetic",
                "patterns": [r"invalid[regex"],  # Malformed regex - missing closing bracket
            }
        }

        with pytest.raises(ValueError) as exc_info:
            OtherKnotMatchingStrategy(malformed_catalog)

        error_message = str(exc_info.value)
        assert "Invalid regex pattern" in error_message
        assert "invalid[regex" in error_message
        assert "File: data/knots.yaml" in error_message
        assert "Brand: Test Brand" in error_message
        assert "Strategy: OtherKnotMatchingStrategy" in error_message
        assert "unterminated character set" in error_message  # The actual regex error
