# pylint: disable=redefined-outer-name
import pytest

from sotd.match.brush.strategies.known.known_brush_strategy import KnownBrushMatchingStrategy


@pytest.fixture
def strategy():
    """Create a test strategy with sample catalog data."""
    catalog = {
        "Simpson": {
            "Chubby 2": {
                "fiber": "Badger",
                "knot_size_mm": 27,
                "patterns": ["simp.*chubby\\s*2\\b", "simp.*ch2\\b"],
            },
            "Chubby 3": {
                "fiber": "Badger",
                "knot_size_mm": 29,
                "patterns": ["simp.*chubby\\s*3", "simp.*ch3"],
            },
        },
        "Omega": {
            "10048": {
                "fiber": "Boar",
                "knot_size_mm": 24,
                "patterns": ["omega.*10048"],
            },
            "Pro 48": {
                "fiber": "Boar",
                "knot_size_mm": 48,
                "patterns": ["omega.*pro.*48"],
            },
        },
        "AP Shave Co": {
            "G5C": {
                "fiber": "Synthetic",
                "knot_size_mm": 24,
                "patterns": ["(?:\\ba ?p\\b.*)?g5c"],
            },
        },
    }
    return KnownBrushMatchingStrategy(catalog)


def test_known_brush_exact_match(strategy):
    result = strategy.match("Simpson Chubby 2")

    assert result.matched is not None
    assert result.matched["brand"] == "Simpson"
    assert result.matched["model"] == "Chubby 2"
    # Check nested structure (no redundant root fields)
    assert "fiber" not in result.matched, "Should not have root-level fiber"
    assert "knot_size_mm" not in result.matched, "Should not have root-level knot_size_mm"
    assert result.matched["knot"]["fiber"] == "Badger"
    assert result.matched["knot"]["knot_size_mm"] == 27
    assert result.matched["handle"]["brand"] == "Simpson"
    assert result.matched["handle"]["model"] is None
    assert result.match_type == "regex"


def test_known_brush_with_user_knot_size(strategy):
    """Test when user provides knot size - strategy returns YAML default, not user override."""
    result = strategy.match("Simpson 29mm CH2")

    assert result.matched is not None
    assert result.matched["brand"] == "Simpson"
    assert result.matched["model"] == "Chubby 2"
    # Check nested structure (no redundant root fields)
    assert "fiber" not in result.matched, "Should not have root-level fiber"
    assert "knot_size_mm" not in result.matched, "Should not have root-level knot_size_mm"
    assert result.matched["knot"]["fiber"] == "Badger"
    assert result.matched["knot"]["knot_size_mm"] == 27  # YAML default, not user override
    assert result.matched["handle"]["brand"] == "Simpson"
    assert result.matched["handle"]["model"] is None
    assert result.match_type == "regex"


def test_known_brush_omega_match(strategy):
    result = strategy.match("Omega Pro 48")

    assert result.matched is not None
    assert result.matched["brand"] == "Omega"
    assert result.matched["model"] == "Pro 48"
    # Check nested structure (no redundant root fields)
    assert "fiber" not in result.matched, "Should not have root-level fiber"
    assert "knot_size_mm" not in result.matched, "Should not have root-level knot_size_mm"
    assert result.matched["knot"]["fiber"] == "Boar"
    assert result.matched["knot"]["knot_size_mm"] == 48
    assert result.matched["handle"]["brand"] == "Omega"
    assert result.matched["handle"]["model"] is None
    assert result.match_type == "regex"


def test_known_brush_no_match(strategy):
    result = strategy.match("Unknown Brand 123")

    assert result.matched is None
    assert result.match_type is None


def test_known_brush_with_user_fiber_conflict(strategy):
    """Test when user provides different fiber - strategy returns YAML default."""
    result = strategy.match("Simpson Chubby 2 Synthetic")

    assert result.matched is not None
    assert result.matched["brand"] == "Simpson"
    assert result.matched["model"] == "Chubby 2"
    # Check nested structure (no redundant root fields)
    assert "fiber" not in result.matched, "Should not have root-level fiber"
    assert "knot_size_mm" not in result.matched, "Should not have root-level knot_size_mm"
    assert result.matched["knot"]["fiber"] == "Badger"  # YAML default, not user override
    assert result.matched["knot"]["knot_size_mm"] == 27
    assert result.matched["handle"]["brand"] == "Simpson"
    assert result.matched["handle"]["model"] is None
    assert result.match_type == "regex"


def test_known_brush_ap_shave_co_g5c(strategy):
    """Test matching AP Shave Co G5C brush"""
    result = strategy.match("AP Shave Co G5C")

    assert result.matched is not None
    assert result.matched["brand"] == "AP Shave Co"
    assert result.matched["model"] == "G5C"
    # Check nested structure (no redundant root fields)
    assert "fiber" not in result.matched, "Should not have root-level fiber"
    assert "knot_size_mm" not in result.matched, "Should not have root-level knot_size_mm"
    assert result.matched["knot"]["fiber"] == "Synthetic"
    assert result.matched["knot"]["knot_size_mm"] == 24
    assert result.matched["handle"]["brand"] == "AP Shave Co"
    assert result.matched["handle"]["model"] is None
    assert result.match_type == "regex"
