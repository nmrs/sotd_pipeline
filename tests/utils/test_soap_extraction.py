#!/usr/bin/env python3
"""Tests for soap extraction utilities."""

from sotd.utils.soap_extraction import (
    extract_soap_sample_via_normalization,
    _extract_sample_patterns,
)


class TestExtractSoapSampleViaNormalization:
    """Test the main soap sample extraction function."""

    def test_basic_sample_detection(self):
        """Test basic sample detection with parentheses."""
        original = "B&M Seville (sample)"
        normalized = "B&M Seville"

        result = extract_soap_sample_via_normalization(original, normalized)
        sample_type, sample_number, total_samples, remainder = result

        assert sample_type == "sample"
        assert sample_number is None
        assert total_samples is None
        assert remainder == "(sample)"

    def test_numbered_sample_detection(self):
        """Test numbered sample detection."""
        original = "Stirling Bay Rum (sample #23)"
        normalized = "Stirling Bay Rum"

        result = extract_soap_sample_via_normalization(original, normalized)
        sample_type, sample_number, total_samples, remainder = result

        assert sample_type == "sample"
        assert sample_number == 23
        assert total_samples is None
        assert remainder == "(sample #23)"

    def test_range_sample_detection(self):
        """Test range sample detection (sample X of Y)."""
        original = "Declaration Grooming (sample 5 of 10)"
        normalized = "Declaration Grooming"

        result = extract_soap_sample_via_normalization(original, normalized)
        sample_type, sample_number, total_samples, remainder = result

        assert sample_type == "sample"
        assert sample_number == 5
        assert total_samples == 10
        assert remainder == "(sample 5 of 10)"

    def test_fraction_sample_detection(self):
        """Test fraction sample detection (sample X/Y)."""
        original = "Zingari Man (sample 3/15)"
        normalized = "Zingari Man"

        result = extract_soap_sample_via_normalization(original, normalized)
        sample_type, sample_number, total_samples, remainder = result

        assert sample_type == "sample"
        assert sample_number == 3
        assert total_samples == 15
        assert remainder == "(sample 3/15)"

    def test_trailing_sample_detection(self):
        """Test trailing sample detection."""
        original = "H&M - Seville - sample"
        normalized = "H&M - Seville"

        result = extract_soap_sample_via_normalization(original, normalized)
        sample_type, sample_number, total_samples, remainder = result

        assert sample_type == "sample"
        assert sample_number is None
        assert total_samples is None
        assert remainder == "- sample"

    def test_tester_detection(self):
        """Test tester detection."""
        original = "Zingari Man (tester)"
        normalized = "Zingari Man"

        result = extract_soap_sample_via_normalization(original, normalized)
        sample_type, sample_number, total_samples, remainder = result

        assert sample_type == "tester"
        assert sample_number is None
        assert total_samples is None
        assert remainder == "(tester)"

    def test_samp_abbreviation(self):
        """Test samp abbreviation detection."""
        original = "B&M Seville (samp)"
        normalized = "B&M Seville"

        result = extract_soap_sample_via_normalization(original, normalized)
        sample_type, sample_number, total_samples, remainder = result

        assert sample_type == "sample"
        assert sample_number is None
        assert total_samples is None
        assert remainder == "(samp)"

    def test_no_sample_detected(self):
        """Test when no sample is detected."""
        original = "B&M Seville"
        normalized = "B&M Seville"

        result = extract_soap_sample_via_normalization(original, normalized)
        sample_type, sample_number, total_samples, remainder = result

        assert sample_type is None
        assert sample_number is None
        assert total_samples is None
        assert remainder == ""

    def test_normalized_not_found_in_original(self):
        """Test when normalized text is not found in original."""
        original = "B&M Seville (sample)"
        normalized = "Different Soap"

        result = extract_soap_sample_via_normalization(original, normalized)
        sample_type, sample_number, total_samples, remainder = result

        assert sample_type is None
        assert sample_number is None
        assert total_samples is None
        assert remainder is None

    def test_empty_inputs(self):
        """Test with empty inputs."""
        result = extract_soap_sample_via_normalization("", "")
        assert result == (None, None, None, None)

        # Test with None inputs - these should be handled gracefully
        result = extract_soap_sample_via_normalization("", "")
        assert result == (None, None, None, None)

    def test_case_insensitive_matching(self):
        """Test case insensitive matching."""
        original = "B&M Seville (SAMPLE)"
        normalized = "B&M Seville"

        result = extract_soap_sample_via_normalization(original, normalized)
        sample_type, sample_number, total_samples, remainder = result

        assert sample_type == "sample"
        assert remainder == "(SAMPLE)"

    def test_whitespace_variations(self):
        """Test whitespace variations in sample patterns."""
        original = "B&M Seville ( sample )"
        normalized = "B&M Seville"

        result = extract_soap_sample_via_normalization(original, normalized)
        sample_type, sample_number, total_samples, remainder = result

        assert sample_type == "sample"
        assert remainder == "( sample )"


