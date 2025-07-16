import re

from sotd.match.brush_matching_strategies.utils.pattern_utils import (
    create_strategy_result,
    validate_string_input,
)
from sotd.match.types import MatchResult


class OmegaSemogueBrushMatchingStrategy:
    def match(self, value: str) -> MatchResult:
        # Use unified string validation
        normalized_text = validate_string_input(value)
        if normalized_text is None:
            return create_strategy_result(
                original_value=value, matched_data=None, pattern=None, strategy_name="OmegaSemogue"
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

            matched_data = {
                "brand": brand,
                "model": model_num,
                "fiber": "boar",
                "knot_size_mm": None,
                "handle_maker": None,
                "source_text": model_match.group(0),
                "source_type": "exact",
            }

            return create_strategy_result(
                original_value=value,
                matched_data=matched_data,
                pattern=model_match.re.pattern,
                strategy_name="OmegaSemogue",
            )

        return create_strategy_result(
            original_value=value, matched_data=None, pattern=None, strategy_name="OmegaSemogue"
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
