# pylint: disable=redefined-outer-name

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


class TestRazorMatcher:
    """Test cases for RazorMatcher."""

    @pytest.fixture
    def matcher(self):
        """Create a RazorMatcher instance for testing."""
        return RazorMatcher()

    def test_match_koraat_moarteen_preserves_specifications(self, matcher):
        """Test that Koraat Moarteen specifications are preserved from catalog."""
        result = matcher.match("Koraat Moarteen")

        assert result["matched"] is not None
        assert result["matched"]["brand"] == "Koraat"
        assert result["matched"]["model"] == "Moarteen (r/Wetshaving exclusive)"
        assert result["matched"]["format"] == "Straight"

        # Verify that catalog specifications are preserved
        assert result["matched"]["grind"] == "Full Hollow"
        assert result["matched"]["point"] == "Square"
        assert result["matched"]["width"] == "15/16"

    def test_match_generic_razor_no_extra_specifications(self, matcher):
        """Test that generic razors don't have extra specifications."""
        result = matcher.match("Merkur 34C")

        assert result["matched"] is not None
        assert result["matched"]["brand"] == "Merkur"
        assert result["matched"]["model"] == "34C"
        assert result["matched"]["format"] == "DE"

        # Should only have basic fields, no extra specifications
        expected_keys = {"brand", "model", "format"}
        actual_keys = set(result["matched"].keys())
        assert actual_keys == expected_keys

    def test_match_straight_razor_with_format(self, matcher):
        """Test that straight razors with format specification are handled correctly."""
        result = matcher.match("Böker Straight")

        assert result["matched"] is not None
        assert result["matched"]["brand"] == "Böker"
        assert result["matched"]["model"] == "Straight"
        assert result["matched"]["format"] == "Straight"

        # Should only have basic fields for this entry
        expected_keys = {"brand", "model", "format"}
        actual_keys = set(result["matched"].keys())
        assert actual_keys == expected_keys

    def test_match_ac_format_razor(self, matcher):
        """Test that AC format razors are handled correctly."""
        result = matcher.match("Feather Artist Club")

        assert result["matched"] is not None
        assert result["matched"]["brand"] == "Feather"
        assert result["matched"]["model"] == "Shavette"
        assert result["matched"]["format"] == "Shavette (AC)"

    def test_no_match_returns_none(self, matcher):
        """Test that unmatched razors return None."""
        result = matcher.match("Nonexistent Razor")

        assert result["matched"] is None
        assert result["pattern"] is None
        assert result["match_type"] is None
