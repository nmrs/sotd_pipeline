import re
from typing import Any, Dict, Optional

from .enricher import BaseEnricher


class SuperSpeedTipEnricher(BaseEnricher):
    """Enricher for extracting Gillette Super Speed tip type (Red, Blue, Black, Flare).

    Extracts tip type from Gillette Super Speed razors:
    - Tip types: Red, Blue, Black, Flare (with "flair" as synonym)
    Output field: 'super_speed_tip'
    """

    @property
    def target_field(self) -> str:
        return "razor"

    def applies_to(self, record: Dict[str, Any]) -> bool:
        """Determine if this enricher applies to the given record.

        Applies to records with Gillette Super Speed razors.
        """
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
        """Extract Super Speed tip type from the user-supplied razor_extracted field.

        Args:
            field_data: The matched razor data (unused in this enricher)
            original_comment: The user-supplied razor_extracted field (not the full comment)

        Returns:
            Dictionary with 'super_speed_tip' if found, or None if not found.
            Includes _enriched_by and _extraction_source metadata fields.
        """
        razor_string = original_comment
        if not razor_string:
            return None

        tip_type = self._extract_tip_type(razor_string)
        if tip_type is not None:
            # Prepare extracted data
            extracted_data = {
                "super_speed_tip": tip_type,
            }

            # Use BaseEnricher's single source method for consistency
            return self._create_single_source_enriched_data(extracted_data, "user_comment")

        return None

    def _extract_tip_type(self, text: str) -> Optional[str]:
        """Extract tip type from text using regex patterns.

        Args:
            text: The text to search for tip type patterns

        Returns:
            The extracted tip type as a string (e.g., "Red", "Blue", "Black", "Flare"),
            or None if not found
        """
        tips = {
            "Red": ["red"],
            "Blue": ["blue"],
            "Black": ["black"],
            "Flare": ["flare", "flair"],
        }

        for tip_name, patterns in tips.items():
            for pattern in patterns:
                if re.search(rf"\b{pattern}\b", text, re.IGNORECASE):
                    return tip_name

        return None
