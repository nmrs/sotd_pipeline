"""
Tests for CorrectMatchesStrategy.

This tests the direct strategy for matching against correct_matches.yaml.
"""

from sotd.match.brush.strategies.correct_matches_strategy import (
    CorrectMatchesStrategy,
)
from sotd.match.correct_matches import CorrectMatchesChecker


class TestCorrectMatchesStrategy:
    """Test the CorrectMatchesStrategy class."""

    def setup_method(self):
        """Set up test fixtures."""
        # Create mock correct_matches data structure
        self.correct_matches_data = {
            "brush": {
                "AP Shave Co": {
                    "G5C": ["a.p. shave co amber smoke g5c fan"],
                    "Mixed Badger/Boar": ["a p shaveco 24mm luxury badger mix"],
                },
                "Simpson": {
                    "Chubby 2": ["simpson - 'chubby 2' silvertip"],
                    "Wee Scot": ["simpson - 'wee scot' best"],
                },
                "Declaration Grooming": {
                    "B13": ["declaration grooming - roil jefferson - 28mm b13"],
                },
            }
        }

        self.strategy = CorrectMatchesStrategy(self.correct_matches_data)

    def test_init(self):
        """Test strategy initialization."""
        assert hasattr(self.strategy, "checker")
        assert isinstance(self.strategy.checker, CorrectMatchesChecker)

    def test_match_exact_pattern(self):
        """Test matching an exact pattern from correct_matches."""
        test_input = "a.p. shave co amber smoke g5c fan"
        result = self.strategy.match(test_input)

        assert result is not None
        assert result.matched is not None
        assert result.matched["brand"] == "AP Shave Co"
        assert result.matched["model"] == "G5C"
        assert result.match_type == "exact"
        assert result.pattern == "exact_match"
        assert result.matched["strategy"] == "correct_matches"

    def test_match_case_insensitive(self):
        """Test that matching is case insensitive."""
        test_input = "A.P. SHAVE CO AMBER SMOKE G5C FAN"
        result = self.strategy.match(test_input)

        assert result is not None
        assert result.matched is not None
        assert result.matched["brand"] == "AP Shave Co"
        assert result.matched["model"] == "G5C"

    def test_match_with_whitespace(self):
        """Test that matching handles whitespace correctly."""
        test_input = "  a.p. shave co amber smoke g5c fan  "
        result = self.strategy.match(test_input)

        assert result is not None
        assert result.matched is not None
        assert result.matched["brand"] == "AP Shave Co"
        assert result.matched["model"] == "G5C"

    def test_match_different_pattern(self):
        """Test matching a different pattern from the same brand/model."""
        test_input = "a p shaveco 24mm luxury badger mix"
        result = self.strategy.match(test_input)

        assert result is not None
        assert result.matched is not None
        assert result.matched["brand"] == "AP Shave Co"
        assert result.matched["model"] == "Mixed Badger/Boar"

    def test_match_simpson_pattern(self):
        """Test matching a Simpson pattern."""
        test_input = "simpson - 'chubby 2' silvertip"
        result = self.strategy.match(test_input)

        assert result is not None
        assert result.matched is not None
        assert result.matched["brand"] == "Simpson"
        assert result.matched["model"] == "Chubby 2"

    def test_no_match(self):
        """Test that no match returns None."""
        test_input = "nonexistent brush pattern"
        result = self.strategy.match(test_input)

        assert result is None

    def test_empty_input(self):
        """Test that empty input returns None."""
        result = self.strategy.match("")
        assert result is None

        result = self.strategy.match(None)  # type: ignore
        assert result is None

    def test_non_string_input(self):
        """Test that non-string input returns None."""
        result = self.strategy.match(123)  # type: ignore
        assert result is None

        result = self.strategy.match(["not", "a", "string"])  # type: ignore
        assert result is None

    def test_malformed_data_structure(self):
        """Test handling of malformed data structure."""
        # Test with non-dict models
        malformed_data = {"brush": {"Bad Brand": "not a dict"}}
        strategy = CorrectMatchesStrategy(malformed_data)

        result = strategy.match("any input")
        assert result is None

        # Test with non-list patterns
        malformed_data = {"brush": {"Bad Brand": {"Bad Model": "not a list"}}}
        strategy = CorrectMatchesStrategy(malformed_data)

        result = strategy.match("any input")
        assert result is None

    def test_empty_brush_section(self):
        """Test handling of empty brush section."""
        empty_data = {"brush": {}}
        strategy = CorrectMatchesStrategy(empty_data)

        result = strategy.match("any input")
        assert result is None

    def test_missing_brush_section(self):
        """Test handling of missing brush section."""
        no_brush_data = {"other_section": {}}
        strategy = CorrectMatchesStrategy(no_brush_data)

        result = strategy.match("any input")
        assert result is None

    def test_match_result_structure(self):
        """Test that match result has correct structure."""
        test_input = "a.p. shave co amber smoke g5c fan"
        result = self.strategy.match(test_input)

        assert result is not None
        assert result.matched is not None
        assert hasattr(result, "original")
        assert hasattr(result, "matched")
        assert hasattr(result, "match_type")
        assert hasattr(result, "pattern")

        # Check matched data structure
        matched = result.matched
        assert "brand" in matched
        assert "model" in matched
        assert "source_text" in matched
        assert "strategy" in matched
        assert "_matched_by" in matched
        assert "_pattern" in matched

        # Check that optional fields are not present (correct_matches without catalogs)
        # Note: With catalogs, these fields would be populated from the catalog lookup
        assert "fiber" not in matched
        assert "knot_size_mm" not in matched
        assert "handle_maker" not in matched

    def test_catalog_integration_with_bfm_brush(self):
        """Test that BFM brush gets complete catalog data including knot_size_mm."""
        # Create test data for BFM brush
        bfm_correct_matches = {
            "brush": {
                "EldrormR Industries/Muninn Woodworks": {
                    "BFM": ["muninn woodworks bfm", "eldrormr industries/muninn woodworks bfm"]
                }
            }
        }

        # Mock catalog data that should be looked up
        bfm_catalogs = {
            "brushes": {
                "known_brushes": {
                    "EldrormR Industries/Muninn Woodworks": {
                        "BFM": {
                            "knot": {
                                "brand": "Moti",
                                "fiber": "Synthetic",
                                "knot_size_mm": 50,
                                "model": "Motherlode",
                            },
                            "handle": {"brand": "Muninn Woodworks"},
                        }
                    }
                }
            }
        }

        # Create strategy with catalogs
        bfm_strategy = CorrectMatchesStrategy(bfm_correct_matches, bfm_catalogs)

        # Test BFM brush match
        result = bfm_strategy.match("muninn woodworks bfm")

        assert result is not None
        assert result.match_type == "exact"
        assert result.matched is not None

        # Should have complete catalog data
        assert result.matched["brand"] == "EldrormR Industries/Muninn Woodworks"
        assert result.matched["model"] == "BFM"

        # Should have nested sections from catalog
        assert "knot" in result.matched
        assert result.matched["knot"]["brand"] == "Moti"
        assert result.matched["knot"]["fiber"] == "Synthetic"
        assert result.matched["knot"]["knot_size_mm"] == 50
        assert result.matched["knot"]["model"] == "Motherlode"

        assert "handle" in result.matched
        assert result.matched["handle"]["brand"] == "Muninn Woodworks"
