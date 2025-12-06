# pylint: disable=redefined-outer-name
import pytest

from sotd.match.brush.strategies.other_brushes_strategy import OtherBrushMatchingStrategy


@pytest.fixture
def strategy():
    """Create a test strategy with sample catalog data."""
    catalog = {
        "Elite": {
            "default": "Badger",
            "patterns": ["elite"],
        },
        "Alpha": {
            "default": "Synthetic",
            "patterns": ["alpha"],
        },
        "Groomatorium": {
            "default": "Badger",
            "knot_size_mm": 24,
            "patterns": ["groomatorium", "cf"],
        },
        "Omega": {
            "default": "Boar",
            "patterns": ["omega"],
        },
        "Chiseled Face": {
            "default": "Badger",
            "patterns": ["chiseled.*face", "cf"],
        },
    }
    return OtherBrushMatchingStrategy(catalog)


def test_other_brush_with_user_fiber(strategy):
    """Test brand match where user specifies fiber"""
    result = strategy.match("Elite 26mm Boar")

    assert result.matched is not None
    assert result.matched["brand"] == "Elite"
    assert result.matched["model"] == "Boar"  # User fiber
    # Check nested structure (no redundant root fields)
    assert "fiber" not in result.matched, "Should not have root-level fiber"
    assert "knot_size_mm" not in result.matched, "Should not have root-level knot_size_mm"
    assert result.matched["knot"]["fiber"] == "Boar"
    assert result.matched["knot"]["knot_size_mm"] == 26
    assert result.matched["handle"]["brand"] == "Elite"
    assert result.matched["handle"]["model"] is None
    assert result.match_type == "brand_default"


def test_other_brush_with_default_fiber(strategy):
    """Test brand match using default fiber"""
    result = strategy.match("Elite 26mm")

    assert result.matched is not None
    assert result.matched["brand"] == "Elite"
    assert result.matched["model"] == "Badger"  # Default fiber
    # Check nested structure (no redundant root fields)
    assert "fiber" not in result.matched, "Should not have root-level fiber"
    assert "knot_size_mm" not in result.matched, "Should not have root-level knot_size_mm"
    assert result.matched["knot"]["fiber"] == "Badger"
    assert result.matched["knot"]["knot_size_mm"] == 26
    assert result.matched["handle"]["brand"] == "Elite"
    assert result.matched["handle"]["model"] is None
    assert result.match_type == "brand_default"


def test_other_brush_alpha_synthetic(strategy):
    """Test Alpha brand with default synthetic"""
    result = strategy.match("Alpha brush")

    assert result.matched is not None
    assert result.matched["brand"] == "Alpha"
    assert result.matched["model"] == "Synthetic"  # Default fiber
    # Check nested structure (no redundant root fields)
    assert "fiber" not in result.matched, "Should not have root-level fiber"
    assert result.matched["knot"]["fiber"] == "Synthetic"
    assert result.matched["handle"]["brand"] == "Alpha"
    assert result.matched["handle"]["model"] is None
    assert result.match_type == "brand_default"


def test_other_brush_with_knot_size_from_yaml(strategy):
    """Test brand that has knot_size_mm in YAML"""
    result = strategy.match("Groomatorium")

    assert result.matched is not None
    assert result.matched["brand"] == "Groomatorium"
    assert result.matched["model"] == "Badger"  # Default fiber
    # Check nested structure (no redundant root fields)
    assert "fiber" not in result.matched, "Should not have root-level fiber"
    assert "knot_size_mm" not in result.matched, "Should not have root-level knot_size_mm"
    assert result.matched["knot"]["fiber"] == "Badger"
    assert result.matched["knot"]["knot_size_mm"] == 24  # From YAML
    assert result.matched["handle"]["brand"] == "Groomatorium"
    assert result.matched["handle"]["model"] is None
    assert result.match_type == "brand_default"


def test_other_brush_cf_pattern(strategy):
    """Test CF abbreviation pattern for Groomatorium"""
    result = strategy.match("CF brush 22mm")

    assert result.matched is not None
    assert result.matched["brand"] == "Groomatorium"
    assert result.matched["model"] == "Badger"  # Default fiber
    # Check nested structure (no redundant root fields)
    assert "fiber" not in result.matched, "Should not have root-level fiber"
    assert "knot_size_mm" not in result.matched, "Should not have root-level knot_size_mm"
    assert result.matched["knot"]["fiber"] == "Badger"
    assert result.matched["knot"]["knot_size_mm"] == 22  # User override
    assert result.matched["handle"]["brand"] == "Groomatorium"
    assert result.matched["handle"]["model"] is None
    assert result.match_type == "brand_default"


