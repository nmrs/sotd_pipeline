import pytest
from sotd.match.brush_matching_strategies.chisel_and_hound_strategy import (
    ChiselAndHoundBrushMatchingStrategy,
)


@pytest.fixture
def strategy():
    return ChiselAndHoundBrushMatchingStrategy()


def test_chisel_and_hound_v27_match(strategy):
    """Test Chisel & Hound V27 pattern"""
    result = strategy.match("Chisel & Hound V27")

    assert result is not None
    assert result["brand"] == "Chisel & Hound"
    assert result["model"] == "V27"
    assert result["fiber"] == "badger"
    assert result["knot_size_mm"] == 26.0
    assert result["source_type"] == "exact"


def test_chisel_and_hound_abbreviated(strategy):
    """Test C&H abbreviation"""
    result = strategy.match("C&H V25")

    assert result is not None
    assert result["brand"] == "Chisel & Hound"
    assert result["model"] == "V25"


def test_chisel_and_hound_typo_fou(strategy):
    """Test common misspelling 'fou' instead of 'hou'"""
    result = strategy.match("Chisel & Fou V20")

    assert result is not None
    assert result["brand"] == "Chisel & Hound"
    assert result["model"] == "V20"


def test_chisel_and_hound_case_insensitive(strategy):
    """Test case insensitive matching"""
    result = strategy.match("chisel & hound v15")

    assert result is not None
    assert result["brand"] == "Chisel & Hound"
    assert result["model"] == "V15"


def test_chisel_and_hound_with_extra_text(strategy):
    """Test with additional text"""
    result = strategy.match("My Chisel & Hound V12 brush is great")

    assert result is not None
    assert result["brand"] == "Chisel & Hound"
    assert result["model"] == "V12"


def test_chisel_and_hound_lowest_version(strategy):
    """Test lowest version number (V10)"""
    result = strategy.match("Chisel & Hound V10")

    assert result is not None
    assert result["brand"] == "Chisel & Hound"
    assert result["model"] == "V10"


def test_chisel_and_hound_no_match_high_version(strategy):
    """Test version numbers outside range (too high)"""
    result = strategy.match("Chisel & Hound V28")

    assert result is None


def test_chisel_and_hound_no_match_low_version(strategy):
    """Test version numbers outside range (too low)"""
    result = strategy.match("Chisel & Hound V9")

    assert result is None


def test_chisel_and_hound_no_match_no_version(strategy):
    """Test Chisel & Hound without version number"""
    result = strategy.match("Chisel & Hound brush")

    assert result is None


def test_chisel_and_hound_no_match_different_brand(strategy):
    """Test with different brand"""
    result = strategy.match("Simpson V25")

    assert result is None


def test_chisel_and_hound_c_and_h_pattern(strategy):
    """Test 'C and H' pattern"""
    result = strategy.match("C and H V23")

    assert result is not None
    assert result["brand"] == "Chisel & Hound"
    assert result["model"] == "V23"


def test_chisel_and_hound_c_plus_h_pattern(strategy):
    """Test 'C+H' pattern"""
    result = strategy.match("C+H V18")

    assert result is not None
    assert result["brand"] == "Chisel & Hound"
    assert result["model"] == "V18"


def test_invalid_input_types(strategy):
    """Test with invalid input types"""
    assert strategy.match(None) is None
    assert strategy.match(123) is None
    assert strategy.match([]) is None
