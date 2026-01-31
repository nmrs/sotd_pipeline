"""Soap mashup enricher: sets is_mashup from catalog countable or text detection."""

from typing import Any, Dict, Optional

from sotd.utils.soap_extraction import detect_soap_mashup

from .enricher import BaseEnricher


class SoapMashupEnricher(BaseEnricher):
    """Enricher that sets soap.enriched.is_mashup for mashup usage reporting.

    Two sources (union):
    1. Catalog: soap.matched.countable === false (catalog scent marked mashup/non-countable).
    2. Text: soap original/normalized contains "mashup", "mash up", or "mash-up" (catches
       unbranded entries like "soap mashup", "Sample mashup" even when matched is null).

    All mashup aggregators and metrics key off soap.enriched.is_mashup only.
    """

    @property
    def target_field(self) -> str:
        """Target soap field for enrichment."""
        return "soap"

    def applies_to(self, record: Dict[str, Any]) -> bool:
        """Apply when record has a soap field (even if matched is null)."""
        return "soap" in record and record["soap"] is not None

    def enrich(
        self,
        field_data: Dict[str, Any],
        original_comment: str,
        record: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Set is_mashup from matched.countable or text detection on original/normalized."""
        is_mashup = False

        # (a) Catalog: matched scent has countable === false
        matched = field_data.get("matched")
        if matched is not None and isinstance(matched, dict):
            if matched.get("countable") is False:
                is_mashup = True

        # (b) Text: original or normalized contains mashup indicator (e.g. "soap mashup")
        if not is_mashup:
            original = field_data.get("original") or ""
            normalized = field_data.get("normalized") or ""
            if detect_soap_mashup(original) or detect_soap_mashup(normalized):
                is_mashup = True

        return {"is_mashup": is_mashup}
