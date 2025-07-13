# pylint: disable=redefined-outer-name

import yaml
import pytest
from sotd.match.razor_matcher import RazorMatcher


@pytest.fixture(scope="session")
def session_razor_catalog():
    """Session-scoped razor catalog for all tests."""
    return {
        "Wolfman": {
            "WR2": {"patterns": ["wolfman.*wr2"], "format": "DE"},
            "WR1": {"patterns": ["(Wolfman)?.*WR[\\s-]*1"], "format": "AC"},
        },
        "Gillette": {
            "Fatboy": {"patterns": ["fat\\s*boy"], "format": "DE"},
            "Tech": {"patterns": ["\\btech\\b"], "format": "DE"},
        },
        "Koraat": {
            "Moarteen (r/Wetshaving exclusive)": {
                "patterns": ["koraat.*moarteen"],
                "format": "Straight",
                "grind": "Full Hollow",
                "point": "Square",
                "width": "15/16",
            }
        },
        "Merkur": {"34C": {"patterns": ["merkur.*34c"], "format": "DE"}},
        "Böker": {"Straight": {"patterns": ["böker.*straight"], "format": "Straight"}},
        "Feather": {"Shavette": {"patterns": ["feather.*artist.*club"], "format": "Shavette (AC)"}},
    }


@pytest.fixture(scope="session")
def session_correct_matches():
    """Session-scoped correct matches for all tests."""
    return {
        "razor": {
            "Koraat": {"Moarteen (r/Wetshaving exclusive)": ["Koraat Moarteen"]},
            "Merkur": {"34C": ["Merkur 34C"]},
            "Böker": {"Straight": ["Böker Straight"]},
            "Feather": {"Shavette": ["Feather Artist Club"]},
        }
    }


@pytest.fixture(scope="session")
def session_matcher(tmp_path_factory, session_razor_catalog, session_correct_matches):
    """Session-scoped RazorMatcher instance."""
    tmp_path = tmp_path_factory.mktemp("razor_matcher_tests")

    # Create catalog file
    catalog_file = tmp_path / "razors.yaml"
    with catalog_file.open("w", encoding="utf-8") as f:
        yaml.dump(session_razor_catalog, f)

    # Create correct matches file
    correct_matches_file = tmp_path / "correct_matches.yaml"
    with correct_matches_file.open("w", encoding="utf-8") as f:
        yaml.dump(session_correct_matches, f)

    return RazorMatcher(catalog_path=catalog_file, correct_matches_path=correct_matches_file)


@pytest.fixture(scope="class")
def matcher(session_matcher):
    """Class-scoped matcher that uses session-scoped instance."""
    return session_matcher


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
      - 'b[öo]ker.*(\s+straight)?'
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

    def test_no_match_returns_none(self, matcher):
        """Test that unmatched razors return None for matched field."""
        result = matcher.match("Unknown Razor Brand")

        assert result["matched"] is None
        assert result["pattern"] is None
        assert result["match_type"] is None


def test_correct_matches_priority_before_regex(tmp_path):
    """Test that correct matches take priority over regex patterns."""
    # Create a test catalog with a regex pattern that would match
    catalog_content = """
Koraat:
  Moarteen:
    patterns:
      - "koraat.*moarteen"
    format: "Straight"
"""
    catalog_file = tmp_path / "razors.yaml"
    catalog_file.write_text(catalog_content)

    # Create a correct_matches.yaml with a different match for the same input
    correct_matches_content = """
razor:
  Koraat:
    Moarteen:
      - "Koraat Moarteen"
"""
    correct_matches_file = tmp_path / "correct_matches.yaml"
    correct_matches_file.write_text(correct_matches_content)

    matcher = RazorMatcher(catalog_path=catalog_file, correct_matches_path=correct_matches_file)

    # This should match the correct match, not the regex pattern
    result = matcher.match("Koraat Moarteen")
    assert result["matched"]["brand"] == "Koraat"
    assert result["matched"]["model"] == "Moarteen"
    assert result["match_type"] == "exact"


def test_regex_fallback_when_not_in_correct_matches(tmp_path):
    """Test that regex patterns are used when not in correct matches."""
    # Create a test catalog with a regex pattern
    catalog_content = """
Koraat:
  Moarteen:
    patterns:
      - "koraat.*moarteen"
    format: "Straight"
"""
    catalog_file = tmp_path / "razors.yaml"
    catalog_file.write_text(catalog_content)

    # Create an empty correct_matches.yaml
    correct_matches_content = """
razor: {}
"""
    correct_matches_file = tmp_path / "correct_matches.yaml"
    correct_matches_file.write_text(correct_matches_content)

    matcher = RazorMatcher(catalog_path=catalog_file, correct_matches_path=correct_matches_file)

    # This should match via regex pattern
    result = matcher.match("Koraat Moarteen")
    assert result["matched"]["brand"] == "Koraat"
    assert result["matched"]["model"] == "Moarteen"
    assert result["match_type"] == "regex"
