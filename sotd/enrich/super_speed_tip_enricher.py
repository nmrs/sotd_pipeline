import re
from typing import Any, Dict, Optional

from .enricher import BaseEnricher


class SuperSpeedTipEnricher(BaseEnricher):
    """Enricher for extracting Gillette Super Speed tip colors and variants.

    Extracts tip information from Gillette Super Speed razors:
    - Tip colors: Red, Blue, Black
    - Tip variants: Flare (with "flair" as synonym)
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

    def enrich(self, field_data: Dict[str, Any], original_comment: str) -> Optional[Dict[str, Any]]:
        """Extract Super Speed tip specifications from the user-supplied razor_extracted field.

        Args:
            field_data: The matched razor data (unused in this enricher)
            original_comment: The user-supplied razor_extracted field (not the full comment)

        Returns:
            Dictionary with tip color and variant if found, or None if no specifications detected.
            Includes _enriched_by and _extraction_source metadata fields.
        """
        razor_string = original_comment
        if not razor_string:
            return None

        tip_color = self._extract_tip_color(razor_string)
        tip_variant = self._extract_tip_variant(razor_string)

        if tip_color is not None or tip_variant is not None:
            result = {
                "_enriched_by": self.get_enricher_name(),
                "_extraction_source": "user_comment",
            }

            if tip_color is not None:
                result["tip_color"] = tip_color
            if tip_variant is not None:
                result["tip_variant"] = tip_variant

            return result

        return None

    def _extract_tip_color(self, text: str) -> Optional[str]:
        """Extract tip color from text using regex patterns.

        Args:
            text: The text to search for tip color patterns

        Returns:
            The extracted tip color as a string (e.g., "Red", "Blue", "Black"), or None if not found
        """
        tips = {
            "Red": ["red"],
            "Blue": ["blue"],
            "Black": ["black"],
        }

        for tip_name, patterns in tips.items():
            for pattern in patterns:
                if re.search(rf"\b{pattern}\b", text, re.IGNORECASE):
                    return tip_name

        return None

    def _extract_tip_variant(self, text: str) -> Optional[str]:
        """Extract tip variant from text using regex patterns.

        Args:
            text: The text to search for tip variant patterns

        Returns:
            The extracted tip variant as a string (e.g., "Flare"), or None if not found
        """
        tips = {
            "Flare": ["flare", "flair"],
        }

        for tip_name, patterns in tips.items():
            for pattern in patterns:
                if re.search(rf"\b{pattern}\b", text, re.IGNORECASE):
                    return tip_name

        return None
