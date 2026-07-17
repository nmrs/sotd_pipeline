import pytest

from sotd.enrich.super_speed_variant_enricher import SuperSpeedVariantEnricher


class TestSuperSpeedVariantEnricher:
    """Test cases for SuperSpeedVariantEnricher."""

    @pytest.fixture
    def enricher(self):
        return SuperSpeedVariantEnricher()

    def test_target_field(self, enricher):
        assert enricher.target_field == "razor"

    def test_applies_to_gillette_super_speed(self, enricher):
        record = {"razor": {"matched": {"brand": "Gillette", "model": "Super Speed"}}}
        assert enricher.applies_to(record) is True

    def test_does_not_apply_to_other_gillette(self, enricher):
        record = {"razor": {"matched": {"brand": "Gillette", "model": "Tech"}}}
        assert enricher.applies_to(record) is False

    def test_does_not_apply_to_other_brands(self, enricher):
        record = {"razor": {"matched": {"brand": "RazoRock", "model": "Game Changer"}}}
        assert enricher.applies_to(record) is False

    def test_does_not_apply_to_no_razor(self, enricher):
        record = {"blade": {"matched": {"brand": "Feather"}}}
        assert enricher.applies_to(record) is False

    def test_does_not_apply_to_none_razor(self, enricher):
        record = {"razor": None}
        assert enricher.applies_to(record) is False

    def test_does_not_apply_to_invalid_razor_structure(self, enricher):
        record = {"razor": "not a dict"}
        assert enricher.applies_to(record) is False

    def test_does_not_apply_to_no_matched_data(self, enricher):
        record = {"razor": {}}
        assert enricher.applies_to(record) is False

    def test_empty_comment_returns_none(self, enricher):
        assert enricher.enrich({}, "") is None

    @pytest.mark.parametrize(
        "comment,expected",
        [
            # TV Special
            ("Gillette TV Special", "TV Special"),
            ("1958 TV Special", "TV Special"),
            ("Gillette TV Superspeed", "TV Special"),
            ("Gillette TV Super Speed", "TV Special"),
            # Red Tip
            ("Gillette Red Tip", "Red Tip"),
            ("Gillette Red Tip Super Speed", "Red Tip"),
            ("1958 Heavy Super Speed", "Red Tip"),
            ("Gillette Redtip Super Speed", "Red Tip"),
            ("Gillette Super Speed Red", "Red Tip"),
            ("Red Super Speed", "Red Tip"),
            # Blue Tip
            ("Gillette Blue Tip", "Blue Tip"),
            ("Blue Tip Super Speed", "Blue Tip"),
            ("Gillette Bluetip Super Speed", "Blue Tip"),
            ("Gillette Super Speed Blue", "Blue Tip"),
            ("Blue Super Speed", "Blue Tip"),
            # Black Handle
            ("Black Handled Super Speed", "Black Handle"),
            ("1976 Gillette Super Speed Black Handle", "Black Handle"),
            ("Birth Quarter Black Handled Superspeed", "Black Handle"),
            ("Black-Handled Super Speed", "Black Handle"),
            # Black Tip
            ("1951 Black Tip", "Black Tip"),
            ("Black Tip Super Speed", "Black Tip"),
            ("Gillette - Blacktip 1952.", "Black Tip"),
            # Flare Tip
            ("Flare Tip Super Speed", "Flare Tip"),
            ("Gillette Flare Tip", "Flare Tip"),
            ("Gillette Flair Tip", "Flare Tip"),
            ("Gillette Flaretip Super Speed", "Flare Tip"),
            ("Gillette Flairtip 1962.", "Flare Tip"),
            # 40's Style (NDC)
            ("40's Style Super Speed", "40's Style (NDC)"),
            ("40s NDC", "40's Style (NDC)"),
            ("Forties Super Speed", "40's Style (NDC)"),
            ("Pre-Date Code Super Speed", "40's Style (NDC)"),
            ("Pre Date Code Super Speed", "40's Style (NDC)"),
            ("No Date Code Super Speed", "40's Style (NDC)"),
            ("NDC Super Speed", "40's Style (NDC)"),
        ],
    )
    def test_explicit_variant_detection(self, enricher, comment, expected):
        result = enricher.enrich({}, comment)
        assert result is not None
        assert result["super_speed_variant"] == expected
        assert result["_enriched_by"] == "SuperSpeedVariantEnricher"
        assert result["_extraction_source"] == "user_comment"

    @pytest.mark.parametrize(
        "comment,expected",
        [
            # Precedence: TV Special over Red Tip / Flare Tip year
            ("1958 TV Special Red Tip", "TV Special"),
            ("1958 Gillette Red Tip Super Speed", "Red Tip"),
            ("1958 Gillette Blue Tip", "Blue Tip"),
            ("1951 Black Tip Super Speed", "Black Tip"),
            ("Black Tip Black Handle Super Speed", "Black Handle"),
            ("Gillette Super Speed Red Flare", "Red Tip"),
        ],
    )
    def test_precedence_order(self, enricher, comment, expected):
        result = enricher.enrich({}, comment)
        assert result is not None
        assert result["super_speed_variant"] == expected

    @pytest.mark.parametrize(
        "comment,expected",
        [
            ("1947 Super Speed", "40's Style (NDC)"),
            ("1948 Super Speed", "40's Style (NDC)"),
            ("1949 Super Speed", "40's Style (NDC)"),
            ("1950 Super Speed", "40's Style (NDC)"),
            ("1951 Gillette Super Speed", "Unknown"),
            ("1952 Gillette Super Speed", "Unknown"),
            ("1953 Gillette Super Speed", "Unknown"),
            ("1954 Super Speed", "Flare Tip"),
            ("1955 Super Speed", "Flare Tip"),
            ("1958 Super Speed", "Flare Tip"),
            ("1959 Super Speed", "Flare Tip"),
            ("1961 Super Speed", "Flare Tip"),
            ("1962 Super Speed", "Flare Tip"),
            ("1964 Super Speed", "Flare Tip"),
            ("1966 Super Speed", "Flare Tip"),
            ("1972 Super Speed", "Unknown"),
            ("1976 Super Speed", "Unknown"),
            ("1980 Super Speed", "Unknown"),
        ],
    )
    def test_year_inference(self, enricher, comment, expected):
        result = enricher.enrich({}, comment)
        assert result is not None
        assert result["super_speed_variant"] == expected

    @pytest.mark.parametrize(
        "comment",
        [
            "Gillette Super Speed Black",
            "Super Speed Black",
            "Black Super Speed",
            "1968 Super Speed Silver Tip",
            "Gillette Silver Tip Super Speed",
            "Regular Super Speed",
            "Standard Super Speed",
            "Gillette Super Speed",
        ],
    )
    def test_unknown_cases(self, enricher, comment):
        result = enricher.enrich({}, comment)
        assert result is not None
        assert result["super_speed_variant"] == "Unknown"

    def test_enrich_preserves_field_data(self, enricher):
        field_data = {"brand": "Gillette", "model": "Super Speed"}
        comment = "Gillette Super Speed Red Tip"
        result = enricher.enrich(field_data, comment)
        assert result is not None
        assert result["super_speed_variant"] == "Red Tip"
        assert field_data == {"brand": "Gillette", "model": "Super Speed"}
