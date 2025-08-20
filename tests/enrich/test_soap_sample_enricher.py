#!/usr/bin/env python3
"""Tests for the SoapSampleEnricher."""

import pytest

from sotd.enrich.soap_sample_enricher import SoapSampleEnricher


class TestSoapSampleEnricher:
    """Test cases for the SoapSampleEnricher."""

    def test_target_field(self, enricher):
        """Test that target_field returns 'soap'."""
        assert enricher.target_field == "soap"

    def test_applies_to_with_soap(self, enricher):
        """Test applies_to when record has a soap field."""
        record = {"soap": {"matched": {"brand": "B&M", "scent": "Seville"}}}
        assert enricher.applies_to(record) is True

    def test_applies_to_without_soap(self, enricher):
        """Test applies_to when record has no soap field."""
        record = {"razor": {"matched": {"brand": "Merkur", "model": "34C"}}}
        assert enricher.applies_to(record) is False

    def test_applies_to_with_none_soap(self, enricher):
        """Test applies_to when soap field is None."""
        record = {"soap": None}
        assert enricher.applies_to(record) is False

    def test_enrich_with_basic_sample(self, enricher):
        """Test extraction of basic sample pattern."""
        field_data = {
            "original": "B&M Seville (sample)",
            "normalized": "B&M Seville",
            "matched": {"brand": "B&M", "scent": "Seville"},
        }
        original_comment = "B&M Seville (sample)"

        result = enricher.enrich(field_data, original_comment)

        assert result is not None
        assert result["sample_type"] == "sample"
        assert result["sample_number"] is None
        assert result["total_samples"] is None
        assert result["extraction_remainder"] == "(sample)"

    def test_enrich_with_numbered_sample(self, enricher):
        """Test extraction of numbered sample pattern."""
        field_data = {
            "original": "Stirling Bay Rum (sample #23)",
            "normalized": "Stirling Bay Rum",
            "matched": {"brand": "Stirling", "scent": "Bay Rum"},
        }
        original_comment = "Stirling Bay Rum (sample #23)"

        result = enricher.enrich(field_data, original_comment)

        assert result is not None
        assert result["sample_type"] == "sample"
        assert result["sample_number"] == 23
        assert result["total_samples"] is None
        assert result["extraction_remainder"] == "(sample #23)"

    def test_enrich_with_range_sample(self, enricher):
        """Test extraction of range sample pattern."""
        field_data = {
            "original": "Declaration Grooming (sample 5 of 10)",
            "normalized": "Declaration Grooming",
            "matched": {"brand": "Declaration Grooming", "scent": "Unknown"},
        }
        original_comment = "Declaration Grooming (sample 5 of 10)"

        result = enricher.enrich(field_data, original_comment)

        assert result is not None
        assert result["sample_type"] == "sample"
        assert result["sample_number"] == 5
        assert result["total_samples"] == 10
        assert result["extraction_remainder"] == "(sample 5 of 10)"

    def test_enrich_with_fraction_sample(self, enricher):
        """Test extraction of fraction sample pattern."""
        field_data = {
            "original": "Zingari Man (sample 3/15)",
            "normalized": "Zingari Man",
            "matched": {"brand": "Zingari Man", "scent": "Unknown"},
        }
        original_comment = "Zingari Man (sample 3/15)"

        result = enricher.enrich(field_data, original_comment)

        assert result is not None
        assert result["sample_type"] == "sample"
        assert result["sample_number"] == 3
        assert result["total_samples"] == 15
        assert result["extraction_remainder"] == "(sample 3/15)"

    def test_enrich_with_trailing_sample(self, enricher):
        """Test extraction of trailing sample pattern."""
        field_data = {
            "original": "H&M - Seville - sample",
            "normalized": "H&M - Seville",
            "matched": {"brand": "H&M", "scent": "Seville"},
        }
        original_comment = "H&M - Seville - sample"

        result = enricher.enrich(field_data, original_comment)

        assert result is not None
        assert result["sample_type"] == "sample"
        assert result["sample_number"] is None
        assert result["total_samples"] is None
        assert result["extraction_remainder"] == "- sample"

    def test_enrich_with_tester(self, enricher):
        """Test extraction of tester pattern."""
        field_data = {
            "original": "Zingari Man (tester)",
            "normalized": "Zingari Man",
            "matched": {"brand": "Zingari Man", "scent": "Unknown"},
        }
        original_comment = "Zingari Man (tester)"

        result = enricher.enrich(field_data, original_comment)

        assert result is not None
        assert result["sample_type"] == "tester"
        assert result["sample_number"] is None
        assert result["total_samples"] is None
        assert result["extraction_remainder"] == "(tester)"

    def test_enrich_with_samp_abbreviation(self, enricher):
        """Test extraction of samp abbreviation."""
        field_data = {
            "original": "B&M Seville (samp)",
            "normalized": "B&M Seville",
            "matched": {"brand": "B&M", "scent": "Seville"},
        }
        original_comment = "B&M Seville (samp)"

        result = enricher.enrich(field_data, original_comment)

        assert result is not None
        assert result["sample_type"] == "sample"
        assert result["sample_number"] is None
        assert result["total_samples"] is None
        assert result["extraction_remainder"] == "(samp)"

    def test_enrich_with_no_sample(self, enricher):
        """Test when no sample is detected."""
        field_data = {
            "original": "B&M Seville",
            "normalized": "B&M Seville",
            "matched": {"brand": "B&M", "scent": "Seville"},
        }
        original_comment = "B&M Seville"

        result = enricher.enrich(field_data, original_comment)

        assert result is not None
        assert result["sample_type"] is None
        assert result["sample_number"] is None
        assert result["total_samples"] is None
        assert result["extraction_remainder"] == ""

    def test_enrich_with_missing_original(self, enricher):
        """Test when original field is missing."""
        field_data = {
            "normalized": "B&M Seville",
            "matched": {"brand": "B&M", "scent": "Seville"},
        }
        original_comment = "B&M Seville"

        result = enricher.enrich(field_data, original_comment)

        assert result == {}

    def test_enrich_with_missing_normalized(self, enricher):
        """Test when normalized field is missing."""
        field_data = {
            "original": "B&M Seville (sample)",
            "matched": {"brand": "B&M", "scent": "Seville"},
        }
        original_comment = "B&M Seville (sample)"

        result = enricher.enrich(field_data, original_comment)

        assert result == {}

    def test_enrich_with_empty_original(self, enricher):
        """Test when original field is empty."""
        field_data = {
            "original": "",
            "normalized": "B&M Seville",
            "matched": {"brand": "B&M", "scent": "Seville"},
        }
        original_comment = "B&M Seville"

        result = enricher.enrich(field_data, original_comment)

        assert result == {}

    def test_enrich_with_empty_normalized(self, enricher):
        """Test when normalized field is empty."""
        field_data = {
            "original": "B&M Seville (sample)",
            "normalized": "",
            "matched": {"brand": "B&M", "scent": "Seville"},
        }
        original_comment = "B&M Seville (sample)"

        result = enricher.enrich(field_data, original_comment)

        assert result == {}

    def test_enrich_with_case_variations(self, enricher):
        """Test extraction with case variations."""
        field_data = {
            "original": "B&M Seville (SAMPLE)",
            "normalized": "B&M Seville",
            "matched": {"brand": "B&M", "scent": "Seville"},
        }
        original_comment = "B&M Seville (SAMPLE)"

        result = enricher.enrich(field_data, original_comment)

        assert result is not None
        assert result["sample_type"] == "sample"
        assert result["extraction_remainder"] == "(SAMPLE)"

    def test_enrich_with_whitespace_variations(self, enricher):
        """Test extraction with whitespace variations."""
        field_data = {
            "original": "B&M Seville ( sample )",
            "normalized": "B&M Seville",
            "matched": {"brand": "B&M", "scent": "Seville"},
        }
        original_comment = "B&M Seville ( sample )"

        result = enricher.enrich(field_data, original_comment)

        assert result is not None
        assert result["sample_type"] == "sample"
        assert result["extraction_remainder"] == "( sample )"

    @pytest.fixture
    def enricher(self):
        """Create a SoapSampleEnricher instance for testing."""
        return SoapSampleEnricher()
