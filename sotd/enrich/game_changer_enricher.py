import re
from typing import Any, Dict, Optional

from .enricher import BaseEnricher


class GameChangerEnricher(BaseEnricher):
    """Enricher for extracting RazoRock Game Changer specifications.

    Extracts gap and variant information from RazoRock Game Changer razors:
    - Gap detection (.68, .76, .84, 1.05) - normalized from various formats
    - Variant detection (OC, JAWS) - open comb or jaws variants
    """

    @property
    def target_field(self) -> str:
        return "razor"

    def applies_to(self, record: Dict[str, Any]) -> bool:
        """Determine if this enricher applies to the given record.

        Applies to records with RazoRock Game Changer razors.
        """
        if "razor" not in record or record["razor"] is None:
            return False

        razor = record["razor"]
        brand = razor.get("brand", "")
        model = razor.get("model", "")

        return brand == "RazoRock" and "Game Changer" in model

    def enrich(self, field_data: Dict[str, Any], original_comment: str) -> Optional[Dict[str, Any]]:
        """Extract Game Changer specifications from the razor field data.

        Args:
            field_data: The matched razor data containing the user's razor string
            original_comment: The original user comment text (unused)

        Returns:
            Dictionary with gap and variant if found, or None if no specifications detected.
            Includes _enriched_by and _extraction_source metadata fields.
        """
        # Extract the user's razor string from the field data
        razor_string = field_data.get("model", "")
        if not razor_string:
            return None

        gap = self._extract_gap(razor_string)
        variant = self._extract_variant(razor_string)

        if gap is not None or variant is not None:
            result = {
                "_enriched_by": self.get_enricher_name(),
                "_extraction_source": "user_comment",
            }

            if gap is not None:
                result["gap"] = gap
            if variant is not None:
                result["variant"] = variant

            return result

        return None

    def _extract_gap(self, text: str) -> Optional[str]:
        """Extract gap specification from text using regex patterns.

        Args:
            text: The text to search for gap patterns

        Returns:
            The extracted gap as a normalized string (e.g., ".68", ".84"), or None if not found
        """
        # Pattern to match gap specifications in various formats
        # Matches 1.05, .68, .76, .84, 0.68, 0.76, 0.84, 105, 68, 76, 84
        pattern = (
            r"(?:GC|Game\s+Changer)?\s*"
            r"((?:1\.05)|(?:0?\.\d{2})|(?:\d{2,3}))"
            r"(?=\s|$|[A-Za-z]|\(|\)|\[|\]|\{|\})"
        )

        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            gap_value = match.group(1).lstrip()
            # Special case: handle '1.05' directly
            if gap_value == "1.05":
                gap_str = "1.05"
            else:
                # Normalize gap_value to just digits for parsing
                if gap_value.startswith("0."):
                    digits = gap_value[2:]
                elif gap_value.startswith("."):
                    digits = gap_value[1:]
                else:
                    digits = gap_value

                # Handle different digit lengths
                if len(digits) == 2:
                    gap_num = int(digits)
                    if gap_num < 50 or gap_num > 99:  # Reasonable gap range
                        return None
                    gap = f".{digits}"
                elif len(digits) == 3:
                    first_digit = int(digits[0])
                    last_two_digits = int(digits[1:3])
                    if first_digit == 1 and 0 <= last_two_digits <= 99:
                        gap = f"{first_digit}.{digits[1:3]}"
                    else:
                        return None
                else:
                    return None

                # Normalize the gap value
                try:
                    gap_float = float(gap)
                    gap_str = f"{gap_float:.2f}".removeprefix("0")
                    if gap_str in [".85", ".94"]:
                        gap_str = ".84"
                except ValueError:
                    return None

            # Only accept the specific valid gaps
            valid_gaps = [".68", ".76", ".84", "1.05"]
            if gap_str not in valid_gaps:
                return None
            return gap_str

        return None

    def _extract_variant(self, text: str) -> Optional[str]:
        """Extract variant specification from text using regex patterns.

        Args:
            text: The text to search for variant patterns

        Returns:
            The extracted variant as a string ("OC" or "JAWS"), or None if not found
        """
        # Check for JAWS first (more specific)
        jaws_pattern = r"\bjaws\b"
        if re.search(jaws_pattern, text, re.IGNORECASE):
            return "JAWS"

        # Check for open comb variants
        oc_patterns = [
            r"\boc\b",
            r"\bopen.*comb\b",
        ]

        for pattern in oc_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return "OC"

        return None
