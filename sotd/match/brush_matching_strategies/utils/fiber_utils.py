import re
from typing import Optional

_FIBER_PATTERNS = {
    "Badger": (
        r"(hmw|high.*mo|(2|3|two|three)\s*band|shd|badger|silvertip|super|"
        r"gelo|gelous|gelousy|finest|best|ultralux|[fm]anchurian|\blod\b)"
    ),
    "Boar": r"\b(boar|shoat)\b",
    "Horse": r"\bhorse(hair)?\b",
    "Mixed Badger/Boar": r"(mix|mixed|mi[sx]tura?|badg.*boar|boar.*badg|hybrid|fusion)",
    "Mixed Badger/Synthetic": r"(badg.*synth|synth.*badg)",
    "Synthetic": (
        r"(acrylic|timber|tux|mew|silk|synt|synbad|2bed|captain|cashmere|"
        r"faux (horse|boar|badger)|black.*(magic|wolf)|g4|boss|st-?(1|2)|trafalgar\s*t[23]|"
        r"\bt[23]\b|kong|hi\s*brush|ak47|g5[abc]|stf|quartermoon|fibre|"
        r"\bmig\b|synthetic badger|motherlode)"
    ),
}


def match_fiber(text: str) -> Optional[str]:
    for fiber, pattern in _FIBER_PATTERNS.items():
        if re.search(pattern, text, re.IGNORECASE):
            return fiber
    return None
