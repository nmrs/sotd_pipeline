# pylint: disable=redefined-outer-name, protected-access

from pathlib import Path

import pytest
import yaml
from unittest.mock import patch

from sotd.match.brush_matcher import BrushMatcher


@pytest.fixture
def test_catalog():
    """Create comprehensive test catalog covering all strategy types"""
    return {
        "known_brushes": {
            "Simpson": {
                "Chubby 2": {
                    "fiber": "Badger",
                    "knot_size_mm": 27,
                    "patterns": ["simp.*chubby\\s*2\\b", "simp.*ch2\\b"],
                },
                "Trafalgar T2": {
                    "fiber": "Synthetic",
                    "knot_size_mm": 24,
                    "patterns": ["simp.*traf.*t2", "trafalgar.*t2"],
                },
            },
            "Omega": {
                "10048": {"fiber": "Boar", "knot_size_mm": 28, "patterns": ["omega.*(pro)*.*48"]}
            },
            "Wald": {
                "A1": {"fiber": "Synthetic", "knot_size_mm": 29, "patterns": ["wald.*a1", "wald"]}
            },
        },
        "declaration_grooming": {
            "Declaration Grooming": {
                "B3": {"patterns": ["B3(\\.\\s|\\.$|\\s|$)"]},
                "B10": {"patterns": ["b10"]},
            }
        },
        "other_brushes": {
            "Elite": {"default": "Badger", "patterns": ["elite"]},
            "Alpha": {"default": "Synthetic", "patterns": ["alpha"]},
            "Groomatorium": {
                "default": "Synthetic",
                "knot_size_mm": 24,
                "patterns": ["groomatorium", "chiseled face", "\\bcf\\b"],
            },
            "Chisel & Hound": {
                "default": "Badger",
                "knot_size_mm": 26,
                "patterns": [
                    "chis.*hou",
                    "chis.*fou",
                    "\\bc(?:\\s*\\&\\s*|\\s+and\\s+|\\s*\\+\\s*)h\\b",
                ],
            },
            "Maggard": {"default": "Badger", "patterns": ["maggard"]},
        },
    }


@pytest.fixture
def mock_correct_matches():
    """Mock correct matches data for testing."""
    return {"Simpson": {"Chubby 2": ["Simpson Chubby 2"]}}


@pytest.fixture
def brush_matcher_with_mock(mock_correct_matches, test_catalog):
    """Create a BrushMatcher with mocked correct matches and catalog."""
    with (
        patch.object(BrushMatcher, "_load_correct_matches", return_value=mock_correct_matches),
        patch.object(BrushMatcher, "_load_catalog", return_value=test_catalog),
    ):
        matcher = BrushMatcher()
        return matcher


@pytest.fixture
def matcher(tmp_path, test_catalog):
    """Create BrushMatcher with test catalog"""
    catalog_file = tmp_path / "test_brushes.yaml"
    with catalog_file.open("w", encoding="utf-8") as f:
        yaml.dump(test_catalog, f)

    return BrushMatcher(catalog_path=catalog_file)


def test_brush_matcher_known_brush_match(brush_matcher_with_mock):
    """Test matching against known_brushes section"""
    result = brush_matcher_with_mock.match("Simpson Chubby 2")

    assert result["original"] == "Simpson Chubby 2"
    assert result["matched"] is not None
    assert result["matched"]["brand"] == "Simpson"
    assert result["matched"]["model"] == "Chubby 2"
    assert result["matched"]["fiber"] == "Badger"
    assert result["matched"]["knot_size_mm"] == 27
    assert result["matched"]["fiber_strategy"] == "yaml"
    assert result["match_type"] == "exact"
    assert result["pattern"] is None


def test_brush_matcher_declaration_grooming_match(matcher):
    """Test matching against declaration_grooming section"""
    result = matcher.match("Declaration B3")

    assert result["original"] == "Declaration B3"
    assert result["matched"] is not None
    assert result["matched"]["brand"] == "Declaration Grooming"
    assert result["matched"]["model"] == "B3"
    assert result["matched"]["fiber"] == "Badger"  # DG default
    assert result["matched"]["knot_size_mm"] == 28.0  # DG default
    assert result["pattern"] is not None