def test_other_brush_omega_boar_default(strategy):
    """Test Omega with boar default"""
    result = strategy.match("Omega brush")

    assert result.matched is not None
    assert result.matched["brand"] == "Omega"
    assert result.matched["model"] == "Boar"  # Default fiber
    # Check nested structure (no redundant root fields)
    assert "fiber" not in result.matched, "Should not have root-level fiber"
    assert result.matched["knot"]["fiber"] == "Boar"
    assert result.matched["handle"]["brand"] == "Omega"
    assert result.matched["handle"]["model"] is None
    assert result.match_type == "brand_default"


def test_other_brush_user_fiber_overrides_default(strategy):
    """Test user fiber overrides default"""
    result = strategy.match("Omega Synthetic brush")

    assert result.matched is not None
    assert result.matched["brand"] == "Omega"
    assert result.matched["model"] == "Synthetic"  # User fiber
    # Check nested structure (no redundant root fields)
    assert "fiber" not in result.matched, "Should not have root-level fiber"
    assert result.matched["knot"]["fiber"] == "Synthetic"
    assert result.matched["handle"]["brand"] == "Omega"
    assert result.matched["handle"]["model"] is None
    assert result.match_type == "brand_default"


def test_other_brush_no_match(strategy):
    """Test no match for unknown brand"""
    result = strategy.match("Unknown Brand 123")

    assert result.matched is None
    assert result.match_type is None


def test_other_brush_case_insensitive(strategy):
    """Test case insensitive matching"""
    result = strategy.match("ELITE synthetic")

    assert result.matched is not None
    assert result.matched["brand"] == "Elite"
    assert result.matched["model"] == "Synthetic"  # User fiber
    # Check nested structure (no redundant root fields)
    assert "fiber" not in result.matched, "Should not have root-level fiber"
    assert result.matched["knot"]["fiber"] == "Synthetic"
    assert result.matched["handle"]["brand"] == "Elite"
    assert result.matched["handle"]["model"] is None
    assert result.match_type == "brand_default"


def test_other_brush_multiple_patterns(strategy):
    """Test brand with multiple patterns"""
    result = strategy.match("Chiseled Face 24mm")

    assert result.matched is not None
    assert result.matched["brand"] == "Chiseled Face"
    assert result.matched["model"] == "Badger"  # Default fiber
    # Check nested structure (no redundant root fields)
    assert "fiber" not in result.matched, "Should not have root-level fiber"
    assert "knot_size_mm" not in result.matched, "Should not have root-level knot_size_mm"
    assert result.matched["knot"]["fiber"] == "Badger"
    assert result.matched["knot"]["knot_size_mm"] == 24
    assert result.matched["handle"]["brand"] == "Chiseled Face"
    assert result.matched["handle"]["model"] is None
    assert result.match_type == "brand_default"


def test_no_default_fiber():
    """Test brand without default fiber - should raise exception during initialization"""
    catalog = {
        "TestBrand": {
            "patterns": ["testbrand"]
            # No default fiber - invalid for other_brushes
        }
    }

    # Should raise ValueError during initialization
    expected_msg = (
        "Missing required fields for brand 'TestBrand' in other_brushes catalog: \\['default'\\]"
    )
    with pytest.raises(ValueError, match=expected_msg):
        OtherBrushMatchingStrategy(catalog)


def test_enhanced_regex_error_reporting():
    """Test that malformed regex patterns produce detailed error messages."""
    malformed_catalog = {
        "Test Brand": {
            "default": "Badger",
            "patterns": [r"invalid[regex"],  # Malformed regex - missing closing bracket
        }
    }

    with pytest.raises(ValueError) as exc_info:
        OtherBrushMatchingStrategy(malformed_catalog)

    error_message = str(exc_info.value)
    assert "Invalid regex pattern" in error_message
    assert "invalid[regex" in error_message
    assert "File: data/brushes.yaml" in error_message
    assert "Brand: Test Brand" in error_message
    assert "Strategy: OtherBrushMatchingStrategy" in error_message
    assert "unterminated character set" in error_message  # The actual regex error


def test_pattern_priority_longer_patterns_first():
    """Test that longer patterns are checked before shorter ones across all brands."""
    # Create a catalog where a shorter pattern (dubl.*duck) would match first
    # if patterns weren't sorted by length across brands
    catalog = {
        "Dubl Duck": {
            "default": "Boar",
            "patterns": ["dubl.*duck"],  # 11 chars - shorter pattern
        },
        "Heritage Collection": {
            "default": "Badger",
            "patterns": ["heritage", "heritage collection"],  # 18 chars - longer pattern
        },
    }
    strategy = OtherBrushMatchingStrategy(catalog)

    # Input that contains both patterns - longer pattern should win
    result = strategy.match("heritage collection dubl duck")

    assert result.matched is not None
    # Should match "Heritage Collection" (longer pattern) not "Dubl Duck" (shorter pattern)
    assert result.matched["brand"] == "Heritage Collection"
    assert result.matched["_pattern_used"] == "heritage collection"
    assert result.match_type == "brand_default"
