"""Tests that extract-phase overridden flags survive match serialization."""

from sotd.match.run import _serialize_matched_record, _with_overridden_from_extract
from sotd.match.types import MatchResult


class TestPreserveOverridden:
    def test_with_overridden_from_extract_adds_flag(self):
        product = {"original": "Ko", "normalized": "Koraat", "matched": {"brand": "Koraat"}}
        result = _with_overridden_from_extract(
            product, {"original": "Ko", "normalized": "Koraat", "overridden": "Normalized"}
        )
        assert result["overridden"] == "Normalized"
        assert result["original"] == "Ko"

    def test_with_overridden_from_extract_no_flag(self):
        product = {"original": "Ko", "normalized": "ko"}
        result = _with_overridden_from_extract(product, {"original": "Ko", "normalized": "ko"})
        assert "overridden" not in result

    def test_with_overridden_does_not_overwrite_existing(self):
        product = {"original": "x", "overridden": "Original,Normalized"}
        result = _with_overridden_from_extract(product, {"overridden": "Normalized"})
        assert result["overridden"] == "Original,Normalized"

    def test_serialize_match_result_preserves_overridden(self):
        extract_record = {
            "id": "abc",
            "razor": {
                "original": "Ko",
                "normalized": "Koraat",
                "overridden": "Normalized",
            },
        }
        matched_record = {
            "id": "abc",
            "razor": MatchResult(
                original="Ko",
                normalized="Koraat",
                matched={"brand": "Koraat", "model": None},
                match_type="regex",
                pattern="koraat",
            ),
        }
        out = _serialize_matched_record(matched_record, extract_record)
        assert out["razor"]["original"] == "Ko"
        assert out["razor"]["normalized"] == "Koraat"
        assert out["razor"]["overridden"] == "Normalized"
        assert out["razor"]["matched"]["brand"] == "Koraat"

    def test_serialize_brush_dict_preserves_overridden(self):
        extract_record = {
            "id": "abc",
            "brush": {
                "original": "Boti Boat",
                "normalized": "Boti Boar",
                "overridden": "Normalized",
            },
        }
        matched_record = {
            "id": "abc",
            "brush": {
                "original": "Boti Boat",
                "normalized": "Boti Boar",
                "matched": {"brand": "Boti"},
                "match_type": "exact",
                "pattern": "exact_match",
            },
        }
        out = _serialize_matched_record(matched_record, extract_record)
        assert out["brush"]["overridden"] == "Normalized"
        assert out["brush"]["normalized"] == "Boti Boar"
