#!/usr/bin/env python3
"""Tests for soap extraction utilities."""

import pytest

from sotd.utils.soap_extraction import (
    extract_soap_sample_via_normalization,
    normalize_soap_suffixes,
)


class TestNormalizeSoapSuffixes:
    """Test soap suffix normalization functionality."""

    def test_empty_input(self):
        """Test handling of empty input."""
        assert normalize_soap_suffixes("") == ""
        # Type ignore for test - we're testing None handling
        assert normalize_soap_suffixes(None) is None  # type: ignore

    def test_no_suffixes(self):
        """Test text with no suffixes to normalize."""
        assert (
            normalize_soap_suffixes("summer break soaps - steady") == "summer break soaps - steady"
        )
        assert normalize_soap_suffixes("barrister and mann - roam") == "barrister and mann - roam"

    def test_product_type_suffixes(self):
        """Test removal of product type suffixes."""
        # - soap suffix
        assert (
            normalize_soap_suffixes("summer break soaps - steady - soap")
            == "summer break soaps - steady"
        )
        # Note: Standalone "soap" at end is NOT removed to avoid breaking brand names like "Soap Commander"
        # Only "- soap" (with dash) is removed
        assert (
            normalize_soap_suffixes("summer break soaps steady soap")
            == "summer break soaps steady soap"
        )

        # - cream suffix
        assert (
            normalize_soap_suffixes("summer break soaps - steady - cream")
            == "summer break soaps - steady"
        )

        # - puck suffix
        assert (
            normalize_soap_suffixes("summer break soaps - steady - puck")
            == "summer break soaps - steady"
        )

        # - croap suffix
        assert (
            normalize_soap_suffixes("summer break soaps - steady - croap")
            == "summer break soaps - steady"
        )
        # croap without dash (should also be stripped, like puck)
        assert (
            normalize_soap_suffixes("summer break soaps - steady croap")
            == "summer break soaps - steady"
        )

        # - shaving soap suffix
        assert (
            normalize_soap_suffixes("summer break soaps - steady - shaving soap")
            == "summer break soaps - steady"
        )

        # - shave soap suffix
        assert (
            normalize_soap_suffixes("summer break soaps - steady - shave soap")
            == "summer break soaps - steady"
        )

        # standalone soap - NOT removed to avoid breaking brand names like "Soap Commander"
        # Only "- soap" (with dash) is removed
        assert (
            normalize_soap_suffixes("summer break soaps steady soap")
            == "summer break soaps steady soap"
        )

        # standalone cream - NOT removed (conservative approach)
        # Only "- cream" (with dash) is removed
        assert (
            normalize_soap_suffixes("summer break soaps steady cream")
            == "summer break soaps steady cream"
        )

    def test_container_type_suffixes(self):
        """Test removal of container type suffixes."""
        # - stick suffix
        assert normalize_soap_suffixes("arko - shave stick") == "arko"
        assert normalize_soap_suffixes("la toja stick") == "la toja"

        # - shave stick suffix
        assert normalize_soap_suffixes("la toja shave stick") == "la toja"

        # - tube suffix
        assert normalize_soap_suffixes("proraso green tube") == "proraso green"

        # - hard suffix
        assert normalize_soap_suffixes("tabac - hard") == "tabac"

    def test_preserves_version_indicators(self):
        """Test that version indicators are preserved (not normalized)."""
        # These should NOT be normalized as they distinguish different products
        assert (
            normalize_soap_suffixes("barrister and mann - roam 2") == "barrister and mann - roam 2"
        )
        assert (
            normalize_soap_suffixes("barrister and mann - roam (v2)")
            == "barrister and mann - roam (v2)"
        )
        assert (
            normalize_soap_suffixes("barrister and mann - roam (2024a)")
            == "barrister and mann - roam (2024a)"
        )
        assert (
            normalize_soap_suffixes("barrister and mann - roam (og)")
            == "barrister and mann - roam (og)"
        )
        assert (
            normalize_soap_suffixes("barrister and mann - roam (original)")
            == "barrister and mann - roam (original)"
        )
        assert (
            normalize_soap_suffixes("barrister and mann - roam (1)")
            == "barrister and mann - roam (1)"
        )
        assert (
            normalize_soap_suffixes("barrister and mann - roam (one)")
            == "barrister and mann - roam (one)"
        )
        assert (
            normalize_soap_suffixes("barrister and mann - roam (i)")
            == "barrister and mann - roam (i)"
        )
        assert (
            normalize_soap_suffixes("barrister and mann - roam ii")
            == "barrister and mann - roam ii"
        )

    def test_case_insensitive(self):
        """Test that normalization is case insensitive but preserves original case."""
        assert (
            normalize_soap_suffixes("SUMMER BREAK SOAPS - STEADY - SOAP")
            == "SUMMER BREAK SOAPS - STEADY"
        )
        assert (
            normalize_soap_suffixes("Summer Break Soaps - Steady - Soap")
            == "Summer Break Soaps - Steady"
        )
        assert (
            normalize_soap_suffixes("summer break soaps - steady - PUCK")
            == "summer break soaps - steady"
        )

    def test_size_indicators(self):
        """Test removal of size indicators in parentheses."""
        # oz indicators
        assert (
            normalize_soap_suffixes("catie's bubbles - le marche du rasage (2oz)")
            == "catie's bubbles - le marche du rasage"
        )
        assert (
            normalize_soap_suffixes(
                "catie's bubbles - le marche du rasage (big ass og 8oz pour - french style)"
            )
            == "catie's bubbles - le marche du rasage"
        )

    def test_base_formula_indicators(self):
        """Test removal of base/formula indicators in parentheses."""
        # premium base
        assert (
            normalize_soap_suffixes("catie's bubbles - blugère (premium base)")
            == "catie's bubbles - blugère"
        )

        # luxury base
        assert (
            normalize_soap_suffixes("catie's bubbles - maggard meet exclusive (luxury base)")
            == "catie's bubbles - maggard meet exclusive"
        )

        # omnibus base
        assert (
            normalize_soap_suffixes("barrister and mann - adagio - omnibus")
            == "barrister and mann - adagio"
        )

        # milksteak
        assert (
            normalize_soap_suffixes("declaration grooming - puzzle (milksteak)")
            == "declaration grooming - puzzle"
        )

        # tusk
        assert (
            normalize_soap_suffixes("house of mammoth - kryptonite (tusk)")
            == "house of mammoth - kryptonite"
        )

        # professional
        assert (
            normalize_soap_suffixes("cella - buongiorno al sandalo - (professional)")
            == "cella - buongiorno al sandalo"
        )

        # tallow base
        assert (
            normalize_soap_suffixes("mäurer & wirtz - tabac (tallow base)")
            == "mäurer & wirtz - tabac"
        )

        # tallow formulation
        assert (
            normalize_soap_suffixes("mauer and wirtz - tabac (tallow formulation)")
            == "mauer and wirtz - tabac"
        )

        # vegan
        assert (
            normalize_soap_suffixes("southern witchcrafts - druantia - (vegan)")
            == "southern witchcrafts - druantia"
        )

    def test_whitespace_cleanup(self):
        """Test cleanup of extra whitespace and dashes."""
        # Remove trailing dash
        assert (
            normalize_soap_suffixes("summer break soaps - steady -")
            == "summer break soaps - steady"
        )

        # Normalize whitespace
        assert (
            normalize_soap_suffixes("summer  break   soaps   -   steady")
            == "summer break soaps - steady"
        )

        # Strip leading/trailing whitespace
        assert (
            normalize_soap_suffixes("  summer break soaps - steady  ")
            == "summer break soaps - steady"
        )

    def test_multiple_suffixes(self):
        """Test handling of multiple suffixes (should remove all)."""
        # Multiple product type suffixes
        assert (
            normalize_soap_suffixes("summer break soaps - steady - soap - puck")
            == "summer break soaps - steady"
        )

        # Product type + container type
        assert (
            normalize_soap_suffixes("summer break soaps - steady - soap - stick")
            == "summer break soaps - steady"
        )

        # Product type + size
        assert (
            normalize_soap_suffixes("summer break soaps - steady - soap (2oz)")
            == "summer break soaps - steady"
        )

    def test_real_world_examples(self):
        """Test with real examples from soap.yaml."""
        # Summer Break Soaps examples
        assert (
            normalize_soap_suffixes("summer break soaps - steady - soap (sample -- thanks!!)")
            == "summer break soaps - steady"
        )
        assert (
            normalize_soap_suffixes("summer break soaps - steady - puck")
            == "summer break soaps - steady"
        )
        assert (
            normalize_soap_suffixes("summer break soaps - steady - croap")
            == "summer break soaps - steady"
        )
        assert (
            normalize_soap_suffixes("summer break soaps - steady - shaving soap")
            == "summer break soaps - steady"
        )
        assert (
            normalize_soap_suffixes("summer break soaps - steady - shave soap")
            == "summer break soaps - steady"
        )

        # Cella examples
        assert normalize_soap_suffixes("cella - crema da barba") == "cella"
        assert (
            normalize_soap_suffixes("cella - milano crema da barba - (est. 1899)")
            == "cella - milano"
        )
        assert (
            normalize_soap_suffixes("cella - buongiorno al sandalo - (professional)")
            == "cella - buongiorno al sandalo"
        )

        # Tabac examples
        assert (
            normalize_soap_suffixes("mäurer & wirtz - tabac original (tallow)")
            == "mäurer & wirtz - tabac original"
        )
        assert normalize_soap_suffixes("tabac - shave stick") == "tabac"
        assert normalize_soap_suffixes("tabac - hard") == "tabac"


