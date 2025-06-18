import pytest
from sotd.match.brush_matching_strategies.declaration_grooming_strategy import (
    DeclarationGroomingBrushMatchingStrategy,
)


@pytest.fixture
def test_catalog():
    return {
        "Declaration Grooming": {
            "B2": {"patterns": ["B2(\\.\\s|\\.$|\\s|$)"]},
            "B3": {"patterns": ["B3(\\.\\s|\\.$|\\s|$)"]},
            "B10": {"patterns": ["b10"]},
            "B9A": {"patterns": ["B9A", "b9.*alpha"]},
        },
        "Zenith": {
            "B16": {"fiber": "Boar", "knot_size_mm": 24, "patterns": ["zenith.*b16"]},
            "B8": {"fiber": "Boar", "knot_size_mm": 28, "patterns": ["zenith.*b8"]},
        },
    }


@pytest.fixture
def strategy(test_catalog):
    return DeclarationGroomingBrushMatchingStrategy(test_catalog)


def test_declaration_grooming_b3_match(strategy):
    result = strategy.match("Declaration B3")

    assert result["matched"] is not None
    assert result["matched"]["brand"] == "Declaration Grooming"
    assert result["matched"]["model"] == "B3"
    assert result["matched"]["fiber"] == "Badger"  # Default for DG
    assert result["matched"]["knot_size_mm"] == 28.0  # Default for DG
    assert result["pattern"] == "B3(\\.\\s|\\.$|\\s|$)"
    assert result["strategy"] == "DeclarationGrooming"


def test_declaration_grooming_b3_with_period(strategy):
    result = strategy.match("Declaration B3. Jefferson")

    assert result["matched"] is not None
    assert result["matched"]["brand"] == "Declaration Grooming"
    assert result["matched"]["model"] == "B3"


def test_declaration_grooming_b10(strategy):
    result = strategy.match("DG B10 Jefferson")

    assert result["matched"] is not None
    assert result["matched"]["brand"] == "Declaration Grooming"
    assert result["matched"]["model"] == "B10"


def test_declaration_grooming_b9a_alpha(strategy):
    result = strategy.match("DG B9 Alpha")

    assert result["matched"] is not None
    assert result["matched"]["brand"] == "Declaration Grooming"
    assert result["matched"]["model"] == "B9A"


def test_zenith_b16_no_match(strategy):
    """Test that DG strategy correctly rejects Zenith brushes (explicit Zenith brand context)"""
    result = strategy.match("Zenith B16")

    assert result["matched"] is None
    assert result["strategy"] == "DeclarationGrooming"


def test_zenith_b8_no_match(strategy):
    """Test that DG strategy correctly rejects Zenith brushes (explicit Zenith brand context)"""
    result = strategy.match("Zenith B8")

    assert result["matched"] is None
    assert result["strategy"] == "DeclarationGrooming"


def test_standalone_model_matches_dg(strategy):
    """Test that standalone model numbers default to Declaration Grooming"""
    result = strategy.match("B2")

    assert result["matched"] is not None
    assert result["matched"]["brand"] == "Declaration Grooming"
    assert result["matched"]["model"] == "B2"
    assert result["strategy"] == "DeclarationGrooming"


def test_no_match(strategy):
    result = strategy.match("Unknown brush")

    assert result["matched"] is None


def test_with_user_fiber(strategy):
    """Test that DG strategy uses defaults regardless of user input"""
    result = strategy.match("Declaration B3 Synthetic")

    assert result["matched"] is not None
    assert result["matched"]["fiber"] == "Badger"  # DG always uses defaults
    assert result["matched"]["brand"] == "Declaration Grooming"


def test_with_user_knot_size(strategy):
    """Test that DG strategy extracts knot size from user input"""
    result = strategy.match("Declaration B3 26mm")

    assert result["matched"] is not None
    assert result["matched"]["knot_size_mm"] == 26.0  # User input takes precedence
    assert result["matched"]["brand"] == "Declaration Grooming"


def test_empty_catalog():
    strategy = DeclarationGroomingBrushMatchingStrategy({})
    result = strategy.match("Declaration B3")

    assert result["matched"] is None


def test_case_insensitive_match(strategy):
    result = strategy.match("declaration b3")

    assert result["matched"] is not None
    assert result["matched"]["brand"] == "Declaration Grooming"
    assert result["matched"]["model"] == "B3"
