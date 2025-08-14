# pylint: disable=redefined-outer-name
import pytest

from sotd.match.brush_matcher import BrushMatcher
from sotd.match.config import BrushMatcherConfig


@pytest.fixture
def brush_matcher():
    """Create a BrushMatcher instance with fallback strategies."""
    config = BrushMatcherConfig.create_default()
    return BrushMatcher(config)


def test_complete_brush_matching_with_timberwolf_split_brush(brush_matcher):
    """Test complete brush matching with 'Timberwolf 24mm' (split brush case)."""
    result = brush_matcher.match("Timberwolf 24mm")

    assert result is not None
    assert result.matched is not None

    # Should have handle and knot sections
    assert "handle" in result.matched
    assert "knot" in result.matched

    # Handle may not be matched (depends on handle matcher)
    # Handle brand may be None if not matched by handle matcher

    # Knot should be matched by KnotMatcher (Timberwolf is in the knot catalog)
    knot = result.matched["knot"]
    assert knot["brand"] == "Generic"  # Timberwolf is matched as Generic brand
    assert knot["model"] == "Timberwolf"  # Model should be Timberwolf
    assert knot["_pattern"] == "timberwolf"  # Should match the timberwolf pattern
    assert result.match_type == "regex"


def test_complete_brush_matching_with_custom_size_only(brush_matcher):
    """Test complete brush matching with 'Custom 26mm' (size-only case)."""
    result = brush_matcher.match("Custom 26mm")

    assert result is not None
    assert result.matched is not None

    # Should have handle and knot sections (treated as split brush)
    assert "handle" in result.matched
    assert "knot" in result.matched

    # Should be matched by KnotSizeFallbackStrategy
    knot = result.matched["knot"]
    assert knot["brand"] is None
    assert knot["model"] == "26mm"
    assert knot["fiber"] is None
    assert knot["_pattern"] == "size_detection"
    assert result.match_type == "regex"


def test_existing_brush_matching_still_works(brush_matcher):
    """Test that existing brush matching still works correctly."""
    # Test a known brush
    result = brush_matcher.match("Simpson Chubby 2")

    assert result is not None
    assert result.matched is not None
    # Check that it's a known brush match (not fallback)
    # The exact structure may vary, but it should be a successful match
    assert result.matched["brand"] == "Simpson"
    assert result.matched["model"] == "Chubby 2"
    # Should not be matched by fallback strategies
    assert "_matched_by_strategy" not in result.matched or result.matched[
        "_matched_by_strategy"
    ] not in ["FiberFallbackStrategy", "KnotSizeFallbackStrategy"]


def test_integration_with_enrich_phase_size_extraction(brush_matcher):
    """Test integration with the enrich phase (size extraction)."""
    # Test that size information is preserved for enrichment
    result = brush_matcher.match("Custom 27.5mm")

    assert result is not None
    assert result.matched is not None

    # Should have knot section with size information
    knot = result.matched["knot"]
    assert knot["brand"] is None
    assert knot["model"] == "27.5mm"
    assert knot["fiber"] is None
    assert knot["_pattern"] == "size_detection"

    # The enrich phase should be able to extract the size from the model field
    # This test verifies the data structure is correct for enrichment


def test_fallback_strategies_dont_interfere_with_known_knots(brush_matcher):
    """Test that the strategies don't interfere with known knot matching."""
    # Test a known knot that should match via existing strategies
    result = brush_matcher.match("Omega 10048")

    assert result is not None
    assert result.matched is not None
    assert result.matched["brand"] == "Omega"
    assert result.matched["model"] == "10048"
    # Should not be matched by fallback strategies
    assert "_matched_by_strategy" not in result.matched or result.matched[
        "_matched_by_strategy"
    ] not in ["FiberFallbackStrategy", "KnotSizeFallbackStrategy"]


