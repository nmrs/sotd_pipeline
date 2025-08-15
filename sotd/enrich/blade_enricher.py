from typing import Any, Dict, Optional

from sotd.utils.blade_patterns import extract_blade_counts

from .enricher import BaseEnricher


class BladeCountEnricher(BaseEnricher):
    """Enricher for extracting blade use count from user comments.

    Extracts the number of times a blade has been used from patterns like:
    - "Astra SP (3)" -> use_count: 3
    - "Feather [5]" -> use_count: 5
    - "Gillette Platinum {2}" -> use_count: 2
    - "Personna x4" -> use_count: 4
    - "7'o clock - yellow (new)" -> use_count: 1
    - "astra green 3rd use" -> use_count: 3
    - "astra green [2\\]" -> use_count: 2
    - "Feather Hi-Stainless (2nd)" -> use_count: 2
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
        blade_count, use_count = extract_blade_counts(original_comment)

        if blade_count is not None or use_count is not None:
            enriched = {
                "_enriched_by": self.get_enricher_name(),
                "_extraction_source": "user_comment",
            }
            if blade_count is not None:
                enriched["blade_count"] = blade_count  # Integer, not string
            if use_count is not None:
                enriched["use_count"] = use_count  # Integer, not string
            return enriched

        return None
