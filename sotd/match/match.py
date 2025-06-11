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
    if "razor" in result:
        result["razor"] = razor_matcher.match(result["razor"])
    if "blade" in result:
        result["blade"] = blade_matcher.match(result["blade"])
    if "soap" in result:
        result["soap"] = soap_matcher.match(result["soap"])
    if "brush" in result:
        result["brush"] = brush_matcher.match(result["brush"])
    return result
