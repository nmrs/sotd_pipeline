# pylint: disable=redefined-outer-name
import pytest
from sotd.match.brush_matching_strategies.chisel_and_hound_strategy import (
    ChiselAndHoundBrushMatchingStrategy,
)


@pytest.fixture
def ch_and_h_strategy():
    return ChiselAndHoundBrushMatchingStrategy()


def test_chisel_and_hound_v27_match(ch_and_h_strategy):
    """Test Chisel & Hound V27 pattern"""
    strategy = ch_and_h_strategy
    result = strategy.match("Chisel & Hound V27")

    assert result is not None
    assert result["brand"] == "Chisel & Hound"
    assert result["model"] == "V27"
    assert result["fiber"] == "badger"
    assert result["knot_size_mm"] == 26.0
    assert result["source_type"] == "exact"


def test_chisel_and_hound_abbreviated(ch_and_h_strategy):
    """Test C&H abbreviation"""
    strategy = ch_and_h_strategy
    result = strategy.match("C&H V25")

    assert result is not None
    assert result["brand"] == "Chisel & Hound"
    assert result["model"] == "V25"


def test_chisel_and_hound_typo_fou(ch_and_h_strategy):
    """Test common misspelling 'fou' instead of 'hou'"""
    strategy = ch_and_h_strategy
    result = strategy.match("Chisel & Fou V20")

    assert result is not None
    assert result["brand"] == "Chisel & Hound"
    assert result["model"] == "V20"


def test_chisel_and_hound_case_insensitive(ch_and_h_strategy):
    """Test case insensitive matching"""
    strategy = ch_and_h_strategy
    result = strategy.match("chisel & hound v15")

    assert result is not None
    assert result["brand"] == "Chisel & Hound"
    assert result["model"] == "V15"


def test_chisel_and_hound_with_extra_text(ch_and_h_strategy):
    """Test with additional text"""
    strategy = ch_and_h_strategy
    result = strategy.match("My Chisel & Hound V12 brush is great")

    assert result is not None
    assert result["brand"] == "Chisel & Hound"
    assert result["model"] == "V12"


def test_chisel_and_hound_lowest_version(ch_and_h_strategy):
    """Test lowest version number (V10)"""
    strategy = ch_and_h_strategy
    result = strategy.match("Chisel & Hound V10")

    assert result is not None
    assert result["brand"] == "Chisel & Hound"
    assert result["model"] == "V10"


def test_chisel_and_hound_no_match_high_version(ch_and_h_strategy):
    """Test version numbers outside range (too high)"""
    strategy = ch_and_h_strategy
    result = strategy.match("Chisel & Hound V28")

    assert result is None


def test_chisel_and_hound_no_match_low_version(ch_and_h_strategy):
    """Test version numbers outside range (too low)"""
    strategy = ch_and_h_strategy
    result = strategy.match("Chisel & Hound V9")

    assert result is None


def test_chisel_and_hound_no_match_no_version(ch_and_h_strategy):
    """Test Chisel & Hound without version number"""
    strategy = ch_and_h_strategy
    result = strategy.match("Chisel & Hound brush")

    assert result is None


def test_chisel_and_hound_no_match_different_brand(ch_and_h_strategy):
    """Test with different brand"""
    strategy = ch_and_h_strategy
    result = strategy.match("Simpson V25")

    assert result is None


def test_chisel_and_hound_c_and_h_pattern(ch_and_h_strategy):
    """Test 'C and H' pattern"""
    strategy = ch_and_h_strategy
    result = strategy.match("C and H V23")

    assert result is not None
    assert result["brand"] == "Chisel & Hound"
    assert result["model"] == "V23"


def test_chisel_and_hound_c_plus_h_pattern(ch_and_h_strategy):
    """Test 'C+H' pattern"""
    strategy = ch_and_h_strategy
    result = strategy.match("C+H V18")

    assert result is not None
    assert result["brand"] == "Chisel & Hound"
    assert result["model"] == "V18"


def test_chisel_and_hound_space_between_v_and_number(ch_and_h_strategy):
    """Test space between 'v' and version number"""
    strategy = ch_and_h_strategy
    result = strategy.match("Chisel & Hound V 26")

    assert result is not None
    assert result["brand"] == "Chisel & Hound"
    assert result["model"] == "V26"
    assert result["fiber"] == "badger"
    assert result["knot_size_mm"] == 26.0


def test_chisel_and_hound_abbreviated_with_space(ch_and_h_strategy):
    """Test C&H with space between v and number"""
    strategy = ch_and_h_strategy
    result = strategy.match("C&H V 15")

    assert result is not None
    assert result["brand"] == "Chisel & Hound"
    assert result["model"] == "V15"


def test_invalid_input_types(ch_and_h_strategy):
    """Test with invalid input types"""
    strategy = ch_and_h_strategy
    assert strategy.match(None) is None
    assert strategy.match(123) is None
    assert strategy.match([]) is None
