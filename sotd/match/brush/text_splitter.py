"""Shared stateless text splitting functions for brush handle/knot separation.

This is the single source of truth for splitting logic. Both BrushSplitter
(legacy, thin wrapper) and AutomatedSplitStrategy delegate here.

All functions are pure — no I/O, no class state, no matcher calls.
"""

import re
from dataclasses import dataclass
from typing import Optional

from .delimiter_patterns import BrushDelimiterPatterns
from .strategies.utils.fiber_utils import match_fiber
from .strategies.utils.knot_signal_utils import (
    HANDLE_CRAFT_TERMS,
    assign_sides,
    knot_signal_score,
)
from .strategies.utils.knot_size_utils import parse_knot_size


@dataclass(frozen=True)
class SplitCandidate:
    """One possible split of a brush string into handle and knot text."""

    handle_text: str
    knot_text: str
    delimiter: str
    priority: str  # "high" or "medium"


# ---------------------------------------------------------------------------
# Text normalisation
# ---------------------------------------------------------------------------


def normalize_text(text: str) -> str:
    """Normalize dashes/spacing so delimiters are detected uniformly.

    - en-dash / em-dash → " - "
    - "word- " → "word - "
    - " -word" → " - word"
    """
    text = re.sub(r"\s*[\u2013\u2014]\s*", " - ", text)
    text = re.sub(r"(\w)- ", r"\1 - ", text)
    text = re.sub(r" -(\w)", r" - \1", text)
    return text


# ---------------------------------------------------------------------------
# Specification guards
# ---------------------------------------------------------------------------


def is_specification_x(text: str) -> bool:
    """Return True when ' x ' is a dimension spec, not a collaboration.

    Dimension patterns (should NOT split):
    - "Stirling Synthetic 26mm x 54mm"
    - "Simpson Chubby 2 x 24mm"  (bare number × trailing size only)

    Collaboration patterns (SHOULD split):
    - "AP Shave Co G5C 26mm x Rad Dinosaur"
    """
    # Unit on left side: "26mm x 54"
    if re.search(r"\d+\s*(mm|in\.|in|cm)\s+x\s+\d+", text, re.IGNORECASE):
        return True
    # Bare number × trailing size only: "Chubby 2 x 24mm" (no words after)
    if re.search(r"\d+\s+x\s+\d+\s*(?:mm|cm)\s*$", text, re.IGNORECASE):
        return True
    return False


def is_specification_slash(text: str, brands_with_slash: set | None = None) -> bool:
    """Return True when '/' is a specification, not a delimiter.

    Protects against splitting on:
    - "50/50", "70/30" percentage specs
    - "Mixed Badger/Boar" fiber specs
    - "r/wetshaving" Reddit references
    - Known brand names containing '/' (e.g. "EldrormR Industries/Muninn Woodworks")
    """
    # Percentage specs
    if re.search(r"\b\d{1,2}/\d{1,2}\b", text, re.IGNORECASE):
        return True
    if re.search(r"(?:horse|badger|boar|synthetic).*?\d{1,2}/\d{1,2}", text, re.IGNORECASE):
        return True

    # Mixed fiber specs
    if re.search(
        r"mixed\s+(?:badger|boar|synthetic|horse)/\s*(?:badger|boar|synthetic|horse)",
        text,
        re.IGNORECASE,
    ):
        return True
    if re.search(
        r"(?:badger|boar|synthetic|horse)/\s*(?:badger|boar|synthetic|horse)\s+mixed",
        text,
        re.IGNORECASE,
    ):
        return True

    # Reddit references
    if re.search(r"\br/\w+\b", text, re.IGNORECASE):
        return True

    # Known brands with "/"
    if brands_with_slash and "/" in text:
        text_lower = text.lower()
        for brand_name in brands_with_slash:
            if brand_name in text_lower:
                return True

    return False


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _find_x_delimiter(text: str) -> str:
    """Return the actual ' x ' / ' X ' variant found in *text*."""
    m = re.search(BrushDelimiterPatterns.X_COLLABORATION_PATTERN, text)
    return m.group() if m else " x "


def _looks_like_brand_alias(alias_part: str, size_fiber_part: str) -> bool:
    """Return True when *alias_part* looks like a brand alias (not size/fiber)."""
    return parse_knot_size(size_fiber_part) is not None or match_fiber(size_fiber_part) is not None


