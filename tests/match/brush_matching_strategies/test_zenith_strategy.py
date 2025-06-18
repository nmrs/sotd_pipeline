import pytest
from sotd.match.brush_matching_strategies.zenith_strategy import ZenithBrushMatchingStrategy


@pytest.fixture
def strategy():
    return ZenithBrushMatchingStrategy()


def test_zenith_b_series_match(strategy):
    """Test Zenith B-series model"""
    result = strategy.match("Zenith B26")

    assert result["matched"] is not None
    assert result["matched"]["brand"] == "Zenith"
    assert result["matched"]["model"] == "B26"
    assert result["matched"]["fiber"] == "Boar"
    assert result["matched"]["knot_size_mm"] is None
    assert result["pattern"] == r"zenith.*([a-wyz]\d{1,3})"


def test_zenith_with_synthetic_fiber(strategy):
    """Test Zenith with synthetic fiber detected"""
    result = strategy.match("Zenith B26 Synthetic")

    assert result["matched"] is not None
    assert result["matched"]["brand"] == "Zenith"
    assert result["matched"]["model"] == "B26"
    assert result["matched"]["fiber"] == "Synthetic"
    assert result["matched"]["knot_size_mm"] is None


def test_zenith_with_badger_fiber(strategy):
    """Test Zenith with badger fiber detected"""
    result = strategy.match("Zenith B26 Badger")

    assert result["matched"] is not None
    assert result["matched"]["brand"] == "Zenith"
    assert result["matched"]["model"] == "B26"
    assert result["matched"]["fiber"] == "Badger"
    assert result["matched"]["knot_size_mm"] is None


def test_zenith_case_insensitive(strategy):
    """Test case insensitive matching"""
    result = strategy.match("zenith b26")

    assert result["matched"] is not None
    assert result["matched"]["brand"] == "Zenith"
    assert result["matched"]["model"] == "B26"  # Model is uppercased
    assert result["matched"]["fiber"] == "Boar"


def test_zenith_various_letters(strategy):
    """Test various letter prefixes (excluding X which is not in range a-wyz)"""
    test_cases = [
        ("Zenith A26", "A26"),
        ("Zenith C15", "C15"),
        ("Zenith F100", "F100"),
        ("Zenith Z3", "Z3"),
    ]

    for input_str, expected_model in test_cases:
        result = strategy.match(input_str)
        assert result["matched"] is not None
        assert result["matched"]["brand"] == "Zenith"
        assert result["matched"]["model"] == expected_model


def test_zenith_single_digit_model(strategy):
    """Test single digit model numbers"""
    result = strategy.match("Zenith B3")

    assert result["matched"] is not None
    assert result["matched"]["brand"] == "Zenith"
    assert result["matched"]["model"] == "B3"
    assert result["matched"]["fiber"] == "Boar"


def test_zenith_three_digit_model(strategy):
    """Test three digit model numbers"""
    result = strategy.match("Zenith B123")

    assert result["matched"] is not None
    assert result["matched"]["brand"] == "Zenith"
    assert result["matched"]["model"] == "B123"
    assert result["matched"]["fiber"] == "Boar"


def test_zenith_with_extra_text(strategy):
    """Test with additional text"""
    result = strategy.match("My favorite Zenith B26 brush")

    assert result["matched"] is not None
    assert result["matched"]["brand"] == "Zenith"
    assert result["matched"]["model"] == "B26"
    assert result["matched"]["fiber"] == "Boar"


def test_zenith_no_match_x_series(strategy):
    """Test that X-series models don't match (X not in range a-wyz)"""
    result = strategy.match("Zenith X26")

    assert result["matched"] is None


def test_zenith_no_match_no_model(strategy):
    """Test Zenith without model"""
    result = strategy.match("Zenith brush")

    assert result["matched"] is None


def test_zenith_no_match_different_brand(strategy):
    """Test with different brand"""
    result = strategy.match("Simpson B26")

    assert result["matched"] is None
    assert result["strategy"] == "Zenith"


def test_zenith_no_match_invalid_pattern(strategy):
    """Test patterns that don't match the regex"""
    test_cases = [
        "Zenith 26",  # No letter prefix
        "Zenith B",  # No number suffix
        "Zenith X26",  # X not in range a-wyz
    ]

    for test_case in test_cases:
        result = strategy.match(test_case)
        assert result["matched"] is None


def test_invalid_input_types(strategy):
    """Test with invalid input types"""
    result = strategy.match(None)
    assert result["matched"] is None
    assert result["strategy"] == "Zenith"

    result = strategy.match(123)
    assert result["matched"] is None


def test_zenith_fiber_detection_priority(strategy):
    """Test that detected fiber overrides default"""
    result = strategy.match("Zenith B26")  # No fiber mentioned
    assert result["matched"]["fiber"] == "Boar"  # Default

    result = strategy.match("Zenith B26 horse")  # Horse fiber
    assert result["matched"]["fiber"] == "Horse"  # Detected


def test_zenith_lowercase_model_conversion(strategy):
    """Test that model is converted to uppercase"""
    result = strategy.match("zenith b26")

    assert result["matched"] is not None
    assert result["matched"]["model"] == "B26"  # B26 is uppercase
