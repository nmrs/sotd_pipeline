"""
Test model naming consistency across all brush matching strategies.
Ensures that no strategy includes brand prefixes in the model field.
"""

from sotd.match.brush_matching_strategies.chisel_and_hound_strategy import (
    ChiselAndHoundBrushMatchingStrategy,
)
from sotd.match.brush_matching_strategies.declaration_grooming_strategy import (
    DeclarationGroomingBrushMatchingStrategy,
)
from sotd.match.brush_matching_strategies.known_brush_strategy import (
    KnownBrushMatchingStrategy,
)
from sotd.match.brush_matching_strategies.omega_semogue_strategy import (
    OmegaSemogueBrushMatchingStrategy,
)
from sotd.match.brush_matching_strategies.other_brushes_strategy import (
    OtherBrushMatchingStrategy,
)
from sotd.match.brush_matching_strategies.zenith_strategy import (
    ZenithBrushMatchingStrategy,
)


class TestModelNamingConsistency:
    """Test that all strategies return clean model names without brand prefixes."""

    def test_chisel_and_hound_clean_model_names(self):
        """Test that Chisel & Hound strategy returns clean model names."""
        strategy = ChiselAndHoundBrushMatchingStrategy()

        test_cases = [
            ("Chisel & Hound V20", "V20"),
            ("C&H V15", "V15"),
            ("chis hou V27", "V27"),
        ]

        for input_text, expected_model in test_cases:
            result = strategy.match(input_text)
            assert result is not None, f"No match for: {input_text}"
            assert result["brand"] == "Chisel & Hound"
            assert result["model"] == expected_model
            # Ensure model doesn't contain brand name
            assert "Chisel" not in result["model"]
            assert "Hound" not in result["model"]

    def test_declaration_grooming_clean_model_names(self):
        """Test that Declaration Grooming strategy returns clean model names."""
        # Use minimal catalog for testing
        catalog = {
            "Declaration Grooming": {
                "B2": {"patterns": ["B2(\\.\\s|\\.$|\\s|$)"]},
                "B15": {"patterns": ["B15(\\.\\s|\\.$|\\s|$)"]},
            }
        }
        strategy = DeclarationGroomingBrushMatchingStrategy(catalog)

        test_cases = [
            ("B2", "B2"),
            ("B15", "B15"),
            ("DG B2", "B2"),
        ]

        for input_text, expected_model in test_cases:
            result = strategy.match(input_text)
            assert result["matched"] is not None, f"No match for: {input_text}"
            assert result["matched"]["brand"] == "Declaration Grooming"
            assert result["matched"]["model"] == expected_model
            # Ensure model doesn't contain brand name
            assert "Declaration" not in result["matched"]["model"]
            assert "Grooming" not in result["matched"]["model"]

    def test_known_brush_clean_model_names(self):
        """Test that Known Brush strategy returns clean model names."""
        catalog = {
            "Simpson": {"Chubby 2": {"fiber": "Badger", "patterns": ["simpson.*chubby.*2"]}},
            "Omega": {"10048": {"fiber": "Boar", "patterns": ["omega.*10048"]}},
        }
        strategy = KnownBrushMatchingStrategy(catalog)

        test_cases = [
            ("Simpson Chubby 2", "Simpson", "Chubby 2"),
            ("Omega 10048", "Omega", "10048"),
        ]

        for input_text, expected_brand, expected_model in test_cases:
            result = strategy.match(input_text)
            assert result["matched"] is not None, f"No match for: {input_text}"
            assert result["matched"]["brand"] == expected_brand
            assert result["matched"]["model"] == expected_model
            # For known brushes, the model should not redundantly include the brand
            # unless it's part of the actual model name (like "Chubby 2")
            if expected_brand == "Omega":
                assert "Omega" not in result["matched"]["model"]

    def test_omega_semogue_clean_model_names(self):
        """Test that Omega/Semogue strategy returns clean model names."""
        strategy = OmegaSemogueBrushMatchingStrategy()

        test_cases = [
            ("Omega 10048", "Omega", "10048"),
            ("Semogue 1800", "Semogue", "1800"),
            ("Semogue C3", "Semogue", "c3"),
            ("OMEGA 456789", "Omega", "456789"),
        ]

        for input_text, expected_brand, expected_model in test_cases:
            result = strategy.match(input_text)
            assert result["matched"] is not None, f"No match for: {input_text}"
            assert result["matched"]["brand"] == expected_brand
            assert result["matched"]["model"] == expected_model
            # Ensure model doesn't contain brand name
            assert expected_brand not in result["matched"]["model"]

    def test_other_brushes_clean_model_names(self):
        """Test that Other Brushes strategy returns clean model names."""
        catalog = {
            "Elite": {"default": "Badger", "patterns": ["elite"]},
            "Wolf Whiskers": {"default": "Badger", "patterns": ["wolf.*whiskers", "ww"]},
        }
        strategy = OtherBrushMatchingStrategy(catalog)

        test_cases = [
            ("Elite Badger", "Elite", "Badger"),
            ("Wolf Whiskers Synthetic", "Wolf Whiskers", "Synthetic"),
            ("WW handle", "Wolf Whiskers", "Badger"),  # Default fiber
        ]

        for input_text, expected_brand, expected_model in test_cases:
            result = strategy.match(input_text)
            assert result["matched"] is not None, f"No match for: {input_text}"
            assert result["matched"]["brand"] == expected_brand
            assert result["matched"]["model"] == expected_model
            # Ensure model doesn't contain brand name
            assert "Elite" not in result["matched"]["model"]
            assert "Wolf" not in result["matched"]["model"]
            assert "Whiskers" not in result["matched"]["model"]

    def test_zenith_clean_model_names(self):
        """Test that Zenith strategy returns clean model names."""
        strategy = ZenithBrushMatchingStrategy()

        test_cases = [
            ("Zenith B2", "Zenith", "B2"),
            ("Zenith B26", "Zenith", "B26"),
            ("zenith c15", "Zenith", "C15"),  # Case conversion
            ("Zenith F100", "Zenith", "F100"),
        ]

        for input_text, expected_brand, expected_model in test_cases:
            result = strategy.match(input_text)
            assert result["matched"] is not None, f"No match for: {input_text}"
            assert result["matched"]["brand"] == expected_brand
            assert result["matched"]["model"] == expected_model
            # Ensure model doesn't contain brand name
            assert "Zenith" not in result["matched"]["model"]

    def test_all_strategies_brand_model_separation(self):
        """Comprehensive test ensuring brand and model are properly separated."""
        test_strategies = [
            (ChiselAndHoundBrushMatchingStrategy(), "Chisel & Hound V20"),
            (OmegaSemogueBrushMatchingStrategy(), "Omega 10048"),
            (ZenithBrushMatchingStrategy(), "Zenith B26"),
        ]

        for strategy, test_input in test_strategies:
            result = strategy.match(test_input)

            # Ensure we got a match
            if hasattr(result, "get") and result.get("matched"):
                matched = result["matched"]
                brand = matched.get("brand")
                model = matched.get("model")
            else:
                # Handle direct return format (some strategies)
                brand = result.get("brand") if result else None
                model = result.get("model") if result else None

            if brand and model:
                # Ensure brand and model are separate
                assert brand != model, f"Brand and model are identical for {test_input}"

                # Ensure model doesn't contain the full brand name
                # (Allow partial matches like "B" in "B26" but not "Zenith" in "Zenith B26")
                brand_words = brand.split()
                for brand_word in brand_words:
                    if len(brand_word) > 2:  # Only check meaningful words
                        assert brand_word not in model, (
                            f"Model '{model}' contains brand word '{brand_word}' "
                            f"for strategy {strategy.__class__.__name__} with input '{test_input}'"
                        )
