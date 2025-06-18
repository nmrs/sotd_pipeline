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
        """Extract blade use count from the original comment text.

        Args:
            field_data: The matched blade data (unused in this enricher)
            original_comment: The original user comment text for extraction

        Returns:
            Dictionary with use_count if found, or None if no count detected.
            Includes _enriched_by and _extraction_source metadata fields.
        """
        use_count = self._extract_use_count(original_comment)

        if use_count is not None:
            return {
                "use_count": use_count,
                "_enriched_by": self.get_enricher_name(),
                "_extraction_source": "user_comment",
            }

        return None

    def _extract_use_count(self, text: str) -> Optional[int]:
        """Extract blade use count from text using regex patterns.

        Args:
            text: The text to search for blade use count patterns

        Returns:
            The extracted use count as an integer, or None if not found
        """
        # Pattern to match blade use count in various formats.
        # This is adapted from the original blade matcher but uses search instead of match
        # to find patterns anywhere in the text, not just at the beginning/end.
        #
        # Matches patterns like:
        # - "Astra SP (3)" -> 3
        # - "Feather [5]" -> 5
        # - "Gillette Platinum {2}" -> 2
        # - "Personna x4" -> 4
        # - "Derby (x2)" -> 2
        # - "Voskhod 2x" -> 2
        # - "Astra SP [5x]" -> 5
        # - "Derby Extra (2X)" -> 2
        pattern = r"(?:[\(\[\{])?(?:x)?(\d+)(?:x)?[\)\]\}]?"

        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            try:
                return int(match.group(1))
            except (ValueError, IndexError):
                return None

        return None
