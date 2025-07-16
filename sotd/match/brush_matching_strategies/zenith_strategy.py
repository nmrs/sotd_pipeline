import re

from sotd.match.brush_matching_strategies.utils.fiber_utils import match_fiber
from sotd.match.brush_matching_strategies.utils.pattern_utils import (
    create_strategy_result,
    validate_string_input,
)
from sotd.match.types import MatchResult


class ZenithBrushMatchingStrategy:
    def match(self, value: str) -> MatchResult:
        # Use unified string validation
        normalized_text = validate_string_input(value)
        if normalized_text is None:
            return create_strategy_result(
                original_value=value, matched_data=None, pattern=None, strategy_name="Zenith"
            )

        zenith_re = r"zenith.*([a-wyz]\d{1,3})"
        res = re.search(zenith_re, normalized_text, re.IGNORECASE)

        if res:
            fiber = match_fiber(normalized_text) or "Boar"
            model = res.group(1).upper()

            matched_data = {
                "brand": "Zenith",
                "model": model,
                "fiber": fiber,
                "knot_size_mm": None,
                "handle_maker": None,
                "source_text": res.group(0),
                "source_type": "exact",
            }

            return create_strategy_result(
                original_value=value,
                matched_data=matched_data,
                pattern=zenith_re,
                strategy_name="Zenith",
            )

        return create_strategy_result(
            original_value=value, matched_data=None, pattern=None, strategy_name="Zenith"
        )

    def _get_default_match(self) -> dict:
        return {
            "brand": "Zenith",
            "model": None,
            "fiber": None,
            "knot_size_mm": None,
            "handle_maker": None,
            "source_text": None,
            "source_type": None,
        }
