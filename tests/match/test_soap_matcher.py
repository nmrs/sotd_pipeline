# pylint: disable=redefined-outer-name

import pytest
from unittest.mock import patch

from sotd.match.soap_matcher import SoapMatcher


@pytest.fixture(scope="session")
def session_soap_catalog():
    """Session-scoped soap catalog for all tests."""
    return {
        "Barrister and Mann": {
            "Seville": {"patterns": ["b&m.*seville", "barrister.*mann.*seville"]},
            "Fougère Gothique": {"patterns": ["fougère.*gothique"]},
        },
        "House of Mammoth": {
            "Alive": {"patterns": ["hom.*alive", "house.*mammoth.*alive"]},
            "Tusk": {"patterns": ["hom.*tusk", "house.*mammoth.*tusk"]},
            "Hygge": {"patterns": ["hom.*hygge", "house.*mammoth.*hygge"]},
            "Almond Leather": {"patterns": ["almond.*leather"]},
        },
        "Noble Otter": {"'Tis the Season": {"patterns": ["'tis.*season"]}},
        "Strike Gold Shave": {"Bee's Knees Soap": {"patterns": ["bee.*knees"]}},
        "Southern Witchcrafts": {"Tres Matres": {"patterns": ["tres.*matres"]}},
    }


@pytest.fixture(scope="session")
def session_correct_matches():
    """Session-scoped correct matches for all tests."""
    return {
        "soap": {
            "Barrister and Mann": {"Seville": ["Barrister and Mann - Seville"]},
            "House of Mammoth": {"Alive": ["House of Mammoth - Alive"]},
        }
    }


@pytest.fixture(scope="session")
def session_matcher(tmp_path_factory, session_soap_catalog, session_correct_matches):
    """Session-scoped SoapMatcher instance."""
    tmp_path = tmp_path_factory.mktemp("soap_matcher_tests")

    # Create catalog file
    catalog_file = tmp_path / "soaps.yaml"
    with catalog_file.open("w", encoding="utf-8") as f:
        import yaml

        yaml.dump(session_soap_catalog, f)

    # Create correct matches file
    correct_matches_file = tmp_path / "correct_matches.yaml"
    with correct_matches_file.open("w", encoding="utf-8") as f:
        yaml.dump(session_correct_matches, f)

    return SoapMatcher(catalog_path=catalog_file, correct_matches_path=correct_matches_file)


@pytest.fixture(scope="class")
def matcher(session_matcher):
    """Class-scoped matcher that uses session-scoped instance."""
    # Clear cache to prevent pollution between tests
    session_matcher.clear_cache()
    return session_matcher


@pytest.fixture
def mock_correct_matches():
    """Mock correct matches data for testing."""
    return {
        "Barrister and Mann": {"Seville": ["Barrister and Mann - Seville"]},
        "House of Mammoth": {"Alive": ["House of Mammoth - Alive"]},
    }


@pytest.fixture
def soap_matcher_with_mock():
    """Create a SoapMatcher with mocked catalog data."""
    mock_catalog = {
        "Barrister and Mann": {
            "patterns": ["barrister.*mann", "b&m"],
            "scents": {
                "Seville": {
                    "patterns": ["seville"],
                }
            },
        },
        "House of Mammoth": {
            "patterns": ["house.*mammoth", "hom"],
            "scents": {
                "Alive": {
                    "patterns": ["alive"],
                },
                "Tusk": {
                    "patterns": ["tusk"],
                },
                "Hygge": {
                    "patterns": ["hygge"],
                },
                "Almond Leather": {
                    "patterns": ["almond.*leather"],
                },
            },
        },
        "Noble Otter": {
            "patterns": ["noble.*otter"],
            "scents": {
                "'Tis the Season": {
                    "patterns": ["'tis.*season"],
                }
            },
        },
        "Mike's Natural Soaps": {
            "patterns": ["mike.*natural"],
            "scents": {
                "Hungarian Lavender": {
                    "patterns": ["hungarian.*lavender"],
                }
            },
        },
    }

    with patch("sotd.utils.yaml_loader.load_yaml_with_nfc", return_value=mock_catalog):
        matcher = SoapMatcher()
        return matcher


def test_match_exact_scent(soap_matcher_with_mock):
    # Pass just the normalized string to matchers
    result = soap_matcher_with_mock.match("Barrister and Mann - Seville")
    assert result.matched is not None
    assert result.matched["maker"] == "Barrister and Mann"
    assert result.matched["scent"] == "Seville"
    assert result.match_type == "regex"  # Using mocked data, so it's regex