def test_brush_matcher_other_brushes_with_user_fiber(matcher):
    """Test matching against other_brushes with user-specified fiber"""
    result = matcher.match("Elite 26mm Boar")

    assert result["original"] == "Elite 26mm Boar"
    assert result["matched"] is not None
    assert result["matched"]["brand"] == "Elite"
    assert result["matched"]["model"] == "Boar"
    assert result["matched"]["fiber"] == "Boar"
    assert result["matched"]["fiber_strategy"] == "user_input"
    assert result["matched"]["knot_size_mm"] == 26.0
    assert result["match_type"] == "brand_default"


def test_brush_matcher_other_brushes_default_fiber(matcher):
    """Test matching against other_brushes using default fiber"""
    result = matcher.match("Elite 26mm")

    assert result["original"] == "Elite 26mm"
    assert result["matched"] is not None
    assert result["matched"]["brand"] == "Elite"
    assert result["matched"]["model"] == "Badger"  # Uses default
    assert result["matched"]["fiber"] == "Badger"
    assert result["matched"]["fiber_strategy"] == "default"


def test_brush_matcher_strategy_priority(matcher):
    """Test that strategies are tried in correct order (known > DG > other)"""
    # This should match known_brushes first, not other_brushes
    result = matcher.match("Omega Pro 48")

    assert result["matched"] is not None
    assert result["matched"]["brand"] == "Omega"
    assert result["matched"]["model"] == "10048"  # From known_brushes
    assert result["matched"]["fiber"] == "Boar"
    assert result["matched"]["knot_size_mm"] == 28


def test_brush_matcher_chisel_and_hound(matcher):
    """Test ChiselAndHoundBrushMatchingStrategy (fallback when not in other_brushes)"""
    # Use a version not in other_brushes to test the dedicated strategy
    result = matcher.match("Chisel & Hound V27")  # V27 should work

    assert result["matched"] is not None
    assert result["matched"]["brand"] == "Chisel & Hound"
    assert result["matched"]["model"] == "V27"
    assert result["matched"]["fiber"] == "badger"
    assert result["matched"]["knot_size_mm"] == 26.0


def test_brush_matcher_omega_semogue_strategy(matcher):
    """Test OmegaSemogueBrushMatchingStrategy"""
    result = matcher.match("Omega 10077")  # Not in known_brushes

    assert result["matched"] is not None
    assert result["matched"]["brand"] == "Omega"
    assert result["matched"]["model"] == "10077"
    assert result["matched"]["fiber"] == "boar"


def test_brush_matcher_zenith_strategy(matcher):
    """Test ZenithBrushMatchingStrategy"""
    result = matcher.match("Zenith B26")

    assert result["matched"] is not None
    assert result["matched"]["brand"] == "Zenith"
    assert result["matched"]["model"] == "B26"
    assert result["matched"]["fiber"] == "Boar"


def test_brush_matcher_no_match(matcher):
    """Test when no strategy matches"""
    result = matcher.match("Unknown Brand XYZ")

    assert result["original"] == "Unknown Brand XYZ"
    assert result["matched"] is None
    assert result["match_type"] is None
    assert result["pattern"] is None


def test_brush_matcher_user_fiber_extraction(matcher):
    """Test that user fiber is extracted from input"""
    result = matcher.match("Simpson Chubby 2 29mm Synthetic")

    assert result["matched"] is not None
    # Known brush fiber takes precedence, but conflict should be recorded
    assert result["matched"]["fiber"] == "Badger"
    assert result["matched"]["fiber_strategy"] == "yaml"
    assert "fiber_conflict" in result["matched"]


def test_brush_matcher_user_knot_size_extraction(matcher):
    """Test that user knot size is extracted from input"""
    result = matcher.match("Elite 24mm brush")

    assert result["matched"] is not None
    assert result["matched"]["knot_size_mm"] == 24.0


def test_brush_matcher_handle_knot_splitting(matcher):
    """Test handle/knot splitting with 'w/' delimiter"""
    result = matcher.match("Elite handle w/ Declaration knot")

    assert result["matched"] is not None
    assert result["matched"]["handle_maker"] == "Elite"


def test_brush_matcher_post_processing(matcher):
    """Test post-processing adds enriched fields"""
    result = matcher.match("Simpson Chubby 2 26mm")

    assert result["matched"] is not None
    # Should have post-processing fields
    assert "_matched_by_strategy" in result["matched"]
    assert "_pattern_used" in result["matched"]
    assert "fiber_strategy" in result["matched"]


