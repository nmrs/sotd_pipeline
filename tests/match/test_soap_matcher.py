# pylint: disable=redefined-outer-name

import pytest
from unittest.mock import patch

from sotd.match.soap_matcher import SoapMatcher


@pytest.fixture
def mock_correct_matches():
    """Mock correct matches data for testing."""
    return {
        "Barrister and Mann": {"Seville": ["Barrister and Mann - Seville"]},
        "House of Mammoth": {"Alive": ["House of Mammoth - Alive"]},
    }


@pytest.fixture
def soap_matcher_with_mock(mock_correct_matches):
    """Create a SoapMatcher with mocked correct matches."""
    with patch.object(SoapMatcher, "_load_correct_matches", return_value=mock_correct_matches):
        matcher = SoapMatcher()
        return matcher


@pytest.fixture
def matcher(tmp_path):
    """Create a SoapMatcher instance for testing with temp files."""
    # Create temp catalog
    catalog_content = """
Barrister and Mann:
  Seville:
    patterns:
      - "b&m.*seville"
      - "barrister.*mann.*seville"
  Fougère Gothique:
    patterns:
      - "fougère.*gothique"
House of Mammoth:
  Alive:
    patterns:
      - "hom.*alive"
      - "house.*mammoth.*alive"
  Tusk:
    patterns:
      - "hom.*tusk"
      - "house.*mammoth.*tusk"
  Hygge:
    patterns:
      - "hom.*hygge"
      - "house.*mammoth.*hygge"
  Almond Leather:
    patterns:
      - "almond.*leather"
Noble Otter:
  'Tis the Season:
    patterns:
      - "'tis.*season"
Strike Gold Shave:
  Bee's Knees Soap:
    patterns:
      - "bee.*knees"
Southern Witchcrafts:
  Tres Matres:
    patterns:
      - "tres.*matres"
"""
    catalog_file = tmp_path / "soaps.yaml"
    catalog_file.write_text(catalog_content)

    # Create temp correct_matches
    correct_matches_content = """
soap:
  Barrister and Mann:
    Seville:
      - "Barrister and Mann - Seville"
  House of Mammoth:
    Alive:
      - "House of Mammoth - Alive"
"""
    correct_matches_file = tmp_path / "correct_matches.yaml"
    correct_matches_file.write_text(correct_matches_content)

    return SoapMatcher(catalog_path=catalog_file)


def test_match_exact_scent(soap_matcher_with_mock):
    result = soap_matcher_with_mock.match("Barrister and Mann - Seville")
    assert result["matched"]["maker"] == "Barrister and Mann"
    assert result["matched"]["scent"] == "Seville"
    assert result["match_type"] == "exact"


def test_match_case_insensitive(soap_matcher_with_mock):
    result = soap_matcher_with_mock.match("barrister and mann - seville")
    assert result["matched"]["maker"] == "Barrister and Mann"
    assert result["matched"]["scent"] == "Seville"
    assert result["match_type"] == "exact"


def test_match_partial_name(soap_matcher_with_mock):
    result = soap_matcher_with_mock.match("B&M - Seville")
    assert result["matched"]["scent"] == "Seville"


def test_no_match(soap_matcher_with_mock):
    result = soap_matcher_with_mock.match("Mystery Soap That Doesn't Exist")
    assert result["matched"] is None
    assert result["pattern"] is None


def test_brand_only_match_fallback(soap_matcher_with_mock):
    result = soap_matcher_with_mock.match("House of Mammoth - Alive")
    assert result["matched"]["maker"] == "House of Mammoth"
    assert result["matched"]["scent"] == "Alive"
    assert result["match_type"] == "exact"


def test_brand_only_match_with_colon(soap_matcher_with_mock):
    result = soap_matcher_with_mock.match("HoM: Tusk")
    assert result["matched"]["maker"] == "House of Mammoth"
    assert result["matched"]["scent"] == "Tusk"


def test_brand_only_match_with_whitespace(soap_matcher_with_mock):
    result = soap_matcher_with_mock.match("   HoM   -   Hygge  ")
    assert result["matched"]["maker"] == "House of Mammoth"
    assert result["matched"]["scent"] == "Hygge"