def _looks_like_handle_description(text: str) -> bool:
    """Return True when *text* looks like a handle description."""
    text_lower = text.lower()
    for term in HANDLE_CRAFT_TERMS:
        if term in text_lower:
            return True
    if parse_knot_size(text) is not None or match_fiber(text) is not None:
        return False
    return False


def _split_smart(text: str, delimiter: str) -> tuple[Optional[str], Optional[str]]:
    """Smart splitting: try every occurrence, pick best by knot signal margin.

    For " - " with multiple dashes, handles the "Brand - Alias - Size Fiber" pattern.
    For " - " without a second dash, only splits when knot signals are present.
    """
    delimiter_positions = []
    start = 0
    while True:
        pos = text.find(delimiter, start)
        if pos == -1:
            break
        delimiter_positions.append(pos)
        start = pos + len(delimiter)

    if not delimiter_positions:
        return None, None

    best_split = None
    best_margin = -float("inf")

    for pos in delimiter_positions:
        part1 = text[:pos].strip()
        part2 = text[pos + len(delimiter) :].strip()
        if not part1 or not part2:
            continue

        # Multi-dash pattern: "Brand - Alias - Size Fiber"
        if delimiter == " - " and " - " in part2:
            sub_parts = part2.split(" - ", 1)
            if len(sub_parts) == 2:
                middle_part = sub_parts[0].strip()
                size_fiber_part = sub_parts[1].strip()

                if _looks_like_brand_alias(middle_part, size_fiber_part):
                    handle, knot, margin = assign_sides(part1, part2)
                    if margin > best_margin:
                        best_margin = margin
                        best_split = (handle, knot)
                elif _looks_like_handle_description(middle_part):
                    combined_handle = f"{part1} - {middle_part}"
                    handle, knot, margin = assign_sides(combined_handle, size_fiber_part)
                    if margin > best_margin:
                        best_margin = margin
                        best_split = (handle, knot)
        else:
            # For " - " without second dash: require knot signals
            if delimiter == " - ":
                if knot_signal_score(part1) <= 0 and knot_signal_score(part2) <= 0:
                    continue

            handle, knot, margin = assign_sides(part1, part2)
            if margin > best_margin:
                best_margin = margin
                best_split = (handle, knot)

    return best_split if best_split else (None, None)


def _split_positional(text: str, delimiter: str) -> tuple[Optional[str], Optional[str]]:
    """Positional split: for 'in', first part = knot, second = handle."""
    parts = text.split(delimiter, 1)
    if len(parts) == 2:
        part1 = parts[0].strip()
        part2 = parts[1].strip()
        if part1 and part2:
            if delimiter == " in ":
                return part2, part1  # handle, knot
            return part1, part2
    return None, None


def _split_parentheses(text: str) -> tuple[Optional[str], Optional[str]]:
    """Split "Part1 (Part2)" using knot signal scoring."""
    match = re.search(r"^(.+?)\s+\(([^)]+)\)", text)
    if not match:
        return None, None
    part1 = match.group(1).strip()
    part2 = match.group(2).strip()
    if not part1 or not part2:
        return None, None
    handle, knot, _margin = assign_sides(part1, part2, "a_is_knot")
    return handle, knot


def _splits_at_all_positions(
    text: str,
    delimiter: str,
    use_signal_scoring: bool = True,
) -> list[tuple[str, str]]:
    """Return (handle, knot) for EVERY occurrence of *delimiter* in *text*.

    When *use_signal_scoring* is True, assign_sides is used for each split.
    When False, simple positional assignment (left=handle, right=knot) is used,
    which is appropriate for match_all where the scoring engine decides later.
    """
    results: list[tuple[str, str]] = []
    pos = 0
    while True:
        idx = text.lower().find(delimiter.lower(), pos)
        if idx == -1:
            break
        part1 = text[:idx].strip()
        part2 = text[idx + len(delimiter) :].strip()
        pos = idx + len(delimiter)
        if not part1 or not part2:
            continue
        if use_signal_scoring:
            handle, knot, _margin = assign_sides(part1, part2)
        else:
            handle, knot = part1, part2
        results.append((handle, knot))
    return results


