"""Test BrushMatcher bypass functionality."""

import pytest
from pathlib import Path
from sotd.match.brush_matcher import BrushMatcher


class TestBrushMatcherBypass:
    """Test that BrushMatcher correctly bypasses correct_matches.yaml when requested."""

    def test_bypass_correct_matches_true(self):
        """Test that bypass_correct_matches=True actually bypasses correct_matches.yaml."""
        # Get project root for data paths
        project_root = Path(__file__).parent.parent.parent
        data_dir = project_root / "data"

        # Create matcher with bypass enabled
        matcher = BrushMatcher(
            brushes_path=data_dir / "brushes.yaml",
            handles_path=data_dir / "handles.yaml",
            knots_path=data_dir / "knots.yaml",
            correct_matches_path=data_dir / "correct_matches.yaml",
            bypass_correct_matches=True,
        )

        # Test the specific pattern that's failing
        test_pattern = "a.p. shave co amber smoke g5c fan"
        result = matcher.match(test_pattern)

        # Debug output
        print(f"🔍 DEBUG: Testing pattern: '{test_pattern}'")
        print(f"🔍 DEBUG: Result: {result}")
        if result and hasattr(result, "matched"):
            print(f"🔍 DEBUG: Matched data: {result.matched}")
            print(f"🔍 DEBUG: Strategy used: {getattr(result, '_matched_by', 'Unknown')}")

        # This should match based on the regex pattern in brushes.yaml
        assert result is not None, f"Pattern '{test_pattern}' should match"
        assert hasattr(result, "matched"), "Result should have matched attribute"
        assert result.matched is not None, "Matched data should not be None"

        # Should match to AP Shave Co G5C based on the regex pattern
        expected_brand = "AP Shave Co"
        expected_model = "G5C"

        actual_brand = result.matched.get("brand")
        actual_model = result.matched.get("model")

        print(f"🔍 DEBUG: Expected: {expected_brand} {expected_model}")
        print(f"🔍 DEBUG: Actual: {actual_brand} {actual_model}")

        assert (
            actual_brand == expected_brand
        ), f"Expected brand '{expected_brand}', got '{actual_brand}'"
        assert (
            actual_model == expected_model
        ), f"Expected model '{expected_model}', got '{actual_model}'"

        # Should NOT be using CorrectMatchesStrategy when bypassing
        strategy_used = getattr(result, "_matched_by", "Unknown")
        assert (
            strategy_used != "CorrectMatchesStrategy"
        ), f"Should not use CorrectMatchesStrategy when bypassing, got '{strategy_used}'"

    def test_bypass_correct_matches_false(self):
        """Test that bypass_correct_matches=False uses correct_matches.yaml."""
        project_root = Path(__file__).parent.parent.parent
        data_dir = project_root / "data"

        # Create matcher with bypass disabled (default)
        matcher = BrushMatcher(
            brushes_path=data_dir / "brushes.yaml",
            handles_path=data_dir / "handles.yaml",
            knots_path=data_dir / "knots.yaml",
            correct_matches_path=data_dir / "correct_matches.yaml",
            bypass_correct_matches=False,
        )

        # Test the same pattern
        test_pattern = "a.p. shave co amber smoke g5c fan"
        result = matcher.match(test_pattern)

        print(f"🔍 DEBUG: Testing pattern with bypass=False: '{test_pattern}'")
        print(f"🔍 DEBUG: Result: {result}")
        if result and hasattr(result, "matched"):
            print(f"🔍 DEBUG: Matched data: {result.matched}")
            print(f"🔍 DEBUG: Strategy used: {getattr(result, '_matched_by', 'Unknown')}")

        # Should still match, but might use different strategy
        assert result is not None, f"Pattern '{test_pattern}' should match even without bypass"
        assert hasattr(result, "matched"), "Result should have matched attribute"
        assert result.matched is not None, "Matched data should not be None"

    def test_regex_pattern_matching(self):
        """Test that the specific regex pattern in brushes.yaml actually matches."""
        import re

        # The pattern from brushes.yaml
        pattern = r"\ba[\s.]*p\b.*g5c"
        test_string = "a.p. shave co amber smoke g5c fan"

        print(f"🔍 DEBUG: Testing regex pattern: '{pattern}'")
        print(f"🔍 DEBUG: Test string: '{test_string}'")

        match = re.search(pattern, test_string, re.IGNORECASE)
        print(f"🔍 DEBUG: Regex match result: {match}")

        # This should definitely match
        assert match is not None, f"Regex pattern '{pattern}' should match '{test_string}'"

        # Print what was matched
        if match:
            print(f"🔍 DEBUG: Matched portion: '{match.group(0)}'")
            print(f"🔍 DEBUG: Match span: {match.span()}")

    def test_brush_matcher_initialization(self):
        """Test that BrushMatcher is initialized with correct bypass setting."""
        project_root = Path(__file__).parent.parent.parent
        data_dir = project_root / "data"

        # Test with bypass=True
        matcher_true = BrushMatcher(
            brushes_path=data_dir / "brushes.yaml",
            handles_path=data_dir / "handles.yaml",
            knots_path=data_dir / "correct_matches.yaml",
            correct_matches_path=data_dir / "correct_matches.yaml",
            bypass_correct_matches=True,
        )

        print(
            f"🔍 DEBUG: Matcher bypass_correct_matches attribute: {getattr(matcher_true, 'bypass_correct_matches', 'NOT_FOUND')}"
        )

        # Should have the bypass attribute set correctly
        assert hasattr(
            matcher_true, "bypass_correct_matches"
        ), "Matcher should have bypass_correct_matches attribute"
        assert matcher_true.bypass_correct_matches is True, "bypass_correct_matches should be True"
