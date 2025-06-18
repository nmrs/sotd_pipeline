import pytest

from sotd.enrich.enricher import BaseEnricher
from sotd.enrich.registry import EnricherRegistry


class MockBladeEnricher(BaseEnricher):
    """Mock blade enricher for testing."""

    @property
    def target_field(self) -> str:
        return "blade"

    def applies_to(self, record):
        return "blade" in record and record["blade"] is not None

    def enrich(self, field_data, original_comment):
        return {
            "use_count": 3,
            "_enriched_by": self.get_enricher_name(),
            "_extraction_source": "user_comment",
        }


class MockRazorEnricher(BaseEnricher):
    """Mock razor enricher for testing."""

    @property
    def target_field(self) -> str:
        return "razor"

    def applies_to(self, record):
        return "razor" in record and record["razor"] is not None

    def enrich(self, field_data, original_comment):
        return {
            "grind": "full_hollow",
            "_enriched_by": self.get_enricher_name(),
            "_extraction_source": "user_comment",
        }


class TestEnricherRegistry:
    """Test cases for the EnricherRegistry class."""

    def test_register_enricher(self):
        """Test that enrichers can be registered."""
        registry = EnricherRegistry()
        enricher = MockBladeEnricher()

        registry.register(enricher)

        assert len(registry.get_all_enrichers()) == 1
        assert registry.get_enrichers_for_field("blade") == [enricher]

    def test_register_multiple_enrichers_same_field(self):
        """Test that multiple enrichers for the same field can be registered."""
        registry = EnricherRegistry()
        enricher1 = MockBladeEnricher()
        enricher2 = MockBladeEnricher()  # Different instance

        registry.register(enricher1)
        registry.register(enricher2)

        blade_enrichers = registry.get_enrichers_for_field("blade")
        assert len(blade_enrichers) == 2
        assert enricher1 in blade_enrichers
        assert enricher2 in blade_enrichers

    def test_register_enrichers_different_fields(self):
        """Test that enrichers for different fields can be registered."""
        registry = EnricherRegistry()
        blade_enricher = MockBladeEnricher()
        razor_enricher = MockRazorEnricher()

        registry.register(blade_enricher)
        registry.register(razor_enricher)

        assert len(registry.get_all_enrichers()) == 2
        assert registry.get_enrichers_for_field("blade") == [blade_enricher]
        assert registry.get_enrichers_for_field("razor") == [razor_enricher]

    def test_register_invalid_enricher(self):
        """Test that registering non-BaseEnricher raises error."""
        registry = EnricherRegistry()

        with pytest.raises(ValueError, match="Enricher must inherit from BaseEnricher"):
            registry.register("not an enricher")  # type: ignore

    def test_get_enrichers_for_nonexistent_field(self):
        """Test that getting enrichers for nonexistent field returns empty list."""
        registry = EnricherRegistry()

        result = registry.get_enrichers_for_field("nonexistent")
        assert result == []

    def test_enrich_single_record(self):
        """Test enriching a single record."""
        registry = EnricherRegistry()
        blade_enricher = MockBladeEnricher()
        registry.register(blade_enricher)

        record = {
            "comment_id": "test123",
            "blade": {"brand": "Astra", "model": "Superior Platinum"},
        }
        original_comment = "Using Astra blade for the 3rd time"

        result = registry.enrich_record(record, original_comment)

        assert "enriched" in result
        assert "blade" in result["enriched"]
        assert result["enriched"]["blade"]["use_count"] == 3
        assert result["enriched"]["blade"]["_enriched_by"] == "MockBladeEnricher"

    def test_enrich_record_no_applicable_enrichers(self):
        """Test enriching a record with no applicable enrichers."""
        registry = EnricherRegistry()
        blade_enricher = MockBladeEnricher()
        registry.register(blade_enricher)

        record = {"comment_id": "test123", "razor": {"brand": "Merkur", "model": "34C"}}
        original_comment = "Using Merkur razor"

        result = registry.enrich_record(record, original_comment)

        # Should return original record unchanged
        assert result == record
        assert "enriched" not in result

    def test_enrich_record_missing_field(self):
        """Test enriching a record with missing target field."""
        registry = EnricherRegistry()
        blade_enricher = MockBladeEnricher()
        registry.register(blade_enricher)

        record = {"comment_id": "test123", "razor": {"brand": "Merkur", "model": "34C"}}
        original_comment = "Using Merkur razor"

        result = registry.enrich_record(record, original_comment)

        # Should return original record unchanged
        assert result == record
        assert "enriched" not in result

    def test_enrich_multiple_records(self):
        """Test enriching multiple records."""
        registry = EnricherRegistry()
        blade_enricher = MockBladeEnricher()
        razor_enricher = MockRazorEnricher()
        registry.register(blade_enricher)
        registry.register(razor_enricher)

        records = [
            {"comment_id": "test1", "blade": {"brand": "Astra", "model": "Superior Platinum"}},
            {"comment_id": "test2", "razor": {"brand": "Dovo", "model": "Straight Razor"}},
        ]
        original_comments = ["Using Astra blade for the 3rd time", "Using Dovo straight razor"]

        results = registry.enrich_records(records, original_comments)

        assert len(results) == 2
        assert "enriched" in results[0]
        assert "blade" in results[0]["enriched"]
        assert "enriched" in results[1]
        assert "razor" in results[1]["enriched"]

    def test_enrich_records_length_mismatch(self):
        """Test that mismatched record and comment lengths raise error."""
        registry = EnricherRegistry()

        records = [{"comment_id": "test1"}]
        original_comments = ["comment1", "comment2"]

        with pytest.raises(
            ValueError, match="Records and original_comments must have the same length"
        ):
            registry.enrich_records(records, original_comments)

    def test_enrich_record_enricher_error_handling(self):
        """Test that enricher errors are handled gracefully."""
        registry = EnricherRegistry()

        class FailingEnricher(BaseEnricher):
            @property
            def target_field(self) -> str:
                return "blade"

            def applies_to(self, record):
                return True

            def enrich(self, field_data, original_comment):
                raise Exception("Test error")

        failing_enricher = FailingEnricher()
        registry.register(failing_enricher)

        record = {
            "comment_id": "test123",
            "blade": {"brand": "Astra", "model": "Superior Platinum"},
        }
        original_comment = "Using Astra blade"

        # Should not raise exception, should return original record
        result = registry.enrich_record(record, original_comment)
        assert result == record
