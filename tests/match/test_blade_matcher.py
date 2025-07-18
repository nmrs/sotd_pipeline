# pylint: disable=redefined-outer-name

import pytest
from pathlib import Path

from sotd.match.blade_matcher import BladeMatcher


@pytest.fixture(scope="session")
def session_matcher():
    """Session-scoped matcher to avoid repeated YAML loading."""
    yaml_content = """
DE:
  Feather:
    DE:
      patterns:
        - feather
  Astra:
    Superior Platinum (Green)":
      patterns:
        - astra.*sp
  Derby:
    Extra:
      patterns:
        - derby.*extra
  Gillette:
    Perma-Sharp:
      patterns:
        - perma.*sharp

GEM:
  Accuforge:
    PTFE:
      patterns:
        - accuforge

AC:
  Feather:
    Pro:
      patterns:
        - feather.*pro

Half DE:
  Gillette:
    Perma-Sharp SE:
      patterns:
        - perma.*sharp
"""
    # Create a temporary file for the session
    import tempfile
    import os

    temp_file = tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False)
    temp_file.write(yaml_content)
    temp_file.close()

    matcher = BladeMatcher(catalog_path=Path(temp_file.name))

    # Clean up the temp file after the session
    def cleanup():
        try:
            os.unlink(temp_file.name)
        except OSError:
            pass

    # Register cleanup
    import atexit

    atexit.register(cleanup)

    return matcher


@pytest.fixture(scope="class")
def matcher(session_matcher):
    """Class-scoped matcher that uses session-scoped instance."""
    # Clear cache to prevent pollution between tests
    session_matcher.clear_cache()
    return session_matcher


@pytest.fixture(scope="class")
def correct_matches_matcher(tmp_path_factory):
    """Create a BladeMatcher with correct matches for testing."""
    tmp_path = tmp_path_factory.mktemp("correct_matches_tests")

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

    return BladeMatcher(catalog_path=catalog_file, correct_matches_path=correct_matches_file)


# Parameterized use count tests
@pytest.mark.parametrize(
    "input_text,expected_brand,expected_model",
    [
        ("Feather (3)", "Feather", "DE"),
        ("Astra SP [5]", "Astra", "Superior Platinum (Green)"),
        ("Derby Extra {7}", "Derby", "Extra"),
        ("Feather (x3)", "Feather", "DE"),
        ("Astra SP [5x]", "Astra", "Superior Platinum (Green)"),
        ("Derby Extra (2X)", "Derby", "Extra"),
        ("Derby Extra", "Derby", "Extra"),  # Without use count
    ],
)
def test_match_with_use_count_variations(matcher, input_text, expected_brand, expected_model):
    """Test blade matching with various use count formats."""
    result = matcher.match(input_text)
    assert result.matched["brand"] == expected_brand
    assert result.matched["model"] == expected_model
    # Blade use count is now handled in the enrich phase
    assert result.original == input_text


# Parameterized format/context tests
@pytest.mark.parametrize(
    "input_text,context,expected_brand,expected_model,expected_format",
    [
        ("Perma-Sharp", "DE", "Gillette", "Perma-Sharp", "DE"),
        ("Perma-Sharp", "HALF DE", "Gillette", "Perma-Sharp SE", "Half DE"),
        (
            "Perma-Sharp 1/2 DE",
            "HALF DE",
            "Gillette",
            "Perma-Sharp SE",
            "Half DE",
        ),  # Context-first: should match Half DE model if it exists
        ("DE Perma-Sharp", "DE", "Gillette", "Perma-Sharp", "DE"),
        (
            "DE Perma-Sharp",
            "HALF DE",
            "Gillette",
            "Perma-Sharp SE",
            "Half DE",
        ),  # DE in text overrides context
        ("Perma-Sharp", None, "Gillette", "Perma-Sharp", "DE"),  # No context defaults to DE
    ],
)
def test_format_context_matching(
    matcher, input_text, context, expected_brand, expected_model, expected_format
):
    """Test blade matching with different format contexts."""
    if context:
        result = matcher.match_with_context(input_text, context)
    else:
        result = matcher.match(input_text)

    assert result.matched is not None
    assert result.matched["brand"] == expected_brand
    assert result.matched["model"] == expected_model
    assert result.matched["format"] == expected_format
    assert result.original == input_text


def test_regex_sorting_order(matcher):
    # Retrieve the compiled patterns directly
    patterns = matcher.patterns
    # Extract the original regex patterns from the compiled list
    regex_strings = [pattern[3] for pattern in patterns]
    # Check that patterns are sorted by length descending
    lengths = [len(p) for p in regex_strings]
    assert lengths == sorted(lengths, reverse=True), "Patterns are not sorted by length descending"


