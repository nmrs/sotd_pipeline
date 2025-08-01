from typing import Optional

from sotd.enrich.enricher import BaseEnricher
from sotd.match.brush_matching_strategies.utils.fiber_utils import match_fiber
from sotd.match.brush_matching_strategies.utils.pattern_utils import extract_knot_size


class BrushEnricher(BaseEnricher):
    """Enricher for brush specifications from user comments."""

    @property
    def target_field(self) -> str:
        return "brush"

    def _extract_knot_size(self, text: str) -> Optional[float]:
        """Extract knot size from text using pattern utils."""
        return extract_knot_size(text)

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
        if field_data is None or not isinstance(field_data, dict):
            return None

        # All extraction is from the brush_extracted field (passed as original_comment)
        brush_extracted = original_comment
        if not brush_extracted:
            return None

        # Extract user data from brush_extracted
        user_knot_size = extract_knot_size(brush_extracted)
        user_fiber = match_fiber(brush_extracted)

        # Get catalog data from new format (knot section) or legacy format (top-level)
        knot_section = field_data.get("knot", {})
        catalog_knot_size = (
            knot_section.get("knot_size_mm") if knot_section else field_data.get("knot_size_mm")
        )
        catalog_fiber = knot_section.get("fiber") if knot_section else field_data.get("fiber")

        # Prepare user data dictionary
        user_data = {}
        if user_knot_size is not None:
            user_data["knot_size_mm"] = user_knot_size
        if user_fiber is not None:
            user_data["fiber"] = user_fiber

        # Prepare catalog data dictionary
        catalog_data = {}
        if catalog_knot_size is not None:
            catalog_data["knot_size_mm"] = catalog_knot_size
        if catalog_fiber is not None:
            catalog_data["fiber"] = catalog_fiber

        # Use BaseEnricher's source tracking method
        enriched_data = self._create_enriched_data(user_data, catalog_data)

        # Handle _fiber_extraction_source separately for backward compatibility
        if user_fiber is not None or catalog_fiber is not None:
            fiber_user_data = {"fiber": user_fiber} if user_fiber is not None else {}
            fiber_catalog_data = {"fiber": catalog_fiber} if catalog_fiber is not None else {}
            fiber_enriched = self._create_enriched_data(fiber_user_data, fiber_catalog_data)
            enriched_data["_fiber_extraction_source"] = fiber_enriched["_extraction_source"]

        # Add custom knot detection logic
        has_custom_knot = False
        if user_fiber is not None and catalog_fiber is not None:
            if user_fiber.lower() != catalog_fiber.lower():
                has_custom_knot = True
        if user_knot_size is not None and catalog_knot_size is not None:
            if abs(user_knot_size - catalog_knot_size) >= 0.1:  # Allow small tolerance
                has_custom_knot = True

        # Add custom knot metadata if detected
        if has_custom_knot:
            enriched_data["_custom_knot"] = True
            enriched_data["_custom_knot_reason"] = []
            if (
                user_fiber is not None
                and catalog_fiber is not None
                and user_fiber.lower() != catalog_fiber.lower()
            ):
                enriched_data["_custom_knot_reason"].append(
                    f"fiber_mismatch:{catalog_fiber}->{user_fiber}"
                )
            if (
                user_knot_size is not None
                and catalog_knot_size is not None
                and abs(user_knot_size - catalog_knot_size) >= 0.1
            ):
                enriched_data["_custom_knot_reason"].append(
                    f"size_mismatch:{catalog_knot_size}->{user_knot_size}"
                )

        # Add catalog conflict tracking for backward compatibility
        if user_knot_size is not None and catalog_knot_size is not None:
            if abs(user_knot_size - catalog_knot_size) >= 0.1:
                enriched_data["_catalog_knot_size_mm"] = catalog_knot_size

        if user_fiber is not None and catalog_fiber is not None:
            if user_fiber.lower() != catalog_fiber.lower():
                enriched_data["_catalog_fiber"] = catalog_fiber

        return enriched_data
