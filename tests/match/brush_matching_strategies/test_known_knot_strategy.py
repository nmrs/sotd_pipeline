from sotd.match.brush_matching_strategies.known_knot_strategy import KnownKnotMatchingStrategy


class TestKnownKnotMatchingStrategy:
    """Test the KnownKnotMatchingStrategy with knots.yaml data."""

    def setup_method(self):
        """Set up test data from knots.yaml structure."""
        self.catalog_data = {
            "AP Shave Co": {
                "APLuxury": {
                    "fiber": "Mixed Badger/Boar",
                    "knot_size_mm": 24,
                    "patterns": ["apluxury", r"\bap\b.*luxury"],
                },
                "Cashmere": {
                    "fiber": "Synthetic",
                    "patterns": [r"\ba[\s.]*p\b.*cashmere"],
                },
            },
            "Declaration Grooming": {
                "B1": {
                    "fiber": "Badger",
                    "patterns": [r"B1(\.\s|\.$|\s|$)"],
                },
                "B10": {
                    "fiber": "Badger",
                    "patterns": ["b10"],
                },
            },
        }
        self.strategy = KnownKnotMatchingStrategy(self.catalog_data)

    def test_known_knot_exact_match(self):
        """Test that known knots match correctly."""
        result = self.strategy.match("APLuxury")
        assert result.matched is not None
        assert result.matched["brand"] == "AP Shave Co"
        assert result.matched["model"] == "APLuxury"
        assert result.matched["fiber"] == "Mixed Badger/Boar"
        assert result.matched["knot_size_mm"] == 24
        assert result.match_type == "regex"  # Uses regex patterns, not exact matches

    def test_known_knot_with_context(self):
        """Test that knots match even with surrounding text."""
        result = self.strategy.match("AP APLuxury knot")
        assert result.matched is not None
        assert result.matched["brand"] == "AP Shave Co"
        assert result.matched["model"] == "APLuxury"

    def test_declaration_grooming_b1_match(self):
        """Test Declaration Grooming B1 pattern matching."""
        result = self.strategy.match("B1")
        assert result.matched is not None
        assert result.matched["brand"] == "Declaration Grooming"
        assert result.matched["model"] == "B1"
        assert result.matched["fiber"] == "Badger"

    def test_declaration_grooming_b10_match(self):
        """Test Declaration Grooming B10 pattern matching."""
        result = self.strategy.match("B10")
        assert result.matched is not None
        assert result.matched["brand"] == "Declaration Grooming"
        assert result.matched["model"] == "B10"
        assert result.matched["fiber"] == "Badger"

    def test_no_match_for_unknown_knot(self):
        """Test that unknown knots return no match."""
        result = self.strategy.match("UnknownKnot")
        assert result.matched is None
        assert result.match_type is None  # match_type is only included when there's a match

    def test_case_insensitive_matching(self):
        """Test that matching is case insensitive."""
        result = self.strategy.match("apluxury")
        assert result.matched is not None
        assert result.matched["brand"] == "AP Shave Co"
        assert result.matched["model"] == "APLuxury"

    def test_empty_input_handling(self):
        """Test that empty input is handled gracefully."""
        result = self.strategy.match("")
        assert result.matched is None

    def test_none_input_handling(self):
        """Test that None input is handled gracefully."""
        result = self.strategy.match("None")
        assert result.matched is None