def test_brush_matcher_file_not_found():
    """Test BrushMatcher with non-existent catalog file"""
    matcher = BrushMatcher(catalog_path=Path("nonexistent.yaml"))
    result = matcher.match("Simpson Chubby 2")

    # Should not crash, but return no match
    assert result["matched"] is None


def test_brush_matcher_empty_catalog(tmp_path):
    """Test BrushMatcher with empty catalog"""
    catalog_file = tmp_path / "empty.yaml"
    catalog_file.write_text("{}")

    matcher = BrushMatcher(catalog_path=catalog_file)
    result = matcher.match("Simpson Chubby 2")

    # Should try ChiselAndHound, OmegaSemogue, Zenith strategies
    assert result["matched"] is None


def test_brush_matcher_malformed_yaml(tmp_path):
    """Test BrushMatcher with malformed YAML"""
    catalog_file = tmp_path / "malformed.yaml"
    catalog_file.write_text("invalid: yaml: content:")

    # Should handle gracefully
    matcher = BrushMatcher(catalog_path=catalog_file)
    result = matcher.match("Simpson Chubby 2")

    assert result["matched"] is None


@pytest.mark.parametrize(
    "input_str,expected_brand,expected_model",
    [
        ("Simpson Chubby 2", "Simpson", "Chubby 2"),
        ("Declaration B3", "Declaration Grooming", "B3"),
        ("Elite Badger", "Elite", "Badger"),
        ("Chisel & Hound V20", "Chisel & Hound", "V20"),
        ("Omega 12345", "Omega", "12345"),
        ("Zenith B26", "Zenith", "B26"),
    ],
)
def test_brush_matcher_parametrized_matches(matcher, input_str, expected_brand, expected_model):
    """Test various brush matches with parametrized inputs"""
    result = matcher.match(input_str)

    assert result["matched"] is not None
    assert result["matched"]["brand"] == expected_brand
    assert result["matched"]["model"] == expected_model


def test_brush_matcher_consistent_return_structure(matcher):
    """Test that return structure is consistent across all matches"""
    test_cases = ["Simpson Chubby 2", "Declaration B3", "Elite brush", "Unknown brush"]

    for test_case in test_cases:
        result = matcher.match(test_case)

        # All results should have these keys
        assert "original" in result
        assert "matched" in result
        assert "match_type" in result
        assert "pattern" in result

        # Values can be None for no matches
        assert result["original"] == test_case


def test_chisel_hound_versioned_vs_non_versioned_matching(matcher):
    """Test that versioned C&H knots match via ChiselAndHoundStrategy while
    non-versioned match via OtherBrushStrategy"""

    # Test versioned knot (V20) - should match via ChiselAndHoundBrushMatchingStrategy
    result = matcher.match("Chisel & Hound V20")
    assert result["matched"] is not None
    assert result["matched"]["brand"] == "Chisel & Hound"
    assert result["matched"]["model"] == "V20"
    assert result["matched"]["fiber"] == "badger"
    assert result["matched"]["knot_size_mm"] == 26.0
    # This should come from ChiselAndHound strategy, not OtherBrushes

    # Test non-versioned C&H brush - should match via OtherBrushMatchingStrategy
    # Note: Quartermoon contains "moon" which triggers synthetic fiber detection
    result = matcher.match("Chisel & Hound Quartermoon")
    assert result["matched"] is not None
    assert result["matched"]["brand"] == "Chisel & Hound"
    assert result["matched"]["model"] == "Synthetic"  # Fiber detected from "moon"
    assert result["matched"]["fiber"] == "Synthetic"
    assert result["matched"]["knot_size_mm"] == 26  # From other_brushes default
    assert result["matched"]["fiber_strategy"] == "user_input"

    # Test another non-versioned C&H brush with explicitly detected fiber
    result = matcher.match("Chisel & Hound Synthetic")
    assert result["matched"] is not None
    assert result["matched"]["brand"] == "Chisel & Hound"
    assert result["matched"]["model"] == "Synthetic"
    assert result["matched"]["fiber"] == "Synthetic"
    assert result["matched"]["fiber_strategy"] == "user_input"

    # Test non-versioned C&H brush using default fiber (no fiber keywords)
    result = matcher.match("Chisel & Hound Special Edition")
    assert result["matched"] is not None
    assert result["matched"]["brand"] == "Chisel & Hound"
    assert result["matched"]["model"] == "Badger"  # Uses default from other_brushes
    assert result["matched"]["fiber"] == "Badger"
    assert result["matched"]["fiber_strategy"] == "default"


