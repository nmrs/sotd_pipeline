# pylint: disable=redefined-outer-name
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
    assert result["matched"]["model"] == "Boar"
    assert result["matched"]["fiber"] == "Boar"
    assert result["matched"]["fiber_strategy"] == "user_input"
    assert result["matched"]["knot_size_mm"] == 26.0
    assert result["match_type"] == "brand_default"
    assert result["pattern"] == "elite"


def test_other_brush_with_default_fiber(strategy):
    """Test brand match using default fiber"""
    result = strategy.match("Elite 26mm")

    assert result["matched"] is not None
    assert result["matched"]["brand"] == "Elite"
    assert result["matched"]["model"] == "Badger"  # Uses default
    assert result["matched"]["fiber"] == "Badger"
    assert result["matched"]["fiber_strategy"] == "default"
    assert result["matched"]["knot_size_mm"] == 26.0


def test_other_brush_alpha_synthetic(strategy):
    """Test Alpha brand with default synthetic"""
    result = strategy.match("Alpha brush")

    assert result["matched"] is not None
    assert result["matched"]["brand"] == "Alpha"
    assert result["matched"]["model"] == "Synthetic"
    assert result["matched"]["fiber"] == "Synthetic"
    assert result["matched"]["fiber_strategy"] == "default"


def test_other_brush_with_knot_size_from_yaml(strategy):
    """Test brand that has knot_size_mm in YAML"""
    result = strategy.match("Groomatorium")

    assert result["matched"] is not None
    assert result["matched"]["brand"] == "Groomatorium"
    assert result["matched"]["model"] == "Synthetic"
    assert result["matched"]["fiber"] == "Synthetic"
    assert result["matched"]["knot_size_mm"] == 24


def test_other_brush_cf_pattern(strategy):
    """Test CF abbreviation pattern for Groomatorium"""
    result = strategy.match("CF brush 22mm")

    assert result["matched"] is not None
    assert result["matched"]["brand"] == "Groomatorium"
    assert result["matched"]["model"] == "Synthetic"
    assert result["matched"]["knot_size_mm"] == 22.0  # User input overrides YAML


def test_other_brush_omega_boar_default(strategy):
    """Test Omega with boar default"""
    result = strategy.match("Omega brush")

    assert result["matched"] is not None
    assert result["matched"]["brand"] == "Omega"
    assert result["matched"]["model"] == "Boar"
    assert result["matched"]["fiber"] == "Boar"
    assert result["matched"]["fiber_strategy"] == "default"


def test_other_brush_user_fiber_overrides_default(strategy):
    """Test user fiber overrides default"""
    result = strategy.match("Omega Synthetic brush")

    assert result["matched"] is not None
    assert result["matched"]["brand"] == "Omega"
    assert result["matched"]["model"] == "Synthetic"
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
    assert result["matched"]["model"] == "Synthetic"
    assert result["matched"]["fiber"] == "Synthetic"


def test_other_brush_multiple_patterns(strategy):
    """Test brand with multiple patterns"""
    result = strategy.match("Chiseled Face 24mm")

    assert result["matched"] is not None
    assert result["matched"]["brand"] == "Groomatorium"
    assert result["matched"]["model"] == "Synthetic"


def test_empty_catalog():
    """Test with empty catalog"""
    strategy = OtherBrushMatchingStrategy({})
    result = strategy.match("Elite brush")

    assert result["matched"] is None


def test_invalid_catalog_structure():
    """Test with malformed catalog data - should raise exceptions during initialization"""

    # Test invalid structure (not a dict)
    invalid_catalog_1 = {
        "Elite": "invalid_structure",  # Should be dict
    }
    with pytest.raises(
        ValueError, match="Invalid catalog structure for brand 'Elite': must be a dictionary"
    ):
        OtherBrushMatchingStrategy(invalid_catalog_1)

    # Test missing patterns
    invalid_catalog_2 = {
        "Alpha": {
            "default": "Synthetic"
            # Missing patterns
        },
    }
    with pytest.raises(ValueError, match="Missing 'patterns' field for brand 'Alpha'"):
        OtherBrushMatchingStrategy(invalid_catalog_2)

    # Test patterns not a list
    invalid_catalog_3 = {
        "Beta": {"default": "Badger", "patterns": "not_a_list"},  # Should be list
    }
    with pytest.raises(ValueError, match="'patterns' field must be a list for brand 'Beta'"):
        OtherBrushMatchingStrategy(invalid_catalog_3)


def test_no_default_fiber():
    """Test brand without default fiber - should raise exception during initialization"""
    catalog = {
        "TestBrand": {
            "patterns": ["testbrand"]
            # No default fiber - invalid for other_brushes
        }
    }

    # Should raise ValueError during initialization
    with pytest.raises(ValueError, match="Missing 'default' fiber field for brand 'TestBrand'"):
        OtherBrushMatchingStrategy(catalog)
