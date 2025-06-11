import pytest
from sotd.match.brush_matching_strategies.known_brush_strategy import KnownBrushMatchingStrategy


@pytest.fixture
def test_catalog():
    return {
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
    }


@pytest.fixture
def strategy(test_catalog):
    return KnownBrushMatchingStrategy(test_catalog)


def test_known_brush_exact_match(strategy):
    result = strategy.match("Simpson Chubby 2")

    assert result["matched"] is not None
    assert result["matched"]["brand"] == "Simpson"
    assert result["matched"]["model"] == "Chubby 2"
    assert result["matched"]["fiber"] == "Badger"
    assert result["matched"]["knot_size_mm"] == 27
    assert result["pattern"] == "simp.*chubby\\s*2"
    assert result["strategy"] == "KnownBrush"


def test_known_brush_with_user_knot_size(strategy):
    result = strategy.match("Simpson 29mm CH2")

    assert result["matched"] is not None
    assert result["matched"]["brand"] == "Simpson"
    assert result["matched"]["model"] == "Chubby 2"
    assert result["matched"]["fiber"] == "Badger"
    assert result["matched"]["knot_size_mm"] == 27  # YAML takes precedence
    assert result["strategy"] == "KnownBrush"


def test_known_brush_omega_match(strategy):
    result = strategy.match("Omega Pro 48")

    assert result["matched"] is not None
    assert result["matched"]["brand"] == "Omega"
    assert result["matched"]["model"] == "10048"
    assert result["matched"]["fiber"] == "Boar"
    assert result["matched"]["knot_size_mm"] == 28


def test_known_brush_no_match(strategy):
    result = strategy.match("Unknown Brand 123")

    assert result["matched"] is None


def test_known_brush_with_user_fiber_conflict(strategy):
    """Test when user provides different fiber than YAML"""
    result = strategy.match("Simpson Chubby 2 Synthetic")

    assert result["matched"] is not None
    assert result["matched"]["fiber"] == "Badger"  # YAML takes precedence
    assert result["strategy"] == "KnownBrush"
    # Note: fiber_conflict is added by BrushMatcher post-processing, not individual strategies


def test_empty_catalog():
    strategy = KnownBrushMatchingStrategy({})
    result = strategy.match("Simpson Chubby 2")

    assert result["matched"] is None


def test_invalid_catalog_structure():
    """Test with malformed catalog data"""
    invalid_catalog = {"Simpson": "invalid_structure"}  # Should be dict
    strategy = KnownBrushMatchingStrategy(invalid_catalog)
    result = strategy.match("Simpson Chubby 2")

    assert result["matched"] is None
