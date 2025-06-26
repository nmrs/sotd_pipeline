from .blade_matcher import BladeMatcher
from .brush_matcher import BrushMatcher  # placeholder
from .razor_matcher import RazorMatcher
from .soap_matcher import SoapMatcher

razor_matcher = RazorMatcher()
blade_matcher = BladeMatcher()
soap_matcher = SoapMatcher()
brush_matcher = BrushMatcher()


def match_record(record: dict) -> dict:
    result = record.copy()

    # Match razor first (required for blade matching)
    if "razor" in result:
        result["razor"] = razor_matcher.match(result["razor"])

    # Blade matching requires razor context
    if "blade" in result:
        razor_matched = result.get("razor", {}).get("matched", {})

        # If no razor context, match blade normally (fallback behavior)
        if not razor_matched:
            result["blade"] = blade_matcher.match(result["blade"])
        else:
            razor_format = razor_matched.get("format", "").upper()

            # Skip blade matching for formats where blade is irrelevant
            irrelevant_formats = ["SHAVETTE (DISPOSABLE)", "CARTRIDGE", "STRAIGHT"]

            if razor_format in irrelevant_formats:
                # Clear blade info since it's irrelevant for these razor formats
                result["blade"] = {"original": result["blade"], "matched": None, "match_type": None}
            else:
                # For other formats, try context-aware matching
                result["blade"] = blade_matcher.match_with_context(result["blade"], razor_format)

    if "soap" in result:
        result["soap"] = soap_matcher.match(result["soap"])
    if "brush" in result:
        result["brush"] = brush_matcher.match(result["brush"])
    return result
