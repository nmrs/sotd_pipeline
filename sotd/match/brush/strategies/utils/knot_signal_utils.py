"""Knot signal scoring for handle/knot side assignment.

Instead of independently scoring each side as "handle-like" or "knot-like",
this module scores how strongly a text fragment looks like a knot description.
The side with more knot signals IS the knot; the other side is the handle
by elimination.

This module is the single source of truth for:
  - Knot signal detection (KNOT_SIGNAL_RE, knot_signal_spans)
  - Knot-likeness scoring (knot_signal_score)
  - Handle/knot term lists (HANDLE_CRAFT_TERMS, HANDLE_MATERIAL_TERMS, HANDLE_ALL_TERMS, KNOT_TERMS)
  - Side assignment (assign_sides)
"""

import re
from typing import List, Tuple

from .fiber_utils import match_fiber
from .knot_size_utils import parse_knot_size

# ---------------------------------------------------------------------------
# Canonical term sets — used by any code that needs knot/handle word lists
# ---------------------------------------------------------------------------

KNOT_TERMS: frozenset = frozenset({
    "badger", "boar", "synthetic", "synth", "nylon", "horse", "cashmere",
    "tuxedo", "silvertip", "fanchurian", "fan", "knot", "shoat",
    "tip", "density",
})

HANDLE_CRAFT_TERMS: frozenset = frozenset({
    "handle", "resin", "wood", "burl", "acrylic", "marble", "ebonite",
    "butterscotch", "stabilized", "turned", "stock", "custom", "artisan",
    "zebra",
})

HANDLE_MATERIAL_TERMS: frozenset = frozenset({
    "metal", "brass", "aluminum", "steel", "titanium",
    "ivory", "horn", "bone", "stone", "granite",
})

HANDLE_ALL_TERMS: frozenset = HANDLE_CRAFT_TERMS | HANDLE_MATERIAL_TERMS

# Keep backward-compatible alias
HANDLE_TERMS: frozenset = HANDLE_CRAFT_TERMS

# ---------------------------------------------------------------------------
# Compiled signal regexes — single source of truth
# ---------------------------------------------------------------------------

# Known knot series patterns (Declaration Grooming batches, Chisel & Hound versions, etc.)
_KNOT_SERIES_PATTERN = re.compile(
    r"""
    \b[Bb]\d{1,2}\b          # B3, B11, B15 (Declaration Grooming batches)
    | \b[Vv]\d{1,2}\b        # V9, V10, V14 (Chisel & Hound / Fanchurian versions)
    | \bSHD\b                 # Super High Density
    | \bHMW\b                 # High Mountain White
    | \b2BED\b                # Two-Band Every Day
    | \bG5[A-C]\b             # AP Shave Co G5 series
    | \bH[0-9]+\b             # H-series (Turn-N-Shave)
    """,
    re.VERBOSE | re.IGNORECASE,
)

# Unified knot signal regex — combines ALL knot indicators into one pattern.
# Used for proximity-based brand position validation (e.g. in
# FullInputComponentMatchingStrategy._correct_brand_positions).
KNOT_SIGNAL_RE = re.compile(
    r"""
      \d{2}\s*mm\b                    # knot size  (25mm, 26 mm)
    | \b(?:badger|boar|synthetic|synth|nylon|horse|cashmere
          |tuxedo|silvertip|fan(?:churian)?)\b   # fiber words
    | \b(?:knot|tip|density)\b         # knot-related keywords
    | \b[Bb]\d{1,2}\b                 # Declaration batches (B3, B15)
    | \b[Vv]\d{1,2}\b                 # Chisel & Hound versions (V10)
    | \bSHD\b | \bHMW\b | \b2BED\b   # knot series tokens
    | \bG5[A-C]\b                     # AP Shave Co G5 series
    | \bH[0-9]+\b                     # H-series (Turn-N-Shave)
    """,
    re.VERBOSE | re.IGNORECASE,
)

# Handle material words — if present, text is LESS likely to be a knot
_HANDLE_MATERIAL_PATTERN = re.compile(
    r"\b(" + "|".join(sorted(HANDLE_CRAFT_TERMS)) + r")\b",
    re.IGNORECASE,
)


def knot_signal_spans(text: str) -> List[Tuple[int, int]]:
    """Return (start, end) spans of all knot-signal matches in *text*.

    Useful for proximity calculations (e.g. which brand is closer to knot signals).
    """
    return [(m.start(), m.end()) for m in KNOT_SIGNAL_RE.finditer(text)]


def knot_signal_score(text: str) -> float:
    """Score how strongly a text fragment looks like a knot description.

    Higher score = more knot-like. Zero or negative = probably not a knot.

    Signals (all high-precision for knot identification):
      - mm size pattern (e.g. "26mm")        +10
      - Fiber type word (badger, synthetic…)  +10
      - "knot" keyword                         +8
      - Knot series token (B3, V10, SHD…)      +8
      - Handle material word (penalty)         −5
    """
    score = 0.0

    # mm size (e.g. "24mm", "26 mm", "28mm")
    if parse_knot_size(text) is not None:
        score += 10.0

    # Fiber type (badger, boar, synthetic, tuxedo, synbad, cashmere, etc.)
    if match_fiber(text) is not None:
        score += 10.0

    # Knot-related keywords: "knot", "tip", "density"
    if re.search(r"\b(knot|tip|density)\b", text, re.IGNORECASE):
        score += 8.0

    # Knot series tokens (B3, B15, V10, SHD, HMW, G5C, etc.)
    if _KNOT_SERIES_PATTERN.search(text):
        score += 8.0

    # Negative signal: handle material words suggest this is NOT a knot
    if _HANDLE_MATERIAL_PATTERN.search(text):
        score -= 5.0

    return score


def assign_sides(
    part_a: str, part_b: str, delimiter_convention: str = "a_is_handle"
) -> Tuple[str, str, float]:
    """Given two sides of a delimiter split, return (handle, knot, margin).

    Scores both sides for knot signals. The side with the higher knot score
    is the knot; the other is the handle.

    When scores are tied, falls back to delimiter convention:
      - "a_is_handle": part_a = handle, part_b = knot (for w/, with, +)
      - "a_is_knot":   part_a = knot, part_b = handle (for "in")

    Args:
        part_a: First text fragment (left of delimiter).
        part_b: Second text fragment (right of delimiter).
        delimiter_convention: Tiebreaker convention.

    Returns:
        (handle, knot, margin) where margin = abs(score_a - score_b).
        Higher margin = more confidence in the assignment.
    """
    score_a = knot_signal_score(part_a)
    score_b = knot_signal_score(part_b)
    margin = abs(score_a - score_b)

    if score_a > score_b:
        # part_a is the knot
        return part_b, part_a, margin
    elif score_b > score_a:
        # part_b is the knot
        return part_a, part_b, margin
    else:
        # Tied — fall back to delimiter convention
        if delimiter_convention == "a_is_knot":
            return part_b, part_a, 0.0
        else:
            # Default: a_is_handle (w/, with, +, -, etc.)
            return part_a, part_b, 0.0