def _should_skip_slash_position(text: str, position: int) -> bool:
    """Return True if slash at *position* is preceded by w/, r/, or u/."""
    before = text[:position].rstrip()
    if before and before[-1].lower() in ("w", "r", "u"):
        return True
    return False


def _split_slash(
    text: str, brands_with_slash: set | None = None
) -> tuple[Optional[str], Optional[str]]:
    """Split on '/' as medium-priority delimiter, guarding specs."""
    if is_specification_slash(text, brands_with_slash):
        return None, None
    slash_match = re.search(r"(.+?)(?<!w)(?<!r)(?<!u)\s*/\s*(.+)", text)
    if slash_match:
        part1 = slash_match.group(1).strip()
        part2 = slash_match.group(2).strip()
        if part1 and part2:
            handle, knot, _margin = assign_sides(part1, part2)
            return handle, knot
    return None, None


def _slash_splits_all(text: str, brands_with_slash: set | None = None) -> list[tuple[str, str]]:
    """Return (handle, knot) for every valid '/' position in *text*."""
    if is_specification_slash(text, brands_with_slash):
        return []
    results: list[tuple[str, str]] = []
    pos = 0
    while True:
        idx = text.find("/", pos)
        if idx == -1:
            break
        pos = idx + 1
        if _should_skip_slash_position(text, idx):
            continue
        part1 = text[:idx].strip()
        part2 = text[idx + 1 :].strip()
        if part1 and part2:
            handle, knot, _margin = assign_sides(part1, part2)
            results.append((handle, knot))
    return results


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def split_on_delimiters(
    text: str,
    brands_with_slash: set | None = None,
) -> list[SplitCandidate]:
    """Run the full delimiter priority cascade and return possible splits.

    Returns ALL possible splits for every delimiter, with signal-based
    handle/knot assignment via assign_sides().  Callers pick the best.

    Args:
        text: The (already normalised) brush string.
        brands_with_slash: Optional set of known brand/model names containing '/'.
    """
    candidates: list[SplitCandidate] = []
    seen: set[tuple[str, str]] = set()

    def _add(handle: Optional[str], knot: Optional[str], delimiter: str, priority: str):
        if handle and knot and (handle, knot) not in seen:
            seen.add((handle, knot))
            candidates.append(SplitCandidate(handle, knot, delimiter, priority))

    # --- High-priority: smart splitting delimiters (w/, with) ---
    for delimiter in BrushDelimiterPatterns.get_smart_splitting_delimiters():
        if delimiter.lower() in text.lower():
            h, k = _split_smart(text, delimiter)
            _add(h, k, delimiter, "high")

    # --- High-priority: positional (' in ') ---
    for delimiter in BrushDelimiterPatterns.get_positional_splitting_delimiters():
        if delimiter.lower() in text.lower():
            # Guard: skip "made in" and "in r/", "in u/"
            idx = text.lower().find(delimiter.lower())
            before = text[:idx].strip()
            after = text[idx + len(delimiter) :].strip()
            if before.lower().endswith("made") or after.lower().startswith(("r/", "u/")):
                continue
            h, k = _split_positional(text, delimiter)
            _add(h, k, delimiter, "high")

    # --- High-priority: ' x ' collaboration (with spec guard) ---
    if re.search(BrushDelimiterPatterns.X_COLLABORATION_PATTERN, text) and not is_specification_x(
        text
    ):
        x_delim = _find_x_delimiter(text)
        h, k = _split_smart(text, x_delim)
        _add(h, k, x_delim, "high")

    # --- Medium-priority: -, +, etc. ---
    medium_no_slash = [
        d for d in BrushDelimiterPatterns.get_medium_priority_delimiters() if d != "/" and d != " ("
    ]
    for delimiter in medium_no_slash:
        if delimiter.lower() in text.lower():
            for h, k in _splits_at_all_positions(text, delimiter):
                _add(h, k, delimiter, "medium")

    # --- Medium-priority: parentheses ---
    if " (" in text:
        h, k = _split_parentheses(text)
        _add(h, k, " (", "medium")

    # --- Medium-priority: slash ---
    if "/" in text and "w/" not in text.lower():
        for h, k in _slash_splits_all(text, brands_with_slash):
            _add(h, k, "/", "medium")

    return candidates
