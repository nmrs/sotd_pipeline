# pylint: disable=redefined-outer-name
import pytest

from sotd.match.brush.strategies.known.known_knot_based_brush_strategy import (
    KnownKnotBasedBrushMatchingStrategy,
)


@pytest.fixture
def strategy():
    """Create a test strategy with sample catalog data."""
    catalog = {
        "Chisel & Hound": {
            "fiber": "Badger",
            "knot_size_mm": 26,
            "v23": {
                "patterns": ["chis.*[fh]ou.*v23", "\\bc(?:\\&|and|\\+)h\\b.*v23", "\\bch\\b.*v23"],
            },
            "v24": {
                "patterns": ["chis.*[fh]ou.*v24", "\\bc(?:\\&|and|\\+)h\\b.*v24", "\\bch\\b.*v24"],
            },
        },
        "Declaration Grooming": {
            "fiber": "Badger",
            "handle_matching": True,
            "knot_size_mm": 28,
            "B1": {
                "patterns": [
                    "^(?!.*dog).*(declaration|\\bdg\\b).*\\bb1\\b",
                    "^(?!.*dog).*\\bb1\\b",
                ],
            },
            "B2": {
                "patterns": [
                    "^(?!.*dog|zen).*(declaration|\\bdg\\b).*\\bb2\\b",
                    "^(?!.*dog|zen).*\\bb2\\b",
                ],
            },
        },
        "Dogwood": {
            "Boar": {
                "patterns": ["dogwood.*boar"],
                "knot": {
                    "brand": "Maggard",
                    "fiber": "Boar",
                    "model": "Boar",
                },
            },
            "SHD Badger": {
                "patterns": ["dogwood.*\\bshd\\b"],
                "knot": {
                    "brand": "Maggard",
                    "fiber": "Badger",
                    "model": "SHD Badger",
                },
            },
        },
    }
    return KnownKnotBasedBrushMatchingStrategy(catalog)


def test_known_knot_based_brush_exact_match(strategy):
    """Test exact match for Chisel & Hound v23."""
    result = strategy.match("chisel & hound v23")

    assert result.matched is not None
    assert result.matched["brand"] == "Chisel & Hound"
    assert result.matched["model"] == "v23"
    # Check nested structure (no redundant root fields)
    assert "fiber" not in result.matched, "Should not have root-level fiber"
    assert "knot_size_mm" not in result.matched, "Should not have root-level knot_size_mm"
    assert result.matched["knot"]["fiber"] == "Badger"
    assert result.matched["knot"]["knot_size_mm"] == 26
    assert result.matched["handle"]["brand"] == "Chisel & Hound"
    assert result.matched["handle"]["model"] is None
    assert result.match_type == "regex"
    assert result.strategy == "known_knot_based_brush"


def test_known_knot_based_brush_case_insensitive(strategy):
    """Test case insensitive matching."""
    result = strategy.match("C&H v23")

    assert result.matched is not None
    assert result.matched["brand"] == "Chisel & Hound"
    assert result.matched["model"] == "v23"
    assert result.matched["knot"]["fiber"] == "Badger"
    assert result.matched["knot"]["knot_size_mm"] == 26
    assert result.strategy == "known_knot_based_brush"


def test_known_knot_based_brush_declaration_grooming_b1(strategy):
    """Test Declaration Grooming B1 matching."""
    result = strategy.match("declaration grooming b1")

    assert result.matched is not None
    assert result.matched["brand"] == "Declaration Grooming"
    assert result.matched["model"] == "B1"
    assert result.matched["knot"]["fiber"] == "Badger"
    assert result.matched["knot"]["knot_size_mm"] == 28
    assert result.strategy == "known_knot_based_brush"


