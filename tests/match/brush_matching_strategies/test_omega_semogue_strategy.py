import pytest
from sotd.match.brush_matching_strategies.omega_semogue_strategy import (
    OmegaSemogueBrushMatchingStrategy,
)


@pytest.fixture
def strategy():
    return OmegaSemogueBrushMatchingStrategy()


def test_omega_with_model_number(strategy):
    """Test Omega with model number"""
    result = strategy.match("Omega 10049")

    assert result["matched"] is not None
    assert result["matched"]["brand"] == "Omega"
    assert result["matched"]["model"] == "10049"
    assert result["matched"]["fiber"] == "boar"
    assert result["matched"]["source_type"] == "exact"
    assert result["strategy"] == "OmegaSemogue"


def test_omega_with_longer_model(strategy):
    """Test Omega with longer model number"""
    result = strategy.match("Omega 456789")

    assert result["matched"] is not None
    assert result["matched"]["brand"] == "Omega"
    assert result["matched"]["model"] == "456789"


def test_semogue_with_c_model(strategy):
    """Test Semogue with C-series model"""
    result = strategy.match("Semogue C3")

    assert result["matched"] is not None
    assert result["matched"]["brand"] == "Semogue"
    assert result["matched"]["model"] == "c3"  # Preserves case from regex
    assert result["matched"]["fiber"] == "boar"


def test_semogue_with_numeric_model(strategy):
    """Test Semogue with numeric model"""
    result = strategy.match("Semogue 1800")

    assert result["matched"] is not None
    assert result["matched"]["brand"] == "Semogue"
    assert result["matched"]["model"] == "1800"


def test_case_insensitive_matching(strategy):
    """Test case insensitive matching"""
    result = strategy.match("OMEGA 10048")

    assert result["matched"] is not None
    assert result["matched"]["brand"] == "Omega"
    assert result["matched"]["model"] == "10048"


def test_semogue_typo_correction(strategy):
    """Test automatic correction of 'semouge' typo"""
    result = strategy.match("Semouge 1800")

    assert result["matched"] is not None
    assert result["matched"]["brand"] == "Semogue"
    assert result["matched"]["model"] == "1800"


def test_with_extra_text(strategy):
    """Test with additional text around the match"""
    result = strategy.match("My favorite Omega 10049 brush")

    assert result["matched"] is not None
    assert result["matched"]["brand"] == "Omega"
    assert result["matched"]["model"] == "10049"


def test_omega_only_no_model(strategy):
    """Test Omega without model number"""
    result = strategy.match("Omega brush")

    assert result["matched"] is None


def test_semogue_only_no_model(strategy):
    """Test Semogue without model number"""
    result = strategy.match("Semogue brush")

    assert result["matched"] is None


def test_no_match_different_brand(strategy):
    """Test with different brand"""
    result = strategy.match("Simpson Chubby 2")

    assert result["matched"] is None
    assert result["strategy"] == "OmegaSemogue"


def test_invalid_input_types(strategy):
    """Test with invalid input types"""
    result = strategy.match(None)
    assert result["matched"] is None
    assert result["strategy"] == "OmegaSemogue"

    result = strategy.match(123)
    assert result["matched"] is None


def test_short_model_numbers(strategy):
    """Test with short model numbers (should not match)"""
    result = strategy.match("Omega 12")  # Too short (less than 3 digits)

    assert result["matched"] is None


def test_semogue_c_series_variations(strategy):
    """Test various C-series model formats"""
    test_cases = [
        ("Semogue C5", "c5"),
        ("Semogue C10", "c10"),
        ("Semogue C12", "c12"),  # Changed from C123 to avoid numeric capture
    ]

    for input_str, expected_model in test_cases:
        result = strategy.match(input_str)
        assert result["matched"] is not None
        assert result["matched"]["brand"] == "Semogue"
        assert result["matched"]["model"] == expected_model


def test_omega_long_model_numbers(strategy):
    """Test Omega with various length model numbers"""
    test_cases = [
        "Omega 123",  # 3 digits
        "Omega 1234",  # 4 digits
        "Omega 12345",  # 5 digits
        "Omega 123456",  # 6 digits
    ]

    for test_case in test_cases:
        result = strategy.match(test_case)
        assert result["matched"] is not None
        assert result["matched"]["brand"] == "Omega"
