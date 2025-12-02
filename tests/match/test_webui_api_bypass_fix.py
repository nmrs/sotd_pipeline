"""Test to drive the fix for webui API bypass issue."""

import pytest
from pathlib import Path
import sys

# Add the project root to the path so we can import sotd modules
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from sotd.match.brush_matcher import BrushMatcher


def test_webui_api_bypass_issue(
    test_correct_matches_path,
    test_brushes_path,
    test_handles_path,
    test_knots_path,
    test_brush_scoring_config_path,
):
    """Test that exposes the webui API bypass issue.

    The webui API is using the old constructor parameter approach:
    self.brush_matcher = BrushMatcher(bypass_correct_matches=True)

    But BrushMatcher now uses the method parameter approach:
    def match(self, value: str, bypass_correct_matches: bool = None)

    This test should FAIL until we fix the webui API.
    """
    # This is what the webui API is currently doing (WRONG):
    # self.brush_matcher = BrushMatcher(bypass_correct_matches=True)
    # result = self.brush_matcher.match(pattern)  # Missing bypass parameter!

    matcher = BrushMatcher(
        correct_matches_path=test_correct_matches_path,
        brushes_path=test_brushes_path,
        handles_path=test_handles_path,
        knots_path=test_knots_path,
        brush_scoring_config_path=test_brush_scoring_config_path,
    )  # NEW approach - no constructor parameter
    test_pattern = "a.p. shave co amber smoke g5c fan"

    # This should work but doesn't because the constructor parameter is ignored
    result = matcher.match(test_pattern)

    # The test should FAIL because the bypass isn't working
    assert result is not None, "Bypass should work with constructor parameter"
    assert result.matched is not None, "Should have matched data"
    assert isinstance(result.matched, dict)
    assert result.matched.get("brand") == "AP Shave Co", "Should match AP Shave Co brand"
    assert result.matched.get("model") == "G5C", "Should match G5C model"


def test_correct_bypass_approach(
    test_correct_matches_path,
    test_brushes_path,
    test_handles_path,
    test_knots_path,
    test_brush_scoring_config_path,
):
    """Test the correct bypass approach that the webui API should use."""
    # This is what the webui API SHOULD do (CORRECT):
    # self.brush_matcher = BrushMatcher()  # No constructor parameter
    # result = self.brush_matcher.match(pattern, bypass_correct_matches=True)  # Method parameter

    matcher = BrushMatcher(
        correct_matches_path=test_correct_matches_path,
        brushes_path=test_brushes_path,
        handles_path=test_handles_path,
        knots_path=test_knots_path,
        brush_scoring_config_path=test_brush_scoring_config_path,
    )  # NEW approach - no constructor parameter
    test_pattern = "a.p. shave co amber smoke g5c fan"

    # This should work correctly
    result = matcher.match(test_pattern, bypass_correct_matches=True)

    # The test should PASS
    assert result is not None, "Bypass should work with method parameter"
    assert result.matched is not None, "Should have matched data"
    assert isinstance(result.matched, dict)
    assert result.matched.get("brand") == "AP Shave Co", "Should match AP Shave Co brand"
    assert result.matched.get("model") == "G5C", "Should match G5C model"


if __name__ == "__main__":
    # Run the failing test to see the issue
    # Create test paths for standalone execution
    test_data_dir = Path(__file__).parent / "test_data"
    test_correct_matches_path = test_data_dir / "correct_matches.yaml"
    test_brushes_path = test_data_dir / "brushes.yaml"
    test_handles_path = test_data_dir / "handles.yaml"
    test_knots_path = test_data_dir / "knots.yaml"
    test_brush_scoring_config_path = test_data_dir / "brush_scoring_config.yaml"

    print("Testing OLD approach (should fail):")
    try:
        test_webui_api_bypass_issue(
            test_correct_matches_path,
            test_brushes_path,
            test_handles_path,
            test_knots_path,
            test_brush_scoring_config_path,
        )
        print("❌ OLD approach unexpectedly passed - this shouldn't happen!")
    except AssertionError as e:
        print(f"✅ OLD approach failed as expected: {e}")

    print("\nTesting NEW approach (should pass):")
    try:
        test_correct_bypass_approach(
            test_correct_matches_path,
            test_brushes_path,
            test_handles_path,
            test_knots_path,
            test_brush_scoring_config_path,
        )
        print("✅ NEW approach passed as expected!")
    except Exception as e:
        print(f"❌ NEW approach failed unexpectedly: {e}")
