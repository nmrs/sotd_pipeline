import re
from typing import Optional

_FIBER_PATTERNS = {
    # Most specific patterns first
    "Mixed Badger/Synthetic": r"(natural fiber.*synthetic|badger/synth|synth/badger)",
    # Specific fiber types with detailed patterns
    "Mixed Badger/Horse": r"(badger/horse|vie-?long.*mix.*badger)",
    # Specific fiber types with detailed patterns
    "Mixed Boar/Horse": r"(boar/horse|horse/boar)",
    # Specific fiber types with detailed patterns
    "Mixed Badger/Boar": (
        r"^(?!.*badger[ -]dyed).*(mix|mixed|mi[sx]tura?|badg.*boar|boar.*badg|(?:badg|boar).*hybrid|hybrid.*(?:badg|boar)|fusion|"
        r"badger.*cased|tasso et setola|bristle (?:&|and) badger|badger (?:&|and) bristle)"
    ),
    "Synthetic": (
        r"(acrylic|timber|tux|mew|silk(?!.*badger)|synt|synbad|2bed|captain|cashmere|"
        r"faux (horse|boar|badger)|black.*(magic|wolf)|g4|boss|st-?(1|2)|trafalgar\s*t[23]|platinum"
        r"\bt[23]\b|kong|hi\s*brush|ak47|g5[abc]|stf|quartermoon|fibre|"
        r"\bmig\b|synthetic badger|mother ?(lode|load)|\bg\d\b|\bt4\b)"
    ),
    # General fiber types (checked last)
    "Boar": r"\b(board?|shoat|badger[- ]dyed.*boar)\b",
    "Badger": (
        r"(hmw|high.*mo|(2|3|two|three)[\s-]*band|shd|badger|silver ?tip|super|"
        r"gelo|gelous|gelousy|finest|best|ultralux|[fm]anchurian|\blod\b)"
    ),
    "Horse": r"\bhorse(hair)?\b",
}


def match_fiber(text: str) -> Optional[str]:
    for fiber, pattern in _FIBER_PATTERNS.items():
        if re.search(pattern, text, re.IGNORECASE):
            return fiber
    return None
