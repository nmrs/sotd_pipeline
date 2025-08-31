"""Tests for strategy field functionality in mismatch analysis API."""

from webui.api.analysis import MismatchItem


class TestStrategyFieldAnalysis:
    """Test strategy field extraction and population in mismatch analysis."""

    def test_mismatch_item_model_strategy_field(self):
        """Test that MismatchItem model includes strategy field."""
        item = MismatchItem(
            original="Test Brush",
            matched={},
            match_type="regex",
            count=1,
            examples=[],
            comment_ids=[],
            matched_by_strategy="known_brush",
        )

        assert item.matched_by_strategy == "known_brush"
        assert hasattr(item, "matched_by_strategy")

    def test_mismatch_item_model_with_all_fields(self):
        """Test that MismatchItem model works with all required fields."""
        item = MismatchItem(
            original="Test Brush",
            matched={"brand": "Test Brand", "model": "Test Model"},
            match_type="regex",
            count=1,
            examples=["example1"],
            comment_ids=["123"],
            matched_by_strategy="known_brush",
            confidence=0.95,
            pattern="test.*pattern",
            mismatch_type="test",
            reason="Test reason",
            is_confirmed=False,
        )

        assert item.original == "Test Brush"
        assert item.matched == {"brand": "Test Brand", "model": "Test Model"}
        assert item.match_type == "regex"
        assert item.count == 1
        assert item.examples == ["example1"]
        assert item.comment_ids == ["123"]
        assert item.matched_by_strategy == "known_brush"
        assert item.confidence == 0.95
        assert item.pattern == "test.*pattern"
        assert item.mismatch_type == "test"
        assert item.reason == "Test reason"
        assert item.is_confirmed is False

    def test_strategy_field_validation(self):
        """Test that strategy field accepts various valid values."""
        valid_strategies = [
            "automated_split",
            "known_brush",
            "dual_component",
            "knot_only",
            "handle_only",
            "brand_fallback",
            "unknown",
        ]

        for strategy in valid_strategies:
            item = MismatchItem(
                original="Test Brush",
                matched={},
                match_type="regex",
                count=1,
                examples=[],
                comment_ids=[],
                matched_by_strategy=strategy,
            )
            assert item.matched_by_strategy == strategy

    def test_strategy_field_optional(self):
        """Test that strategy field is optional."""
        item = MismatchItem(
            original="Test Brush",
            matched={},
            match_type="regex",
            count=1,
            examples=[],
            comment_ids=[],
            # No matched_by_strategy field
        )

        # Should default to None
        assert item.matched_by_strategy is None

    def test_strategy_field_with_split_brush_data(self):
        """Test strategy field with split brush specific data."""
        item = MismatchItem(
            original="Semogue - Barbear Classico Cerda Boar 22mm",
            matched={
                "handle_component": "Semogue - Barbear Classico Cerda",
                "knot_component": "Boar 22mm",
            },
            match_type="split_brush",
            count=1,
            examples=[],
            comment_ids=[],
            matched_by_strategy="automated_split",
        )

        assert item.matched_by_strategy == "automated_split"
        assert item.matched["handle_component"] == "Semogue - Barbear Classico Cerda"
        assert item.matched["knot_component"] == "Boar 22mm"

    def test_strategy_field_with_complete_brush_data(self):
        """Test strategy field with complete brush data."""
        item = MismatchItem(
            original="A P ShaveCo 22mm Synbad",
            matched={"brand": "A P ShaveCo", "model": "22mm Synbad", "fiber": "Synthetic"},
            match_type="regex",
            count=1,
            examples=[],
            comment_ids=[],
            matched_by_strategy="known_brush",
        )

        assert item.matched_by_strategy == "known_brush"
        assert item.matched["brand"] == "A P ShaveCo"
        assert item.matched["model"] == "22mm Synbad"
        assert item.matched["fiber"] == "Synthetic"
