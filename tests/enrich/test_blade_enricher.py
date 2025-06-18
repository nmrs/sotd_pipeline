import pytest

from sotd.enrich.blade_enricher import BladeCountEnricher


class TestBladeCountEnricher:
    """Test cases for the BladeCountEnricher."""

    @pytest.fixture
    def enricher(self):
        """Create a BladeCountEnricher instance for testing."""
        return BladeCountEnricher()

    def test_target_field(self, enricher):
        """Test that target_field returns 'blade'."""
        assert enricher.target_field == "blade"

    def test_applies_to_with_blade(self, enricher):
        """Test applies_to when record has a blade field."""
        record = {"blade": {"matched": {"brand": "Astra", "model": "SP"}}}
        assert enricher.applies_to(record) is True

    def test_applies_to_without_blade(self, enricher):
        """Test applies_to when record has no blade field."""
        record = {"razor": {"matched": {"brand": "Merkur", "model": "34C"}}}
        assert enricher.applies_to(record) is False

    def test_applies_to_with_none_blade(self, enricher):
        """Test applies_to when blade field is None."""
        record = {"blade": None}
        assert enricher.applies_to(record) is False

    def test_enrich_with_parentheses_count(self, enricher):
        """Test extraction of use count in parentheses format."""
        field_data = {"brand": "Astra", "model": "SP"}
        blade_extracted = "Astra SP (3)"

        result = enricher.enrich(field_data, blade_extracted)

        assert result is not None
        assert result["use_count"] == 3
        assert result["_enriched_by"] == "BladeCountEnricher"
        assert result["_extraction_source"] == "user_comment"

    def test_enrich_with_brackets_count(self, enricher):
        """Test extraction of use count in brackets format."""
        field_data = {"brand": "Feather", "model": "Hi-Stainless"}
        blade_extracted = "Feather [5]"

        result = enricher.enrich(field_data, blade_extracted)

        assert result is not None
        assert result["use_count"] == 5
        assert result["_enriched_by"] == "BladeCountEnricher"
        assert result["_extraction_source"] == "user_comment"

    def test_enrich_with_braces_count(self, enricher):
        """Test extraction of use count in braces format."""
        field_data = {"brand": "Gillette", "model": "Platinum"}
        blade_extracted = "Gillette Platinum {2}"

        result = enricher.enrich(field_data, blade_extracted)

        assert result is not None
        assert result["use_count"] == 2
        assert result["_enriched_by"] == "BladeCountEnricher"
        assert result["_extraction_source"] == "user_comment"

    def test_enrich_with_x_prefix(self, enricher):
        """Test extraction of use count with x prefix."""
        field_data = {"brand": "Personna", "model": "Platinum"}
        blade_extracted = "Personna x4"

        result = enricher.enrich(field_data, blade_extracted)

        assert result is not None
        assert result["use_count"] == 4
        assert result["_enriched_by"] == "BladeCountEnricher"
        assert result["_extraction_source"] == "user_comment"

    def test_enrich_with_x_suffix(self, enricher):
        """Test extraction of use count with x suffix."""
        field_data = {"brand": "Voskhod", "model": "Teflon Coated"}
        blade_extracted = "Voskhod 2x"

        result = enricher.enrich(field_data, blade_extracted)

        assert result is not None
        assert result["use_count"] == 2
        assert result["_enriched_by"] == "BladeCountEnricher"
        assert result["_extraction_source"] == "user_comment"

    def test_enrich_with_parentheses_and_x(self, enricher):
        """Test extraction of use count with parentheses and x."""
        field_data = {"brand": "Derby", "model": "Extra"}
        blade_extracted = "Derby (x2)"

        result = enricher.enrich(field_data, blade_extracted)

        assert result is not None
        assert result["use_count"] == 2
        assert result["_enriched_by"] == "BladeCountEnricher"
        assert result["_extraction_source"] == "user_comment"

    def test_enrich_with_no_count(self, enricher):
        """Test enrichment when no use count is found."""
        field_data = {"brand": "Astra", "model": "SP"}
        blade_extracted = "Astra SP"

        result = enricher.enrich(field_data, blade_extracted)

        assert result is None

    def test_enrich_with_multiple_numbers(self, enricher):
        """Test extraction when multiple numbers are present (should get first match)."""
        field_data = {"brand": "Feather", "model": "Hi-Stainless"}
        blade_extracted = "Feather (3) shave #5"

        result = enricher.enrich(field_data, blade_extracted)

        assert result is not None
        assert result["use_count"] == 3

    def test_enrich_with_large_number(self, enricher):
        """Test extraction with large use count numbers."""
        field_data = {"brand": "Astra", "model": "SP"}
        blade_extracted = "Astra SP (15)"

        result = enricher.enrich(field_data, blade_extracted)

        assert result is not None
        assert result["use_count"] == 15

    def test_enrich_with_single_digit(self, enricher):
        """Test extraction with single digit use count."""
        field_data = {"brand": "Gillette", "model": "Silver Blue"}
        blade_extracted = "Gillette Silver Blue (1)"

        result = enricher.enrich(field_data, blade_extracted)

        assert result is not None
        assert result["use_count"] == 1

    def test_enrich_case_insensitive(self, enricher):
        """Test that extraction is case insensitive."""
        field_data = {"brand": "Astra", "model": "SP"}
        blade_extracted = "Astra SP (X3)"

        result = enricher.enrich(field_data, blade_extracted)

        assert result is not None
        assert result["use_count"] == 3

    def test_enrich_with_extra_text(self, enricher):
        """Test extraction when count is embedded in longer text."""
        field_data = {"brand": "Feather", "model": "Hi-Stainless"}
        blade_extracted = "Great shave today with Feather [5] blades, really smooth"

        result = enricher.enrich(field_data, blade_extracted)

        assert result is not None
        assert result["use_count"] == 5

    def test_extract_use_count_method(self, enricher):
        """Test the _extract_use_count method directly."""
        # Test various formats
        assert enricher._extract_use_count("Astra SP (3)") == 3
        assert enricher._extract_use_count("Feather [5]") == 5
        assert enricher._extract_use_count("Gillette {2}") == 2
        assert enricher._extract_use_count("Personna x4") == 4
        assert enricher._extract_use_count("Derby (x2)") == 2
        assert enricher._extract_use_count("Voskhod 2x") == 2

        # Test no match cases
        assert enricher._extract_use_count("Astra SP") is None
        assert enricher._extract_use_count("") is None
        assert enricher._extract_use_count("Just text with no numbers") is None

    def test_extract_use_count_edge_cases(self, enricher):
        """Test edge cases for use count extraction."""
        # Test with leading/trailing whitespace
        assert enricher._extract_use_count("  Astra SP (3)  ") == 3

        # Test with mixed case
        assert enricher._extract_use_count("Astra SP (X3)") == 3
        assert enricher._extract_use_count("Astra SP (x3)") == 3

        # Test with multiple matches (should get first)
        assert enricher._extract_use_count("Astra SP (3) shave #5") == 3

    # Additional tests to validate against original blade matcher behavior
    def test_original_blade_matcher_compatibility_parentheses(self, enricher):
        """Test compatibility with original blade matcher parentheses format."""
        field_data = {"brand": "Feather", "model": "DE"}
        blade_extracted = "Feather (3)"

        result = enricher.enrich(field_data, blade_extracted)

        assert result is not None
        assert result["use_count"] == 3

    def test_original_blade_matcher_compatibility_brackets(self, enricher):
        """Test compatibility with original blade matcher brackets format."""
        field_data = {"brand": "Astra", "model": "SP"}
        blade_extracted = "Astra SP [5]"

        result = enricher.enrich(field_data, blade_extracted)

        assert result is not None
        assert result["use_count"] == 5

    def test_original_blade_matcher_compatibility_curly_braces(self, enricher):
        """Test compatibility with original blade matcher curly braces format."""
        field_data = {"brand": "Derby", "model": "Extra"}
        blade_extracted = "Derby Extra {7}"

        result = enricher.enrich(field_data, blade_extracted)

        assert result is not None
        assert result["use_count"] == 7

    def test_original_blade_matcher_compatibility_x_prefix(self, enricher):
        """Test compatibility with original blade matcher x prefix format."""
        field_data = {"brand": "Feather", "model": "DE"}
        blade_extracted = "Feather (x3)"

        result = enricher.enrich(field_data, blade_extracted)

        assert result is not None
        assert result["use_count"] == 3

    def test_original_blade_matcher_compatibility_x_suffix(self, enricher):
        """Test compatibility with original blade matcher x suffix format."""
        field_data = {"brand": "Astra", "model": "SP"}
        blade_extracted = "Astra SP [5x]"

        result = enricher.enrich(field_data, blade_extracted)

        assert result is not None
        assert result["use_count"] == 5

    def test_original_blade_matcher_compatibility_uppercase_x(self, enricher):
        """Test compatibility with original blade matcher uppercase X format."""
        field_data = {"brand": "Derby", "model": "Extra"}
        blade_extracted = "Derby Extra (2X)"

        result = enricher.enrich(field_data, blade_extracted)

        assert result is not None
        assert result["use_count"] == 2

    def test_original_blade_matcher_compatibility_no_count(self, enricher):
        """Test compatibility with original blade matcher no count format."""
        field_data = {"brand": "Derby", "model": "Extra"}
        blade_extracted = "Derby Extra"

        result = enricher.enrich(field_data, blade_extracted)

        assert result is None

    def test_enrich_with_real_world_examples(self, enricher):
        """Test with real-world comment examples."""
        test_cases = [
            ("Astra SP (3)", 3),
            ("Feather [5]", 5),
            ("Gillette Platinum {2}", 2),
            ("Personna x4", 4),
            ("Derby (x2)", 2),
            ("Voskhod 2x", 2),
            ("Astra SP [5x]", 5),
            ("Derby Extra (2X)", 2),
            ("Great shave with Feather (3) today", 3),
            ("Using Astra SP [5] for the first time", 5),
            ("Derby Extra {7} - still going strong", 7),
        ]

        for comment, expected_count in test_cases:
            field_data = {"brand": "Test", "model": "Blade"}
            blade_extracted = comment
            result = enricher.enrich(field_data, blade_extracted)

            assert result is not None, f"Failed to extract count from: {comment}"
            assert (
                result["use_count"] == expected_count
            ), f"Expected {expected_count}, got {result['use_count']} for: {comment}"
            assert result["_enriched_by"] == "BladeCountEnricher"
            assert result["_extraction_source"] == "user_comment"
