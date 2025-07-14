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
        assert result["matched"]["brand"] == "AP Shave Co"
        assert result["matched"]["model"] == "APLuxury"
        assert result["matched"]["fiber"] == "Mixed Badger/Boar"
        assert result["matched"]["knot_size_mm"] == 24
        assert result["match_type"] == "regex"  # Uses regex patterns, not exact matches

    def test_known_knot_with_context(self):
        """Test that knots match even with surrounding text."""
        result = self.strategy.match("AP APLuxury knot")
        assert result["matched"]["brand"] == "AP Shave Co"
        assert result["matched"]["model"] == "APLuxury"

    def test_declaration_grooming_b1_match(self):
        """Test Declaration Grooming B1 pattern matching."""
        result = self.strategy.match("B1")
        assert result["matched"]["brand"] == "Declaration Grooming"
        assert result["matched"]["model"] == "B1"
        assert result["matched"]["fiber"] == "Badger"

    def test_declaration_grooming_b10_match(self):
        """Test Declaration Grooming B10 pattern matching."""
        result = self.strategy.match("B10")
        assert result["matched"]["brand"] == "Declaration Grooming"
        assert result["matched"]["model"] == "B10"
        assert result["matched"]["fiber"] == "Badger"

    def test_no_match_for_unknown_knot(self):
        """Test that unknown knots return no match."""
        result = self.strategy.match("UnknownKnot")
        assert result["matched"] is None
        assert "match_type" not in result  # match_type is only included when there's a match

    def test_case_insensitive_matching(self):
        """Test that matching is case insensitive."""
        result = self.strategy.match("apluxury")
        assert result["matched"]["brand"] == "AP Shave Co"
        assert result["matched"]["model"] == "APLuxury"

    def test_empty_input_handling(self):
        """Test that empty input is handled gracefully."""
        result = self.strategy.match("")
        assert result["matched"] is None

    def test_none_input_handling(self):
        """Test that None input is handled gracefully."""
        result = self.strategy.match("None")
        assert result["matched"] is None

    def test_template_patterns_with_batch_substitution(self):
        """Test that template patterns with batch substitution work correctly."""
        template_catalog_data = {
            "Declaration Grooming": {
                "fiber": "Badger",
                "batch_patterns": [
                    {
                        "name": "B{batch}",
                        "patterns": ["(declaration|\\bdg\\b)?.*\\bb{batch}\\b"],
                        "valid_batches": ["1", "2", "10", "15"],
                    }
                ],
            },
            "Chisel & Hound": {
                "fiber": "Badger",
                "batch_patterns": [
                    {
                        "name": "V{batch}",
                        "patterns": [
                            "(chis.*hou|chis.*fou|\\bc(?:\&|and|\\+)?h\\b|\\bch\\b).*v{batch}\\b"
                        ],
                        "valid_batches": ["10", "15", "20", "27"],
                    }
                ],
            },
        }

        strategy = KnownKnotMatchingStrategy(template_catalog_data)

        # Debug: Print generated patterns
        print(f"Generated patterns: {len(strategy.patterns)}")
        for i, pattern in enumerate(strategy.patterns[:5]):  # Show first 5
            print(f"Pattern {i}: {pattern}")

        # Test DG B-series
        result = strategy.match("B1")
        print(f"B1 match result: {result}")
        assert result["matched"]["brand"] == "Declaration Grooming"
        assert result["matched"]["model"] == "B1"
        assert result["matched"]["fiber"] == "Badger"

        result = strategy.match("B15")
        assert result["matched"]["brand"] == "Declaration Grooming"
        assert result["matched"]["model"] == "B15"
        assert result["matched"]["fiber"] == "Badger"

        # Test C&H V-series
        result = strategy.match("ch&h V10")
        print(f"ch&h V10 match result: {result}")
        assert result["matched"]["brand"] == "Chisel & Hound"
        assert result["matched"]["model"] == "V10"
        assert result["matched"]["fiber"] == "Badger"

        result = strategy.match("chisel & hound V27")
        assert result["matched"]["brand"] == "Chisel & Hound"
        assert result["matched"]["model"] == "V27"
        assert result["matched"]["fiber"] == "Badger"

        # Test that invalid batches don't match
        result = strategy.match("B99")
        assert result["matched"] is None

        result = strategy.match("V30")
        assert result["matched"] is None
