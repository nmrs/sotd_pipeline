import pytest
from sotd.match.brush_matching_strategies.other_brushes_strategy import OtherBrushMatchingStrategy


@pytest.fixture
def test_catalog():
    return {
        "Elite": {"default": "Badger", "patterns": ["elite"]},
        "Alpha": {"default": "Synthetic", "patterns": ["alpha"]},
        "Groomatorium": {
            "default": "Synthetic",
            "knot_size_mm": 24,
            "patterns": ["groomatorium", "chiseled face", "\\bcf\\b"],
        },
        "Omega": {"default": "Boar", "patterns": ["omega"]},
    }


@pytest.fixture
def strategy(test_catalog):
    return OtherBrushMatchingStrategy(test_catalog)


def test_other_brush_with_user_fiber(strategy):
    """Test brand match where user specifies fiber"""
    result = strategy.match("Elite 26mm Boar")

    assert result["matched"] is not None
    assert result["matched"]["brand"] == "Elite"
    assert result["matched"]["model"] == "Elite Boar"
    assert result["matched"]["fiber"] == "Boar"
    assert result["matched"]["fiber_strategy"] == "user_input"
    assert result["matched"]["knot_size_mm"] == 26.0
    assert result["matched"]["knot_size_strategy"] == "user_input"
    assert result["match_type"] == "brand_default"
    assert result["pattern"] == "elite"


def test_other_brush_with_default_fiber(strategy):
    """Test brand match using default fiber"""
    result = strategy.match("Elite 26mm")

    assert result["matched"] is not None
    assert result["matched"]["brand"] == "Elite"
    assert result["matched"]["model"] == "Elite Badger"  # Uses default
    assert result["matched"]["fiber"] == "Badger"
    assert result["matched"]["fiber_strategy"] == "default"
    assert result["matched"]["knot_size_mm"] == 26.0
    assert result["matched"]["knot_size_strategy"] == "user_input"


def test_other_brush_alpha_synthetic(strategy):
    """Test Alpha brand with default synthetic"""
    result = strategy.match("Alpha brush")

    assert result["matched"] is not None
    assert result["matched"]["brand"] == "Alpha"
    assert result["matched"]["model"] == "Alpha Synthetic"
    assert result["matched"]["fiber"] == "Synthetic"
    assert result["matched"]["fiber_strategy"] == "default"


def test_other_brush_with_knot_size_from_yaml(strategy):
    """Test brand that has knot_size_mm in YAML"""
    result = strategy.match("Groomatorium")

    assert result["matched"] is not None
    assert result["matched"]["brand"] == "Groomatorium"
    assert result["matched"]["model"] == "Groomatorium Synthetic"
    assert result["matched"]["fiber"] == "Synthetic"
    assert result["matched"]["knot_size_mm"] == 24
    assert result["matched"]["knot_size_strategy"] == "yaml"


def test_other_brush_cf_pattern(strategy):
    """Test CF abbreviation pattern for Groomatorium"""
    result = strategy.match("CF brush 22mm")

    assert result["matched"] is not None
    assert result["matched"]["brand"] == "Groomatorium"
    assert result["matched"]["model"] == "Groomatorium Synthetic"
    assert result["matched"]["knot_size_mm"] == 22.0  # User input overrides YAML


def test_other_brush_omega_boar_default(strategy):
    """Test Omega with boar default"""
    result = strategy.match("Omega brush")

    assert result["matched"] is not None
    assert result["matched"]["brand"] == "Omega"
    assert result["matched"]["model"] == "Omega Boar"
    assert result["matched"]["fiber"] == "Boar"
    assert result["matched"]["fiber_strategy"] == "default"


def test_other_brush_user_fiber_overrides_default(strategy):
    """Test user fiber overrides default"""
    result = strategy.match("Omega Synthetic brush")

    assert result["matched"] is not None
    assert result["matched"]["brand"] == "Omega"
    assert result["matched"]["model"] == "Omega Synthetic"
    assert result["matched"]["fiber"] == "Synthetic"
    assert result["matched"]["fiber_strategy"] == "user_input"


def test_other_brush_no_match(strategy):
    """Test no match for unknown brand"""
    result = strategy.match("Unknown Brand 123")

    assert result["matched"] is None
    assert result["match_type"] is None
    assert result["pattern"] is None


def test_other_brush_case_insensitive(strategy):
    """Test case insensitive matching"""
    result = strategy.match("ELITE synthetic")

    assert result["matched"] is not None
    assert result["matched"]["brand"] == "Elite"
    assert result["matched"]["model"] == "Elite Synthetic"
    assert result["matched"]["fiber"] == "Synthetic"


def test_other_brush_multiple_patterns(strategy):
    """Test brand with multiple patterns"""
    result = strategy.match("Chiseled Face 24mm")

    assert result["matched"] is not None
    assert result["matched"]["brand"] == "Groomatorium"
    assert result["matched"]["model"] == "Groomatorium Synthetic"


def test_empty_catalog():
    """Test with empty catalog"""
    strategy = OtherBrushMatchingStrategy({})
    result = strategy.match("Elite brush")

    assert result["matched"] is None


def test_invalid_catalog_structure():
    """Test with malformed catalog data"""
    invalid_catalog = {
        "Elite": "invalid_structure",  # Should be dict
        "Alpha": {
            "default": "Synthetic"
            # Missing patterns
        },
    }
    strategy = OtherBrushMatchingStrategy(invalid_catalog)

    # Should not match Elite (invalid structure)
    result = strategy.match("Elite brush")
    assert result["matched"] is None

    # Should not match Alpha (missing patterns)
    result = strategy.match("Alpha brush")
    assert result["matched"] is None


def test_no_default_fiber():
    """Test brand without default fiber"""
    catalog = {
        "TestBrand": {
            "patterns": ["testbrand"]
            # No default fiber
        }
    }
    strategy = OtherBrushMatchingStrategy(catalog)
    result = strategy.match("TestBrand brush")

    assert result["matched"] is not None
    assert result["matched"]["brand"] == "TestBrand"
    assert result["matched"]["model"] == "TestBrand"  # No fiber to append
    assert result["matched"]["fiber"] is None
