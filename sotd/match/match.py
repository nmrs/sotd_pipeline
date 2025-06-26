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

            if razor_format not in irrelevant_formats:
                result["blade"] = blade_matcher.match(result["blade"])
            else:
                # Clear blade info since it's irrelevant for these razor formats
                result["blade"] = {"original": result["blade"], "matched": None, "match_type": None}

    if "soap" in result:
        result["soap"] = soap_matcher.match(result["soap"])
    if "brush" in result:
        result["brush"] = brush_matcher.match(result["brush"])
    return result


def match_record_with_monitoring(
    record: dict,
    razor_matcher: RazorMatcher,
    blade_matcher: BladeMatcher,
    soap_matcher: SoapMatcher,
    brush_matcher: BrushMatcher,
    monitor=None,
) -> dict:
    """Context-aware record matching with performance monitoring support."""
    import time

    result = record.copy()

    # Match razor first (required for blade matching)
    if "razor" in result:
        start_time = time.time()
        result["razor"] = razor_matcher.match(result["razor"])
        if monitor:
            monitor.record_matcher_timing("razor", time.time() - start_time)

    # Blade matching requires razor context
    if "blade" in result:
        razor_matched = result.get("razor", {}).get("matched", {})

        # If no razor context, match blade normally (fallback behavior)
        if not razor_matched:
            start_time = time.time()
            result["blade"] = blade_matcher.match(result["blade"])
            if monitor:
                monitor.record_matcher_timing("blade", time.time() - start_time)
        else:
            razor_format = razor_matched.get("format", "").upper()

            # Skip blade matching for formats where blade is irrelevant
            irrelevant_formats = ["SHAVETTE (DISPOSABLE)", "CARTRIDGE", "STRAIGHT"]

            if razor_format not in irrelevant_formats:
                start_time = time.time()
                result["blade"] = blade_matcher.match(result["blade"])
                if monitor:
                    monitor.record_matcher_timing("blade", time.time() - start_time)
            else:
                # Clear blade info since it's irrelevant for these razor formats
                result["blade"] = {"original": result["blade"], "matched": None, "match_type": None}

    if "soap" in result:
        start_time = time.time()
        result["soap"] = soap_matcher.match(result["soap"])
        if monitor:
            monitor.record_matcher_timing("soap", time.time() - start_time)
    if "brush" in result:
        start_time = time.time()
        result["brush"] = brush_matcher.match(result["brush"])
        if monitor:
            monitor.record_matcher_timing("brush", time.time() - start_time)
    return result