def test_format_prioritization_with_multiple_matches(matcher):
    """Test that format prioritization works with multiple potential matches."""
    # This test verifies the format prioritization logic works correctly
    # when there are multiple potential matches for the same blade
    result = matcher.match_with_context("Perma-Sharp", "DE")
    assert result.matched["format"] == "DE"

    result = matcher.match_with_context("Perma-Sharp", "HALF DE")
    assert result.matched["format"] == "Half DE"


def test_format_fallback_for_half_de_razors(matcher):
    """Test that Half DE razors use Half DE format when context is HALF DE."""
    result = matcher.match_with_context("DE Perma-Sharp", "HALF DE")
    assert result.matched["format"] == "Half DE"  # Should use Half DE due to context


def test_correct_matches_priority_before_regex(correct_matches_matcher):
    """Test that correct matches take priority over regex patterns."""
    # This should match the correct match, not the regex pattern
    result = correct_matches_matcher.match("Gillette Nacet")
    assert result.matched["brand"] == "Gillette"
    assert result.matched["model"] == "Nacet"
    assert result.match_type == "exact"


def test_fail_fast_on_malformed_yaml_data(tmp_path):
    """Test that malformed YAML data causes immediate failure."""
    malformed_yaml = """
DE:
  Feather:
    DE:
      patterns: null  # This should cause an error when trying to iterate
"""
    catalog_file = tmp_path / "malformed_blades.yaml"
    catalog_file.write_text(malformed_yaml)

    with pytest.raises(Exception):
        BladeMatcher(catalog_path=catalog_file)


def test_fail_fast_on_non_dict_entry(tmp_path):
    """Test that non-dict entries in YAML cause immediate failure."""
    invalid_yaml = """
DE:
  Feather: "this should be a dict, not a string"
"""
    catalog_file = tmp_path / "invalid_blades.yaml"
    catalog_file.write_text(invalid_yaml)

    with pytest.raises(Exception):
        BladeMatcher(catalog_path=catalog_file)


def test_flexible_fallback_system():
    """Test the new flexible fallback system with format tracking."""
    # Create a test catalog with blades in different formats
    yaml_content = """
DE:
  Feather:
    DE:
      patterns:
        - feather
  Astra:
    Superior Platinum (Green):
      patterns:
        - astra
GEM:
  Personna:
    GEM PTFE:
      patterns:
        - ptfe
        - gem
AC:
  Feather:
    Pro:
      patterns:
        - feather.*pro
INJECTOR:
  Schick:
    Injector:
      patterns:
        - schick
FHS:
  Feather:
    FHS-1:
      patterns:
        - fhs
"""
    import tempfile
    import os

    temp_file = tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False)
    temp_file.write(yaml_content)
    temp_file.close()

    matcher = BladeMatcher(catalog_path=Path(temp_file.name))

    def cleanup():
        try:
            os.unlink(temp_file.name)
        except OSError:
            pass

    import atexit

    atexit.register(cleanup)

    # Test 1: DE razor with DE blade (no fallback needed)
    result = matcher.match_with_context("Feather", "DE")
    assert result.matched is not None
    assert result.matched["format"] == "DE"
    assert result.matched["brand"] == "Feather"

    # Test 2: GEM razor with blade that doesn't exist in GEM, should fallback to DE
    result = matcher.match_with_context("Feather", "GEM")
    assert result.matched is not None
    assert result.matched["format"] == "DE"  # Should fallback to DE
    assert result.matched["brand"] == "Feather"

    # Test 3: AC razor with blade that doesn't exist in AC, should fallback to DE
    result = matcher.match_with_context("Astra", "AC")
    assert result.matched is not None
    assert result.matched["format"] == "DE"  # Should fallback to DE
    assert result.matched["brand"] == "Astra"

    # Test 4: INJECTOR razor with blade that doesn't exist in INJECTOR, should fallback to DE
    result = matcher.match_with_context("Astra", "INJECTOR")
    assert result.matched is not None
    assert result.matched["format"] == "DE"  # Should fallback to DE
    assert result.matched["brand"] == "Astra"

    # Test 5: FHS razor with blade that doesn't exist in FHS, should fallback to DE
    result = matcher.match_with_context("Astra", "FHS")
    assert result.matched is not None
    assert result.matched["format"] == "DE"  # Should fallback to DE
    assert result.matched["brand"] == "Astra"


