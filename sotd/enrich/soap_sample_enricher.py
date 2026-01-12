from typing import Any, Dict, Optional

from sotd.utils.soap_extraction import extract_soap_sample_via_normalization

from .enricher import BaseEnricher


class SoapSampleEnricher(BaseEnricher):
    """Enricher for extracting soap sample information from user comments.

    Extracts sample information from patterns like:
    - "Summer Break Soaps - Steady (sample)" -> sample_type: "sample"
    - "Summer Break Soaps - Steady - soap (sample -- thanks!!)" -> sample_type: "sample"
    - "Summer Break Soaps - Steady (sample 3 of 10)" -> sample_type: "sample",
      sample_number: 3, total_samples: 10

    Uses the normalization-difference approach to avoid confusion between product names
    and sample indicators by leveraging the already-done normalization work.
    """

    @property
    def target_field(self) -> str:
        """Target soap field for enrichment."""
        return "soap"

    def applies_to(self, record: Dict[str, Any]) -> bool:
        """Check if this enricher applies to the record."""
        return "soap" in record and record["soap"] is not None

    def enrich(
        self,
        field_data: Dict[str, Any],
        original_comment: str,
        record: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Enrich soap data with sample information using normalization approach."""
        original = field_data.get("original", "")
        normalized = field_data.get("normalized", "")

        if not original or not normalized:
            return {}

        # Extract sample information using normalization-difference method
        result = extract_soap_sample_via_normalization(original, normalized)
        sample_type = result[0] if result else None
        sample_number = result[1] if result else None
        total_samples = result[2] if result else None
        extraction_remainder = result[3] if result else None

        # Create enriched data
        enriched_data = {
            "sample_type": sample_type,
            "sample_number": sample_number,
            "total_samples": total_samples,
            "extraction_remainder": extraction_remainder,
        }

        return enriched_data