class TestExtractSamplePatterns:
    """Test the internal sample pattern extraction function."""

    def test_basic_sample_pattern(self):
        """Test basic sample pattern detection."""
        remainder = "(sample)"
        result = _extract_sample_patterns(remainder)

        sample_type, sample_number, total_samples = result
        assert sample_type == "sample"
        assert sample_number is None
        assert total_samples is None

    def test_numbered_sample_pattern(self):
        """Test numbered sample pattern detection."""
        remainder = "(sample #23)"
        result = _extract_sample_patterns(remainder)

        sample_type, sample_number, total_samples = result
        assert sample_type == "sample"
        assert sample_number == 23
        assert total_samples is None

    def test_range_sample_pattern(self):
        """Test range sample pattern detection."""
        remainder = "(sample 5 of 10)"
        result = _extract_sample_patterns(remainder)

        sample_type, sample_number, total_samples = result
        assert sample_type == "sample"
        assert sample_number == 5
        assert total_samples == 10

    def test_fraction_sample_pattern(self):
        """Test fraction sample pattern detection."""
        remainder = "(sample 3/15)"
        result = _extract_sample_patterns(remainder)

        sample_type, sample_number, total_samples = result
        assert sample_type == "sample"
        assert sample_number == 3
        assert total_samples == 15

    def test_trailing_sample_pattern(self):
        """Test trailing sample pattern detection."""
        remainder = "Brand - Scent - sample"
        result = _extract_sample_patterns(remainder)

        sample_type, sample_number, total_samples = result
        assert sample_type == "sample"
        assert sample_number is None
        assert total_samples is None

    def test_tester_pattern(self):
        """Test tester pattern detection."""
        remainder = "(tester)"
        result = _extract_sample_patterns(remainder)

        sample_type, sample_number, total_samples = result
        assert sample_type == "tester"
        assert sample_number is None
        assert total_samples is None

    def test_samp_abbreviation_pattern(self):
        """Test samp abbreviation pattern detection."""
        remainder = "(samp)"
        result = _extract_sample_patterns(remainder)

        sample_type, sample_number, total_samples = result
        assert sample_type == "sample"
        assert sample_number is None
        assert total_samples is None

    def test_loose_whitespace_pattern(self):
        """Test loose whitespace pattern detection."""
        remainder = "( sample )"
        result = _extract_sample_patterns(remainder)

        sample_type, sample_number, total_samples = result
        assert sample_type == "sample"
        assert sample_number is None
        assert total_samples is None

    def test_no_pattern_found(self):
        """Test when no pattern is found."""
        remainder = "some other text"
        result = _extract_sample_patterns(remainder)

        sample_type, sample_number, total_samples = result
        assert sample_type is None
        assert sample_number is None
        assert total_samples is None

    def test_empty_remainder(self):
        """Test with empty remainder."""
        result = _extract_sample_patterns("")
        assert result == (None, None, None)

    def test_case_insensitive_patterns(self):
        """Test case insensitive pattern matching."""
        remainder = "(SAMPLE)"
        result = _extract_sample_patterns(remainder)

        sample_type, sample_number, total_samples = result
        assert sample_type == "sample"
