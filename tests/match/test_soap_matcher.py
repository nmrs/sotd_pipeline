# pylint: disable=redefined-outer-name

import pytest

from sotd.match.soap_matcher import SoapMatcher


@pytest.fixture
def matcher(tmp_path):
    yaml_content = r"""
Barrister and Mann:
  patterns:
  - '\bb ?(and|&|\+|a)? ?m\b'
  - 'barrister (and|\+|&) mann'
  scents:
    Seville:
      patterns:
      - seville
House of Mammoth:
  patterns:
    - hou.*mammoth
    - '\\bhom\\b'
    - ^mammoth
    - mammoth soaps
  scents:
    Almond Leather:
      patterns:
        - almond leather
    Hygge:
      patterns:
        - hygge
    Tusk:
      patterns:
        - tusk
    Alive:
      patterns:
        - alive
    Seville:
      patterns:
        - seville
    Beloved:
      patterns:
        - beloved
Noble Otter:
  patterns:
  - nob.*otter
  - '^\W*no\b'
  scents:
    '''Tis the Season':
      patterns:
      - tis the season
"""
    path = tmp_path / "soaps.yaml"
    path.write_text(yaml_content)
    return SoapMatcher(catalog_path=path)


def test_match_exact_scent(matcher):
    result = matcher.match("Barrister and Mann - Seville")
    assert result["matched"]["maker"] == "Barrister and Mann"
    assert result["matched"]["scent"] == "Seville"
    assert result["pattern"]


def test_match_case_insensitive(matcher):
    result = matcher.match("barrister and mann - seville")
    assert result["matched"]["maker"] == "Barrister and Mann"
    assert result["matched"]["scent"] == "Seville"


def test_match_partial_name(matcher):
    result = matcher.match("B&M - Seville")
    assert result["matched"]["scent"] == "Seville"


def test_no_match(matcher):
    result = matcher.match("Mystery Soap That Doesn't Exist")
    assert result["matched"] is None
    assert result["pattern"] is None


def test_brand_only_match_fallback(matcher):
    result = matcher.match("House of Mammoth - Alive")
    assert result["matched"]["maker"] == "House of Mammoth"
    assert result["matched"]["scent"] == "Alive"
    assert result["pattern"]


def test_brand_only_match_with_colon(matcher):
    result = matcher.match("HoM: Tusk")
    assert result["matched"]["maker"] == "House of Mammoth"
    assert result["matched"]["scent"] == "Tusk"


def test_brand_only_match_with_whitespace(matcher):
    result = matcher.match("   HoM   -   Hygge  ")
    assert result["matched"]["maker"] == "House of Mammoth"
    assert result["matched"]["scent"] == "Hygge"


def test_exact_scent_match_takes_priority(matcher):
    result = matcher.match("HoM - Almond Leather")
    assert result["matched"]["maker"] == "House of Mammoth"
    assert result["matched"]["scent"].lower() == "almond leather"


# Additional test: ensure all match results include a non-null "match_type" when a match is present.
def test_match_always_has_match_type(matcher):
    examples = [
        "Barrister and Mann - Seville",
        "HoM - Tusk",
        "House of Mammoth - Alive",
        "Strike Gold Shave - Bee's Knees Soap",
        "Southern Witchcrafts - Tres Matres",
    ]
    for example in examples:
        result = matcher.match(example)
        if result["matched"] is not None:
            assert "match_type" in result
            assert result["match_type"] is not None


# Test for correct match_type values in known scenarios
def test_match_returns_correct_match_type(matcher):
    test_cases = [
        ("Barrister and Mann - Seville", "exact"),
        ("House of Mammoth - Alive", "exact"),
        ("House of Mammoth - Aliive", "brand_fallback"),
        ("UnknownBrand - SomeNewScent", "split_fallback"),
    ]
    for input_text, expected_type in test_cases:
        result = matcher.match(input_text)
        assert result["matched"] is not None, f"No match for: {input_text}"
        assert (
            result["match_type"] == expected_type
        ), f"{input_text} expected {expected_type}, got {result['match_type']}"


# Test normalization and cleanup of scent and maker names
def test_normalize_scent_and_maker_cleanup(matcher):
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
        result = matcher.match(input_text)
        assert result["matched"] is not None, f"No match for: {input_text}"
        assert result["matched"]["maker"] == expected_maker
        assert result["matched"]["scent"] == expected_scent


def test_apostrophe_scent_preserved(matcher):
    result = matcher.match("Noble Otter - 'Tis the Season")
    assert result["matched"] is not None
    assert result["matched"]["maker"] == "Noble Otter"
    assert result["matched"]["scent"] == "'Tis the Season"


# Test that scent regex patterns in SoapMatcher are sorted by length descending
def test_scent_regex_sorting_order(matcher):
    # Retrieve the compiled patterns directly from matcher
    scent_patterns = matcher.scent_patterns
    # Extract the original regex patterns from the compiled list
    regex_strings = [entry["pattern"] for entry in scent_patterns]
    # Check that patterns are sorted by length descending
    lengths = [len(p) for p in regex_strings]
    assert lengths == sorted(
        lengths, reverse=True
    ), "Scent patterns are not sorted by length descending"


# Test that scent regex patterns in SoapMatcher are sorted by length descending
def test_brand_regex_sorting_order(matcher):
    # Retrieve the compiled patterns directly from matcher
    brand_patterns = matcher.brand_patterns
    # Extract the original regex patterns from the compiled list
    regex_strings = [entry["pattern"] for entry in brand_patterns]
    # Check that patterns are sorted by length descending
    lengths = [len(p) for p in regex_strings]
    assert lengths == sorted(
        lengths, reverse=True
    ), "Scent patterns are not sorted by length descending"
