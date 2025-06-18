import pytest

from sotd.enrich.super_speed_tip_enricher import SuperSpeedTipEnricher


class TestSuperSpeedTipEnricher:
    """Test cases for SuperSpeedTipEnricher (single mutually exclusive tip type)."""

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

    @pytest.mark.parametrize(
        "comment,expected",
        [
            ("Gillette Super Speed Red", "Red"),
            ("Gillette Super Speed Blue", "Blue"),
            ("Gillette Super Speed Black", "Black"),
            ("Gillette Super Speed Flare", "Flare"),
            ("Gillette Super Speed Flair", "Flare"),
            ("Super Speed Blue", "Blue"),
            ("Super Speed Flare", "Flare"),
            ("Super Speed Flair", "Flare"),
        ],
    )
    def test_extract_tip_type(self, enricher, comment, expected):
        """Test extraction of tip type (Red, Blue, Black, Flare/Flair)."""
        result = enricher.enrich({}, comment)
        assert result is not None
        assert result["super_speed_tip"] == expected
        assert result["_enriched_by"] == "SuperSpeedTipEnricher"
        assert result["_extraction_source"] == "user_comment"

    def test_mutual_exclusivity(self, enricher):
        """Test that only one tip type is set, even if multiple keywords are present (first match wins)."""
        # If both Red and Flare are present, Red should be returned (first match wins)
        comment = "Gillette Super Speed Red Flare"
        result = enricher.enrich({}, comment)
        assert result is not None
        assert result["super_speed_tip"] == "Red"
        # Only _enriched_by, _extraction_source, super_speed_tip
        assert len(result) == 3

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

    def test_enrich_preserves_field_data(self, enricher):
        """Test that field_data is preserved when enriching."""
        field_data = {"brand": "Gillette", "model": "Super Speed"}
        comment = "Gillette Super Speed Red"
        result = enricher.enrich(field_data, comment)
        assert result is not None
        assert result["super_speed_tip"] == "Red"
        # Field data should not be modified
        assert field_data == {"brand": "Gillette", "model": "Super Speed"}
