# pylint: disable=redefined-outer-name

import pytest
from sotd.match.blade_matcher import BladeMatcher


@pytest.fixture
def matcher(tmp_path):
    yaml_content = r"""
DE:
  Feather:
    DE:
      patterns:
        - feather

  Astra:
    Superior Platinum (Green):
      patterns:
        - astra.*sp
        - astra.*plat
        - astra.*green
        - astra

  Derby:
    Extra:
      patterns:
        - derby.*extra

  Gillette:
    Perma-Sharp:
      patterns:
        - perma\s*-*sharp

Half DE:
  Gillette:
    Perma-Sharp SE:
      patterns:
        - ^(?!.*\bde\b).*perma\s*-*sharp
"""
    path = tmp_path / "blades.yaml"
    path.write_text(yaml_content)
    return BladeMatcher(catalog_path=path)


def test_match_with_use_count_parentheses(matcher):
    result = matcher.match("Feather (3)")
    assert result["matched"]["brand"] == "Feather"
    assert result["matched"]["model"] == "DE"
    # Blade use count is now handled in the enrich phase
    assert result["original"] == "Feather (3)"


def test_match_with_use_count_brackets(matcher):
    result = matcher.match("Astra SP [5]")
    assert result["matched"]["brand"] == "Astra"
    assert result["matched"]["model"] == "Superior Platinum (Green)"
    # Blade use count is now handled in the enrich phase
    assert result["original"] == "Astra SP [5]"


def test_match_with_use_count_curly_braces(matcher):
    result = matcher.match("Derby Extra {7}")
    assert result["matched"]["brand"] == "Derby"
    assert result["matched"]["model"] == "Extra"
    # Blade use count is now handled in the enrich phase
    assert result["original"] == "Derby Extra {7}"


def test_match_with_use_count_x_prefix(matcher):
    result = matcher.match("Feather (x3)")
    assert result["matched"]["brand"] == "Feather"
    assert result["matched"]["model"] == "DE"
    # Blade use count is now handled in the enrich phase
    assert result["original"] == "Feather (x3)"


def test_match_with_use_count_x_suffix(matcher):
    result = matcher.match("Astra SP [5x]")
    assert result["matched"]["brand"] == "Astra"
    assert result["matched"]["model"] == "Superior Platinum (Green)"
    # Blade use count is now handled in the enrich phase
    assert result["original"] == "Astra SP [5x]"


def test_match_with_use_count_uppercase_x(matcher):
    result = matcher.match("Derby Extra (2X)")
    assert result["matched"]["brand"] == "Derby"
    assert result["matched"]["model"] == "Extra"
    # Blade use count is now handled in the enrich phase
    assert result["original"] == "Derby Extra (2X)"


def test_match_without_use_count(matcher):
    result = matcher.match("Derby Extra")
    assert result["matched"]["brand"] == "Derby"
    assert result["matched"]["model"] == "Extra"
    # Blade use count is now handled in the enrich phase
    assert result["original"] == "Derby Extra"


def test_regex_sorting_order(matcher):
    # Retrieve the compiled patterns directly
    patterns = matcher.patterns
    # Extract the original regex patterns from the compiled list
    regex_strings = [pattern[3] for pattern in patterns]
    # Check that patterns are sorted by length descending
    lengths = [len(p) for p in regex_strings]
    assert lengths == sorted(lengths, reverse=True), "Patterns are not sorted by length descending"


# Test cases for DE vs SE Perma-Sharp blade matching with format prioritization
def test_de_razor_with_perma_sharp_blade(matcher):
    """Test DE razor (Gillette Super Speed) with Perma-Sharp blade - should match DE format"""
    result = matcher.match_with_context("Perma-Sharp", "DE")
    assert result["matched"]["brand"] == "Gillette"
    assert result["matched"]["model"] == "Perma-Sharp"
    assert result["matched"]["format"] == "DE"
    assert result["original"] == "Perma-Sharp"


def test_se_razor_with_perma_sharp_blade(matcher):
    """Test SE razor (Leaf Twig) with Perma-Sharp blade - should match Half DE format"""
    result = matcher.match_with_context("Perma-Sharp", "HALF DE")
    assert result["matched"]["brand"] == "Gillette"
    assert result["matched"]["model"] == "Perma-Sharp SE"
    assert result["matched"]["format"] == "Half DE"
    assert result["original"] == "Perma-Sharp"


def test_se_razor_with_perma_sharp_half_de_blade(matcher):
    """Test SE razor with 'Perma-Sharp 1/2 DE' blade - should match DE format due to DE in text"""
    result = matcher.match_with_context("Perma-Sharp 1/2 DE", "HALF DE")
    # Should not match SE pattern due to "DE" in text, so falls back to DE pattern
    assert result["matched"]["brand"] == "Gillette"
    assert result["matched"]["model"] == "Perma-Sharp"
    assert result["matched"]["format"] == "DE"
    assert result["original"] == "Perma-Sharp 1/2 DE"


def test_de_razor_with_de_perma_sharp_blade(matcher):
    """Test DE razor with 'DE Perma-Sharp' blade - should match DE format"""
    result = matcher.match_with_context("DE Perma-Sharp", "DE")
    assert result["matched"]["brand"] == "Gillette"
    assert result["matched"]["model"] == "Perma-Sharp"
    assert result["matched"]["format"] == "DE"
    assert result["original"] == "DE Perma-Sharp"