def test_mixed_fiber_types_in_split_brushes(brush_matcher):
    """Test mixed fiber types in split brush scenarios."""
    result = brush_matcher.match("Wolf Whiskers - Mixed Badger/Boar")

    assert result is not None
    assert result.matched is not None

    # Should have handle and knot sections
    assert "handle" in result.matched
    assert "knot" in result.matched

    # Handle may not be matched (depends on handle matcher)
    # Handle brand may be None if not matched by handle matcher

    # Since there's no brush split entry, this is matched as dual-component
    # Wolf Whiskers is matched as both handle and knot maker
    knot = result.matched["knot"]
    assert knot["brand"] == "Wolf Whiskers"
    assert knot["model"] == "Mixed Badger/Boar"  # Full fiber description preserved
    assert knot["fiber"] == "Mixed Badger/Boar"
    # Pattern should now contain the actual regex pattern used for matching
    assert knot["_pattern"] is not None
    assert knot["_pattern"] != "dual_component_fallback"


def test_decimal_sizes_in_split_brushes(brush_matcher):
    """Test decimal sizes in split brush scenarios."""
    result = brush_matcher.match("Custom Handle - Custom 26.5mm")

    assert result is not None
    assert result.matched is not None

    # Should have handle and knot sections
    assert "handle" in result.matched
    assert "knot" in result.matched

    # Handle may not be matched (depends on handle matcher)
    # Handle brand may be None if not matched by handle matcher

    # Knot should be matched by KnotSizeFallbackStrategy
    knot = result.matched["knot"]
    assert knot["brand"] is None
    assert knot["model"] == "26.5mm"
    assert knot["fiber"] is None
    assert knot["_pattern"] == "size_detection"


def test_nx_patterns_in_split_brushes(brush_matcher):
    """Test NxM patterns in split brush scenarios."""
    result = brush_matcher.match("Elite Handle - Unknown 28x50")

    assert result is not None
    assert result.matched is not None

    # Should have handle and knot sections
    assert "handle" in result.matched
    assert "knot" in result.matched

    # Note: This case is matched by dual_component_fallback strategy, not fallback strategies
    # The knot is matched as "Elite" brand with "Badger" fiber
    knot = result.matched["knot"]
    assert knot["brand"] == "Elite"
    assert knot["model"] == "Badger"
    assert knot["fiber"] == "Badger"
    # Pattern should now contain the actual regex pattern used for matching
    assert knot["_pattern"] is not None
    assert knot["_pattern"] != "dual_component_fallback"


def test_completely_unmatched_brushes_return_none(brush_matcher):
    """Test that completely unmatched brushes return None."""
    result = brush_matcher.match("Completely Unknown Brush")

    # BrushMatcher returns a MatchResult with matched=None when no match is found
    assert result is not None
    assert result.matched is None


def test_empty_and_whitespace_inputs_e2e(brush_matcher):
    """Test that empty and whitespace inputs are handled correctly in E2E."""
    # Empty string
    result = brush_matcher.match("")
    assert result is None

    # Whitespace only
    result = brush_matcher.match("   ")
    assert result is not None
    assert result.matched is None

    # None input
    result = brush_matcher.match(None)  # type: ignore
    assert result is None


def test_fallback_strategy_priority_in_complex_scenarios(brush_matcher):
    """Test that fallback strategies have correct priority in complex scenarios."""
    # Test that fiber detection takes priority over size detection
    result = brush_matcher.match("Timberwolf 24mm")

    assert result is not None
    assert result.matched is not None
    knot = result.matched["knot"]
    assert (
        knot["_pattern"] == "timberwolf"
    )  # Should match the timberwolf pattern, not fiber_detection

    # Test that size detection works when no fiber is detected
    result = brush_matcher.match("Custom 26mm")

    assert result is not None
    assert result.matched is not None
    knot = result.matched["knot"]
    assert knot["_pattern"] == "size_detection"
    assert knot["fiber"] is None
    assert knot["model"] == "26mm"
