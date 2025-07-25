"""Integration tests for brush matcher using production YAML files."""

import pytest
from pathlib import Path

from sotd.match.brush_matcher import BrushMatcher


@pytest.fixture
def production_brush_matcher():
    """Create brush matcher with production YAML files."""
    data_dir = Path("data")

    return BrushMatcher(
        catalog_path=data_dir / "brushes.yaml",
        handles_path=data_dir / "handles.yaml",
        knots_path=data_dir / "knots.yaml",
        correct_matches_path=data_dir / "correct_matches.yaml",
    )


class TestBrushMatcherIntegration:
    """Integration tests using production YAML files."""

    def test_production_knot_only_matching(self, production_brush_matcher):
        """Test that knot-only strings match correctly with production data."""
        # Test the specific case from the plan
        result = production_brush_matcher.match("Richman Shaving 28 mm S2 innovator knot")

        # Should match as knot-only (not complete brush)
        assert result.match_type == "regex"
        assert result.pattern == "rich.*man.*shav.*s-?2.*innovator"

        # Verify handle is None (no handle component)
        assert result.matched["handle"]["brand"] is None
        assert result.matched["handle"]["model"] is None

        # Verify knot has correct brand, model, fiber, and size
        assert result.matched["knot"]["brand"] == "Rich Man Shaving"
        assert result.matched["knot"]["model"] == "S2 Innovator"
        assert result.matched["knot"]["fiber"] == "Badger"
        assert result.matched["knot"]["knot_size_mm"] == 26

        # Verify top-level brand/model are None (not a complete brush)
        assert result.matched["brand"] is None
        assert result.matched["model"] is None

    def test_multiple_knot_only_strings(self, production_brush_matcher):
        """Test multiple knot-only strings to ensure consistent behavior."""
        test_cases = [
            "Richman Shaving 28 mm S2 innovator knot",
            "Rich Man Shaving S2 Innovator 26mm",
            "Rich Man Shaving S2 Innovator knot",
        ]

        for test_string in test_cases:
            result = production_brush_matcher.match(test_string)

            # Should match as knot-only
            assert result.match_type == "regex"
            assert result.matched["knot"]["brand"] == "Rich Man Shaving"
            assert result.matched["knot"]["model"] == "S2 Innovator"
            assert result.matched["handle"]["brand"] is None
            assert result.matched["brand"] is None
