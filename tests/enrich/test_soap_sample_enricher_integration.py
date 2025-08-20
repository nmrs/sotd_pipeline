#!/usr/bin/env python3
"""Integration tests for SoapSampleEnricher in the enrich phase."""

from sotd.enrich.enrich import setup_enrichers
from sotd.enrich.registry import enricher_registry


class TestSoapSampleEnricherIntegration:
    """Test that SoapSampleEnricher integrates correctly with the enrich phase."""

    def test_enricher_registered(self):
        """Test that SoapSampleEnricher is properly registered."""
        # Reset enrichers to ensure clean state
        enricher_registry._enrichers.clear()
        enricher_registry._enrichers_by_field.clear()

        # Reset the global setup flag to allow re-registration
        import sotd.enrich.enrich

        sotd.enrich.enrich._enrichers_setup = False

        # Setup enrichers
        setup_enrichers()

        # Check that SoapSampleEnricher is registered
        soap_enrichers = enricher_registry.get_enrichers_for_field("soap")
        assert len(soap_enrichers) > 0, "No soap enrichers found"

        # Check that at least one is SoapSampleEnricher
        soap_enricher_names = [e.get_enricher_name() for e in soap_enrichers]
        assert (
            "SoapSampleEnricher" in soap_enricher_names
        ), f"SoapSampleEnricher not found in {soap_enricher_names}"

    def test_enricher_applies_to_soap_records(self):
        """Test that SoapSampleEnricher applies to soap records."""
        # Reset and setup enrichers
        enricher_registry._enrichers.clear()
        enricher_registry._enrichers_by_field.clear()

        # Reset the global setup flag
        import sotd.enrich.enrich

        sotd.enrich.enrich._enrichers_setup = False

        setup_enrichers()

        # Get soap enrichers
        soap_enrichers = enricher_registry.get_enrichers_for_field("soap")
        soap_sample_enricher = None

        for enricher in soap_enrichers:
            if enricher.get_enricher_name() == "SoapSampleEnricher":
                soap_sample_enricher = enricher
                break

        assert soap_sample_enricher is not None, "SoapSampleEnricher not found"

        # Test that it applies to records with soap
        record_with_soap = {
            "soap": {
                "original": "B&M Seville (sample)",
                "normalized": "B&M Seville",
                "matched": {"brand": "B&M", "scent": "Seville"},
            }
        }

        assert soap_sample_enricher.applies_to(
            record_with_soap
        ), "Should apply to records with soap"

        # Test that it doesn't apply to records without soap
        record_without_soap = {
            "razor": {
                "original": "Merkur 34C",
                "matched": {"brand": "Merkur", "model": "34C"},
            }
        }

        assert not soap_sample_enricher.applies_to(
            record_without_soap
        ), "Should not apply to records without soap"

    def test_enricher_enriches_soap_data(self):
        """Test that SoapSampleEnricher actually enriches soap data."""
        # Reset and setup enrichers
        enricher_registry._enrichers.clear()
        enricher_registry._enrichers_by_field.clear()

        # Reset the global setup flag
        import sotd.enrich.enrich

        sotd.enrich.enrich._enrichers_setup = False

        setup_enrichers()

        # Get soap enrichers
        soap_enrichers = enricher_registry.get_enrichers_for_field("soap")
        soap_sample_enricher = None

        for enricher in soap_enrichers:
            if enricher.get_enricher_name() == "SoapSampleEnricher":
                soap_sample_enricher = enricher
                break

        assert soap_sample_enricher is not None, "SoapSampleEnricher not found"

        # Test enrichment
        field_data = {
            "original": "B&M Seville (sample)",
            "normalized": "B&M Seville",
            "matched": {"brand": "B&M", "scent": "Seville"},
        }
        original_comment = "B&M Seville (sample)"

        enriched_data = soap_sample_enricher.enrich(field_data, original_comment)

        assert enriched_data is not None, "Should return enriched data"
        assert "sample_type" in enriched_data, "Should include sample_type"
        assert enriched_data["sample_type"] == "sample", "Should detect sample type"
        assert (
            enriched_data["extraction_remainder"] == "(sample)"
        ), "Should include extraction remainder"
