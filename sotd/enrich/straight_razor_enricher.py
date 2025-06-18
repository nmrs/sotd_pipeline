import re
from typing import Any, Dict, Optional

from .enricher import BaseEnricher


class StraightRazorEnricher(BaseEnricher):
    """Enricher for extracting straight razor specifications from user comments.

    Extracts grind type, width, and point type from patterns like:
    - "full hollow 6/8 round point" -> grind: "full_hollow", width_eighths: 6, point: "round"
    - "wedge 7/8 square" -> grind: "wedge", width_eighths: 7, point: "square"
    - "half hollow 5/8" -> grind: "half_hollow", width_eighths: 5, point: null
    """

    @property
    def target_field(self) -> str:
        return "razor"

    def applies_to(self, record: Dict[str, Any]) -> bool:
        """Determine if this enricher applies to the given record.

        Applies to records that have a matched razor product that is a straight razor.
        """
        if "razor" not in record or record["razor"] is None:
            return False

        # Check if the razor is identified as a straight razor
        razor_data = record["razor"]

        # Check for format field indicating straight razor
        if isinstance(razor_data, dict) and razor_data.get("format") == "Straight":
            return True

        # Check for brand/model patterns that indicate straight razors
        if isinstance(razor_data, dict):
            brand = razor_data.get("brand", "").lower()
            model = razor_data.get("model", "").lower()

            # Known straight razor brands
            straight_brands = {
                "böker",
                "boker",
                "dovo",
                "filarmonica",
                "henckels",
                "henkels",
                "koraat",
                "portland razor co",
                "ralf aust",
                "thiers issard",
                "wade & butcher",
                "wade and butcher",
                "w&b",
            }

            if brand in straight_brands:
                return True

            # Check for "straight" in model name
            if "straight" in model:
                return True

        return False

    def enrich(self, field_data: Dict[str, Any], original_comment: str) -> Optional[Dict[str, Any]]:
        """Extract straight razor specifications from the user-supplied razor_extracted field.

        Args:
            field_data: The matched razor data from the match phase
            original_comment: The user-supplied razor_extracted field (not the full comment)

        Returns:
            Dictionary with grind, width_eighths, and point if found, or None if no specs detected.
            Includes _enriched_by and _extraction_source metadata fields.
            Preserves existing specifications from the match phase catalog data.
        """
        # Extract specifications from the razor_extracted field
        user_grind = self._extract_grind(original_comment)
        user_width_eighths = self._extract_width(original_comment)
        user_point = self._extract_point(original_comment)

        # Get existing specifications from match phase catalog data
        catalog_grind = field_data.get("grind") if isinstance(field_data, dict) else None
        catalog_width = field_data.get("width") if isinstance(field_data, dict) else None
        catalog_point = field_data.get("point") if isinstance(field_data, dict) else None

        # Convert catalog width to eighths if it's in fractional format
        catalog_width_eighths = None
        if catalog_width:
            catalog_width_eighths = self._parse_catalog_width(catalog_width)

        # Merge specifications: user comment takes precedence over catalog data
        final_grind = user_grind or catalog_grind
        final_width_eighths = user_width_eighths or catalog_width_eighths
        final_point = user_point or catalog_point

        # Determine extraction source for metadata
        extraction_sources = []
        if user_grind or user_width_eighths or user_point:
            extraction_sources.append("user_comment")
        if catalog_grind or catalog_width or catalog_point:
            extraction_sources.append("catalog_data")

        # Only return enriched data if we have specifications from any source
        if any([final_grind, final_width_eighths, final_point]):
            enriched_data: Dict[str, Any] = {
                "_enriched_by": self.get_enricher_name(),
                "_extraction_source": (
                    " + ".join(extraction_sources) if extraction_sources else "none"
                ),
            }

            if final_grind:
                enriched_data["grind"] = final_grind
            if final_width_eighths:
                enriched_data["width_eighths"] = final_width_eighths
            if final_point:
                enriched_data["point"] = final_point

            return enriched_data

        return None

    def _parse_catalog_width(self, width_str: str) -> Optional[int]:
        """Parse width specification from catalog data into eighths.

        Args:
            width_str: Width string from catalog (e.g., "15/16", "6/8", "0.75")

        Returns:
            Width in eighths as integer, or None if cannot parse
        """
        if not width_str:
            return None

        # Handle fractional formats
        fractional_match = re.match(r"(\d+)/(\d+)", width_str)
        if fractional_match:
            numerator = int(fractional_match.group(1))
            denominator = int(fractional_match.group(2))

            if denominator == 8:
                return numerator
            elif denominator == 16:
                return numerator // 2
            else:
                # Convert to eighths (assuming inches)
                return int((numerator / denominator) * 8)

        # Handle decimal formats
        try:
            width_float = float(width_str)
            return int(width_float * 8)
        except ValueError:
            return None

    def _extract_grind(self, text: str) -> Optional[str]:
        """Extract grind type from text using regex patterns.

        Args:
            text: The text to search for grind patterns

        Returns:
            The extracted grind type as a string, or None if not found
        """
        # Normalize text for case-insensitive matching
        text_lower = text.lower()

        # Grind patterns in order of specificity (most specific first)
        grind_patterns = [
            (r"\bfull\s*hollow\b", "full_hollow"),
            (r"\bthree\s*quarter\s*hollow\b", "three_quarter_hollow"),
            (r"\bhalf\s*hollow\b", "half_hollow"),
            (r"\bquarter\s*hollow\b", "quarter_hollow"),
            (r"\b5/8\s*hollow\b", "five_eighth_hollow"),
            (r"\bhollow\b", "hollow"),  # Generic hollow
            (r"\bwedge\b", "wedge"),
            (r"\bframeback\b", "frameback"),
            (r"\bconcave\b", "concave"),
        ]

        for pattern, grind_type in grind_patterns:
            if re.search(pattern, text_lower):
                return grind_type

        return None

    def _extract_width(self, text: str) -> Optional[int]:
        """Extract width from text using regex patterns.

        Args:
            text: The text to search for width patterns

        Returns:
            The extracted width in eighths as an integer, or None if not found
        """
        # Width patterns - look for fractional and decimal formats
        width_patterns = [
            # Direct eighth patterns (4/8, 5/8, etc.) - most specific first
            (r"\b(4|5|6|7|8)/8\b", lambda m: int(m.group(1))),
            # Direct sixteenth patterns (8/16, 10/16, etc.)
            (r"\b(8|10|12|14|16)/16\b", lambda m: int(m.group(1)) // 2),
            # Fractional patterns (4/8, 5/8, 6/8, 7/8, 8/8, etc.)
            (
                r"\b(\d{1,2})/(8|16)\b",
                lambda m: int(m.group(1)) if m.group(2) == "8" else int(m.group(1)) // 2,
            ),
            # Decimal patterns (0.5, 0.625, 0.75, 0.875, 1.0, etc.)
            (
                r"\b(0\.5|0\.625|0\.75|0\.875|1\.0)\b",
                lambda m: {"0.5": 4, "0.625": 5, "0.75": 6, "0.875": 7, "1.0": 8}[m.group(1)],
            ),
        ]

        for pattern, converter in width_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    return converter(match)
                except (ValueError, KeyError):
                    continue

        return None

    def _extract_point(self, text: str) -> Optional[str]:
        """Extract point type from text using regex patterns.

        Args:
            text: The text to search for point patterns

        Returns:
            The extracted point type as a string, or None if not found
        """
        # Normalize text for case-insensitive matching
        text_lower = text.lower()

        # Point patterns in order of specificity
        point_patterns = [
            (r"\bround\s*point\b", "round"),
            (r"\bsquare\s*point\b", "square"),
            (r"\bfrench\s*point\b", "french"),
            (r"\bspanish\s*point\b", "spanish"),
            (r"\bbarber['']?s\s*notch\b", "barbers_notch"),
            (r"\bnotch\b", "notch"),
            (r"\bspear\s*point\b", "spear"),
            (r"\bcoffin\s*point\b", "coffin"),
            (r"\bround\b", "round"),  # Generic round
            (r"\bsquare\b", "square"),  # Generic square
        ]

        for pattern, point_type in point_patterns:
            if re.search(pattern, text_lower):
                return point_type

        return None
