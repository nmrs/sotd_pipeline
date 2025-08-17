from typing import Any, Dict

from .enricher import BaseEnricher
from sotd.utils.blade_extraction import extract_blade_use_count_via_normalization


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

    Uses the normalization-difference approach to avoid confusion between model numbers
    and actual use counts by leveraging the already-done normalization work.
    """

    @property
    def target_field(self) -> str:
        """Target blade field for enrichment."""
        return "blade"

    def applies_to(self, record: Dict[str, Any]) -> bool:
        """Check if this enricher applies to the record."""
        return "blade" in record and record["blade"] is not None

    def enrich(self, field_data: Dict[str, Any], original_comment: str) -> Dict[str, Any]:
        """Enrich blade data with use count information using normalization approach."""
        original = field_data.get("original", "")
        normalized = field_data.get("normalized", "")
        matched = field_data.get("matched", {})
        model = matched.get("model") if matched else None

        if not original or not normalized:
            return {}

        # Extract use count using normalization-difference method
        result = extract_blade_use_count_via_normalization(original, normalized, model)
        use_count = result[0] if result else None
        extraction_remainder = result[1] if result else None

        # Create enriched data
        enriched_data = {
            "use_count": use_count,
            "extraction_remainder": extraction_remainder,
        }

        return enriched_data
