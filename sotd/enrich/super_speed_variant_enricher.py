import re
from typing import Any, Dict, Optional

from .enricher import BaseEnricher

# Canonical variant labels
TV_SPECIAL = "TV Special"
RED_TIP = "Red Tip"
BLUE_TIP = "Blue Tip"
BLACK_HANDLE = "Black Handle"
BLACK_TIP = "Black Tip"
FLARE_TIP = "Flare Tip"
FORTIES_NDC = "40's Style (NDC)"
UNKNOWN = "Unknown"

# Explicit detection patterns in precedence order (first match wins).
# Each entry is (compiled regex, variant label).
_EXPLICIT_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    # 1. TV Special
    (re.compile(r"\btv\s+special\b", re.IGNORECASE), TV_SPECIAL),
    (re.compile(r"\btv\s+super[\s-]*speed\b", re.IGNORECASE), TV_SPECIAL),
    # 2. Red Tip (including Heavy Super Speed and bare Red)
    (re.compile(r"\bred\s*tip\b", re.IGNORECASE), RED_TIP),
    (re.compile(r"\bheavy\s+super[\s-]*speed\b", re.IGNORECASE), RED_TIP),
    (re.compile(r"\bred\b", re.IGNORECASE), RED_TIP),
    # 3. Blue Tip (including bare Blue)
    (re.compile(r"\bblue\s*tip\b", re.IGNORECASE), BLUE_TIP),
    (re.compile(r"\bblue\b", re.IGNORECASE), BLUE_TIP),
    # 4. Black Handle (before Black Tip)
    (re.compile(r"\bblack[\s-]*handled?\b", re.IGNORECASE), BLACK_HANDLE),
    # 5. Black Tip (explicit tip only — not bare Black)
    (re.compile(r"\bblack\s*tip\b", re.IGNORECASE), BLACK_TIP),
    # 6. Flare Tip (Flair is a common misspelling)
    (re.compile(r"\b(?:flare|flair)\s*tip\b", re.IGNORECASE), FLARE_TIP),
    # 7. 40's Style (NDC)
    (re.compile(r"\b40'?s\b", re.IGNORECASE), FORTIES_NDC),
    (re.compile(r"\bforties\b", re.IGNORECASE), FORTIES_NDC),
    (re.compile(r"\bno\s+date\s+code\b", re.IGNORECASE), FORTIES_NDC),
    (re.compile(r"\bpre[\s-]+date\s+code\b", re.IGNORECASE), FORTIES_NDC),
    (re.compile(r"\bndc\b", re.IGNORECASE), FORTIES_NDC),
]

_YEAR_PATTERN = re.compile(r"\b((?:19|20)\d{2})\b")


class SuperSpeedVariantEnricher(BaseEnricher):
    """Classify Gillette Super Speed razors into reporting variants.

    Applies explicit text matches in a fixed precedence order, then year-based
    inference when no explicit variant is found. Always writes
    ``super_speed_variant`` for non-empty input (including ``Unknown``).
    """

    @property
    def target_field(self) -> str:
        return "razor"

    def applies_to(self, record: Dict[str, Any]) -> bool:
        """Apply only to matched Gillette Super Speed razors."""
        if "razor" not in record or record["razor"] is None:
            return False

        razor = record["razor"]
        if not isinstance(razor, dict):
            return False

        matched_data = razor.get("matched", {})
        if not matched_data:
            return False

        brand = matched_data.get("brand", "")
        model = matched_data.get("model", "")

        return brand == "Gillette" and model == "Super Speed"

    def enrich(
        self,
        field_data: Dict[str, Any],
        original_comment: str,
        record: Optional[Dict[str, Any]] = None,
    ) -> Optional[Dict[str, Any]]:
        """Classify Super Speed variant from the user-supplied razor string.

        Args:
            field_data: The matched razor data (unused)
            original_comment: The user-supplied razor_extracted field

        Returns:
            Dictionary with ``super_speed_variant`` for non-empty input, or None
            when the input string is empty.
        """
        razor_string = original_comment
        if not razor_string:
            return None

        variant = self._classify_variant(razor_string)
        extracted_data = {"super_speed_variant": variant}
        return self._create_single_source_enriched_data(extracted_data, "user_comment")

    def _classify_variant(self, text: str) -> str:
        """Return exactly one canonical Super Speed variant label."""
        for pattern, variant in _EXPLICIT_PATTERNS:
            if pattern.search(text):
                return variant

        return self._infer_from_year(text)

    def _infer_from_year(self, text: str) -> str:
        """Infer variant from the first 4-digit year in the text, if any."""
        match = _YEAR_PATTERN.search(text)
        if not match:
            return UNKNOWN

        year = int(match.group(1))
        if 1947 <= year <= 1950:
            return FORTIES_NDC
        if 1951 <= year <= 1953:
            return UNKNOWN
        if 1954 <= year <= 1966:
            return FLARE_TIP
        if year >= 1967:
            return UNKNOWN

        return UNKNOWN
