#!/usr/bin/env python3
"""Test file for "r/wetshaving MOAR BOAR" brush matching case."""

# No imports needed for this test file
from sotd.match.brush_matcher import BrushMatcher
from sotd.match.scoring_brush_matcher import BrushScoringMatcher


class TestMoarBoarBrushMatching:
    """Test the specific "r/wetshaving MOAR BOAR" brush matching case."""

    def setup_method(self):
        """Set up test fixtures."""
        self.legacy_matcher = BrushMatcher()
        self.scoring_matcher = BrushScoringMatcher()
        self.test_input = "Zenith - r/Wetshaving exclusive MOAR BOAR (31 mm × 57 mm bleached boar)"

    def test_legacy_system_moar_boar_matching(self):
        """Test that legacy system correctly matches MOAR BOAR brush."""
        result = self.legacy_matcher.match(self.test_input)

        assert result is not None
        assert result.matched is not None

        # Top level should be correct
        assert result.matched["brand"] == "Zenith"
        assert result.matched["model"] == "r/wetshaving MOAR BOAR"
        assert result.matched.get("fiber") is None  # Top level fiber should be None

        # Handle section should be correct
        handle = result.matched["handle"]
        assert handle["brand"] == "Zenith"
        assert handle["model"] is None  # No specific handle model defined in YAML
        assert handle["_matched_by"] == "KnownBrushMatchingStrategy"

        # Knot section should be correct
        knot = result.matched["knot"]
        assert knot["brand"] == "Zenith"
        assert knot["model"] == "B35"  # From YAML knot configuration
        assert knot["fiber"] == "Boar"  # From YAML knot configuration
        assert knot["knot_size_mm"] == 31  # From YAML knot configuration
        assert knot["_matched_by"] == "KnownBrushMatchingStrategy"

    def test_scoring_system_moar_boar_matching(self):
        """Test that scoring system correctly matches MOAR BOAR brush."""
        result = self.scoring_matcher.match(self.test_input)

        assert result is not None
        assert result.matched is not None

        # Top level should be correct
        assert result.matched["brand"] == "Zenith"
        assert result.matched["model"] == "r/wetshaving MOAR BOAR"
        assert result.matched.get("fiber") is None  # Top level fiber should be None

        # Handle section should be correct
        handle = result.matched["handle"]
        assert handle["brand"] == "Zenith"
        assert handle["model"] is None  # No specific handle model defined in YAML
        assert handle["_matched_by"] == "known_brush"

        # Knot section should be correct
        knot = result.matched["knot"]
        assert knot["brand"] == "Zenith"
        assert knot["model"] == "B35"  # From YAML knot configuration
        assert knot["fiber"] == "Boar"  # From YAML knot configuration
        assert knot["knot_size_mm"] == 31  # From YAML knot configuration
        assert knot["_matched_by"] == "known_brush"

    def test_systems_align_for_moar_boar(self):
        """Test that both systems produce identical results for MOAR BOAR."""
        legacy_result = self.legacy_matcher.match(self.test_input)
        scoring_result = self.scoring_matcher.match(self.test_input)

        assert legacy_result is not None
        assert scoring_result is not None

        # Compare top level
        assert legacy_result.matched["brand"] == scoring_result.matched["brand"]
        assert legacy_result.matched["model"] == scoring_result.matched["model"]
        assert legacy_result.matched.get("fiber") == scoring_result.matched.get("fiber")

        # Compare handle sections
        legacy_handle = legacy_result.matched["handle"]
        scoring_handle = scoring_result.matched["handle"]
        assert legacy_handle["brand"] == scoring_handle["brand"]
        assert legacy_handle["model"] == scoring_handle["model"]

        # Compare knot sections
        legacy_knot = legacy_result.matched["knot"]
        scoring_knot = scoring_result.matched["knot"]
        assert legacy_knot["brand"] == scoring_knot["brand"]
        assert legacy_knot["model"] == scoring_knot["model"]
        assert legacy_knot["fiber"] == scoring_knot["fiber"]
        assert legacy_knot["knot_size_mm"] == scoring_knot["knot_size_mm"]

    def test_known_brush_strategy_returns_correct_fields(self):
        """Test that KnownBrushMatchingStrategy returns correct handle_model and knot_model."""
        # Get the KnownBrushMatchingStrategy from the scoring system
        strategy = self.scoring_matcher.strategy_orchestrator.strategies[4]  # known_brush strategy
        result = strategy.match(self.test_input)

        assert result is not None
        assert result.matched is not None

        # Strategy should return correct fields
        assert result.matched["brand"] == "Zenith"
        assert result.matched["model"] == "r/wetshaving MOAR BOAR"
        assert result.matched.get("handle_model") is None  # No handle model defined in YAML
        assert result.matched.get("knot_model") == "B35"  # From YAML knot configuration
        assert result.matched.get("fiber") == "Boar"  # From YAML knot configuration
        assert result.matched.get("knot_size_mm") == 31  # From YAML knot configuration