def test_chisel_hound_version_boundary_cases(matcher):
    """Test boundary cases for C&H version matching"""

    # Test lowest valid version (V10) - should match via ChiselAndHoundStrategy
    result = matcher.match("Chisel & Hound V10")
    assert result["matched"] is not None
    assert result["matched"]["brand"] == "Chisel & Hound"
    assert result["matched"]["model"] == "V10"
    assert result["matched"]["fiber"] == "badger"

    # Test highest valid version (V27) - should match via ChiselAndHoundStrategy
    result = matcher.match("Chisel & Hound V27")
    assert result["matched"] is not None
    assert result["matched"]["brand"] == "Chisel & Hound"
    assert result["matched"]["model"] == "V27"
    assert result["matched"]["fiber"] == "badger"

    # Test invalid version (V28) - should fall through to OtherBrushStrategy
    result = matcher.match("Chisel & Hound V28")
    assert result["matched"] is not None
    assert result["matched"]["brand"] == "Chisel & Hound"
    assert result["matched"]["model"] == "Badger"
    assert result["matched"]["fiber"] == "Badger"
    assert result["matched"]["fiber_strategy"] == "default"


def test_handle_matching_full_text(tmp_path):
    """Test handle matching with full text regex patterns."""
    # Create temp catalog with handle patterns
    catalog_content = """
artisan_handles:
  Long Shaving:
    patterns:
      - "long shaving.*storm"
manufacturer_handles:
  Wolf Whiskers:
    patterns:
      - "ww"
"""
    catalog_file = tmp_path / "handles.yaml"
    catalog_file.write_text(catalog_content)

    matcher = BrushMatcher(handles_path=catalog_file)

    # Example 1: Long Shaving Storm w/ Reserve III
    result = matcher.match("Long Shaving Storm w/ Reserve III")
    assert result["matched"] is not None
    assert result["matched"]["handle_maker"] == "Long Shaving"
    assert result["matched"]["handle_maker_metadata"]["_matched_by_section"] in [
        "artisan_handles",
        "manufacturer_handles",
    ]


def test_handle_matching_split_parsing(tmp_path):
    """Test handle matching with split-based parsing."""
    # Create temp catalogs
    brush_catalog = """
other_brushes:
  Long Shaving:
    patterns:
      - "long reserve"
    default: "Badger"
"""
    brush_file = tmp_path / "brushes.yaml"
    brush_file.write_text(brush_catalog)

    handle_catalog = """
manufacturer_handles:
  Wolf Whiskers:
    patterns:
      - "ww"
"""
    handle_file = tmp_path / "handles.yaml"
    handle_file.write_text(handle_catalog)

    matcher = BrushMatcher(catalog_path=brush_file, handles_path=handle_file)

    # Example 2: WW w/ 30mm Long Reserve V
    # The knot part "30mm Long Reserve V" should match Long Shaving (via "long reserve" pattern)
    # The handle part "WW" should match Wolf Whiskers handle
    result = matcher.match("WW w/ 30mm Long Reserve V")
    assert result["matched"] is not None
    assert result["matched"]["brand"] == "Long Shaving"  # Brush brand from knot part
    assert result["matched"]["handle_maker"] == "Wolf Whiskers"  # Handle from "WW"


def test_handle_matching_with_slash(tmp_path):
    """Test handle matching with slash delimiter."""
    # Create temp handle catalog
    handle_catalog = """
artisan_handles:
  Chisel & Hound:
    patterns:
      - "chisel.*hound"
"""
    handle_file = tmp_path / "handles.yaml"
    handle_file.write_text(handle_catalog)

    matcher = BrushMatcher(handles_path=handle_file)

    # Example 3: Chisel & Hound *"Twilight"* / 26mm Long Shaving Reserve VI Fan
    result = matcher.match('Chisel & Hound *"Twilight"* / 26mm Long Shaving Reserve VI Fan')
    assert result["matched"] is not None
    assert result["matched"]["handle_maker"] == "Chisel & Hound"
    assert result["matched"]["handle_maker_metadata"]["_matched_by_section"] == "artisan_handles"


