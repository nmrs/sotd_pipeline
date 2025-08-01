#!/usr/bin/env python3
"""
Tests for fixing user intent logic and unicode corruption issues.

This test file demonstrates the problems that need to be fixed:
1. Simple brushes should not have user_intent (only composite brushes)
2. Unicode characters should be preserved properly in YAML
3. Mismatcher analyzer should show user intent
"""

import pytest
import yaml
from pathlib import Path
from unittest.mock import patch, MagicMock  # noqa: F401

from sotd.match.brush_matcher import BrushMatcher
from sotd.match.config import BrushMatcherConfig


class TestBrushUserIntentFixes:
    """Test cases for fixing user intent logic and unicode issues."""

    def test_simple_brushes_should_not_have_user_intent(self):
        """Test that simple brushes should not have user_intent field."""
        # Simple brushes like "alpha amber" should not have user_intent
        # because they are not composite (no separate handle/knot components)

        config = BrushMatcherConfig.create_default()
        brush_matcher = BrushMatcher(config=config)

        # Test simple brush - should not have user_intent
        result = brush_matcher.match("alpha amber")

        # Simple brushes should not have user_intent at top level
        # They should only have user_intent if they are composite brushes
        assert result is not None
        assert result.matched is not None

        # For simple brushes, user_intent should be None or not present at top level
        # The user_intent should only be in the handle/knot sections if it's composite
        if "user_intent" in result.matched:
            # If present, it should only be in handle/knot sections, not at top level
            assert result.matched["user_intent"] is None

    def test_composite_brushes_should_have_user_intent(self):
        """Test that composite brushes should have user_intent field."""
        # Composite brushes like "G5C Rad Dinosaur" should have user_intent
        # because they have separate handle and knot components

        config = BrushMatcherConfig.create_default()
        brush_matcher = BrushMatcher(config=config)

        # Test composite brush - should have user_intent
        result = brush_matcher.match("G5C Rad Dinosaur Creation")

        assert result is not None
        assert result.matched is not None

        # Composite brushes should have user_intent
        assert "user_intent" in result.matched
        assert result.matched["user_intent"] in ["handle_primary", "knot_primary"]

    def test_unicode_preservation_in_yaml(self):
        """Test that unicode characters are preserved properly in YAML."""
        # Test that "Böker" is preserved as "Böker", not "B\xF6ker"

        test_data = {
            "brands": {
                "Böker": {"Synthetic": {"böker synthetic": {"user_intent": "handle_primary"}}}
            }
        }

        # Save to temporary file
        temp_path = Path("test_unicode.yaml")
        with open(temp_path, "w", encoding="utf-8") as f:
            yaml.dump(
                test_data,
                f,
                default_flow_style=False,
                indent=2,
                allow_unicode=True,
                sort_keys=False,
            )

        # Read back and verify unicode is preserved
        with open(temp_path, "r", encoding="utf-8") as f:
            loaded_data = yaml.safe_load(f)

        # Clean up
        temp_path.unlink()

        # Verify unicode is preserved
        assert "Böker" in loaded_data["brands"]
        assert "böker synthetic" in loaded_data["brands"]["Böker"]["Synthetic"]
        synthetic_data = loaded_data["brands"]["Böker"]["Synthetic"]["böker synthetic"]
        assert synthetic_data["user_intent"] == "handle_primary"

    def test_correct_matches_yaml_unicode_issues(self):
        """Test that correct_matches.yaml has unicode corruption issues."""
        # Load the current correct_matches.yaml and check for unicode issues

        correct_matches_path = Path("data/correct_matches.yaml")
        if not correct_matches_path.exists():
            pytest.skip("correct_matches.yaml not found")

        with open(correct_matches_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Check for escaped unicode sequences
        assert "\\xF6" not in content, "Unicode corruption detected: \\xF6 found"
        assert "Böker" in content, "Proper unicode 'Böker' should be present"

    def test_brush_matcher_preserves_unicode(self):
        """Test that brush matcher preserves unicode in output."""
        config = BrushMatcherConfig.create_default()
        brush_matcher = BrushMatcher(config=config)

        # Test with unicode characters
        result = brush_matcher.match("böker synthetic")

        assert result is not None
        assert result.matched is not None

        # The brand should preserve unicode
        if result.matched.get("brand"):
            assert "ö" in result.matched["brand"], "Unicode 'ö' should be preserved in brand"

    def test_user_intent_logic_distinction(self):
        """Test the distinction between simple and composite brushes for user intent."""
        config = BrushMatcherConfig.create_default()
        brush_matcher = BrushMatcher(config=config)

        # Simple brush - no user intent needed
        simple_result = brush_matcher.match("simpson chubby 2")
        assert simple_result is not None

        # Composite brush - user intent needed
        composite_result = brush_matcher.match("G5C Rad Dinosaur Creation")
        assert composite_result is not None

        # Simple brushes should not have user_intent at top level
        # Composite brushes should have user_intent at top level
        if simple_result.matched and "user_intent" in simple_result.matched:
            # If present, it should be None for simple brushes
            assert simple_result.matched["user_intent"] is None

        if composite_result.matched and "user_intent" in composite_result.matched:
            # Composite brushes should have valid user_intent
            assert composite_result.matched["user_intent"] in ["handle_primary", "knot_primary"]
