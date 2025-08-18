#!/usr/bin/env python3
"""Soap sample enricher for the SOTD pipeline."""

from typing import Any, Dict

from sotd.utils.soap_extraction import extract_soap_sample_via_normalization

from .enricher import BaseEnricher


class SoapSampleEnricher(BaseEnricher):
    """Enricher for extracting soap sample information from user comments.

    Extracts sample information from patterns like:
    - "B&M Seville (sample)" -> sample_type: "sample"
    - "Stirling Bay Rum (sample #23)" -> sample_type: "sample", sample_number: 23
    - "Declaration Grooming (sample 5 of 10)" -> sample_type: "sample",
      sample_number: 5, total_samples: 10
    - "H&M - Seville - sample" -> sample_type: "sample"
    - "Zingari Man (tester)" -> sample_type: "tester"

    Uses the normalization-difference approach to avoid confusion by leveraging the
    already-done normalization work.
    """

    @property
    def target_field(self) -> str:
        """Target soap field for enrichment."""
        return "soap"

    def applies_to(self, record: Dict[str, Any]) -> bool:
        """Check if this enricher applies to the record."""
        return "soap" in record and record["soap"] is not None

    def enrich(self, field_data: Dict[str, Any], original_comment: str) -> Dict[str, Any]:
        """Enrich soap data with sample information using normalization approach."""
        original = field_data.get("original", "")
        normalized = field_data.get("normalized", "")

        if not original or not normalized:
            return {}

        # Extract sample information using normalization-difference method
        result = extract_soap_sample_via_normalization(original, normalized)
        sample_type, sample_number, total_samples, extraction_remainder = result

        # Create enriched data
        enriched_data = {
            "sample_type": sample_type,
            "sample_number": sample_number,
            "total_samples": total_samples,
            "extraction_remainder": extraction_remainder,
        }

        return enriched_data
