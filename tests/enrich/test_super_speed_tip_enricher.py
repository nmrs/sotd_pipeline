import pytest

from sotd.enrich.super_speed_tip_enricher import SuperSpeedTipEnricher


class TestSuperSpeedTipEnricher:
    """Test cases for SuperSpeedTipEnricher."""

    @pytest.fixture
    def enricher(self):
        """Create a SuperSpeedTipEnricher instance for testing."""
        return SuperSpeedTipEnricher()

    def test_target_field(self, enricher):
        """Test that the target field is correctly set to 'razor'."""
        assert enricher.target_field == "razor"

    def test_applies_to_gillette_super_speed(self, enricher):
        """Test that enricher applies to Gillette Super Speed razors."""
        record = {"razor": {"matched": {"brand": "Gillette", "model": "Super Speed"}}}
        assert enricher.applies_to(record) is True

    def test_does_not_apply_to_other_gillette(self, enricher):
        """Test that enricher does not apply to other Gillette razors."""
        record = {"razor": {"matched": {"brand": "Gillette", "model": "Tech"}}}
        assert enricher.applies_to(record) is False

    def test_does_not_apply_to_other_brands(self, enricher):
        """Test that enricher does not apply to other brands."""
        record = {"razor": {"matched": {"brand": "RazoRock", "model": "Game Changer"}}}
        assert enricher.applies_to(record) is False

    def test_does_not_apply_to_no_razor(self, enricher):
        """Test that enricher does not apply when no razor is present."""
        record = {"blade": {"matched": {"brand": "Feather"}}}
        assert enricher.applies_to(record) is False

    def test_does_not_apply_to_none_razor(self, enricher):
        """Test that enricher does not apply when razor is None."""
        record = {"razor": None}
        assert enricher.applies_to(record) is False

    def test_does_not_apply_to_invalid_razor_structure(self, enricher):
        """Test that enricher does not apply when razor structure is invalid."""
        record = {"razor": "not a dict"}
        assert enricher.applies_to(record) is False

    def test_does_not_apply_to_no_matched_data(self, enricher):
        """Test that enricher does not apply when no matched data is present."""
        record = {"razor": {}}
        assert enricher.applies_to(record) is False

    def test_extract_tip_color_red(self, enricher):
        """Test extraction of Red tip."""
        comment = "Gillette Super Speed Red"
        result = enricher.enrich({}, comment)
        assert result is not None
        assert result["tip_color"] == "Red"
        assert result["_enriched_by"] == "SuperSpeedTipEnricher"
        assert result["_extraction_source"] == "user_comment"

    def test_extract_tip_color_blue(self, enricher):
        """Test extraction of Blue tip."""
        comment = "Gillette Super Speed Blue"
        result = enricher.enrich({}, comment)
        assert result is not None
        assert result["tip_color"] == "Blue"

    def test_extract_tip_color_black(self, enricher):
        """Test extraction of Black tip."""
        comment = "Gillette Super Speed Black"
        result = enricher.enrich({}, comment)
        assert result is not None
        assert result["tip_color"] == "Black"

    def test_extract_tip_variant_flare(self, enricher):
        """Test extraction of Flare tip."""
        comment = "Gillette Super Speed Flare"
        result = enricher.enrich({}, comment)
        assert result is not None
        assert result["tip_variant"] == "Flare"

    def test_extract_tip_variant_flair(self, enricher):
        """Test extraction of Flair tip (synonym for Flare)."""
        comment = "Gillette Super Speed Flair"
        result = enricher.enrich({}, comment)
        assert result is not None
        assert result["tip_variant"] == "Flare"

    def test_extract_both_tip_color_and_variant(self, enricher):
        """Test extraction of both tip color and variant."""
        comment = "Gillette Super Speed Red Flare"
        result = enricher.enrich({}, comment)
        assert result is not None
        assert result["tip_color"] == "Red"
        assert result["tip_variant"] == "Flare"

    def test_case_insensitive_extraction(self, enricher):
        """Test that extraction works regardless of case."""
        test_cases = [
            ("GILLETTE SUPER SPEED RED", "Red"),
            ("gillette super speed blue", "Blue"),
            ("Gillette Super Speed Black", "Black"),
            ("Gillette Super Speed Flare", "Flare"),
            ("Gillette Super Speed Flair", "Flare"),
        ]

        for comment, expected in test_cases:
            result = enricher.enrich({}, comment)
            assert result is not None, f"Failed for comment: {comment}"
            if "Flare" in comment or "Flair" in comment:
                assert result["tip_variant"] == expected, f"Failed for comment: {comment}"
            else:
                assert result["tip_color"] == expected, f"Failed for comment: {comment}"

    def test_no_tip_found(self, enricher):
        """Test that None is returned when no tip is found."""
        comment = "Gillette Super Speed"
        result = enricher.enrich({}, comment)
        assert result is None

    def test_empty_comment(self, enricher):
        """Test that None is returned for empty comment."""
        comment = ""
        result = enricher.enrich({}, comment)
        assert result is None

    def test_real_world_examples(self, enricher):
        """Test with real-world comment examples."""
        test_cases = [
            ("Gillette Super Speed Red", "Red"),
            ("Super Speed Blue", "Blue"),
            ("Gillette Super Speed Black", "Black"),
            ("Super Speed Flare", "Flare"),
            ("Gillette Super Speed Flair", "Flare"),
        ]

        for comment, expected in test_cases:
            result = enricher.enrich({}, comment)
            assert result is not None, f"Failed for comment: {comment}"
            if "Flare" in comment or "Flair" in comment:
                assert result["tip_variant"] == expected, f"Failed for comment: {comment}"
            else:
                assert result["tip_color"] == expected, f"Failed for comment: {comment}"

    def test_enrich_preserves_field_data(self, enricher):
        """Test that field_data is preserved when enriching."""
        field_data = {"brand": "Gillette", "model": "Super Speed"}
        comment = "Gillette Super Speed Red"

        result = enricher.enrich(field_data, comment)

        assert result is not None
        assert result["tip_color"] == "Red"
        # Field data should not be modified
        assert field_data == {"brand": "Gillette", "model": "Super Speed"}
