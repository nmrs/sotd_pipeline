import re
from typing import Any, Dict, Optional

from .enricher import BaseEnricher


class ChristopherBradleyEnricher(BaseEnricher):
    """Enricher for extracting Karve Christopher Bradley plate specifications.

    Extracts plate level (AA-G) and plate type (SB/OC) from the razor field.
    """

    VALID_PLATE_LEVELS = ["AA", "A", "B", "C", "D", "E", "F", "G"]

    @property
    def target_field(self) -> str:
        return "razor"

    def applies_to(self, record: Dict[str, Any]) -> bool:
        """Determine if this enricher applies to the given record.

        Applies to records with Karve Christopher Bradley razors.
        """
        if "razor" not in record or record["razor"] is None:
            return False

        razor = record["razor"]
        brand = razor.get("brand", "")
        model = razor.get("model", "")

        return brand == "Karve" and ("Christopher Bradley" in model or "CB" in model)

    def enrich(self, field_data: Dict[str, Any], original_comment: str) -> Optional[Dict[str, Any]]:
        """Extract Christopher Bradley specifications from the user-supplied razor_extracted field.

        Args:
            field_data: The matched razor data (unused in this enricher)
            original_comment: The user-supplied razor_extracted field (not the full comment)

        Returns:
            Dictionary with plate and material if found, or None if no specifications detected.
            Includes _enriched_by and _extraction_source metadata fields.
        """
        razor_string = original_comment
        if not razor_string:
            return None
        plate_level = self._extract_plate_level(razor_string)
        if not plate_level:
            return None
        plate_type = self._extract_plate_type(razor_string)
        result = {
            "plate_level": plate_level,
            "plate_type": plate_type,
            "_enriched_by": self.get_enricher_name(),
            "_extraction_source": "user_comment",
        }
        return result

    def _extract_plate_level(self, text: str) -> Optional[str]:
        """Extract plate level from text using regex patterns.

        Args:
            text: The text to search for plate level patterns

        Returns:
            The extracted plate level as a string (e.g., "A", "B", "C"), or None if not found
        """
        # Match AA, A, B, C, D, E, F, G (case-insensitive, word boundary)
        pattern = r"\b(AA|A|B|C|D|E|F|G)\b"
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            level = match.group(1).upper()
            if level in self.VALID_PLATE_LEVELS:
                return level
        return None

    def _extract_plate_type(self, text: str) -> str:
        """Extract plate type from text using regex patterns.

        Args:
            text: The text to search for plate type patterns

        Returns:
            The extracted plate type as a string ("OC" for open comb, "SB" for solid bar)
        """
        # Match OC (open comb) or SB (solid bar), default to SB
        if re.search(r"\bOC\b|open comb", text, re.IGNORECASE):
            return "OC"
        return "SB"

    def _extract_material(self, text: str) -> Optional[str]:
        """Extract material specification from text using regex patterns.

        Args:
            text: The text to search for material patterns

        Returns:
            The extracted material as a string, or None if not found
        """
        # Check for titanium first (more specific)
        titanium_patterns = [
            r"\btitanium\b",
            r"\bti\b",
        ]
        for pattern in titanium_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return "titanium"
        # Check for stainless steel - be more specific to avoid false positives
        stainless_single_word_pattern = r"\bstainless(?=\b|\s|$|[.,;:!])"
        stainless_patterns = [r"\bstainless\s+steel\b", r"\bss\b", stainless_single_word_pattern]
        for pattern in stainless_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return "stainless steel"
        return None