def test_exact_scent_match_takes_priority(soap_matcher_with_mock):
    result = soap_matcher_with_mock.match("HoM - Almond Leather")
    assert result["matched"]["maker"] == "House of Mammoth"
    assert result["matched"]["scent"].lower() == "almond leather"


# Additional test: ensure all match results include a non-null "match_type" when a match is present.
def test_match_always_has_match_type(soap_matcher_with_mock):
    examples = [
        "Barrister and Mann - Seville",
        "HoM - Tusk",
        "House of Mammoth - Alive",
        "Strike Gold Shave - Bee's Knees Soap",
        "Southern Witchcrafts - Tres Matres",
    ]
    for example in examples:
        result = soap_matcher_with_mock.match(example)
        if result["matched"] is not None:
            assert "match_type" in result
            assert result["match_type"] is not None


def test_match_returns_correct_match_type(soap_matcher_with_mock):
    test_cases = [
        ("Barrister and Mann - Seville", "exact"),
        ("House of Mammoth - Alive", "exact"),
        ("House of Mammoth - Aliive", "brand"),
        ("UnknownBrand - SomeNewScent", "alias"),
    ]
    for input_text, expected_type in test_cases:
        result = soap_matcher_with_mock.match(input_text)
        assert result["matched"] is not None, f"No match for: {input_text}"
        assert (
            result["match_type"] == expected_type
        ), f"{input_text} expected {expected_type}, got {result['match_type']}"


# Test normalization and cleanup of scent and maker names
def test_normalize_scent_and_maker_cleanup(soap_matcher_with_mock):
    cases = [
        ("House of Mammoth - Fú Dào (23)", "House of Mammoth", "Fú Dào"),
        ("House of Mammoth - Fú Dào (24)", "House of Mammoth", "Fú Dào"),
        (
            "Mike's Natural Soaps - Hungarian Lavender.",
            "Mike's Natural Soaps",
            "Hungarian Lavender",
        ),
        ("   House of Mammoth / - Fú Dào , ", "House of Mammoth", "Fú Dào"),
        ("*House of Mammoth* - *Fú Dào*", "House of Mammoth", "Fú Dào"),
    ]
    for input_text, expected_maker, expected_scent in cases:
        result = soap_matcher_with_mock.match(input_text)
        assert result["matched"] is not None, f"No match for: {input_text}"
        assert result["matched"]["maker"] == expected_maker
        assert result["matched"]["scent"] == expected_scent


def test_apostrophe_scent_preserved(soap_matcher_with_mock):
    result = soap_matcher_with_mock.match("Noble Otter - 'Tis the Season")
    assert result["matched"] is not None
    assert result["matched"]["maker"] == "Noble Otter"
    assert result["matched"]["scent"] == "'Tis the Season"


# Test that scent regex patterns in SoapMatcher are sorted by length descending
def test_scent_regex_sorting_order(soap_matcher_with_mock):
    # Retrieve the compiled patterns directly from matcher
    scent_patterns = soap_matcher_with_mock.scent_patterns
    # Extract the original regex patterns from the compiled list
    regex_strings = [entry["pattern"] for entry in scent_patterns]
    # Check that patterns are sorted by length descending
    lengths = [len(p) for p in regex_strings]
    assert lengths == sorted(
        lengths, reverse=True
    ), "Scent patterns are not sorted by length descending"


# Test that scent regex patterns in SoapMatcher are sorted by length descending
def test_brand_regex_sorting_order(soap_matcher_with_mock):
    # Retrieve the compiled patterns directly from matcher
    brand_patterns = soap_matcher_with_mock.brand_patterns
    # Extract the original regex patterns from the compiled list
    regex_strings = [entry["pattern"] for entry in brand_patterns]
    # Check that patterns are sorted by length descending
    lengths = [len(p) for p in regex_strings]
    assert lengths == sorted(
        lengths, reverse=True
    ), "Scent patterns are not sorted by length descending"
