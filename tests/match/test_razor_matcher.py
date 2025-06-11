import yaml
import pytest
from sotd.match.razor_matcher import RazorMatcher


@pytest.fixture
def matcher(tmp_path):
    yaml_content = r"""
Wolfman:
  WR2:
    patterns:
      - 'wolfman.*wr2'
  WR1:
    patterns:
      - '(Wolfman)?.*WR[\s-]*1'
    format: AC
Gillette:
  Fatboy:
    patterns:
      - 'fat\s*boy'
  Tech:
    patterns:
      - '\btech\b'
"""
    path = tmp_path / "razors.yaml"
    path.write_text(yaml_content)
    return RazorMatcher(catalog_path=path)


def test_matches_wr2_with_default_format(matcher):
    result = matcher.match("Wolfman WR2")
    assert result["matched"] == {"brand": "Wolfman", "model": "WR2", "format": "DE"}
    assert "wr2" in result["pattern"].lower()


def test_matches_wr1_with_explicit_format(matcher):
    result = matcher.match("Wolfman WR1")
    assert result["matched"]["format"] == "AC"


def test_matches_fatboy(matcher):
    result = matcher.match("Gillette Fatboy")
    assert result["matched"]["brand"] == "Gillette"
    assert result["matched"]["model"] == "Fatboy"


def test_unmatched_returns_nulls(matcher):
    result = matcher.match("Unknown Razor")
    assert result["matched"] is None
    assert result["pattern"] is None


def test_boker_king_cutter_has_highest_priority_pattern(tmp_path):
    yaml_content = r"""
Böker:
  KingCutter:
    patterns:
      - 'b[oö]ker.*king.*cutter(?# PAD FOR PRIORITY LENGTH xxxxxxxxxxxx)'
  Fallback:
    patterns:
      - 'b[oö]ker.*king.*cutter(?# PAD FOR PRIORITY LENGTH xxxxxxxxxxxx)'
      - 'b[öo]ker.*(\s+straight)?'
"""
    path = tmp_path / "razors.yaml"
    path.write_text(yaml_content)
    matcher = RazorMatcher(catalog_path=path)

    result = matcher.match("Boker King Cutter")
    assert result["matched"]["brand"] == "Böker"
    assert result["matched"]["model"] == "KingCutter"
    assert "king.*cutter" in result["pattern"]
    assert "xxxxxxxxxxxx" in result["pattern"]


def test_duplicate_model_key_raises_constructor_error(tmp_path):
    yaml_content = r"""
Böker:
  KingCutter:
    patterns:
      - 'b[oö]ker.*king.*cutter'
  KingCutter:
    patterns:
      - 'b[oö]ker.*duplicate'
"""
    path = tmp_path / "razors.yaml"
    path.write_text(yaml_content)
    with pytest.raises(yaml.constructor.ConstructorError):
        RazorMatcher(catalog_path=path)


def test_regex_sorting_order(matcher):
    # Retrieve the compiled patterns directly
    patterns = matcher.patterns
    # Extract the original regex patterns from the compiled list
    regex_strings = [pattern[3] for pattern in patterns]
    # Check that patterns are sorted by length descending
    lengths = [len(p) for p in regex_strings]
    assert lengths == sorted(lengths, reverse=True), "Patterns are not sorted by length descending"