def test_match_case_insensitive(soap_matcher_with_mock):
    # Pass just the normalized string to matchers
    result = soap_matcher_with_mock.match("barrister and mann - seville")
    assert result.matched is not None
    assert result.matched["maker"] == "Barrister and Mann"
    assert result.matched["scent"] == "Seville"
    assert result.match_type == "regex"  # Case-insensitive matching now handled by regex fallback


def test_match_partial_name(soap_matcher_with_mock):
    # Pass just the normalized string to matchers
    result = soap_matcher_with_mock.match("B&M - Seville")
    assert result.matched is not None
    assert result.matched["scent"] == "Seville"


def test_no_match(soap_matcher_with_mock):
    structured_data = {
        "original": "Mystery Soap That Doesn't Exist",
        "normalized": "Mystery Soap That Doesn't Exist",
    }
    result = soap_matcher_with_mock.match(structured_data)
    assert result.matched is None
    assert result.pattern is None


def test_brand_only_match_fallback(soap_matcher_with_mock):
    # Pass just the normalized string to matchers
    result = soap_matcher_with_mock.match("House of Mammoth - Alive")
    assert result.matched is not None
    assert result.matched["maker"] == "House of Mammoth"
    assert result.matched["scent"] == "Alive"
    assert result.match_type == "brand"  # Using mocked data, so it's brand


def test_brand_only_match_with_colon(soap_matcher_with_mock):
    # Pass just the normalized string to matchers
    result = soap_matcher_with_mock.match("HoM: Tusk")
    assert result.matched is not None
    assert result.matched["maker"] == "House of Mammoth"
    assert result.matched["scent"] == "Tusk"


def test_brand_only_match_with_whitespace(soap_matcher_with_mock):
    # Pass just the normalized string to matchers
    result = soap_matcher_with_mock.match("   HoM   -   Hygge  ")
    assert result.matched is not None
    assert result.matched["maker"] == "House of Mammoth"
    assert result.matched["scent"] == "Hygge"


def test_exact_scent_match_takes_priority(soap_matcher_with_mock):
    # Pass just the normalized string to matchers
    result = soap_matcher_with_mock.match("HoM - Almond Leather")
    assert result.matched is not None
    assert result.matched["maker"] == "House of Mammoth"
    assert result.matched["scent"] == "Almond Leather"


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
        structured_data = {"original": example, "normalized": example}
        result = soap_matcher_with_mock.match(structured_data)
        if result.matched is not None:
            assert result.match_type is not None


def test_match_returns_correct_match_type(soap_matcher_with_mock):
    test_cases = [
        ("Barrister and Mann - Seville", "regex"),  # Matches scent pattern
        ("House of Mammoth - Alive", "brand"),  # Matches brand pattern, scent from remainder
        ("House of Mammoth - Aliive", "brand"),  # Matches brand pattern, scent from remainder
        ("UnknownBrand - SomeNewScent", "alias"),  # Dash-split fallback
    ]
    for input_text, expected_type in test_cases:
        # Pass just the normalized string to matchers
        result = soap_matcher_with_mock.match(input_text)
        assert result.matched is not None, f"No match for: {input_text}"
        assert (
            result.match_type == expected_type
        ), f"{input_text} expected {expected_type}, got {result.match_type}"


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
        # Pass just the normalized string to matchers
        result = soap_matcher_with_mock.match(input_text)
        assert result.matched is not None, f"No match for: {input_text}"
        assert result.matched["maker"] == expected_maker
        assert result.matched["scent"] == expected_scent


def test_apostrophe_scent_preserved(soap_matcher_with_mock):
    # Pass just the normalized string to matchers
    result = soap_matcher_with_mock.match("Noble Otter - 'Tis the Season")
    assert result.matched is not None
    assert result.matched["maker"] == "Noble Otter"
    assert result.matched["scent"] == "'Tis the Season"


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


def test_correct_matches_priority_before_regex(tmp_path):
    """Test that correct matches are checked before regex patterns for soaps."""
    # Create a test catalog with a regex pattern that would match
    catalog_content = """
Barrister and Mann:
  Seville:
    patterns:
      - "barrister.*mann.*seville"
"""
    catalog_file = tmp_path / "soaps.yaml"
    catalog_file.write_text(catalog_content)

    # Create a correct_matches.yaml with a different match for the same input
    correct_matches_content = """
soap:
  Barrister and Mann:
    Seville:
      - "Barrister and Mann - Seville"
"""
    correct_matches_file = tmp_path / "correct_matches.yaml"
    correct_matches_file.write_text(correct_matches_content)

    matcher = SoapMatcher(catalog_path=catalog_file, correct_matches_path=correct_matches_file)

    # Test that the input matches the correct_matches entry, not the regex
    # Pass just the normalized string to matchers
    result = matcher.match("Barrister and Mann - Seville")

    # Should match from correct_matches (exact match)
    assert result.matched is not None
    assert result.matched["maker"] == "Barrister and Mann"
    assert result.matched["scent"] == "Seville"
    assert result.match_type == "exact"
    assert result.pattern is None


