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
    if result["pattern"] is not None:
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
    def matcher(self, tmp_path):
        """Create a RazorMatcher instance for testing with temp files."""
        # Create temp catalog
        catalog_content = """
Koraat:
  Moarteen (r/Wetshaving exclusive):
    patterns:
      - "koraat.*moarteen"
    format: "Straight"
    grind: "Full Hollow"
    point: "Square"
    width: "15/16"
Merkur:
  34C:
    patterns:
      - "merkur.*34c"
    format: "DE"
Böker:
  Straight:
    patterns:
      - "böker.*straight"
    format: "Straight"
Feather:
  Shavette:
    patterns:
      - "feather.*artist.*club"
    format: "Shavette (AC)"
"""
        catalog_file = tmp_path / "razors.yaml"
        catalog_file.write_text(catalog_content)

        # Create temp correct_matches
        correct_matches_content = """
razor:
  Koraat:
    Moarteen (r/Wetshaving exclusive):
      - "Koraat Moarteen"
  Merkur:
    34C:
      - "Merkur 34C"
  Böker:
    Straight:
      - "Böker Straight"
  Feather:
    Shavette:
      - "Feather Artist Club"
"""
        correct_matches_file = tmp_path / "correct_matches.yaml"
        correct_matches_file.write_text(correct_matches_content)

        return RazorMatcher(catalog_path=catalog_file)

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


def test_correct_matches_priority_before_regex(tmp_path):
    """Test that correct matches are checked before regex patterns."""
    # Create a test catalog with a regex pattern that would match
    catalog_content = """
Karve:
  Christopher Bradley:
    patterns:
      - "karve.*cb"
    format: "DE"
"""
    catalog_file = tmp_path / "razors.yaml"
    catalog_file.write_text(catalog_content)

    # Create a correct_matches.yaml with a different match for the same input
    correct_matches_content = """
razor:
  Karve:
    Christopher Bradley:
      - "Karve CB"
"""
    correct_matches_file = tmp_path / "correct_matches.yaml"
    correct_matches_file.write_text(correct_matches_content)

    # Create matcher with test files
    matcher = RazorMatcher(catalog_path=catalog_file)

    # Test that the input matches the correct_matches entry, not the regex
    result = matcher.match("Karve CB")

    # Should match from correct_matches (exact match)
    assert result["matched"] is not None
    assert result["matched"]["brand"] == "Karve"
    assert result["matched"]["model"] == "Christopher Bradley"
    assert result["match_type"] == "exact"
    assert result["pattern"] is None  # No pattern used for correct matches


def test_regex_fallback_when_not_in_correct_matches(tmp_path):
    """Test that regex patterns are used when input is not in correct_matches."""
    # Create a test catalog with a regex pattern
    catalog_content = """
Karve:
  Christopher Bradley:
    patterns:
      - "karve.*cb"
    format: "DE"
"""
    catalog_file = tmp_path / "razors.yaml"
    catalog_file.write_text(catalog_content)

    # Create a correct_matches.yaml with a different entry
    correct_matches_content = """
razor:
  Other:
    Different:
      - "Different Razor"
"""
    correct_matches_file = tmp_path / "correct_matches.yaml"
    correct_matches_file.write_text(correct_matches_content)

    # Create matcher with test files
    matcher = RazorMatcher(catalog_path=catalog_file)

    # Patch the correct_matches to use our test file
    matcher.correct_matches = {"Other": {"Different": ["Different Razor"]}}

    # Test that the input matches via regex since it's not in correct_matches
    result = matcher.match("Karve CB")

    # Should match from regex patterns
    assert result["matched"] is not None
    assert result["matched"]["brand"] == "Karve"
    assert result["matched"]["model"] == "Christopher Bradley"
    assert result["match_type"] == "regex"
    assert result["pattern"] is not None  # Pattern should be used for regex matches