def test_format_tracking_optimization():
    """Test that the format tracking optimization prevents redundant searches."""
    # Create a test catalog with specific patterns
    yaml_content = """
DE:
  Feather:
    DE:
      patterns:
        - feather
GEM:
  Personna:
    GEM PTFE:
      patterns:
        - ptfe
AC:
  Feather:
    Pro:
      patterns:
        - feather.*pro
"""
    import tempfile
    import os

    temp_file = tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False)
    temp_file.write(yaml_content)
    temp_file.close()

    matcher = BladeMatcher(catalog_path=Path(temp_file.name))

    def cleanup():
        try:
            os.unlink(temp_file.name)
        except OSError:
            pass

    import atexit

    atexit.register(cleanup)

    # Test 1: DE razor searches DE, should not search DE again in fallback
    result = matcher.match_with_context("Feather", "DE")
    assert result.matched is not None
    assert result.matched["format"] == "DE"

    # Test 2: GEM razor searches GEM first, then falls back to DE (not GEM again)
    result = matcher.match_with_context("Feather", "GEM")
    assert result.matched is not None
    assert result.matched["format"] == "DE"  # Should fallback to DE, not search GEM twice

    # Test 3: AC razor searches AC first, then falls back to DE (not AC again)
    result = matcher.match_with_context("Feather Pro", "AC")
    assert result.matched is not None
    # Should match AC format since "feather.*pro" pattern exists
    assert result.matched["format"] == "AC"


def test_straight_razor_skip():
    """Test that straight razors skip blade matching entirely."""
    # Create a simple test catalog
    yaml_content = """
DE:
  Feather:
    DE:
      patterns:
        - feather
"""
    import tempfile
    import os

    temp_file = tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False)
    temp_file.write(yaml_content)
    temp_file.close()

    matcher = BladeMatcher(catalog_path=Path(temp_file.name))

    def cleanup():
        try:
            os.unlink(temp_file.name)
        except OSError:
            pass

    import atexit

    atexit.register(cleanup)

    # Test that straight razors return no match for any blade
    result = matcher.match_with_context("Feather", "STRAIGHT")
    assert result.matched is None
    assert result.match_type is None
    assert result.pattern is None
    assert result.original == "Feather"

    # Test with any blade string
    result = matcher.match_with_context("Any Blade", "STRAIGHT")
    assert result.matched is None
    assert result.match_type is None
    assert result.pattern is None
    assert result.original == "Any Blade"


def test_half_de_special_fallback():
    """Test that Half DE razors use the special Half DE → DE fallback."""
    # Create a test catalog with Half DE and DE blades
    yaml_content = """
DE:
  Feather:
    DE:
      patterns:
        - feather
  Astra:
    Superior Platinum (Green):
      patterns:
        - astra
Half DE:
  Gillette:
    Perma-Sharp SE:
      patterns:
        - perma.*sharp
"""
    import tempfile
    import os

    temp_file = tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False)
    temp_file.write(yaml_content)
    temp_file.close()

    matcher = BladeMatcher(catalog_path=Path(temp_file.name))

    def cleanup():
        try:
            os.unlink(temp_file.name)
        except OSError:
            pass

    import atexit

    atexit.register(cleanup)

    # Test 1: Half DE razor with blade that exists in Half DE
    result = matcher.match_with_context("Perma-Sharp", "HALF DE")
    assert result.matched is not None
    assert result.matched["format"] == "Half DE"
    assert result.matched["brand"] == "Gillette"

    # Test 2: Half DE razor with blade that only exists in DE (should fallback)
    result = matcher.match_with_context("Feather", "HALF DE")
    assert result.matched is not None
    assert result.matched["format"] == "DE"  # Should fallback to DE
    assert result.matched["brand"] == "Feather"

    # Test 3: Half DE razor with blade that only exists in DE (should fallback)
    result = matcher.match_with_context("Astra", "HALF DE")
    assert result.matched is not None
    assert result.matched["format"] == "DE"  # Should fallback to DE
    assert result.matched["brand"] == "Astra"


def test_non_context_match_fallback():
    """Test that the non-context match method also uses the flexible fallback."""
    # Create a test catalog
    yaml_content = """
DE:
  Feather:
    DE:
      patterns:
        - feather
GEM:
  Personna:
    GEM PTFE:
      patterns:
        - ptfe
"""
    import tempfile
    import os

    temp_file = tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False)
    temp_file.write(yaml_content)
    temp_file.close()

    matcher = BladeMatcher(catalog_path=Path(temp_file.name))

    def cleanup():
        try:
            os.unlink(temp_file.name)
        except OSError:
            pass

    import atexit

    atexit.register(cleanup)

    # Test that non-context matching uses flexible fallback
    result = matcher.match("Feather")
    assert result.matched is not None
    assert result.matched["format"] == "DE"
    assert result.matched["brand"] == "Feather"

    # Test with a blade that doesn't exist in any format
    result = matcher.match("NonexistentBlade")
    assert result.matched is None
    assert result.match_type is None
    assert result.pattern is None
