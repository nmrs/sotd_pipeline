#!/usr/bin/env python3
"""Tests for analysis endpoints."""

import sys
from pathlib import Path

import pytest

# Add the webui directory to the Python path
webui_dir = Path(__file__).parent.parent
if str(webui_dir) not in sys.path:
    sys.path.insert(0, str(webui_dir))

from api.analysis import MismatchItem  # noqa: E402


class TestMismatchItemModel:
    """Test MismatchItem model with split brush fields."""

    def test_mismatch_item_basic_fields(self):
        """Test MismatchItem with basic fields."""
        item = MismatchItem(
            original="Test Razor",
            matched={"brand": "Test Brand", "model": "Test Model"},
            pattern="test_pattern",
            match_type="regex",
            count=1,
            examples=["example1"],
            comment_ids=["123"],
        )

        assert item.original == "Test Razor"
        assert item.matched == {"brand": "Test Brand", "model": "Test Model"}
        assert item.pattern == "test_pattern"
        assert item.match_type == "regex"
        assert item.count == 1
        assert item.examples == ["example1"]
        assert item.comment_ids == ["123"]
        assert item.is_split_brush is None
        assert item.handle_component is None
        assert item.knot_component is None

    def test_mismatch_item_split_brush_fields(self):
        """Test MismatchItem with split brush fields."""
        item = MismatchItem(
            original="Jayaruh #441 w/ AP Shave Co G5C",
            matched={
                "brand": None,
                "model": None,
                "handle": "Jayaruh #441",
                "knot": "AP Shave Co G5C",
            },
            pattern="split_brush_pattern",
            match_type="split",
            count=1,
            examples=["example1"],
            comment_ids=["123"],
            is_split_brush=True,
            handle_component="Jayaruh #441",
            knot_component="AP Shave Co G5C",
        )

        assert item.original == "Jayaruh #441 w/ AP Shave Co G5C"
        assert item.is_split_brush is True
        assert item.handle_component == "Jayaruh #441"
        assert item.knot_component == "AP Shave Co G5C"

    def test_mismatch_item_handle_only_split_brush(self):
        """Test MismatchItem with handle-only split brush."""
        item = MismatchItem(
            original="Jayaruh #441",
            matched={"brand": None, "model": None, "handle": "Jayaruh #441"},
            pattern="handle_only_pattern",
            match_type="split",
            count=1,
            examples=["example1"],
            comment_ids=["123"],
            is_split_brush=True,
            handle_component="Jayaruh #441",
            knot_component=None,
        )

        assert item.is_split_brush is True
        assert item.handle_component == "Jayaruh #441"
        assert item.knot_component is None

    def test_mismatch_item_knot_only_split_brush(self):
        """Test MismatchItem with knot-only split brush."""
        item = MismatchItem(
            original="AP Shave Co G5C",
            matched={"brand": None, "model": None, "knot": "AP Shave Co G5C"},
            pattern="knot_only_pattern",
            match_type="split",
            count=1,
            examples=["example1"],
            comment_ids=["123"],
            is_split_brush=True,
            handle_component=None,
            knot_component="AP Shave Co G5C",
        )

        assert item.is_split_brush is True
        assert item.handle_component is None
        assert item.knot_component == "AP Shave Co G5C"

    def test_mismatch_item_backward_compatibility(self):
        """Test MismatchItem backward compatibility with existing fields."""
        item = MismatchItem(
            original="Test Razor",
            matched={"brand": "Test Brand", "model": "Test Model"},
            pattern="test_pattern",
            match_type="regex",
            confidence=0.8,
            mismatch_type="levenshtein_distance",
            reason="High Levenshtein distance",
            count=1,
            examples=["example1"],
            comment_ids=["123"],
            is_confirmed=False,
        )

        assert item.confidence == 0.8
        assert item.mismatch_type == "levenshtein_distance"
        assert item.reason == "High Levenshtein distance"
        assert item.is_confirmed is False
        # Split brush fields should be None by default
        assert item.is_split_brush is None
        assert item.handle_component is None
        assert item.knot_component is None


# Keep the existing test classes for when we can run them properly
class TestAnalysisEndpoints:
    """Test analysis endpoints."""

    @pytest.mark.skip(reason="Requires FastAPI app setup")
    def test_placeholder(self):
        """Placeholder test to prevent pytest from failing."""
        pass
