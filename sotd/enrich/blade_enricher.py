from typing import Any, Dict

from sotd.utils.match_filter_utils import (
    extract_blade_and_use_count,
    extract_blade_use_count_via_normalization,
)

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

    A/B TESTING: This enricher now outputs both the current regex-based approach
    and the new normalization-difference approach for comparison.
    """

    @property
    def target_field(self) -> str:
        """Target blade field for enrichment."""
        return "blade"

    def applies_to(self, record: Dict[str, Any]) -> bool:
        """Check if this enricher applies to the record."""
        return "blade" in record and record["blade"] is not None

    def enrich(self, field_data: Dict[str, Any], original_comment: str) -> Dict[str, Any]:
        """Enrich blade data with use count information using both approaches."""
        original = field_data.get("original", "")
        normalized = field_data.get("normalized", "")
        matched = field_data.get("matched", {})
        model = matched.get("model") if matched else None

        if not original or not normalized:
            return {}

        # Extract counts using both approaches
        # Approach A: Current regex-based method
        result_a = extract_blade_and_use_count(original_comment, model)
        use_count_a = result_a[1] if result_a and result_a[1] else None

        # Approach B: New normalization-difference method
        result_b = extract_blade_use_count_via_normalization(original, normalized, model)
        use_count_b = result_b[0] if result_b else None
        extraction_remainder = result_b[1] if result_b else None

        # Create enriched data
        enriched_data = {
            "use_count": use_count_a,
            "use_count_b": use_count_b,
            "extraction_remainder": extraction_remainder,
        }

        # Add blade_count if available from Approach A
        if result_a and result_a[0]:
            enriched_data["blade_count"] = result_a[0]

        return enriched_data
