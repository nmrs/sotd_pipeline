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
    assert result["matched"]["blade"] == "Feather DE"
    assert result["matched"]["use"] == 3
    assert result["original"] == "Feather (3)"


def test_match_with_use_count_brackets(matcher):
    result = matcher.match("Astra SP [5]")
    assert result["matched"]["blade"] == "Astra SP"
    assert result["matched"]["use"] == 5
    assert result["original"] == "Astra SP [5]"


def test_match_without_use_count(matcher):
    result = matcher.match("Derby Extra")
    assert result["matched"]["blade"] == "Derby Extra"
    assert result["matched"]["use"] is None
    assert result["original"] == "Derby Extra"
