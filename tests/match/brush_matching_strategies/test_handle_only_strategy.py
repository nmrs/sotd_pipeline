from unittest.mock import Mock

from sotd.match.brush_matching_strategies.handle_only_strategy import HandleOnlyStrategy
from sotd.match.types import MatchResult


class TestHandleOnlyStrategy:
    """Test the HandleOnlyStrategy class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_handle_matcher = Mock()
        self.strategy = HandleOnlyStrategy(self.mock_handle_matcher)

    def test_init(self):
        """Test strategy initialization."""
        assert self.strategy.handle_matcher == self.mock_handle_matcher

    def test_match_with_empty_input(self):
        """Test matching with empty or whitespace input."""
        assert self.strategy.match("") is None
        assert self.strategy.match("   ") is None

    def test_match_with_handle_match(self):
        """Test successful handle matching."""
        # Mock handle matcher response
        mock_handle_match = {
            "handle_maker": "Chisel and Hound",
            "handle_model": "Padauk Wood",
            "_pattern_used": "chisel.*hound.*padauk",
        }
        self.mock_handle_matcher.match_handle_maker.return_value = mock_handle_match

        result = self.strategy.match("Chisel and Hound Padauk Wood handle")

        assert result is not None
        assert isinstance(result, MatchResult)
        assert result.original == "Chisel and Hound Padauk Wood handle"
        assert result.strategy == "handle_only"
        assert result.pattern == "chisel.*hound.*padauk"
        assert result.match_type == "handle_only"

        # Check matched data structure (simplified component data)
        matched = result.matched
        assert matched is not None
        assert matched["handle_maker"] == "Chisel and Hound"
        assert matched["handle_model"] == "Padauk Wood"
        assert matched["source_text"] == "Chisel and Hound Padauk Wood handle"
        assert matched["_matched_by"] == "HandleOnlyStrategy"
        assert matched["_pattern"] == "chisel.*hound.*padauk"

        # Component strategies no longer create nested structure
        assert "handle" not in matched
        assert "knot" not in matched
        assert "brand" not in matched
        assert "model" not in matched

    def test_match_with_handle_match_no_pattern(self):
        """Test handle matching when no pattern is provided."""
        # Mock handle matcher response without pattern
        mock_handle_match = {"handle_maker": "Declaration Grooming", "handle_model": "Washington"}
        self.mock_handle_matcher.match_handle_maker.return_value = mock_handle_match

        result = self.strategy.match("Declaration Grooming Washington")

        assert result is not None
        assert result.pattern == "handle_only"  # Default pattern when none provided
        assert result.matched is not None
        assert result.matched["_pattern"] == "handle_only"

    def test_match_with_no_handle_match(self):
        """Test matching when handle matcher returns no match."""
        self.mock_handle_matcher.match_handle_maker.return_value = None

        result = self.strategy.match("Some random text")

        assert result is None

    def test_match_with_empty_handle_match(self):
        """Test matching when handle matcher returns empty dict."""
        self.mock_handle_matcher.match_handle_maker.return_value = {}

        result = self.strategy.match("Some random text")

        assert result is None

    def test_match_with_handle_match_no_handle_maker(self):
        """Test matching when handle matcher returns match without handle_maker."""
        mock_handle_match = {
            "handle_model": "Some Model"
            # Missing handle_maker
        }
        self.mock_handle_matcher.match_handle_maker.return_value = mock_handle_match

        result = self.strategy.match("Some text")

        assert result is None

    def test_match_preserves_original_input(self):
        """Test that the strategy preserves the original input text."""
        mock_handle_match = {
            "handle_maker": "Test Maker",
            "handle_model": "Test Model",
            "_pattern_used": "test_pattern",
        }
        self.mock_handle_matcher.match_handle_maker.return_value = mock_handle_match

        input_text = "Test Maker Test Model with special characters!@#"
        result = self.strategy.match(input_text)

        assert result is not None
        assert result.original == input_text
        assert result.matched is not None
        assert result.matched["source_text"] == input_text