def test_se_razor_with_de_perma_sharp_blade(matcher):
    """Test SE razor with 'DE Perma-Sharp' blade - should match DE format due to DE in text"""
    result = matcher.match_with_context("DE Perma-Sharp", "HALF DE")
    # Should not match SE pattern due to "DE" in text, so falls back to DE pattern
    assert result["matched"]["brand"] == "Gillette"
    assert result["matched"]["model"] == "Perma-Sharp"
    assert result["matched"]["format"] == "DE"
    assert result["original"] == "DE Perma-Sharp"


def test_simple_perma_sharp_without_context(matcher):
    """Test simple Perma-Sharp without context - should match SE format (more specific pattern)"""
    result = matcher.match("Perma-Sharp")
    assert result["matched"]["brand"] == "Gillette"
    assert result["matched"]["model"] == "Perma-Sharp SE"
    assert result["matched"]["format"] == "Half DE"
    assert result["original"] == "Perma-Sharp"


def test_perma_sharp_with_use_count_de_context(matcher):
    """Test Perma-Sharp with use count in DE context"""
    result = matcher.match_with_context("Perma-Sharp (3)", "DE")
    assert result["matched"]["brand"] == "Gillette"
    assert result["matched"]["model"] == "Perma-Sharp"
    assert result["matched"]["format"] == "DE"
    assert result["original"] == "Perma-Sharp (3)"


def test_perma_sharp_with_use_count_se_context(matcher):
    """Test Perma-Sharp with use count in SE context"""
    result = matcher.match_with_context("Perma-Sharp [5]", "HALF DE")
    assert result["matched"]["brand"] == "Gillette"
    assert result["matched"]["model"] == "Perma-Sharp SE"
    assert result["matched"]["format"] == "Half DE"
    assert result["original"] == "Perma-Sharp [5]"


def test_format_prioritization_with_multiple_matches(matcher):
    """Test that format prioritization works correctly when multiple patterns match"""
    # Both DE and SE patterns should match "Perma-Sharp" in SE context
    # But SE pattern should be prioritized due to format matching
    result = matcher.match_with_context("Perma-Sharp", "HALF DE")
    assert result["matched"]["format"] == "Half DE"
    assert result["matched"]["model"] == "Perma-Sharp SE"


def test_format_fallback_for_half_de_razors(matcher):
    """Test that Half DE razors can fall back to DE blades when SE pattern doesn't match"""
    # "Perma-Sharp 1/2 DE" should not match SE pattern due to "DE" in text
    # But should fall back to DE pattern since Half DE can use DE blades
    result = matcher.match_with_context("Perma-Sharp 1/2 DE", "HALF DE")
    assert result["matched"]["format"] == "DE"
    assert result["matched"]["model"] == "Perma-Sharp"


def test_correct_matches_priority_before_regex(tmp_path):
    """Test that correct matches are checked before regex patterns for blades."""
    # Create a test catalog with a regex pattern that would match
    catalog_content = """
DE:
  Gillette:
    Nacet:
      patterns:
        - "gillette.*nacet"
      format: "DE"
"""
    catalog_file = tmp_path / "blades.yaml"
    catalog_file.write_text(catalog_content)

    # Create a correct_matches.yaml with a different match for the same input
    correct_matches_content = """
blade:
  DE:
    Gillette:
      Nacet:
        - "Gillette Nacet"
"""
    correct_matches_file = tmp_path / "correct_matches.yaml"
    correct_matches_file.write_text(correct_matches_content)

    matcher = BladeMatcher(catalog_path=catalog_file, correct_matches_path=correct_matches_file)

    # Test that the input matches the correct_matches entry, not the regex
    result = matcher.match("Gillette Nacet")

    # Should match from correct_matches (exact match)
    assert result["matched"] is not None
    assert result["matched"]["brand"] == "Gillette"
    assert result["matched"]["model"] == "Nacet"
    assert result["match_type"] == "exact"
    # No pattern used for correct matches
    assert result["pattern"] is None


def test_fail_fast_on_malformed_yaml_data(tmp_path):
    """Test that blade matcher fails fast when encountering malformed YAML data."""
    # Create malformed YAML with list entries instead of dict entries
    malformed_yaml = """
DE:
  Feather:
    DE:
      - feather  # This is a list, not a dict with patterns
  Astra:
    SP:
      patterns:
        - astra.*sp
"""
    path = tmp_path / "malformed_blades.yaml"
    path.write_text(malformed_yaml)

    # The matcher should fail fast when trying to compile patterns
    with pytest.raises(AttributeError) as exc_info:
        BladeMatcher(catalog_path=path)

    # Verify the error message indicates the issue
    error_msg = str(exc_info.value).lower()
    assert "list" in error_msg or "get" in error_msg


def test_fail_fast_on_non_dict_entry(tmp_path):
    """Test that blade matcher fails fast when encountering non-dict entries."""
    # Create YAML with string entries instead of dict entries
    malformed_yaml = """
DE:
  Feather:
    DE: "feather"  # This is a string, not a dict with patterns
  Astra:
    SP:
      patterns:
        - astra.*sp
"""
    path = tmp_path / "malformed_blades.yaml"
    path.write_text(malformed_yaml)

    # The matcher should fail fast when trying to compile patterns
    with pytest.raises(AttributeError) as exc_info:
        BladeMatcher(catalog_path=path)

    # Verify the error message indicates the issue
    error_msg = str(exc_info.value).lower()
    assert "str" in error_msg or "get" in error_msg