def test_sample_detection(soap_matcher_with_mock):
    # Should detect sample and still match
    # Pass just the normalized string to matchers
    result = soap_matcher_with_mock.match("Barrister and Mann - Seville (Sample)")
    assert result.matched is not None
    assert result.matched["maker"] == "Barrister and Mann"
    assert result.matched["scent"] == "Seville"
    assert result.match_type in ("regex", "brand", "exact")  # Accept any match type


def test_empty_string_input(soap_matcher_with_mock):
    structured_data = {"original": "", "normalized": ""}
    result = soap_matcher_with_mock.match(structured_data)
    assert result.matched is None
    assert result.match_type is None


def test_none_input(soap_matcher_with_mock):
    # Should not raise error - just returns None match
    result = soap_matcher_with_mock.match(None)  # type: ignore
    assert result.matched is None


def test_non_string_input(soap_matcher_with_mock):
    # Should not raise error - just returns None match
    result = soap_matcher_with_mock.match(123)  # type: ignore
    assert result.matched is None


def test_brand_match_with_missing_scent(soap_matcher_with_mock):
    # Only brand pattern matches, scent is empty
    # Pass just the normalized string to matchers
    result = soap_matcher_with_mock.match("House of Mammoth - ")
    assert result.matched is not None
    assert result.matched["maker"] == "House of Mammoth"
    assert result.matched["scent"] == ""
    assert result.match_type == "brand"


def test_unusual_delimiters(soap_matcher_with_mock):
    # Slash delimiter
    result = soap_matcher_with_mock.match("House of Mammoth / Alive")
    assert result.matched is not None
    assert result.matched["maker"] == "House of Mammoth"
    assert result.matched["scent"] == "Alive"

    # Colon delimiter
    result = soap_matcher_with_mock.match("House of Mammoth: Alive")
    assert result.matched is not None
    assert result.matched["maker"] == "House of Mammoth"
    assert result.matched["scent"] == "Alive"


def test_ambiguous_multiple_matches(soap_matcher_with_mock):
    # Add a scent pattern that could match multiple entries
    # (simulate by patching scent_patterns directly)
    matcher = soap_matcher_with_mock
    original_patterns = matcher.scent_patterns.copy()
    matcher.scent_patterns.append(
        {
            "maker": "House of Mammoth",
            "scent": "Alive",
            "pattern": "alive|seville",
            "regex": __import__("re").compile("alive|seville", __import__("re").IGNORECASE),
        }
    )
    # Should still match the most specific (longest) pattern first
    # Pass just the normalized string to matchers
    result = matcher.match("House of Mammoth - Alive")
    assert result.matched is not None
    matcher.scent_patterns = original_patterns  # Restore


def test_invalid_regex_pattern_handling():
    # Should not raise exception, should skip invalid pattern
    mock_catalog = {
        "Test Brand": {
            "patterns": ["[invalid regex"],
            "scents": {"Test Scent": {"patterns": ["test.*scent"]}},
        }
    }
    with patch("sotd.utils.yaml_loader.load_yaml_with_nfc", return_value=mock_catalog):
        matcher = SoapMatcher()
        # Should still match valid scent pattern
        # Pass just the normalized string to matchers
        result = matcher.match("Test Brand - Test Scent")
        assert result.matched is not None


def test_enhanced_regex_error_reporting():
    """Test that malformed regex patterns produce detailed error messages."""
    mock_catalog = {
        "Test Brand": {
            "patterns": [r"invalid[regex"],  # Malformed regex - missing closing bracket
            "scents": {"Test Scent": {"patterns": ["test.*scent"]}},
        }
    }

    # Mock the load_yaml_with_nfc function to return our mock catalog
    with patch("sotd.match.soap_matcher.load_yaml_with_nfc", return_value=mock_catalog):
        with pytest.raises(ValueError) as exc_info:
            SoapMatcher()

        error_message = str(exc_info.value)
        assert "Invalid regex pattern" in error_message
        assert "invalid[regex" in error_message
        assert "File: data/soaps.yaml" in error_message
        assert "Maker: Test Brand" in error_message
        assert "unterminated character set" in error_message  # The actual regex error