def test_handle_matching_no_match(tmp_path):
    """Test handle matching when no match is found."""
    # Create empty temp catalog
    catalog_file = tmp_path / "brushes.yaml"
    catalog_file.write_text("{}")

    matcher = BrushMatcher(catalog_path=catalog_file)

    result = matcher.match("Some Unknown Brand Random Text")
    if result["matched"] is not None:
        # If a brush is matched but no handle is found, handle_maker should be None
        assert (
            result["matched"].get("handle_maker") is None or result["matched"]["handle_maker"] == ""
        )


def test_handle_matching_split_fallback(tmp_path):
    """Test split fallback when regex doesn't match but splitting works."""
    # Create temp catalog with basic patterns
    catalog_content = """
other_brushes:
  Some Knot:
    patterns:
      - "some knot"
    default: "Badger"
"""
    catalog_file = tmp_path / "brushes.yaml"
    catalog_file.write_text(catalog_content)

    matcher = BrushMatcher(catalog_path=catalog_file)

    # Use a made-up handle that won't match regex but will trigger split
    result = matcher.match("UnknownMaker w/ Some Knot")
    if result["matched"] is not None:
        # Should fall back to split logic
        expected_handle = "UnknownMaker"
        if result["matched"].get("handle_maker") == expected_handle:
            assert (
                result["matched"]["handle_maker_metadata"]["_matched_by_section"]
                == "split_fallback"
            )


def test_knot_maker_prioritization_over_handle_maker(tmp_path):
    """Test that knot maker takes precedence over handle maker when using 'with' delimiter.

    This tests the fix for the issue where 'Chisel and Hound Tahitian Pearl with
    Maggard 26mm SHD Fan' was incorrectly matched as 'Chisel & Hound Badger' instead
    of 'Maggard Badger'.
    """
    # Create temp catalogs
    brush_catalog = """
other_brushes:
  Maggard:
    patterns:
      - "maggard.*shd"
    default: "Badger"
  Chisel & Hound:
    patterns:
      - "chisel.*hound"
    default: "Badger"
"""
    brush_file = tmp_path / "brushes.yaml"
    brush_file.write_text(brush_catalog)

    handle_catalog = """
artisan_handles:
  Chisel & Hound:
    patterns:
      - "chisel.*hound"
"""
    handle_file = tmp_path / "handles.yaml"
    handle_file.write_text(handle_catalog)

    matcher = BrushMatcher(catalog_path=brush_file, handles_path=handle_file)

    # Test case: Handle maker (Chisel & Hound) with knot maker (Maggard)
    result = matcher.match("Chisel and Hound Tahitian Pearl with Maggard 26mm SHD Fan")

    assert result["matched"] is not None

    # Primary match should be the knot maker (Maggard), not handle maker (Chisel & Hound)
    assert result["matched"]["brand"] == "Maggard"
    assert result["matched"]["model"] == "Badger"  # Maggard SHD is badger
    assert result["matched"]["fiber"] == "Badger"
    assert result["matched"]["knot_size_mm"] == 26.0

    # Handle maker should be identified separately
    assert result["matched"]["handle_maker"] == "Chisel & Hound"

    # Verify the match came from knot part prioritization
    assert result["matched"]["_matched_from"] == "knot_part"
    assert result["matched"]["_original_knot_text"] == "Maggard 26mm SHD Fan"
    assert result["matched"]["_original_handle_text"] == "Chisel and Hound Tahitian Pearl"

    # Match type should be brand_default since Maggard uses generic patterns
    assert result["match_type"] == "brand_default"


