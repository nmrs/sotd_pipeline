import re
from typing import Any, Dict, Optional, TypedDict


class BladeEnrichment(TypedDict):
    raw: str
    name: str
    use: Optional[int]


class BrushEnrichment(TypedDict):
    raw: str
    name: str
    fiber: Optional[str]
    knot_mm: Optional[int]


_fibers = {
    "Synthetic": (
        r"(acrylic|timber|tux|mew|silk|synt|synbad|2bed|captain|cashmere|"
        r"faux.*horse|black.*(magic|wolf)|g4|boss|st-?(1|2)|trafalgar\\s*t[23]|"
        r"\\bt[23]\\b|kong|hi\\s*brush|ak47|g5[abc]|stf|quartermoon|fibre|"
        r"\bmig\b)"
    ),
    "Mixed Badger/Boar": r"(mix|mixed|mi[sx]tura?|badg.*boar|boar.*badg|hybrid|fusion)",
    "Boar": r"\b(boar|shoat)\b",
    "Badger": (
        r"(hmw|high.*mo|(2|3|two|three)\\s*band|shd|badger|silvertip|super|"
        r"gelo|gelous|gelousy|finest|best|ultralux|fanchurian)"
    ),
    "Horse": r"\bhorse(hair)?\b",
}


def enrich_blade(blade: str) -> BladeEnrichment:
    enriched_blade: BladeEnrichment = {
        "raw": blade.strip(),
        "name": blade.strip(),
        "use": None,
    }
    # Updated regex: allow optional x or X prefix before the number, e.g., (x2), (X2), (2)
    match = re.search(r"[\(\{\[]\s*(?:[xX])?\s*(\d+)\s*[\)\}\]]", blade)
    if match:
        enriched_blade["use"] = int(match.group(1))
        enriched_blade["name"] = blade[: match.start()].strip()
    return enriched_blade


def enrich_brush(brush: str) -> BrushEnrichment:
    enriched_brush: BrushEnrichment = {
        "raw": brush.strip(),
        "name": brush.strip(),
        "fiber": None,
        "knot_mm": None,
    }
    if match := re.search(r"\b(\d{2})(?:\s*)mm\b", brush.lower()):
        enriched_brush["knot_mm"] = int(match.group(1))
    for fiber, pattern in _fibers.items():
        if re.search(pattern, brush, re.IGNORECASE):
            enriched_brush["fiber"] = fiber
            break
    return enriched_brush


def enrich_entry(entry: Dict[str, Any]) -> Dict[str, Any]:
    enriched = {}

    if blade := entry.get("blade"):
        enriched["blade"] = enrich_blade(blade)

    if brush := entry.get("brush"):
        enriched["brush"] = enrich_brush(brush)

    result = dict(entry)
    if "blade" in enriched:
        result["blade"] = enriched["blade"]["name"]
        if enriched["blade"]["use"] is not None:
            result["blade_use"] = enriched["blade"]["use"]
    if "brush" in enriched:
        result["brush"] = enriched["brush"]["name"]
        if enriched["brush"]["fiber"] is not None:
            result["brush_fiber"] = enriched["brush"]["fiber"]
        if enriched["brush"]["knot_mm"] is not None:
            result["brush_knot_mm"] = enriched["brush"]["knot_mm"]
    return result
