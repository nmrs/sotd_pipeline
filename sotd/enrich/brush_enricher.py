import re
from typing import Optional

from sotd.enrich.enricher import BaseEnricher


class BrushEnricher(BaseEnricher):
    """Enricher for brush specifications from user comments."""

    @property
    def target_field(self) -> str:
        return "brush"

    def applies_to(self, record: dict) -> bool:
        """Check if this enricher applies to the record."""
        brush_data = record.get("brush", {})
        if not brush_data or not isinstance(brush_data, dict):
            return False
        matched_data = brush_data.get("matched")
        if matched_data and isinstance(matched_data, dict):
            # Check for either top-level brand (legacy) or knot section brand (new format)
            top_level_brand = matched_data.get("brand") is not None
            knot_section = matched_data.get("knot", {})
            knot_brand = knot_section.get("brand") if isinstance(knot_section, dict) else None
            return top_level_brand or (knot_brand is not None)
        return False

    def enrich(self, field_data: dict, original_comment: str) -> Optional[dict]:
        """Extract brush specifications from the user-supplied brush_extracted field and merge
        with catalog data.

        Args:
            field_data: The matched brush data from the match phase
            original_comment: The user-supplied brush_extracted field (not the full comment)

        Returns:
            Dictionary with enriched data, or None if no enrichment possible.
        """
        if not field_data or not isinstance(field_data, dict):
            return None

        # All extraction is from the brush_extracted field (passed as original_comment)
        brush_extracted = original_comment
        if not brush_extracted:
            return None

        user_knot_size = self._extract_knot_size(brush_extracted)
        user_fiber = self._extract_fiber(brush_extracted)

        # Get catalog data from new format (knot section) or legacy format (top-level)
        knot_section = field_data.get("knot", {})
        catalog_knot_size = (
            knot_section.get("knot_size_mm") if knot_section else field_data.get("knot_size_mm")
        )
        catalog_fiber = knot_section.get("fiber") if knot_section else field_data.get("fiber")

        # Start with catalog data (preserved from match phase)
        enriched_data = {
            "knot_size_mm": catalog_knot_size,
            "fiber": catalog_fiber,
            "_enriched_by": "BrushEnricher",
            "_extraction_source": "catalog" if catalog_knot_size else "none",
        }

        # Handle knot size merging
        if user_knot_size is not None:
            if catalog_knot_size is not None:
                # Both catalog and user have knot size - check for conflicts
                if abs(catalog_knot_size - user_knot_size) < 0.1:
                    # Values match (within tolerance) - use user value, mark as confirmed
                    enriched_data["knot_size_mm"] = user_knot_size
                    enriched_data["_extraction_source"] = "user_confirmed_catalog"
                else:
                    # Values conflict - user takes precedence, mark conflict
                    enriched_data["knot_size_mm"] = user_knot_size
                    enriched_data["_extraction_source"] = "user_override_catalog"
                    enriched_data["_catalog_knot_size_mm"] = catalog_knot_size
            else:
                # Only user has knot size - use it
                enriched_data["knot_size_mm"] = user_knot_size
                enriched_data["_extraction_source"] = "user_comment"

        # Handle fiber conflict resolution (catalog fiber is preserved from match phase)
        if user_fiber is not None:
            if catalog_fiber is not None:
                if catalog_fiber.lower() == user_fiber.lower():
                    # Values match - use user value, mark as confirmed
                    enriched_data["fiber"] = user_fiber
                    enriched_data["_fiber_extraction_source"] = "user_confirmed_catalog"
                else:
                    # Values conflict - user takes precedence, mark conflict
                    enriched_data["fiber"] = user_fiber
                    enriched_data["_fiber_extraction_source"] = "user_override_catalog"
                    enriched_data["_catalog_fiber"] = catalog_fiber
            else:
                # Only user has fiber - use it
                enriched_data["fiber"] = user_fiber
                enriched_data["_fiber_extraction_source"] = "user_comment"

        return enriched_data

    def _extract_knot_size(self, text: str) -> Optional[float]:
        """Extract knot size in mm from text."""
        if not text:
            return None

        # Look for standalone number with 'mm' (highest priority)
        match = re.search(r"\b(\d+(?:\.\d+)?)\s*mm?\b", text, re.IGNORECASE)
        if match:
            return float(match.group(1))

        # Look for patterns like '27x50' or '27.5x50' (take first number)
        match = re.search(r"(\d+(?:\.\d+)?)\s*[x×]\s*\d+(?:\.\d+)?", text)
        if match:
            return float(match.group(1))

        # Fallback: any number in the text (but be more conservative)
        # Only match numbers that could reasonably be knot sizes (20-35mm range)
        # Include decimals in the range
        match = re.search(r"\b(2[0-9](?:\.\d+)?|3[0-5](?:\.\d+)?)\b", text)
        if match:
            return float(match.group(1))

        return None

    def _extract_fiber(self, text: str) -> Optional[str]:
        """Extract fiber type from text."""
        if not text:
            return None

        # Order matters - check more specific patterns first
        fiber_patterns = [
            ("Mixed Badger/Boar", r"(mix|mixed|mi[sx]tura?|badg.*boar|boar.*badg|hybrid|fusion)"),
            (
                "Synthetic",
                (
                    r"(acrylic|timber|tux|mew|silk|synt|synbad|2bed|captain|cashmere|"
                    r"faux.*horse|black.*(magic|wolf)|g4|boss|st-?(1|2)|trafalgar\s*t[23]|"
                    r"\bt[23]\b|kong|hi\s*brush|ak47|g5[abc]|stf|quartermoon|fibre|"
                    r"\bmig\b|synthetic badger|motherlode)"
                ),
            ),
            (
                "Badger",
                (
                    r"(hmw|high.*mo|(2|3|two|three)[\s-]*band|shd|badger|silvertip|super|"
                    r"gelo|gelous|gelousy|finest|best|ultralux|fanchurian|\blod\b)"
                ),
            ),
            ("Boar", r"\b(boar|shoat)\b"),
            ("Horse", r"\bhorse(hair)?\b"),
        ]

        for fiber, pattern in fiber_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return fiber

        return None