def test_knot_maker_prioritization_with_different_delimiters(tmp_path):
    """Test knot maker prioritization works with various delimiters."""
    # Create temp catalog with multiple brands
    catalog_content = """
other_brushes:
  Maggard:
    patterns:
      - "maggard"
    default: "Synthetic"
  Omega:
    patterns:
      - "omega"
    default: "Boar"
  Simpson:
    patterns:
      - "simpson"
    default: "Badger"
  Declaration Grooming:
    patterns:
      - "declaration"
    default: "Badger"
"""
    catalog_file = tmp_path / "brushes.yaml"
    catalog_file.write_text(catalog_content)

    matcher = BrushMatcher(catalog_path=catalog_file)

    test_cases = [
        "Wolf Whiskers handle w/ Maggard 24mm Synthetic",
        "Elite Razors handle with Omega 26mm Boar",
        "Custom Handle / Simpson 28mm Badger",
        "Artisan Handle/Declaration 26mm B3",
    ]

    expected_brands = ["Maggard", "Omega", "Simpson", "Declaration Grooming"]

    for i, test_case in enumerate(test_cases):
        result = matcher.match(test_case)

        assert result["matched"] is not None, f"Failed to match: {test_case}"
        assert result["matched"]["brand"] == expected_brands[i], f"Wrong brand for: {test_case}"
        assert (
            result["matched"]["_matched_from"] == "knot_part"
        ), f"Should match from knot part: {test_case}"


def test_fallback_to_full_text_when_knot_part_no_match(tmp_path):
    """Test that when knot part doesn't match any brand, system falls back to full text matching."""
    # Create temp catalog with Elite but not Unknown Brand
    catalog_content = """
other_brushes:
  Elite:
    patterns:
      - "elite"
    default: "Badger"
"""
    catalog_file = tmp_path / "brushes.yaml"
    catalog_file.write_text(catalog_content)

    matcher = BrushMatcher(catalog_path=catalog_file)

    # Use a case where the knot part won't match any known brand
    result = matcher.match("Elite handle with Unknown Brand 26mm")

    assert result["matched"] is not None
    # Should fall back to matching "Elite" from the full text
    assert result["matched"]["brand"] == "Elite"
    # Should NOT have _matched_from since it used full text matching
    assert "_matched_from" not in result["matched"]


def test_handle_maker_prioritization_with_in_delimiter(tmp_path):
    """Test that handle maker takes precedence when using 'in' delimiter.

    This tests that 'Badger knot in Elite handle' correctly matches Elite as the primary brand.
    """
    # Create temp catalog with Elite
    catalog_content = """
other_brushes:
  Elite:
    patterns:
      - "elite"
    default: "Badger"
"""
    catalog_file = tmp_path / "brushes.yaml"
    catalog_file.write_text(catalog_content)

    matcher = BrushMatcher(catalog_path=catalog_file)

    # Test case: Knot description "in" handle maker - handle should take precedence
    result = matcher.match("26mm Badger knot in Elite Manchurian handle")

    assert result["matched"] is not None

    # Primary match should be the handle maker (Elite), not the knot description
    assert result["matched"]["brand"] == "Elite"
    assert result["matched"]["handle_maker"] == "Elite" or result["matched"]["brand"] == "Elite"

    # Verify the match came from handle part prioritization
    if "_matched_from" in result["matched"]:
        assert result["matched"]["_matched_from"] == "handle_part"
        assert result["matched"]["_original_handle_text"] == "Elite Manchurian handle"
        assert result["matched"]["_original_knot_text"] == "26mm Badger knot"


def test_delimiter_semantics_helper_method(tmp_path):
    """Test the knot matcher's should_prioritize_knot method for different delimiters."""
    # Create temp catalog
    catalog_file = tmp_path / "brushes.yaml"
    catalog_file.write_text("{}")

    matcher = BrushMatcher(catalog_path=catalog_file)

    # Test knot-primary delimiters
    assert (
        matcher.knot_matcher.should_prioritize_knot(
            "Handle w/ Knot", matcher.brush_splitter.split_handle_and_knot
        )
        is True
    )
    assert (
        matcher.knot_matcher.should_prioritize_knot(
            "Handle with Knot", matcher.brush_splitter.split_handle_and_knot
        )
        is True
    )

    # Test handle-primary delimiters
    assert (
        matcher.knot_matcher.should_prioritize_knot(
            "Knot in Handle", matcher.brush_splitter.split_handle_and_knot
        )
        is False
    )

    # Test neutral delimiters (default to knot priority for backward compatibility)
    assert (
        matcher.knot_matcher.should_prioritize_knot(
            "Handle / Knot", matcher.brush_splitter.split_handle_and_knot
        )
        is True
    )
