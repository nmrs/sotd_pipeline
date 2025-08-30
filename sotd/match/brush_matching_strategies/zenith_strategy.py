import re
from typing import Optional

from sotd.match.brush_matching_strategies.utils.pattern_utils import (
    create_strategy_result,
    validate_string_input,
)
from sotd.match.types import MatchResult


class ZenithBrushMatchingStrategy:
    def match(self, value: str) -> Optional[MatchResult]:
        # Use unified string validation
        normalized_text = validate_string_input(value)
        if normalized_text is None:
            return create_strategy_result(
                original_value=value, matched_data=None, pattern=None, strategy_name="zenith_brush"
            )

        # Normalize text
        normalized = normalized_text.lower()

        # Match Zenith B-series patterns (e.g., 'zenith b2', 'zenith b15') - only 1-2 digit models
        brand_match = re.search(r"zenith", normalized, re.IGNORECASE)
        model_match = re.search(r"zenith\s+(b\d{1,2})\b", normalized, re.IGNORECASE)

        if brand_match and model_match:
            brand = "Zenith"
            model_num = model_match.group(1)

            matched_data = {
                "brand": brand,
                "model": model_num,
                "fiber": "Boar",
                "knot_size_mm": None,
                "handle_maker": None,
                "source_text": model_match.group(0),
                "source_type": "exact",
            }

            return create_strategy_result(
                original_value=value,
                matched_data=matched_data,
                pattern=model_match.re.pattern,
                strategy_name="zenith_brush",
                match_type="regex",
            )

        # Return None when no match is found - this is the correct behavior
        # The StrategyOrchestrator will skip None results
        return None

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
