from .blade_matcher import BladeMatcher
from .brush_matcher import BrushMatcher  # placeholder
from .razor_matcher import RazorMatcher
from .soap_matcher import SoapMatcher
from .types import MatchResult

razor_matcher = RazorMatcher()
blade_matcher = BladeMatcher()
soap_matcher = SoapMatcher()
brush_matcher = BrushMatcher()


def match_record(record: dict) -> dict:
    result = record.copy()

    # Match razor first (required for blade matching)
    if "razor" in result:
        razor_result = razor_matcher.match(result["razor"])
        result["razor"] = razor_result

    # Blade matching requires razor context
    if "blade" in result:
        razor_matched = result.get("razor", {}).get("matched", {})

        # If no razor context, match blade normally (fallback behavior)
        if not razor_matched:
            blade_result = blade_matcher.match(result["blade"])
            result["blade"] = blade_result
        else:
            razor_format = razor_matched.get("format", "").upper()

            # Skip blade matching for formats where blade is irrelevant
            irrelevant_formats = ["SHAVETTE (DISPOSABLE)", "CARTRIDGE", "STRAIGHT"]

            if razor_format in irrelevant_formats:
                # Clear blade info since it's irrelevant for these razor formats
                result["blade"] = MatchResult(
                    original=result["blade"], matched=None, match_type=None, pattern=None
                )
            else:
                # For other formats, try context-aware matching
                blade_result = blade_matcher.match_with_context(result["blade"], razor_format)
                result["blade"] = blade_result

    if "soap" in result:
        soap_result = soap_matcher.match(result["soap"])
        result["soap"] = soap_result

    if "brush" in result:
        brush_result = brush_matcher.match(result["brush"])
        result["brush"] = brush_result

    return result
