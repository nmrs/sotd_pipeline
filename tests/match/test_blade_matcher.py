# pylint: disable=redefined-outer-name

import pytest
from sotd.match.blade_matcher import BladeMatcher


@pytest.fixture
def matcher(tmp_path):
    yaml_content = """
Feather:
  DE:
    patterns:
      - feather

Astra:
  SP:
    format: DE
    patterns:
      - astra.*sp

Derby:
  Extra:
    format: DE
    patterns:
      - derby.*extra
"""
    path = tmp_path / "blades.yaml"
    path.write_text(yaml_content)
    return BladeMatcher(catalog_path=path)


def test_match_with_use_count_parentheses(matcher):
    result = matcher.match("Feather (3)")
    assert result["matched"]["brand"] == "Feather"
    assert result["matched"]["model"] == "DE"
    assert result["matched"]["use"] == 3
    assert result["original"] == "Feather (3)"


def test_match_with_use_count_brackets(matcher):
    result = matcher.match("Astra SP [5]")
    assert result["matched"]["brand"] == "Astra"
    assert result["matched"]["model"] == "SP"
    assert result["matched"]["use"] == 5
    assert result["original"] == "Astra SP [5]"


def test_match_with_use_count_curly_braces(matcher):
    result = matcher.match("Derby Extra {7}")
    assert result["matched"]["brand"] == "Derby"
    assert result["matched"]["model"] == "Extra"
    assert result["matched"]["use"] == 7
    assert result["original"] == "Derby Extra {7}"


def test_match_with_use_count_x_prefix(matcher):
    result = matcher.match("Feather (x3)")
    assert result["matched"]["brand"] == "Feather"
    assert result["matched"]["model"] == "DE"
    assert result["matched"]["use"] == 3
    assert result["original"] == "Feather (x3)"


def test_match_with_use_count_x_suffix(matcher):
    result = matcher.match("Astra SP [5x]")
    assert result["matched"]["brand"] == "Astra"
    assert result["matched"]["model"] == "SP"
    assert result["matched"]["use"] == 5
    assert result["original"] == "Astra SP [5x]"


def test_match_with_use_count_uppercase_x(matcher):
    result = matcher.match("Derby Extra (2X)")
    assert result["matched"]["brand"] == "Derby"
    assert result["matched"]["model"] == "Extra"
    assert result["matched"]["use"] == 2
    assert result["original"] == "Derby Extra (2X)"


def test_match_without_use_count(matcher):
    result = matcher.match("Derby Extra")
    assert result["matched"]["brand"] == "Derby"
    assert result["matched"]["model"] == "Extra"
    assert result["matched"]["use"] is None
    assert result["original"] == "Derby Extra"


def test_regex_sorting_order(matcher):
    # Retrieve the compiled patterns directly
    patterns = matcher.patterns
    # Extract the original regex patterns from the compiled list
    regex_strings = [pattern[3] for pattern in patterns]
    # Check that patterns are sorted by length descending
    lengths = [len(p) for p in regex_strings]
    assert lengths == sorted(lengths, reverse=True), "Patterns are not sorted by length descending"
