import re
from typing import Any, Dict, Optional

from .enricher import BaseEnricher


class BladeCountEnricher(BaseEnricher):
    """Enricher for extracting blade use count from user comments.

    Extracts the number of times a blade has been used from patterns like:
    - "Astra SP (3)" -> use_count: 3
    - "Feather [5]" -> use_count: 5
    - "Gillette Platinum {2}" -> use_count: 2
    - "Personna x4" -> use_count: 4
    """

    @property
    def target_field(self) -> str:
        return "blade"

    def applies_to(self, record: Dict[str, Any]) -> bool:
        """Determine if this enricher applies to the given record.

        Applies to any record that has a matched blade product.
        """
        return "blade" in record and record["blade"] is not None

    def enrich(self, field_data: Dict[str, Any], original_comment: str) -> Optional[Dict[str, Any]]:
        """Extract blade use count and blade count from the user-supplied blade_extracted field.

        Args:
            field_data: The matched blade data (unused in this enricher)
            original_comment: The user-supplied blade_extracted field (not the full comment)

        Returns:
            Dictionary with use_count and/or blade_count if found, or None if no count detected.
            Includes _enriched_by and _extraction_source metadata fields.
        """
        blade_count, use_count = self._extract_blade_and_use_count(original_comment)

        if blade_count is not None or use_count is not None:
            enriched = {
                "_enriched_by": self.get_enricher_name(),
                "_extraction_source": "user_comment",
            }
            if blade_count is not None:
                enriched["blade_count"] = str(blade_count)
            if use_count is not None:
                enriched["use_count"] = str(use_count)
            return enriched

        return None

    def _extract_blade_and_use_count(self, text: str) -> tuple[Optional[int], Optional[int]]:
        """Extract blade count and use count from text.

        Blade count patterns (leading only): [2x], (2x), {2x}, [X2], (x2), etc.
        Use count patterns: (3x), [x3], (4 times), {7th use}, (second use), etc.
        """
        if not text:
            return None, None

        # Pattern for leading blade count: e.g. [2x], (2x), {2x}, [X2], (x2), etc.
        leading_blade_count_pattern = r"^\s*(?:[\(\[\{])\s*(?:x)?(\d+)(?:x)?\s*[\)\]\}]"
        m = re.match(leading_blade_count_pattern, text, re.IGNORECASE)
        blade_count = int(m.group(1)) if m else None

        # If found, strip it from the front
        stripped = text[m.end() :] if m else text

        # Now extract use count patterns from remaining text
        # These can be (3x), [x3], (4 times), {7th use}, (second use), etc.
        use_count = self._extract_use_count(stripped)

        return blade_count, use_count

    def _extract_use_count(self, text: str) -> Optional[int]:
        """Extract use count from various patterns in text."""
        if not text:
            return None

        # Pattern 1: (3x), [x3], {2x}, etc.
        pattern1 = r"(?:[\(\[\{])\s*(?:x)?(\d+)(?:x)?\s*[\)\]\}]"
        match = re.search(pattern1, text, re.IGNORECASE)
        if match:
            return int(match.group(1))

        # Pattern 2: (4 times), [5 times], {3 times}, etc.
        pattern2 = r"(?:[\(\[\{])\s*(\d+)\s+times?\s*[\)\]\}]"
        match = re.search(pattern2, text, re.IGNORECASE)
        if match:
            return int(match.group(1))

        # Pattern 3: (7th use), [3rd use], {2nd use}, etc.
        pattern3 = r"(?:[\(\[\{])\s*(\d+)(?:st|nd|rd|th)\s+use\s*[\)\]\}]"
        match = re.search(pattern3, text, re.IGNORECASE)
        if match:
            return int(match.group(1))

        # Pattern 4: (second use), [third use], {fourth use}, etc.
        ordinal_words = {
            "first": 1,
            "second": 2,
            "third": 3,
            "fourth": 4,
            "fifth": 5,
            "sixth": 6,
            "seventh": 7,
            "eighth": 8,
            "ninth": 9,
            "tenth": 10,
            "eleventh": 11,
            "twelfth": 12,
            "thirteenth": 13,
            "fourteenth": 14,
            "fifteenth": 15,
            "sixteenth": 16,
            "seventeenth": 17,
            "eighteenth": 18,
            "nineteenth": 19,
            "twentieth": 20,
        }
        pattern4 = r"(?:[\(\[\{])\s*(" + "|".join(ordinal_words.keys()) + r")\s+use\s*[\)\]\}]"
        match = re.search(pattern4, text, re.IGNORECASE)
        if match:
            ordinal = match.group(1).lower()
            return ordinal_words.get(ordinal)

        # Pattern 5: (use 3), [use 5], {use 2}, etc.
        pattern5 = r"(?:[\(\[\{])\s*use\s+(\d+)\s*[\)\]\}]"
        match = re.search(pattern5, text, re.IGNORECASE)
        if match:
            return int(match.group(1))

        # Pattern 6: x4, 2x (standalone patterns without brackets)
        pattern6 = r"(?:^|\s)(?:x)?(\d+)(?:x)?(?:\s|$)"
        match = re.search(pattern6, text, re.IGNORECASE)
        if match:
            return int(match.group(1))

        return None
