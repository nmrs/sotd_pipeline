import pytest

from sotd.enrich.enricher import BaseEnricher


class TestEnricher(BaseEnricher):
    """Test implementation of BaseEnricher for testing."""

    @property
    def target_field(self) -> str:
        return "test_field"

    def applies_to(self, record):
        return "test_field" in record and record["test_field"] is not None

    def enrich(self, field_data, original_comment):
        return {
            "test_value": "enriched",
            "_enriched_by": self.get_enricher_name(),
            "_extraction_source": "user_comment",
        }


class TestBaseEnricher:
    """Test cases for the BaseEnricher abstract class."""

    def test_target_field_property(self):
        """Test that target_field property is implemented."""
        enricher = TestEnricher()
        assert enricher.target_field == "test_field"

    def test_applies_to_method(self):
        """Test that applies_to method works correctly."""
        enricher = TestEnricher()

        # Should apply when field exists and is not None
        record = {"test_field": {"brand": "test"}}
        assert enricher.applies_to(record) is True

        # Should not apply when field is None
        record = {"test_field": None}
        assert enricher.applies_to(record) is False

        # Should not apply when field doesn't exist
        record = {"other_field": "test"}
        assert enricher.applies_to(record) is False

    def test_enrich_method(self):
        """Test that enrich method returns expected structure."""
        enricher = TestEnricher()
        field_data = {"brand": "test"}
        original_comment = "test comment"

        result = enricher.enrich(field_data, original_comment)

        assert result is not None
        assert "test_value" in result
        assert result["test_value"] == "enriched"
        assert "_enriched_by" in result
        assert result["_enriched_by"] == "TestEnricher"
        assert "_extraction_source" in result
        assert result["_extraction_source"] == "user_comment"

    def test_get_enricher_name(self):
        """Test that get_enricher_name returns class name."""
        enricher = TestEnricher()
        assert enricher.get_enricher_name() == "TestEnricher"

    def test_base_enricher_is_abstract(self):
        """Test that BaseEnricher is properly abstract."""
        # Check that BaseEnricher has abstract methods
        assert hasattr(BaseEnricher, "__abstractmethods__")
        assert len(BaseEnricher.__abstractmethods__) > 0

        # Verify that target_field, applies_to, and enrich are abstract
        abstract_methods = BaseEnricher.__abstractmethods__
        assert "target_field" in abstract_methods
        assert "applies_to" in abstract_methods
        assert "enrich" in abstract_methods
