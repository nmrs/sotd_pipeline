import pytest
import yaml
from pathlib import Path
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
                    "patterns": ["simp.*chubby\\s*2", "simp.*ch2"],
                },
                "Trafalgar T2": {
                    "fiber": "Synthetic",
                    "knot_size_mm": 24,
                    "patterns": ["simp(?:.*traf)?.*t?2"],
                },
            },
            "Omega": {
                "10048": {"fiber": "Boar", "knot_size_mm": 28, "patterns": ["omega.*(pro)*.*48"]}
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
        },
    }


@pytest.fixture
def matcher(tmp_path, test_catalog):
    """Create BrushMatcher with test catalog"""
    catalog_file = tmp_path / "test_brushes.yaml"
    with catalog_file.open("w", encoding="utf-8") as f:
        yaml.dump(test_catalog, f)

    return BrushMatcher(catalog_path=catalog_file)


def test_brush_matcher_known_brush_match(matcher):
    """Test matching against known_brushes section"""
    result = matcher.match("Simpson Chubby 2")

    assert result["original"] == "Simpson Chubby 2"
    assert result["matched"] is not None
    assert result["matched"]["brand"] == "Simpson"
    assert result["matched"]["model"] == "Chubby 2"
    assert result["matched"]["fiber"] == "Badger"
    assert result["matched"]["knot_size_mm"] == 27
    assert result["matched"]["fiber_strategy"] == "yaml"
    assert result["matched"]["knot_size_strategy"] == "yaml"
    assert result["match_type"] == "exact"
    assert result["pattern"] is not None


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
    assert result["matched"]["model"] == "Elite Boar"
    assert result["matched"]["fiber"] == "Boar"
    assert result["matched"]["fiber_strategy"] == "user_input"
    assert result["matched"]["knot_size_mm"] == 26.0
    assert result["matched"]["knot_size_strategy"] == "user_input"
    assert result["match_type"] == "brand_default"


def test_brush_matcher_other_brushes_default_fiber(matcher):
    """Test matching against other_brushes using default fiber"""
    result = matcher.match("Elite 26mm")

    assert result["original"] == "Elite 26mm"
    assert result["matched"] is not None
    assert result["matched"]["brand"] == "Elite"
    assert result["matched"]["model"] == "Elite Badger"  # Uses default
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
    assert result["matched"]["model"] == "Omega 10077"
    assert result["matched"]["fiber"] == "boar"


def test_brush_matcher_zenith_strategy(matcher):
    """Test ZenithBrushMatchingStrategy"""
    result = matcher.match("Zenith B26")

    assert result["matched"] is not None
    assert result["matched"]["brand"] == "Zenith"
    assert result["matched"]["model"] == "Zenith B26"
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
    assert result["matched"]["knot_size_strategy"] == "user_input"


def test_brush_matcher_handle_knot_splitting(matcher):
    """Test handle/knot splitting with 'w/' delimiter"""
    result = matcher.match("Elite handle w/ Declaration knot")

    assert result["matched"] is not None
    assert result["matched"]["handle maker"] == "Elite Handle"
    assert result["matched"]["knot maker"] == "Declaration Knot"


def test_brush_matcher_post_processing(matcher):
    """Test post-processing adds enriched fields"""
    result = matcher.match("Simpson Chubby 2 26mm")

    assert result["matched"] is not None
    # Should have post-processing fields
    assert "_matched_by_strategy" in result["matched"]
    assert "_pattern_used" in result["matched"]
    assert "fiber_strategy" in result["matched"]
    assert "knot_size_strategy" in result["matched"]


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
        ("Elite Badger", "Elite", "Elite Badger"),
        ("Chisel & Hound V20", "Chisel & Hound", "V20"),
        ("Omega 12345", "Omega", "Omega 12345"),
        ("Zenith B26", "Zenith", "Zenith B26"),
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
    """Test that versioned C&H knots match via ChiselAndHoundStrategy while non-versioned match via OtherBrushStrategy"""

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
    assert result["matched"]["model"] == "Chisel & Hound Synthetic"  # Fiber detected from "moon"
    assert result["matched"]["fiber"] == "Synthetic"
    assert result["matched"]["knot_size_mm"] == 26  # From other_brushes default
    assert result["matched"]["fiber_strategy"] == "user_input"
    assert result["matched"]["knot_size_strategy"] == "yaml"

    # Test another non-versioned C&H brush with explicitly detected fiber
    result = matcher.match("Chisel & Hound Synthetic")
    assert result["matched"] is not None
    assert result["matched"]["brand"] == "Chisel & Hound"
    assert result["matched"]["model"] == "Chisel & Hound Synthetic"
    assert result["matched"]["fiber"] == "Synthetic"
    assert result["matched"]["fiber_strategy"] == "user_input"

    # Test non-versioned C&H brush using default fiber (no fiber keywords)
    result = matcher.match("Chisel & Hound Special Edition")
    assert result["matched"] is not None
    assert result["matched"]["brand"] == "Chisel & Hound"
    assert result["matched"]["model"] == "Chisel & Hound Badger"  # Uses default from other_brushes
    assert result["matched"]["fiber"] == "Badger"
    assert result["matched"]["fiber_strategy"] == "default"
    assert result["matched"]["knot_size_strategy"] == "yaml"


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
    assert result["matched"]["model"] == "Chisel & Hound Badger"
    assert result["matched"]["fiber"] == "Badger"
    assert result["matched"]["fiber_strategy"] == "default"
