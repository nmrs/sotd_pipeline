import re
from typing import Optional

from sotd.match.brush_matching_strategies.utils.pattern_utils import (
    create_strategy_result,
    validate_string_input,
)
from sotd.match.types import MatchResult


class OmegaSemogueBrushMatchingStrategy:
    def match(self, value: str) -> Optional[MatchResult]:
        # Use unified string validation
        normalized_text = validate_string_input(value)
        if normalized_text is None:
            return create_strategy_result(
                original_value=value,
                matched_data=None,
                pattern=None,
                strategy_name="omega_semogue_brush",
            )

        # Normalize and fix common typo
        normalized = normalized_text.lower().replace("semouge", "semogue")

        brand_match = re.search(r"(omega|semogue)", normalized, re.IGNORECASE)
        # Match e.g. 'omega 10049', 'semogue c3', etc.
        model_match = re.search(
            r"(omega|semogue)[^\]\n\d]*(c\d{1,3}|\d{3,6})", normalized, re.IGNORECASE
        )

        if brand_match and model_match:
            brand = brand_match.group(1).title()
            model_num = model_match.group(2)

            # Create result with nested structure (no redundant root fields)
            matched_data = {
                "brand": brand,
                "model": model_num,
                "handle_maker": None,
                "source_text": model_match.group(0),
                "source_type": "exact",
                # Create nested handle section
                "handle": {
                    "brand": brand,  # Handle brand same as brush brand for Omega/Semogue
                    "model": None,  # Handle model not specified for Omega/Semogue
                },
                # Create nested knot section with fiber and size info
                "knot": {
                    "brand": brand,  # Knot brand same as brush brand for Omega/Semogue
                    "model": model_num,  # Knot model same as brush model for Omega/Semogue
                    "fiber": "Boar",
                    "knot_size_mm": None,
                },
            }

            return create_strategy_result(
                original_value=value,
                matched_data=matched_data,
                pattern=model_match.re.pattern,
                strategy_name="omega_semogue_brush",
                match_type="regex",
            )

        # Return MatchResult with matched=None when no match is found
        # This maintains consistency with the expected interface
        return create_strategy_result(
            original_value=value,
            matched_data=None,
            pattern=None,
            strategy_name="omega_semogue_brush",
        )

    def _get_default_match(self) -> dict:
        return {
            "brand": None,
            "model": None,
            "fiber": None,
            "knot_size_mm": None,
            "handle_maker": None,
            "source_text": None,
            "source_type": None,
        }