def test_known_knot_based_brush_declaration_grooming_b2(strategy):
    """Test Declaration Grooming B2 matching."""
    result = strategy.match("dg b2")

    assert result.matched is not None
    assert result.matched["brand"] == "Declaration Grooming"
    assert result.matched["model"] == "B2"
    assert result.matched["knot"]["fiber"] == "Badger"
    assert result.matched["knot"]["knot_size_mm"] == 28
    assert result.strategy == "known_knot_based_brush"


def test_known_knot_based_brush_dogwood_boar(strategy):
    """Test Dogwood Boar matching with nested knot structure."""
    result = strategy.match("dogwood boar")

    assert result.matched is not None
    assert result.matched["brand"] == "Dogwood"
    assert result.matched["model"] == "Boar"
    # Check nested knot structure
    assert result.matched["knot"]["brand"] == "Maggard"
    assert result.matched["knot"]["fiber"] == "Boar"
    assert result.matched["knot"]["model"] == "Boar"
    assert result.strategy == "known_knot_based_brush"


def test_known_knot_based_brush_dogwood_shd_badger(strategy):
    """Test Dogwood SHD Badger matching with nested knot structure."""
    result = strategy.match("dogwood shd")

    assert result.matched is not None
    assert result.matched["brand"] == "Dogwood"
    assert result.matched["model"] == "SHD Badger"
    # Check nested knot structure
    assert result.matched["knot"]["brand"] == "Maggard"
    assert result.matched["knot"]["fiber"] == "Badger"
    assert result.matched["knot"]["model"] == "SHD Badger"
    assert result.strategy == "known_knot_based_brush"


def test_known_knot_based_brush_no_match(strategy):
    """Test when no pattern matches."""
    result = strategy.match("unknown brush 123")

    assert result.matched is None
    assert result.match_type is None
    assert result.strategy == "known_knot_based_brush"


def test_known_knot_based_brush_empty_input(strategy):
    """Test with empty input."""
    result = strategy.match("")

    assert result.matched is None
    assert result.match_type is None
    assert result.strategy == "known_knot_based_brush"


def test_known_knot_based_brush_multiple_patterns(strategy):
    """Test that multiple patterns work for the same model."""
    # Test different patterns for Chisel & Hound v23
    test_cases = [
        "chisel & hound v23",
        "c&h v23",
        "ch v23",
    ]

    for test_case in test_cases:
        result = strategy.match(test_case)
        assert result.matched is not None
        assert result.matched["brand"] == "Chisel & Hound"
        assert result.matched["model"] == "v23"
        assert result.strategy == "known_knot_based_brush"


def test_known_knot_based_brush_negative_lookahead(strategy):
    """Test that negative lookahead patterns work correctly."""
    # B1 should match
    result = strategy.match("declaration grooming b1")
    assert result.matched is not None
    assert result.matched["model"] == "B1"

    # B1 should NOT match if it contains "dog" (negative lookahead)
    result = strategy.match("dogwood declaration grooming b1")
    assert result.matched is None


def test_known_knot_based_brush_strategy_name(strategy):
    """Test that the strategy name is correctly set."""
    result = strategy.match("chisel & hound v23")
    assert result.strategy == "known_knot_based_brush"


def test_known_knot_based_brush_pattern_used_field(strategy):
    """Test that the pattern used field is correctly set."""
    result = strategy.match("chisel & hound v23")
    assert result.matched is not None
    assert "_pattern_used" in result.matched
    assert result.matched["_pattern_used"] is not None


def test_known_knot_based_brush_fiber_strategy_field(strategy):
    """Test that fiber strategy field is correctly set."""
    result = strategy.match("chisel & hound v23")
    assert result.matched is not None
    assert "fiber_strategy" in result.matched
    assert result.matched["fiber_strategy"] == "yaml"


def test_known_knot_based_brush_knot_size_strategy_field(strategy):
    """Test that knot size strategy field is correctly set."""
    result = strategy.match("chisel & hound v23")
    assert result.matched is not None
    assert "knot_size_strategy" in result.matched
    assert result.matched["knot_size_strategy"] == "yaml"
