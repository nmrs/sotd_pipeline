import pytest

from sotd.enrich.straight_razor_enricher import StraightRazorEnricher


class TestStraightRazorEnricher:
    """Test cases for StraightRazorEnricher."""

    @pytest.fixture
    def enricher(self):
        """Create a StraightRazorEnricher instance for testing."""
        return StraightRazorEnricher()

    def test_target_field(self, enricher):
        """Test that the target field is correctly set to 'razor'."""
        assert enricher.target_field == "razor"

    def test_applies_to_straight_format(self, enricher):
        """Test that enricher applies to records with format: Straight."""
        record = {"razor": {"matched": {"format": "Straight"}}}
        assert enricher.applies_to(record) is True

    def test_applies_to_straight_brand(self, enricher):
        """Test that enricher applies to records with format: Straight."""
        record = {"razor": {"matched": {"format": "Straight"}}}
        assert enricher.applies_to(record) is True

    def test_applies_to_straight_in_model(self, enricher):
        """Test that enricher applies to records with format: Straight."""
        record = {"razor": {"matched": {"format": "Straight"}}}
        assert enricher.applies_to(record) is True

    def test_does_not_apply_to_non_straight(self, enricher):
        """Test that enricher does not apply to non-straight razors."""
        record = {"razor": {"matched": {"brand": "Gillette", "model": "Super Speed"}}}
        assert enricher.applies_to(record) is False

    def test_does_not_apply_to_no_razor(self, enricher):
        """Test that enricher does not apply when no razor is present."""
        record = {"blade": {"matched": {"brand": "Feather"}}}
        assert enricher.applies_to(record) is False

    def test_does_not_apply_to_none_razor(self, enricher):
        """Test that enricher does not apply when razor is None."""
        record = {"razor": None}
        assert enricher.applies_to(record) is False

    def test_extract_grind_full_hollow(self, enricher):
        """Test extraction of full hollow grind."""
        comment = "Using my full hollow straight razor today"
        result = enricher.enrich({}, comment)
        assert result is not None
        assert result["grind"] == "Full Hollow"
        assert result["_enriched_by"] == "StraightRazorEnricher"
        assert result["_extraction_source"] == "user_comment"

    def test_extract_grind_half_hollow(self, enricher):
        """Test extraction of half hollow grind."""
        comment = "Half hollow grind provides great feedback"
        result = enricher.enrich({}, comment)
        assert result is not None
        assert result["grind"] == "Half Hollow"

    def test_extract_grind_quarter_hollow(self, enricher):
        """Test extraction of quarter hollow grind."""
        comment = "Quarter hollow grind is perfect for beginners"
        result = enricher.enrich({}, comment)
        assert result is not None
        assert result["grind"] == "Quarter Hollow"

    def test_extract_grind_three_quarter_hollow(self, enricher):
        """Test extraction of three quarter hollow grind."""
        comment = "Three quarter hollow grind offers good balance"
        result = enricher.enrich({}, comment)
        assert result is not None
        assert result["grind"] == "Three Quarter Hollow"

    def test_extract_grind_generic_hollow(self, enricher):
        """Test extraction of generic hollow grind."""
        comment = "Hollow grind razors are very common"
        result = enricher.enrich({}, comment)
        assert result is not None
        assert result["grind"] == "Hollow"

    def test_extract_grind_wedge(self, enricher):
        """Test extraction of wedge grind."""
        comment = "Wedge grind provides excellent stability"
        result = enricher.enrich({}, comment)
        assert result is not None
        assert result["grind"] == "Wedge"

    def test_extract_grind_frameback(self, enricher):
        """Test extraction of frameback grind."""
        comment = "Frameback grind is a unique design"
        result = enricher.enrich({}, comment)
        assert result is not None
        assert result["grind"] == "Frameback"

    def test_extract_grind_extra_hollow(self, enricher):
        """Test extraction of extra hollow grind."""
        comment = "Extra hollow grind provides excellent flexibility"
        result = enricher.enrich({}, comment)
        assert result is not None
        assert result["grind"] == "Extra Hollow"

    def test_extract_grind_pretty_hollow(self, enricher):
        """Test extraction of pretty hollow grind."""
        comment = "Pretty hollow grind is a nice middle ground"
        result = enricher.enrich({}, comment)
        assert result is not None
        assert result["grind"] == "Pretty Hollow"

    def test_extract_grind_near_wedge(self, enricher):
        """Test extraction of near wedge grind."""
        comment = "Near wedge grind offers good stability"
        result = enricher.enrich({}, comment)
        assert result is not None
        assert result["grind"] == "Near Wedge"

    def test_extract_width_fractional_eighths(self, enricher):
        """Test extraction of width in fractional eighths."""
        test_cases = [
            ("4/8 straight razor", "4/8"),
            ("5/8 blade", "5/8"),
            ("6/8 razor", "6/8"),
            ("7/8 straight", "7/8"),
            ("8/8 blade", "8/8"),
        ]

        for comment, expected in test_cases:
            result = enricher.enrich({}, comment)
            assert result is not None, f"Failed for comment: {comment}"
            assert result["width"] == expected, f"Failed for comment: {comment}"

    def test_extract_width_fractional_sixteenths(self, enricher):
        """Test extraction of width in fractional sixteenths."""
        test_cases = [
            ("8/16 straight razor", "8/16"),
            ("10/16 blade", "10/16"),
            ("12/16 razor", "12/16"),
            ("14/16 straight", "14/16"),
            ("16/16 blade", "16/16"),
        ]

        for comment, expected in test_cases:
            result = enricher.enrich({}, comment)
            assert result is not None, f"Failed for comment: {comment}"
            assert result["width"] == expected, f"Failed for comment: {comment}"

    def test_extract_width_decimal(self, enricher):
        """Test extraction of width in decimal format."""
        test_cases = [
            ("0.5 inch blade", "4/8"),
            ("0.625 straight", "5/8"),
            ("0.75 razor", "6/8"),
            ("0.875 blade", "7/8"),
            ("1.0 inch straight", "8/8"),
        ]

        for comment, expected in test_cases:
            result = enricher.enrich({}, comment)
            assert result is not None, f"Failed for comment: {comment}"
            assert result["width"] == expected, f"Failed for comment: {comment}"

    def test_extract_point_round(self, enricher):
        """Test extraction of round point."""
        comment = "Round point is very forgiving"
        result = enricher.enrich({}, comment)
        assert result is not None
        assert result["point"] == "Round"

    def test_extract_point_round_point(self, enricher):
        """Test extraction of round point with explicit 'point'."""
        comment = "Round point blade is great for beginners"
        result = enricher.enrich({}, comment)
        assert result is not None
        assert result["point"] == "Round"

    def test_extract_point_square(self, enricher):
        """Test extraction of square point."""
        comment = "Square point offers precise control"
        result = enricher.enrich({}, comment)
        assert result is not None
        assert result["point"] == "Square"

    def test_extract_point_square_point(self, enricher):
        """Test extraction of square point with explicit 'point'."""
        comment = "Square point blade requires careful handling"
        result = enricher.enrich({}, comment)
        assert result is not None
        assert result["point"] == "Square"

    def test_extract_point_french(self, enricher):
        """Test extraction of French point."""
        comment = "French point is very elegant"
        result = enricher.enrich({}, comment)
        assert result is not None
        assert result["point"] == "French"

    def test_extract_point_spanish(self, enricher):
        """Test extraction of Spanish point."""
        comment = "Spanish point is very stylish"
        result = enricher.enrich({}, comment)
        assert result is not None
        assert result["point"] == "Spanish"

    def test_extract_point_barbers_notch(self, enricher):
        """Test extraction of barber's notch."""
        test_cases = [
            "Barber's notch is traditional",
            "Barbers notch is classic",
        ]

        for comment in test_cases:
            result = enricher.enrich({}, comment)
            assert result is not None, f"Failed for comment: {comment}"
            assert result["point"] == "Barber's Notch", f"Failed for comment: {comment}"

    def test_extract_point_spear(self, enricher):
        """Test extraction of spear point."""
        comment = "Spear point is very sharp"
        result = enricher.enrich({}, comment)
        assert result is not None
        assert result["point"] == "Spear"

    def test_extract_combined_specifications(self, enricher):
        """Test extraction of multiple specifications in one comment."""
        comment = "Full hollow 6/8 round point straight razor"
        result = enricher.enrich({}, comment)
        assert result is not None
        assert result["grind"] == "Full Hollow"
        assert result["width"] == "6/8"
        assert result["point"] == "Round"

    def test_extract_partial_specifications(self, enricher):
        """Test extraction when only some specifications are present."""
        comment = "Half hollow 7/8 straight razor"
        result = enricher.enrich({}, comment)
        assert result is not None
        assert result["grind"] == "Half Hollow"
        assert result["width"] == "7/8"
        assert "point" not in result

    def test_no_specifications_found(self, enricher):
        """Test that None is returned when no specifications are found."""
        comment = "Generic straight razor"
        result = enricher.enrich({}, comment)
        assert result is None

    def test_case_insensitive_extraction(self, enricher):
        """Test that extraction works regardless of case."""
        test_cases = [
            ("FULL HOLLOW 6/8 ROUND POINT", "Full Hollow", "6/8", "Round"),
            ("Half Hollow 7/8 Square", "Half Hollow", "7/8", "Square"),
            ("wedge 5/8", "Wedge", "5/8", None),
        ]

        for comment, expected_grind, expected_width, expected_point in test_cases:
            result = enricher.enrich({}, comment)
            assert result is not None, f"Failed for comment: {comment}"
            if expected_grind:
                assert result["grind"] == expected_grind, f"Failed for comment: {comment}"
            if expected_width:
                assert result["width"] == expected_width, f"Failed for comment: {comment}"
            if expected_point:
                assert result["point"] == expected_point, f"Failed for comment: {comment}"

    def test_real_world_examples(self, enricher):
        """Test with real-world comment examples."""
        test_cases = [
            (
                "Dovo Best Quality 6/8 full hollow round point",
                {"grind": "Full Hollow", "width": "6/8", "point": "Round"},
            ),
            (
                "Böker King Cutter 7/8 wedge square point",
                {"grind": "Wedge", "width": "7/8", "point": "Square"},
            ),
            ("Filarmonica 5/8 half hollow", {"grind": "Half Hollow", "width": "5/8"}),
            (
                "Wade & Butcher 8/8 quarter hollow round",
                {"grind": "Quarter Hollow", "width": "8/8", "point": "Round"},
            ),
        ]

        for comment, expected in test_cases:
            result = enricher.enrich({}, comment)
            assert result is not None, f"Failed for comment: {comment}"
            for key, value in expected.items():
                assert result[key] == value, f"Failed for {key} in comment: {comment}"

    def test_enrich_preserves_catalog_data(self, enricher):
        """Test that catalog data is preserved when no user specifications are found."""
        field_data = {
            "brand": "Koraat",
            "model": "Moarteen (r/Wetshaving exclusive)",
            "format": "Straight",
            "grind": "Full Hollow",
            "point": "Square",
            "width": "15/16",
        }
        razor_extracted = field_data["model"]

        result = enricher.enrich(field_data, razor_extracted)

        assert result is not None
        assert result["grind"] == "Full Hollow"
        assert result["point"] == "Square"
        assert result["width"] == "15/16"
        assert result["_extraction_source"] == "catalog_data"

    def test_enrich_merges_user_and_catalog_data(self, enricher):
        """Test that user comment data takes precedence over catalog data."""
        field_data = {
            "brand": "Koraat",
            "model": "Moarteen (r/Wetshaving exclusive)",
            "format": "Straight",
            "grind": "Full Hollow",
            "point": "Square",
            "width": "15/16",
        }
        razor_extracted = "Koraat Moarteen - half hollow 6/8 round point"

        result = enricher.enrich(field_data, razor_extracted)

        assert result is not None
        assert result["grind"] == "Half Hollow"  # User comment takes precedence
        assert result["width"] == "6/8"  # User comment takes precedence
        assert result["point"] == "Round"  # User comment takes precedence
        assert result["_extraction_source"] == "user_comment + catalog_data"

    def test_enrich_partial_user_data_merges_with_catalog(self, enricher):
        """Test that partial user data merges with catalog data."""
        field_data = {
            "brand": "Koraat",
            "model": "Moarteen (r/Wetshaving exclusive)",
            "format": "Straight",
            "grind": "Full Hollow",
            "point": "Square",
            "width": "15/16",
        }
        razor_extracted = "Koraat Moarteen - 7/8"  # Only width specified

        result = enricher.enrich(field_data, razor_extracted)

        assert result is not None
        assert result["grind"] == "Full Hollow"  # From catalog
        assert result["point"] == "Square"  # From catalog
        assert result["width"] == "7/8"  # From user comment
        assert result["_extraction_source"] == "user_comment + catalog_data"

    def test_parse_catalog_width_fractional_eighths(self, enricher):
        """Test parsing catalog width in eighths format."""
        assert enricher._parse_catalog_width("6/8") == 6
        assert enricher._parse_catalog_width("7/8") == 7
        assert enricher._parse_catalog_width("8/8") == 8

    def test_parse_catalog_width_fractional_sixteenths(self, enricher):
        """Test parsing catalog width in sixteenths format."""
        assert enricher._parse_catalog_width("12/16") == 6  # 12/16 = 6/8
        assert enricher._parse_catalog_width("14/16") == 7  # 14/16 = 7/8
        assert enricher._parse_catalog_width("15/16") == 7  # 15/16 = 7.5/8, rounded to 7

    def test_parse_catalog_width_decimal(self, enricher):
        """Test parsing catalog width in decimal format."""
        assert enricher._parse_catalog_width("0.75") == 6  # 0.75 = 6/8
        assert enricher._parse_catalog_width("0.875") == 7  # 0.875 = 7/8
        assert enricher._parse_catalog_width("1.0") == 8  # 1.0 = 8/8

    def test_parse_catalog_width_invalid(self, enricher):
        """Test parsing invalid catalog width values."""
        assert enricher._parse_catalog_width("") is None
        assert enricher._parse_catalog_width("invalid") is None
        assert enricher._parse_catalog_width("3/4") == 6  # 3/4 = 6/8

    def test_enrich_no_specifications_anywhere(self, enricher):
        """Test that no enriched data is returned when no specifications are found."""
        field_data = {"brand": "Generic", "model": "Straight Razor", "format": "Straight"}
        razor_extracted = field_data["model"]

        result = enricher.enrich(field_data, razor_extracted)

        assert result is None

    def test_enrich_catalog_data_only(self, enricher):
        """Test enrichment with only catalog data (no user specifications)."""
        field_data = {
            "brand": "Dovo",
            "model": "Straight",
            "format": "Straight",
            "grind": "Full Hollow",
            "width": "6/8",
        }
        razor_extracted = field_data["model"]

        result = enricher.enrich(field_data, razor_extracted)

        assert result is not None
        assert result["grind"] == "Full Hollow"
        assert result["width"] == "6/8"
        assert "point" not in result
        assert result["_extraction_source"] == "catalog_data"

    def test_enrich_user_data_only(self, enricher):
        """Test enrichment with only user data (no catalog specifications)."""
        field_data = {"brand": "Generic", "model": "Straight Razor", "format": "Straight"}
        razor_extracted = "Generic straight - wedge 7/8 square point"

        result = enricher.enrich(field_data, razor_extracted)

        assert result is not None
        assert result["grind"] == "Wedge"
        assert result["width"] == "7/8"
        assert result["point"] == "Square"
        assert result["_extraction_source"] == "user_comment"

    def test_extract_point_spike(self, enricher):
        """Test extraction of spike point."""
        comment = "Spike point offers precise control"
        result = enricher.enrich({}, comment)
        assert result is not None
        assert result["point"] == "Spike"

    def test_extract_point_spike_point(self, enricher):
        """Test extraction of spike point with explicit 'point'."""
        comment = "Spike point blade requires careful handling"
        result = enricher.enrich({}, comment)
        assert result is not None
        assert result["point"] == "Spike"

    def test_extract_point_round_tip(self, enricher):
        """Test extraction of round point with 'tip' instead of 'point'."""
        comment = "Round tip is very forgiving"
        result = enricher.enrich({}, comment)
        assert result is not None
        assert result["point"] == "Round"

    def test_extract_point_square_tip(self, enricher):
        """Test extraction of square point with 'tip' instead of 'point'."""
        comment = "Square tip offers precise control"
        result = enricher.enrich({}, comment)
        assert result is not None
        assert result["point"] == "Square"

    def test_extract_point_spanish_tip(self, enricher):
        """Test extraction of Spanish point with 'tip' instead of 'point'."""
        comment = "Spanish tip is very stylish"
        result = enricher.enrich({}, comment)
        assert result is not None
        assert result["point"] == "Spanish"
