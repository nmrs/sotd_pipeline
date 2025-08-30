"""
Tests for BrushMatcher's correct matches priority rule.

This tests the core behavior that correct matches have highest priority
and return immediately, while other strategies only run when correct matches
find nothing.
"""

import pytest
import yaml
from pathlib import Path

from sotd.match.brush_matcher import BrushMatcher


class TestBrushMatcherCorrectMatchesPriority:
    """Test that correct matches have highest priority in BrushMatcher."""

    def setup_method(self):
        """Set up test fixtures."""
        # Use current BrushMatcher constructor signature
        self.brush_matcher = BrushMatcher(
            correct_matches_path=Path("data/correct_matches.yaml"),
            brushes_path=Path("data/brushes.yaml"),
            handles_path=Path("data/handles.yaml"),
            knots_path=Path("data/knots.yaml"),
            brush_scoring_config_path=Path("data/brush_scoring_config.yaml"),
        )

        # Load actual correct_matches.yaml for testing
        correct_matches_path = Path("data/correct_matches.yaml")
        if correct_matches_path.exists():
            with open(correct_matches_path, "r") as f:
                self.correct_matches = yaml.safe_load(f)
        else:
            pytest.skip("correct_matches.yaml not found")

    def test_correct_matches_have_highest_priority(self):
        """Test that correct matches return immediately and don't run other strategies."""
        # Find a brush entry in correct_matches that has a specific pattern
        brush_entries = self.correct_matches.get("brush", {})
        if not brush_entries:
            pytest.skip("No brush entries in correct_matches.yaml")

        # Look for an entry with specific patterns (not just brand names)
        test_input = None
        expected_match = None

        for brand, models in brush_entries.items():
            for model, patterns in models.items():
                if isinstance(patterns, list) and patterns:
                    # Use the first pattern as test input
                    test_input = patterns[0]
                    expected_match = {"brand": brand, "model": model}
                    break
            if test_input:
                break

        if not test_input:
            pytest.skip("No brush patterns found in correct_matches.yaml")

        # Test that correct matches returns immediately
        result = self.brush_matcher.match(test_input)

        assert result is not None
        assert result.matched is not None
        assert result.match_type == "exact"  # Should be exact for correct matches
        assert result.matched["strategy"] == "correct_matches"  # Should use correct matches

        # Verify the match data matches what's in correct_matches.yaml
        assert result.matched is not None
        assert expected_match is not None
        assert result.matched["brand"] == expected_match["brand"]
        assert result.matched["model"] == expected_match["model"]

    def test_correct_matches_no_match_runs_other_strategies(self):
        """Test that when correct matches finds nothing, other strategies are run."""
        # Test with a brush that is NOT in correct_matches but should match via other strategies
        test_input = "Simpson Chubby 2"  # This should match via known_brush strategy

        # First verify it's not in correct_matches
        brush_entries = self.correct_matches.get("brush", {})
        assert test_input.lower() not in brush_entries, (
            f"Test input {test_input} is in correct_matches, " f"choose different input"
        )

        # Test that it matches via other strategies
        result = self.brush_matcher.match(test_input)

        assert result is not None
        assert result.matched is not None
        assert result.match_type == "regex"  # Should be regex for known brush strategy
        assert result.matched["strategy"] == "known_brush"  # Should use known brush strategy

    def test_correct_matches_priority_overrides_other_strategies(self):
        """Test that correct matches take precedence even when other strategies could match."""
        # This test verifies that if correct matches finds something,
        # other strategies don't get a chance to run

        # Find a brush entry that could potentially match via other strategies too
        brush_entries = self.correct_matches.get("brush", {})
        if not brush_entries:
            pytest.skip("No brush entries in correct_matches.yaml")

        # Look for a simple brand name that might match via other strategies
        test_input = None
        for brand in brush_entries.keys():
            if len(brand.split()) <= 3:  # Simple brand name
                # Check if this brand has a pattern that matches the brand name itself
                for model, patterns in brush_entries[brand].items():
                    for pattern in patterns:
                        if brand.lower() in pattern.lower():
                            test_input = brand
                            break
                    if test_input:
                        break
                if test_input:
                    break
