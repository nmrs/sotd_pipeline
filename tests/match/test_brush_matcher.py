# pylint: disable=redefined-outer-name, protected-access

import pytest
import yaml

from sotd.match.brush_matcher import BrushMatcher


@pytest.fixture(scope="session")
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
            # Add BFM brush with nested knot and handle structures
            "Muninn Woodworks/EldrormR Industries": {
                "BFM": {
                    "patterns": ["\\bbfm\\b(.*50mm)?"],
                    "knot": {
                        "brand": "Moti",
                        "fiber": "Synthetic",
                        "knot_size_mm": 50,
                        "model": "Motherlode",
                    },
                    "handle": {"brand": "Muninn Woodworks"},
                }
            },
        },
        "declaration_grooming": {
            "Declaration Grooming": {
                "B3": {"patterns": ["B3(\\.\\s|\\.$|\\s|$)"]},
                "B10": {"patterns": ["b10"]},
                "B15": {"patterns": ["b15"]},
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


@pytest.fixture(scope="session")
def test_handles_catalog():
    """Create test handles catalog"""
    return {
        "artisan_handles": {
            "Muninn Woodworks": {"patterns": ["mun+in", "muninn.*woodworks"]},
            "Chisel & Hound": {
                "patterns": [
                    "chis.*hou",
                    "chis.*fou",
                    "\\bc(?:\\s*\\&\\s*|\\s+and\\s+|\\s*\\+\\s*)h\\b",
                ]
            },
        },
        "manufacturer_handles": {"Elite": {"patterns": ["elite"]}},
        "other_handles": {"Wolf Whiskers": {"patterns": ["wolf.*whis"]}},
    }


@pytest.fixture
def brush_matcher(test_catalog, test_handles_catalog, tmp_path):
    """Create brush matcher with test catalogs"""
    # Create temporary catalog files
    catalog_path = tmp_path / "brushes.yaml"
    handles_path = tmp_path / "handles.yaml"
    correct_matches_path = tmp_path / "correct_matches.yaml"

    with catalog_path.open("w", encoding="utf-8") as f:
        yaml.dump(test_catalog, f)

    with handles_path.open("w", encoding="utf-8") as f:
        yaml.dump(test_handles_catalog, f)

    # Create correct matches file with test entries
    correct_matches_data = {
        "handle": {"Chisel & Hound": {"Zebra": ["DG B15 w/ C&H Zebra"]}},
        "knot": {
            "Declaration Grooming": {
                "B15": {"strings": ["DG B15 w/ C&H Zebra"], "fiber": "Badger", "knot_size_mm": 26.0}
            }
        },
    }
    with correct_matches_path.open("w", encoding="utf-8") as f:
        yaml.dump(correct_matches_data, f)

    return BrushMatcher(
        catalog_path=catalog_path,
        handles_path=handles_path,
        correct_matches_path=correct_matches_path,
    )


class TestBrushMatcher:
    """Test brush matcher functionality."""

    def test_known_brush_matching(self, brush_matcher):
        """Test matching of known brushes from catalog."""
        result = brush_matcher.match("Simpson Chubby 2")
        assert result["matched"]["brand"] == "Simpson"
        assert result["matched"]["model"] == "Chubby 2"
        assert result["matched"]["fiber"] == "Badger"
        assert result["matched"]["knot_size_mm"] == 27

    def test_nested_knot_handle_structure(self, brush_matcher):
        """Test that brush matcher can handle nested knot and handle structures in catalog."""
        result = brush_matcher.match("Muninn Woodworks BFM")
        print(f"DEBUG: Full result: {result}")
        print(f"DEBUG: Matched: {result['matched']}")
        assert result["matched"]["brand"] == "Muninn Woodworks/EldrormR Industries"
        assert result["matched"]["model"] == "BFM"

        # Check that nested knot information is extracted
        assert result["matched"]["fiber"] == "Synthetic"
        assert result["matched"]["knot_size_mm"] == 50

        # Check that handle maker information is extracted from nested structure
        assert result["matched"]["handle_maker"] == "Muninn Woodworks"

        # Check that knot maker information is extracted from nested structure
        assert result["matched"]["knot_maker"] == "Moti"

    def test_declaration_grooming_matching(self, brush_matcher):
        """Test Declaration Grooming brush matching."""
        result = brush_matcher.match("B3")
        assert result["matched"]["brand"] == "Declaration Grooming"
        assert result["matched"]["model"] == "B3"

    def test_other_brush_matching(self, brush_matcher):
        """Test matching of other brushes with defaults."""
        result = brush_matcher.match("Elite handle")
        assert result["matched"]["brand"] == "Elite"
        assert result["matched"]["fiber"] == "Badger"  # Default from catalog

    def test_handle_knot_splitting(self, brush_matcher):
        """Test handle/knot splitting functionality."""
        result = brush_matcher.match("DG B15 w/ C&H Zebra")
        # No top-level brand/model (deferred to reporting)
        assert result["matched"]["brand"] is None
        assert result["matched"]["model"] is None
        # Handle and knot information should be preserved in subsections
        assert result["matched"]["handle_maker"] == "Chisel & Hound"
        assert result["matched"]["knot"]["brand"] == "Declaration Grooming"
        assert result["matched"]["knot"]["model"] == "B15"

    def test_fiber_strategy_tracking(self, brush_matcher):
        """Test that fiber strategy is properly tracked."""
        result = brush_matcher.match("Simpson Chubby 2")
        assert result["matched"]["fiber_strategy"] == "yaml"

    def test_no_match_handling(self, brush_matcher):
        """Test handling of unmatched brushes."""
        result = brush_matcher.match("Unknown Brush 123")
        assert result["matched"] is None
        assert result["match_type"] is None

    def test_empty_input_handling(self, brush_matcher):
        """Test handling of empty input."""
        result = brush_matcher.match("")
        assert result["matched"] is None
        assert result["match_type"] is None

    def test_none_input_handling(self, brush_matcher):
        """Test handling of None input."""
        result = brush_matcher.match(None)
        assert result["matched"] is None
        assert result["match_type"] is None


# Parameterized strategy/fiber tests


class TestBrushMatcherCorrectMatches:
    """Test brush matcher correct matches functionality."""

    def test_load_correct_matches_with_handle_knot_sections(self):
        """Test that correct matches loads both brush and handle/knot sections."""
        matcher = BrushMatcher()

        # Verify the structure is loaded correctly
        assert "brush" in matcher.correct_matches
        assert "handle" in matcher.correct_matches
        assert "knot" in matcher.correct_matches

        # Verify brush section has expected entries
        brush_section = matcher.correct_matches["brush"]
        assert "Simpson" in brush_section
        assert "Chubby 2" in brush_section["Simpson"]

        # Verify handle section has expected entries
        handle_section = matcher.correct_matches["handle"]
        assert "AP Shave Co" in handle_section
        assert "Black Matte Alumihandle Layered Comfort" in handle_section["AP Shave Co"]
        assert "Muninn Woodworks" in handle_section
        assert None in handle_section["Muninn Woodworks"]  # YAML null becomes Python None

        # Verify knot section has expected entries
        knot_section = matcher.correct_matches["knot"]
        assert "Mühle" in knot_section
        assert "STF" in knot_section["Mühle"]
        assert "Moti" in knot_section
        assert "Motherlode" in knot_section["Moti"]

    def test_brush_section_correct_match(self):
        """Test that simple brushes work with brush section."""
        matcher = BrushMatcher()

        result = matcher.match("Simpson Chubby 2")

        assert result["match_type"] == "exact"
        assert result["matched"]["brand"] == "Simpson"
        assert result["matched"]["model"] == "Chubby 2"
        assert result["matched"]["handle_maker"] is None  # Simple brush, no handle maker

    def test_handle_knot_section_correct_match(self):
        """Test that combo brush/handle brushes work with handle/knot sections."""
        matcher = BrushMatcher()

        result = matcher.match(
            "AP Shave Co - Black Matte Alumihandle Layered Comfort - 25mm Mühle STF"
        )

        assert result["match_type"] == "exact"
        # No top-level brand/model (deferred to reporting)
        assert result["matched"]["brand"] is None
        assert result["matched"]["model"] is None
        # Handle information should be preserved
        assert result["matched"]["handle_maker"] == "AP Shave Co"
        assert result["matched"]["handle"]["brand"] == "AP Shave Co"
        assert result["matched"]["handle"]["model"] == "Black Matte Alumihandle Layered Comfort"
        # Knot information should be complete
        assert result["matched"]["knot"]["brand"] == "Mühle"
        assert result["matched"]["knot"]["model"] == "STF"
        assert result["matched"]["knot"]["fiber"] == "Synthetic"
        assert result["matched"]["knot"]["knot_size_mm"] == 25.0

    def test_handle_only_correct_match(self):
        """Test that handle-only entries work correctly."""
        matcher = BrushMatcher()

        result = matcher.match("Muninn Woodworks BFM")

        assert result["match_type"] == "exact"
        # No top-level brand/model (deferred to reporting)
        assert result["matched"]["brand"] is None
        assert result["matched"]["model"] is None
        # Handle information should be preserved
        assert result["matched"]["handle_maker"] == "Muninn Woodworks"
        assert result["matched"]["handle"]["brand"] == "Muninn Woodworks"
        assert result["matched"]["handle"]["model"] is None  # No specific model
        # Knot information should be complete
        assert result["matched"]["knot"]["brand"] == "Moti"
        assert result["matched"]["knot"]["model"] == "Motherlode"
        assert result["matched"]["knot"]["fiber"] == "Synthetic"
        assert result["matched"]["knot"]["knot_size_mm"] == 50.0

    def test_backward_compatibility(self):
        """Test that existing brush section functionality continues to work."""
        matcher = BrushMatcher()

        # Test that simple brush still works
        result = matcher.match("Simpson Chubby 2")
        assert result["match_type"] == "exact"
        assert result["matched"]["brand"] == "Simpson"
        assert result["matched"]["model"] == "Chubby 2"

    def test_no_correct_match_falls_back_to_regex(self):
        """Test that unmatched brushes fall back to regex matching."""
        matcher = BrushMatcher()

        result = matcher.match("Unknown Brush Brand")

        # Should not be an exact match
        assert result["match_type"] != "exact"
        # Should attempt regex matching
        assert result["matched"] is None or result["match_type"] == "regex"

    def test_handle_knot_section_priority(self):
        """Test that handle/knot sections are checked before brush section."""
        matcher = BrushMatcher()

        # This string appears in both handle and brush sections
        # Should match handle/knot section first
        result = matcher.match(
            "AP Shave Co - Black Matte Alumihandle Layered Comfort - 25mm Mühle STF"
        )

        assert result["match_type"] == "exact"
        # No top-level brand/model (deferred to reporting)
        assert result["matched"]["brand"] is None
        assert result["matched"]["model"] is None
        # Knot information should be preserved in knot subsection
        assert result["matched"]["knot"]["brand"] == "Mühle"
        assert result["matched"]["knot"]["model"] == "STF"
        # Handle information should be preserved in handle subsection
        assert result["matched"]["handle"]["brand"] == "AP Shave Co"
        assert result["matched"]["handle"]["model"] == "Black Matte Alumihandle Layered Comfort"
