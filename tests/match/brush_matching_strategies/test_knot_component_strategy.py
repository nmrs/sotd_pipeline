from unittest.mock import Mock

from sotd.match.brush_matching_strategies.knot_component_strategy import KnotComponentStrategy
from sotd.match.types import MatchResult


class TestKnotComponentStrategy:
    """Test the KnotComponentStrategy class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_knot_matcher = Mock()
        self.strategy = KnotComponentStrategy(self.mock_knot_matcher)

    def test_init(self):
        """Test strategy initialization."""
        assert self.strategy.knot_matcher == self.mock_knot_matcher

    def test_match_with_empty_input(self):
        """Test matching with empty or whitespace input."""
        assert self.strategy.match("") is None
        assert self.strategy.match("   ") is None

    def test_match_with_knot_match(self):
        """Test successful knot matching."""
        # Mock knot strategy response
        mock_result = Mock()
        mock_result.matched = {
            "brand": "Declaration Grooming",
            "model": "B2",
            "fiber": "badger",
            "knot_size_mm": 26.0,
            "knot_maker": "Declaration Grooming",
            "fiber_strategy": "yaml",
            "fiber_conflict": None,
        }
        mock_result.pattern = "declaration.*b2"
        mock_result.match_type = "regex"

        # Mock the knot matcher strategies
        mock_strategy = Mock()
        mock_strategy.match.return_value = mock_result
        self.mock_knot_matcher.strategies = [mock_strategy]

        result = self.strategy.match("Declaration B2")

        assert result is not None
        assert isinstance(result, MatchResult)
        assert result.original == "Declaration B2"
        assert result.strategy == "knot_only"
        assert result.pattern == "declaration.*b2"
        assert result.match_type == "knot_only"

        # Check matched data structure (simplified component data)
        matched = result.matched
        assert matched is not None
        assert matched["brand"] == "Declaration Grooming"
        assert matched["model"] == "B2"
        assert matched["fiber"] == "badger"
        assert matched["knot_size_mm"] == 26.0
        assert matched["source_text"] == "Declaration B2"
        assert matched["_matched_by"] == "KnotComponentStrategy"
        assert matched["_pattern"] == "declaration.*b2"

        # Component strategies no longer create nested structure
        assert "handle" not in matched
        assert "knot" not in matched

    def test_match_with_knot_match_no_pattern(self):
        """Test knot matching when no pattern is provided."""
        # Mock knot strategy response without pattern
        mock_result = Mock()
        mock_result.matched = {
            "brand": "Zenith",
            "model": "B15",
            "fiber": "boar",
            "knot_size_mm": 28.0,
            "knot_maker": "Zenith",
            "fiber_strategy": "yaml",
            "fiber_conflict": None,
        }
        mock_result.pattern = None
        mock_result.match_type = "regex"

        # Mock the knot matcher strategies
        mock_strategy = Mock()
        mock_strategy.match.return_value = mock_result
        self.mock_knot_matcher.strategies = [mock_strategy]

        result = self.strategy.match("Zenith B15")

        assert result is not None
        assert result.pattern == "knot_only"  # Default pattern when none provided
        assert result.matched is not None
        assert result.matched["_pattern"] == "knot_only"

    def test_match_with_no_knot_match(self):
        """Test matching when no knot strategies return a match."""
        # Mock knot matcher strategies that return no match
        mock_strategy = Mock()
        mock_strategy.match.return_value = None
        self.mock_knot_matcher.strategies = [mock_strategy]

        result = self.strategy.match("Some random text")

        assert result is None

    def test_match_with_strategy_exception(self):
        """Test matching when a strategy throws an exception."""
        # Mock knot matcher strategies that throw exceptions
        mock_strategy = Mock()
        mock_strategy.match.side_effect = Exception("Strategy error")
        self.mock_knot_matcher.strategies = [mock_strategy]

        result = self.strategy.match("Some text")

        assert result is None

    def test_match_with_multiple_strategies(self):
        """Test matching with multiple knot strategies."""
        # Mock first strategy that returns no match
        mock_strategy1 = Mock()
        mock_strategy1.match.return_value = None

        # Mock second strategy that returns a match
        mock_result = Mock()
        mock_result.matched = {
            "brand": "Omega",
            "model": "10049",
            "fiber": "boar",
            "knot_size_mm": 24.0,
            "knot_maker": "Omega",
            "fiber_strategy": "yaml",
            "fiber_conflict": None,
        }
        mock_result.pattern = "omega.*10049"
        mock_result.match_type = "regex"

        mock_strategy2 = Mock()
        mock_strategy2.match.return_value = mock_result

        self.mock_knot_matcher.strategies = [mock_strategy1, mock_strategy2]

        result = self.strategy.match("Omega 10049")

        assert result is not None
        assert result.matched is not None
        assert result.matched["brand"] == "Omega"
        assert result.matched["model"] == "10049"

    def test_match_preserves_original_input(self):
        """Test that the strategy preserves the original input text."""
        mock_result = Mock()
        mock_result.matched = {
            "brand": "Test Brand",
            "model": "Test Model",
            "fiber": "synthetic",
            "knot_size_mm": 26.0,
            "knot_maker": "Test Brand",
            "fiber_strategy": "yaml",
            "fiber_conflict": None,
        }
        mock_result.pattern = "test_pattern"
        mock_result.match_type = "regex"

        mock_strategy = Mock()
        mock_strategy.match.return_value = mock_result
        self.mock_knot_matcher.strategies = [mock_strategy]

        input_text = "Test Brand Test Model with special characters!@#"
        result = self.strategy.match(input_text)

        assert result is not None
        assert result.original == input_text
        assert result.matched is not None
        assert result.matched["source_text"] == input_text
