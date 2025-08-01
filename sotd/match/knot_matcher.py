from typing import Optional

from sotd.match.types import MatchResult


class KnotMatcher:
    """Knot matching functionality extracted from BrushMatcher."""

    def __init__(self, strategies: list):
        self.strategies = strategies
        # Calculate section priorities based on strategy order
        self.section_priorities = self._calculate_section_priorities()

    def _calculate_section_priorities(self) -> dict:
        """Calculate priority for each strategy based on order (first = highest priority)."""
        priorities = {}
        for i, strategy in enumerate(self.strategies, 1):
            strategy_name = strategy.__class__.__name__
            if "KnownKnot" in strategy_name:
                priorities[strategy] = ("known_knots", i)
            elif "OtherKnot" in strategy_name:
                priorities[strategy] = ("other_knots", i)
            elif "FiberFallback" in strategy_name:
                priorities[strategy] = ("fiber_fallback", i)
            elif "KnotSizeFallback" in strategy_name:
                priorities[strategy] = ("knot_size_fallback", i)
            else:
                priorities[strategy] = ("unknown", i)
        return priorities

    def match(self, value: str) -> Optional["MatchResult"]:
        """
        Match knot patterns in the given text using all available strategies.

        Args:
            value: Text to match against

        Returns:
            MatchResult if a match is found, None otherwise
        """
        if not value or not isinstance(value, str):
            return None

        for strategy in self.strategies:
            try:
                result = strategy.match(value)
                if result and result.matched:
                    # Add section/priority information to the result
                    section, priority = self.section_priorities.get(strategy, ("unknown", 999))
                    return MatchResult(
                        original=result.original,
                        matched=result.matched,
                        match_type=result.match_type,
                        pattern=result.pattern,
                        section=section,
                        priority=priority,
                    )
            except Exception:
                # Continue to next strategy if one fails
                continue

        return None

    def should_prioritize_knot(self, text: str, split_handle_and_knot_func) -> bool:
        """Determine if knot maker should take precedence based on delimiter semantics."""
        handle_primary_delimiters = [" in "]  # Handle takes precedence

        # Check for handle-primary delimiters
        for delimiter in handle_primary_delimiters:
            if delimiter in text:
                return False

        # For all other delimiters, let the smart analysis determine priority
        # by checking if we successfully split and which part scored higher as handle
        handle, knot, delimiter_type = split_handle_and_knot_func(text)
        if handle and knot and delimiter_type == "smart_analysis":
            # If smart analysis was used, trust its determination
            # The smart analysis already put the handle first and knot second
            return True  # Process knot part first since it's usually more distinctive

        # Default behavior when no delimiters found
        return True  # Default to knot priority for backward compatibility

    def is_known_handle_maker(self, brand: str) -> bool:
        """Check if a brand is primarily known as a handle maker."""
        # These brands are primarily handle makers
        handle_maker_brands = {
            "Chisel & Hound",
            "Wolf Whiskers",
            "Elite",
            "Dogwood",
            "Declaration Grooming",
            "Grizzly Bay",
            "Paladin",
        }
        return brand in handle_maker_brands

    def try_knot_maker_fallback(self, value: str, handle_result: dict) -> dict | None:
        """Try to find a knot maker when full-text matching found a handle maker."""
        if not self.is_known_handle_maker(handle_result.get("brand", "")):
            return None

        # Try to find knot maker brands in the text
        for strategy in self.strategies:
            # Skip the strategy that already matched the handle
            if strategy.__class__.__name__ == handle_result.get("_matched_by_strategy"):
                continue

            result = strategy.match(value)
            if result.matched:
                knot_match = result.matched.copy()
                # If we found a different brand, prioritize it as the knot maker
                if knot_match.get("brand") != handle_result.get("brand"):
                    knot_match["_matched_by_strategy"] = strategy.__class__.__name__
                    knot_match["_pattern_used"] = result.pattern
                    knot_match["_matched_from"] = "knot_fallback"
                    knot_match["handle_maker"] = handle_result.get("brand")
                    return knot_match
        return None

    def match_knot_priority(
        self,
        value: str,
        handle: Optional[str],
        knot: Optional[str],
        extract_match_dict_func,
        post_process_match_func,
    ) -> Optional["MatchResult"]:
        """Match brush with knot priority (when we have a clear handle/knot split)."""
        for strategy in self.strategies:
            result = strategy.match(knot)
            # All strategies now return MatchResult objects
            if result.matched:
                m = extract_match_dict_func(result, strategy, "knot_part", handle, knot)
                if m:
                    from sotd.match.types import create_match_result

                    match_result = create_match_result(
                        original=value,
                        matched=m,
                        match_type=result.match_type or "exact",
                        pattern=result.pattern or "unknown",
                    )
                    return post_process_match_func(match_result, value)
        return None

    def match_handle_priority(
        self,
        value: str,
        handle: Optional[str],
        knot: Optional[str],
        extract_match_dict_func,
        post_process_match_func,
    ) -> Optional["MatchResult"]:
        """Match brush with handle priority (when we have a clear handle/knot split)."""
        for strategy in self.strategies:
            result = strategy.match(handle)
            # All strategies now return MatchResult objects
            if result.matched:
                m = extract_match_dict_func(result, strategy, "handle_part", handle, knot)
                if m:
                    from sotd.match.types import create_match_result

                    match_result = create_match_result(
                        original=value,
                        matched=m,
                        match_type=result.match_type or "exact",
                        pattern=result.pattern or "unknown",
                    )
                    return post_process_match_func(match_result, value)
        return None