class TestExtractSoapSampleViaNormalization:
    """Test soap sample extraction functionality."""

    def test_empty_input(self):
        """Test handling of empty input."""
        result = extract_soap_sample_via_normalization("", "")
        assert result == (None, None, None, None)

        result = extract_soap_sample_via_normalization("text", "")
        assert result == (None, None, None, None)

        result = extract_soap_sample_via_normalization("", "text")
        assert result == (None, None, None, None)

    def test_no_sample_indicators(self):
        """Test text with no sample indicators."""
        result = extract_soap_sample_via_normalization(
            "summer break soaps - steady", "summer break soaps - steady"
        )
        assert result == (None, None, None, "")

    def test_basic_sample_patterns(self):
        """Test basic sample pattern extraction."""
        # (sample)
        result = extract_soap_sample_via_normalization(
            "summer break soaps - steady (sample)", "summer break soaps - steady"
        )
        assert result == ("sample", None, None, "(sample)")

        # (tester)
        result = extract_soap_sample_via_normalization(
            "summer break soaps - steady (tester)", "summer break soaps - steady"
        )
        assert result == ("tester", None, None, "(tester)")

        # (samp) - should normalize to sample
        result = extract_soap_sample_via_normalization(
            "summer break soaps - steady (samp)", "summer break soaps - steady"
        )
        assert result == ("sample", None, None, "(samp)")

    def test_numbered_sample_patterns(self):
        """Test numbered sample pattern extraction."""
        # (sample #23)
        result = extract_soap_sample_via_normalization(
            "summer break soaps - steady (sample #23)", "summer break soaps - steady"
        )
        assert result == ("sample", 23, None, "(sample #23)")

        # (sample 5 of 10)
        result = extract_soap_sample_via_normalization(
            "summer break soaps - steady (sample 5 of 10)", "summer break soaps - steady"
        )
        assert result == ("sample", 5, 10, "(sample 5 of 10)")

        # (sample 3/15)
        result = extract_soap_sample_via_normalization(
            "summer break soaps - steady (sample 3/15)", "summer break soaps - steady"
        )
        assert result == ("sample", 3, 15, "(sample 3/15)")

    def test_trailing_sample_patterns(self):
        """Test trailing sample pattern extraction."""
        # - sample at end
        result = extract_soap_sample_via_normalization(
            "summer break soaps - steady - sample", "summer break soaps - steady"
        )
        assert result == ("sample", None, None, "- sample")

        # - tester at end
        result = extract_soap_sample_via_normalization(
            "summer break soaps - steady - tester", "summer break soaps - steady"
        )
        assert result == ("tester", None, None, "- tester")

    def test_loose_sample_patterns(self):
        """Test loose sample pattern extraction with whitespace variations."""
        # ( sample ) with spaces
        result = extract_soap_sample_via_normalization(
            "summer break soaps - steady ( sample )", "summer break soaps - steady"
        )
        assert result == ("sample", None, None, "( sample )")

        # (tester) with spaces
        result = extract_soap_sample_via_normalization(
            "summer break soaps - steady ( tester )", "summer break soaps - steady"
        )
        assert result == ("tester", None, None, "( tester )")

    def test_gratitude_sample_patterns(self):
        """Test sample patterns with gratitude expressions."""
        # (sample -- thanks!!)
        result = extract_soap_sample_via_normalization(
            "summer break soaps - steady (sample -- thanks!!)", "summer break soaps - steady"
        )
        assert result == ("sample", None, None, "(sample -- thanks!!)")

    def test_case_insensitive(self):
        """Test that sample extraction is case insensitive."""
        # SAMPLE
        result = extract_soap_sample_via_normalization(
            "summer break soaps - steady (SAMPLE)", "summer break soaps - steady"
        )
        assert result == ("sample", None, None, "(SAMPLE)")

        # Sample
        result = extract_soap_sample_via_normalization(
            "summer break soaps - steady (Sample)", "summer break soaps - steady"
        )
        assert result == ("sample", None, None, "(Sample)")

    def test_real_world_examples(self):
        """Test with real examples from soap.yaml."""
        # Summer Break Soaps examples
        result = extract_soap_sample_via_normalization(
            "summer break soaps - steady - soap (sample -- thanks!!)", "summer break soaps - steady"
        )
        assert result == ("sample", None, None, "- soap (sample -- thanks!!)")

        result = extract_soap_sample_via_normalization(
            "summer break soaps - steady (sample)", "summer break soaps - steady"
        )
        assert result == ("sample", None, None, "(sample)")

        result = extract_soap_sample_via_normalization(
            "summer break soaps - steady - sample", "summer break soaps - steady"
        )
        assert result == ("sample", None, None, "- sample")

    def test_normalized_text_not_found(self):
        """Test when normalized text is not found in original."""
        result = extract_soap_sample_via_normalization(
            "completely different text", "summer break soaps - steady"
        )
        assert result == (None, None, None, None)
