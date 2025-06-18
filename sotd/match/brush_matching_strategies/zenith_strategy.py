import re

from sotd.match.brush_matching_strategies.utils.fiber_utils import match_fiber


class ZenithBrushMatchingStrategy:
    def match(self, value: str) -> dict:
        if not isinstance(value, str):
            return {"original": value, "matched": None, "pattern": None, "strategy": "Zenith"}

        zenith_re = r"zenith.*([a-wyz]\d{1,3})"
        res = re.search(zenith_re, value, re.IGNORECASE)

        if res:
            fiber = match_fiber(value) or "Boar"
            model = res.group(1).upper()

            matched = {
                "brand": "Zenith",
                "model": model,
                "fiber": fiber,
                "knot_size_mm": None,
                "handle_maker": None,
                "source_text": res.group(0),
                "source_type": "exact",
            }

            return {
                "original": value,
                "matched": matched,
                "pattern": zenith_re,
                "strategy": "Zenith",
            }

        return {"original": value, "matched": None, "pattern": None, "strategy": "Zenith"}

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
