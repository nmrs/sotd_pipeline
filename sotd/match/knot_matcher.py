from typing import Optional


class KnotMatcher:
    """Handles matching of brush knot makers from text input."""

    def __init__(self, catalog_data: dict):
        self.catalog_data = catalog_data

    def match_knot_priority(
        self, value: str, handle: Optional[str], knot: Optional[str]
    ) -> Optional[dict]:
        """
        Match brush with knot priority (when we have a clear handle/knot split).
        This prioritizes finding the knot maker over the handle maker.
        """
        if not knot:
            return None

        # Try to match the knot part using all strategies
        for strategy in self._get_strategies():
            result = strategy.match(knot)
            if result:
                # Extract the match result
                match_dict = self._extract_match_dict(
                    result, strategy, matched_from="knot_priority", handle=handle, knot=knot
                )

                # Set handle_maker if we have a handle and it's not already set
                if handle and not match_dict.get("handle_maker"):
                    match_dict["handle_maker"] = handle

                return match_dict

        return None

    def try_knot_maker_fallback(self, value: str, handle_result: dict) -> dict | None:
        """
        Try to find a knot maker when we have a handle match but no knot match.
        This is a fallback strategy for cases where the handle is clear but the knot is ambiguous.
        """
        # Extract the handle maker from the handle result
        handle_maker = handle_result.get("handle_maker")
        if not handle_maker:
            return None

        # Look for knot makers that are commonly paired with this handle maker
        # This is a simplified approach - in practice, you might have a mapping
        # of common handle/knot combinations

        # For now, we'll try to match the full text again, but with lower confidence
        for strategy in self._get_strategies():
            result = strategy.match(value)
            if result:
                match_dict = self._extract_match_dict(
                    result, strategy, matched_from="knot_fallback"
                )

                # If we found a different brand than the handle maker, it might be the knot maker
                brand = match_dict.get("brand", "").strip()
                if brand and brand.lower() != handle_maker.lower():
                    # This could be the knot maker
                    match_dict["handle_maker"] = handle_maker
                    match_dict["_confidence"] = "low"  # Mark as low confidence
                    return match_dict

        return None

    def _get_strategies(self):
        """Get all available matching strategies."""
        # This would be injected from the main BrushMatcher
        # For now, return an empty list - this will be set up when integrating
        return []

    def _extract_match_dict(
        self,
        result,
        strategy,
        matched_from: Optional[str] = None,
        handle: Optional[str] = None,
        knot: Optional[str] = None,
    ):
        """Extract match dictionary from strategy result."""
        if hasattr(result, "to_dict"):
            match_dict = result.to_dict()
        else:
            match_dict = dict(result)

        # Add metadata
        match_dict["_strategy"] = strategy.__class__.__name__
        if matched_from:
            match_dict["_matched_from"] = matched_from
        if handle:
            match_dict["_handle_part"] = handle
        if knot:
            match_dict["_knot_part"] = knot

        return match_dict
