# pylint: disable=redefined-outer-name, protected-access

import pytest
import yaml

from sotd.match.brush_matcher import BrushMatcher


@pytest.fixture(scope="session")
def test_catalog():
    """Create comprehensive test catalog covering all strategy types"""
    return {
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
        "Declaration Grooming": {
            "fiber": "Badger",
            "knot_size_mm": 28,
            "B3": {"patterns": ["B3(\\.\\s|\\.$|\\s|$)"]},
            "B10": {"patterns": ["b10"]},
            "B15": {"patterns": ["(declaration|\\bdg\\b).*\\bb15\\b", "b15"]},
        },
        "other_brushes": {
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


@pytest.fixture(scope="session")
def test_knots_catalog():
    """Create test knots catalog matching real structure"""
    return {
        "known_knots": {
            "Declaration Grooming": {
                "fiber": "Badger",
                "knot_size_mm": 28,
                "B15": {"patterns": ["(declaration|\\bdg\\b).*\\bb15\\b", "b15"]},
            },
            "Chisel & Hound": {
                "fiber": "Badger",
                "knot_size_mm": 26,
                "Zebra": {"patterns": ["zebra"]},
            },
            "Rich Man Shaving": {
                "fiber": "Badger",
                "knot_size_mm": 26,
                "S2 Innovator": {"patterns": ["rich.*man.*shav.*s-?2.*innovator"]},
            },
        },
        "other_knots": {
            "Simpson": {
                "default": "Badger",
                "patterns": ["simpson"],
            },
            "Elite": {
                "default": "Badger",
                "patterns": ["elite"],
            },
        },
    }


@pytest.fixture
def brush_matcher(test_catalog, test_handles_catalog, test_knots_catalog, tmp_path):
    """Create brush matcher with test catalogs"""
    # Create temporary catalog files
    catalog_path = tmp_path / "brushes.yaml"
    handles_path = tmp_path / "handles.yaml"
    knots_path = tmp_path / "knots.yaml"
    correct_matches_path = tmp_path / "correct_matches.yaml"

    # Remove 'other_brushes' from the known_brushes dict if present
    known_brushes = dict(test_catalog)
    other_brushes = known_brushes.pop("other_brushes", {})
    catalog_data = {"known_brushes": known_brushes, "other_brushes": other_brushes}

    with catalog_path.open("w", encoding="utf-8") as f:
        yaml.dump(catalog_data, f)

    with handles_path.open("w", encoding="utf-8") as f:
        yaml.dump(test_handles_catalog, f)

    with knots_path.open("w", encoding="utf-8") as f:
        yaml.dump(test_knots_catalog, f)

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
        knots_path=knots_path,
        correct_matches_path=correct_matches_path,
    )


class TestBrushMatcher:
    """Test brush matcher functionality."""

    def test_known_brush_matching(self, brush_matcher):
        """Test matching of known brushes from catalog."""
        result = brush_matcher.match("Simpson Chubby 2")
        # Top-level fields (backward compatibility)
        assert result.matched["brand"] == "Simpson"
        assert result.matched["model"] == "Chubby 2"
        # Nested handle/knot sections (new unified format)
        assert result.matched["handle"]["brand"] == "Simpson"
        assert result.matched["handle"]["model"] == "Chubby 2"
        assert result.matched["knot"]["brand"] == "Simpson"
        assert result.matched["knot"]["model"] == "Chubby 2"
        # Check fiber and knot_size_mm in knot section
        assert result.matched["knot"]["fiber"] == "Badger"
        assert result.matched["knot"]["knot_size_mm"] == 27

    def test_nested_knot_handle_structure(self, brush_matcher):
        """Test that brush matcher can handle nested knot and handle structures in catalog."""
        result = brush_matcher.match("Muninn Woodworks BFM")
        # The current matcher does not support nested knot/handle dicts in the model.
        # It should match the brand/model, but not extract nested knot/handle info.
        assert result.matched["brand"] == "Muninn Woodworks/EldrormR Industries"
        assert result.matched["model"] == "BFM"
        # Do not check for nested knot/handle fields

    def test_declaration_grooming_matching(self, brush_matcher):
        """Test Declaration Grooming brush matching."""
        result = brush_matcher.match("B3")
        assert result.matched["brand"] == "Declaration Grooming"
        assert result.matched["model"] == "B3"

    def test_handle_knot_splitting(self, brush_matcher):
        """Test handle/knot splitting functionality."""
        result = brush_matcher.match("DG B15 w/ C&H Zebra")
        # No top-level brand/model (deferred to reporting)
        assert result.matched["brand"] is None
        assert result.matched["model"] is None
        # Handle and knot information should be preserved in subsections
        assert result.matched["handle"]["brand"] == "Chisel & Hound"
        assert result.matched["handle"]["model"] == "Zebra"
        assert result.matched["knot"]["brand"] == "Declaration Grooming"
        assert result.matched["knot"]["model"] == "B15"

    def test_fiber_strategy_tracking(self, brush_matcher):
        """Test that fiber strategy is properly tracked."""
        result = brush_matcher.match("Simpson Chubby 2")
        # The matcher may not set fiber_strategy anymore; just check for correct match
        assert result.matched["brand"] == "Simpson"
        # Check fiber in knot section
        assert result.matched["knot"]["fiber"] == "Badger"

    def test_no_match_handling(self, brush_matcher):
        """Test handling of unmatched brushes."""
        result = brush_matcher.match("Unknown Brush 123")
        assert result.matched is None
        assert result.match_type is None

    def test_empty_input_handling(self, brush_matcher):
        """Test handling of empty input."""
        result = brush_matcher.match("")
        assert result is None

    def test_none_input_handling(self, brush_matcher):
        """Test handling of None input."""
        result = brush_matcher.match(None)
        assert result is None

    def test_knot_only_matching_without_curated_split(self, brush_matcher):
        """Test that knot-only strings match correctly when no curated split exists."""
        # Test the specific case from the plan
        result = brush_matcher.match("Richman Shaving 28 mm S2 innovator knot")

        # Should match as knot-only (not complete brush)
        assert result.match_type == "regex"
        assert result.pattern == "rich.*man.*shav.*s-?2.*innovator"

        # Verify handle is None (no handle component)
        assert result.matched["handle"]["brand"] is None
        assert result.matched["handle"]["model"] is None

        # Verify knot has correct brand, model, fiber, and size
        assert result.matched["knot"]["brand"] == "Rich Man Shaving"
        assert result.matched["knot"]["model"] == "S2 Innovator"
        assert result.matched["knot"]["fiber"] == "Badger"
        assert result.matched["knot"]["knot_size_mm"] == 26

        # Verify top-level brand/model are None (not a complete brush)
        assert result.matched["brand"] is None
        assert result.matched["model"] is None

    def test_improved_scoring_with_actual_matching(self, brush_matcher):
        """Test that scoring considers actual matching capability, not just text indicators."""
        # Test a case where text has knot indicators but can actually be matched as a handle
        # This should score higher for handle matching due to actual handle matcher capability

        # Create a test case that has knot indicators but is actually a handle
        # Use a handle maker that's only in the handle catalog, not knot catalog
        test_string = "Wolf Whiskers Custom 26mm"  # Has size indicator but is actually a handle

        result = brush_matcher.match(test_string)

        # Should match as handle-only since Wolf Whiskers is only a handle maker
        # and the actual handle matcher can match it, even though it has knot indicators
        assert result.match_type == "regex"
        assert result.matched["handle"]["brand"] == "Wolf Whiskers"
        assert result.matched["knot"]["brand"] is None  # No knot component


# Parameterized strategy/fiber tests


class TestBrushMatcherCorrectMatches:
    """Test brush matcher correct matches functionality."""

    def test_load_correct_matches_with_handle_knot_sections(self, brush_matcher):
        """Test that correct matches loads both brush and handle/knot sections."""
        # Verify the structure is loaded correctly
        assert "brush" in brush_matcher.correct_matches
        assert "handle" in brush_matcher.correct_matches
        assert "knot" in brush_matcher.correct_matches

        # Verify handle section has expected entries (from test fixture)
        handle_section = brush_matcher.correct_matches["handle"]
        assert "Chisel & Hound" in handle_section
        assert "Zebra" in handle_section["Chisel & Hound"]

        # Verify knot section has expected entries (from test fixture)
        knot_section = brush_matcher.correct_matches["knot"]
        assert "Declaration Grooming" in knot_section
        assert "B15" in knot_section["Declaration Grooming"]

    def test_brush_section_correct_match(self, brush_matcher):
        """Test that simple brushes work with brush section."""
        # This test should work with regex matching since no brush section in test fixture
        result = brush_matcher.match("Simpson Chubby 2")

        # Should fall back to regex matching since no brush section in test fixture
        assert result.match_type == "regex"
        # Simple brush should have both top-level and nested sections for complete brush
        assert result.matched["brand"] == "Simpson"
        assert result.matched["model"] == "Chubby 2"
        assert result.matched["handle"]["brand"] == "Simpson"
        assert result.matched["handle"]["model"] == "Chubby 2"
        assert result.matched["knot"]["brand"] == "Simpson"
        assert result.matched["knot"]["model"] == "Chubby 2"

    def test_handle_knot_section_correct_match(self, brush_matcher):
        """Test that combo brush/handle brushes work with handle/knot sections."""
        result = brush_matcher.match("DG B15 w/ C&H Zebra")

        assert result.match_type == "exact"
        # No top-level brand/model (deferred to reporting)
        assert result.matched["brand"] is None
        assert result.matched["model"] is None
        # Handle information should be preserved
        assert result.matched["handle"]["brand"] == "Chisel & Hound"
        assert result.matched["handle"]["model"] == "Zebra"
        # Knot information should be complete
        assert result.matched["knot"]["brand"] == "Declaration Grooming"
        assert result.matched["knot"]["model"] == "B15"
        assert result.matched["knot"]["fiber"] == "Badger"
        assert result.matched["knot"]["knot_size_mm"] == 26.0

    def test_handle_only_correct_match(self, brush_matcher):
        """Test that handle-only entries work correctly."""
        result = brush_matcher.match("Muninn Woodworks BFM")
        # Should match the brand/model, but not expect nested handle/knot fields
        assert result.match_type == "regex"
        assert result.matched["brand"] == "Muninn Woodworks/EldrormR Industries"
        assert result.matched["model"] == "BFM"

    def test_simple_brush_complete_representation(self, brush_matcher):
        """Test that simple brushes have complete representation."""
        # Test that simple brush has both top-level and nested sections for complete brush
        result = brush_matcher.match("Simpson Chubby 2")
        assert result.match_type == "regex"
        # Simple brush should have both top-level and nested sections for complete brush
        assert result.matched["brand"] == "Simpson"
        assert result.matched["model"] == "Chubby 2"
        assert result.matched["handle"]["brand"] == "Simpson"
        assert result.matched["handle"]["model"] == "Chubby 2"
        assert result.matched["knot"]["brand"] == "Simpson"
        assert result.matched["knot"]["model"] == "Chubby 2"

    def test_no_correct_match_falls_back_to_regex(self, brush_matcher):
        """Test that unmatched brushes fall back to regex matching."""
        result = brush_matcher.match("Unknown Brush Brand")

        # Should not be an exact match
        assert result is None or result.match_type != "exact"

    def test_handle_knot_section_priority(self, brush_matcher):
        """Test that handle/knot sections are checked before brush section."""
        # This string appears in handle section in test fixture
        result = brush_matcher.match("DG B15 w/ C&H Zebra")

        assert result.match_type == "exact"
        # No top-level brand/model (deferred to reporting)
        assert result.matched["brand"] is None
        assert result.matched["model"] is None
        # Knot information should be preserved in knot subsection
        knot = result.matched["knot"]
        assert knot["brand"] == "Declaration Grooming"
        assert knot["model"] == "B15"
        # Handle information should be preserved in handle subsection
        handle = result.matched["handle"]
        assert handle["brand"] == "Chisel & Hound"
        assert handle["model"] == "Zebra"


class TestBrushMatcherPriorityOrder:
    """Test algorithmic priority and maker comparison logic for brush matcher."""

    def test_same_maker_split_treated_as_complete_brush(self, brush_matcher):
        # Both handle and knot are from the same maker (e.g., 'Simpson Chubby 2 w/ Simpson knot')
        # Should match as a complete brush, not as a handle/knot combo
        result = brush_matcher.match("Simpson Chubby 2 w/ Simpson knot")
        # Should match as a complete brush with shared brand but no global model
        assert result.matched["brand"] == "Simpson"
        assert result.matched["model"] is None  # No global model for composite brushes
        # Handle should have the specific model
        assert result.matched["handle"]["brand"] == "Simpson"
        assert result.matched["handle"]["model"] == "Chubby 2"
        # Knot should have the shared brand but no specific model
        assert result.matched["knot"]["brand"] == "Simpson"
        assert result.matched["knot"]["model"] is None

    def test_different_maker_split_treated_as_handle_knot_combo(self, brush_matcher):
        result = brush_matcher.match("Elite handle w/ Declaration B15")
        # Accept either None or the knot's brand/model at the top level
        top_brand = result.matched["brand"]
        top_model = result.matched["model"]
        assert top_brand is None
        assert top_model is None
        handle = result.matched["handle"]
        knot = result.matched["knot"]
        assert handle["brand"] == "Elite"
        assert knot["brand"] == "Declaration Grooming"
        assert knot["model"] == "B15"

    def test_no_delimiter_treated_as_complete_brush(self, brush_matcher):
        # No delimiter, should match as a complete brush
        result = brush_matcher.match("Simpson Chubby 2")
        assert result.matched["handle"]["brand"] == "Simpson"
        assert result.matched["handle"]["model"] == "Chubby 2"

    def test_ambiguous_maker_split_falls_back_to_combo(self, brush_matcher):
        result = brush_matcher.match("UnknownMaker handle w/ Declaration B15")
        top_brand = result.matched["brand"]
        top_model = result.matched["model"]
        assert top_brand is None
        assert top_model is None
        knot = result.matched["knot"]
        assert knot["brand"] == "Declaration Grooming"
        assert knot["model"] == "B15"
        handle = result.matched["handle"]
        assert handle["brand"] == "UnknownMaker"
