import re
from typing import Optional

from sotd.match.brush_matching_strategies.utils.fiber_utils import _FIBER_PATTERNS, match_fiber


class EnhancedBrushSplitter:
    """Enhanced brush splitting functionality extracted from BrushMatcher."""

    def __init__(self, handle_matcher=None, strategies=None):
        self.handle_matcher = handle_matcher
        self.strategies = strategies or []

    def split_handle_and_knot(
        self, text: str
    ) -> tuple[Optional[str], Optional[str], Optional[str]]:
        """Split handle and knot using various delimiters and fiber detection."""
        if not text:
            return None, None, None

        # Try delimiter-based splitting first (most reliable)
        handle, knot, delimiter_type = self._split_by_delimiters(text)
        if handle and knot:
            return handle, knot, delimiter_type

        # Try fiber detection as a hint (next most reliable)
        handle, knot, delimiter_type = self._split_by_fiber_hint(text)
        if handle and knot:
            return handle, knot, delimiter_type

        # Try brand-context splitting as last resort (most speculative)
        handle, knot, delimiter_type = self._split_by_brand_context(text)
        if handle and knot:
            return handle, knot, delimiter_type

        # If no splitting is possible, try to match against known brushes/knots/handles
        # Try matching as a complete brush first, then try splitting, then individual components
        if self._is_known_brush(text):
            # It's a known complete brush, don't split it
            return None, None, None
        else:
            # Try to split and see if we can match the parts
            handle, knot, delimiter_type = self._split_by_delimiters(text)
            if handle and knot:
                # Splitting succeeded - return the split components regardless of match status
                # The brush matcher will handle matching each component separately
                return handle, knot, delimiter_type

            # Try other splitting methods
            handle, knot, delimiter_type = self._split_by_fiber_hint(text)
            if handle and knot:
                return handle, knot, delimiter_type

            handle, knot, delimiter_type = self._split_by_brand_context(text)
            if handle and knot:
                return handle, knot, delimiter_type

            # If splitting fails, try to match as individual components
            if self._is_known_knot(text):
                # It's a known knot, treat as unsplittable knot
                return None, text, "unsplittable_knot"
            elif self._is_known_handle(text):
                # It's a known handle, treat as unsplittable handle
                return text, None, "unsplittable_handle"
            else:
                # Unknown string that can't be split - treat as knot (user preference)
                return None, text, "unsplittable"

    def _split_by_delimiters(self, text: str) -> tuple[Optional[str], Optional[str], Optional[str]]:
        """Split text using known delimiters and return parts and delimiter type.

        - `/` is treated as a high-reliability delimiter regardless of spaces
          (e.g., 'A/B', 'A / B', 'A/ B', 'A /B').
        - Always check for ' w/ ' and ' with ' delimiters before '/' to avoid
          mis-splitting 'w/' as '/'.
        - Other delimiters retain their original logic.
        """
        # High-reliability delimiters (always trigger splitting with simple logic)
        high_reliability_delimiters = [" w/ ", " with "]
        # Handle-primary delimiters (first part is handle)
        handle_primary_delimiters = [" in "]
        # Medium-reliability delimiters (need smart analysis)
        medium_reliability_delimiters = [" + ", " - "]

        # Always check for ' w/ ' and ' with ' first to avoid misinterpreting 'w/' as '/'
        for delimiter in high_reliability_delimiters:
            if delimiter in text:
                return self._split_by_delimiter_simple(text, delimiter, "high_reliability")

        # Special handling for `/` as high-reliability delimiter (any spaces, not part of 'w/')
        slash_match = re.search(r"(.+?)(?<!w)\s*/\s*(.+)", text)
        if slash_match:
            part1 = slash_match.group(1).strip()
            part2 = slash_match.group(2).strip()
            if part1 and part2:
                # Score both parts to determine which is handle vs knot
                part1_handle_score = self._score_as_handle(part1)
                part2_handle_score = self._score_as_handle(part2)
                if part1_handle_score > part2_handle_score:
                    return part1, part2, "high_reliability"
                else:
                    return part2, part1, "high_reliability"

        # Check handle-primary delimiters (first part is handle)
        for delimiter in handle_primary_delimiters:
            if delimiter in text:
                return self._split_by_delimiter_simple(text, delimiter, "handle_primary")

        # Check medium-reliability delimiters (use smart analysis)
        for delimiter in medium_reliability_delimiters:
            if delimiter in text:
                return self._split_by_delimiter_smart(text, delimiter, "smart_analysis")

        return None, None, None

    def _split_by_delimiter_positional(
        self, text: str, delimiter: str, delimiter_type: str
    ) -> tuple[Optional[str], Optional[str], Optional[str]]:
        """Positional splitting for 'w/' and 'with' delimiters.

        Respects positional order: first part = handle, second part = knot.
        """
        parts = text.split(delimiter, 1)
        if len(parts) == 2:
            handle = parts[0].strip()
            knot = parts[1].strip()
            if handle and knot:
                return handle, knot, delimiter_type
        return None, None, None

    def _split_by_delimiter_simple(
        self, text: str, delimiter: str, delimiter_type: str
    ) -> tuple[Optional[str], Optional[str], Optional[str]]:
        """Content-based splitting for high-reliability delimiters.

        Analyzes both sides to determine which is handle vs knot.
        """
        parts = text.split(delimiter, 1)
        if len(parts) == 2:
            part1 = parts[0].strip()
            part2 = parts[1].strip()
            if part1 and part2:
                # Score both parts to determine which is handle vs knot
                part1_handle_score = self._score_as_handle(part1)
                part2_handle_score = self._score_as_handle(part2)

                if part1_handle_score > part2_handle_score:
                    return part1, part2, delimiter_type
                else:
                    return part2, part1, delimiter_type
        return None, None, None

    def _split_by_delimiter_smart(
        self, text: str, delimiter: str, delimiter_type: str
    ) -> tuple[Optional[str], Optional[str], Optional[str]]:
        """Smart splitting for ambiguous delimiters like 'w/' by analyzing content."""
        # Find all occurrences of the delimiter
        delimiter_positions = []
        start = 0
        while True:
            pos = text.find(delimiter, start)
            if pos == -1:
                break
            delimiter_positions.append(pos)
            start = pos + len(delimiter)

        if not delimiter_positions:
            return None, None, None

        # Try each split point and score the results
        best_split = None
        best_score_diff = -float("inf")

        for pos in delimiter_positions:
            part1 = text[:pos].strip()
            part2 = text[pos + len(delimiter) :].strip()

            if not part1 or not part2:
                continue

            # Score each part as handle
            part1_handle_score = self._score_as_handle(part1)
            part2_handle_score = self._score_as_handle(part2)

            # Calculate the difference between the better handle score and the worse one
            # This helps us find the split that creates the most distinct handle/knot separation
            if part1_handle_score > part2_handle_score:
                score_diff = part1_handle_score - part2_handle_score
                potential_split = (part1, part2, delimiter_type)
            else:
                score_diff = part2_handle_score - part1_handle_score
                potential_split = (part2, part1, delimiter_type)

            # Choose the split with the largest score difference
            if score_diff > best_score_diff:
                best_score_diff = score_diff
                best_split = potential_split

        return best_split if best_split else (None, None, None)

    def _split_by_delimiter(
        self, text: str, delimiter: str, delimiter_type: str, handle_first: bool
    ) -> tuple[Optional[str], Optional[str], Optional[str]]:
        """Basic splitting for delimiters with fixed semantic order."""
        parts = text.split(delimiter, 1)
        if len(parts) == 2:
            if handle_first:
                handle = parts[0].strip()
                knot = parts[1].strip()
            else:
                knot = parts[0].strip()
                handle = parts[1].strip()
            if handle and knot:
                return handle, knot, delimiter_type
        return None, None, None

    def _score_as_handle(self, text: str) -> int:
        """Score how likely a text is to be a handle (higher = more likely handle)."""
        score = 0
        text_lower = text.lower()

        # Strong handle indicators
        if "handle" in text_lower:
            score += 10

        # Test against actual handle patterns from handles.yaml
        if self.handle_matcher:
            handle_match = self.handle_matcher.match_handle_maker(text)
            if handle_match:
                # Found a handle pattern match - strong indicator this is a handle
                section = handle_match.get("_matched_by_section", "")
                if section == "artisan_handles":
                    score += 12  # Artisan handles are most specific
                elif section == "manufacturer_handles":
                    score += 10
                elif section == "other_handles":
                    score += 8
                else:
                    score += 6

        # Test against brush strategies to see if this looks like a knot
        knot_strategy_matches = 0
        for strategy in self.strategies:
            try:
                result = strategy.match(text)
                if result and (
                    (isinstance(result, dict) and result.get("matched"))
                    or (isinstance(result, dict) and result.get("brand"))
                ):
                    knot_strategy_matches += 1
            except (AttributeError, KeyError, TypeError, re.error):
                # Some strategies might fail on certain inputs due to regex errors,
                # missing attributes, or type issues - skip and continue
                continue

        # If multiple strategies match this as a knot, reduce handle score
        if knot_strategy_matches >= 2:
            score -= 8
        elif knot_strategy_matches == 1:
            score -= 4

        # Handle-related terms
        handle_terms = ["stock", "custom", "artisan", "turned", "wood", "resin", "zebra", "burl"]
        for term in handle_terms:
            if term in text_lower:
                score += 2

        # Knot indicators (negative score for handle likelihood)
        knot_terms = ["syn", "mm", "knot"]
        for term in knot_terms:
            if term in text_lower:
                score -= 5

        # Fiber type patterns (strong knot indicators) - use fiber_utils
        fiber_type = match_fiber(text)
        if fiber_type:
            score -= 8

        # Size patterns (knot indicators)
        if re.search(r"\d{2}\s*mm", text_lower):
            score -= 6

        # Chisel & Hound versioning patterns (knot indicators)
        if re.search(r"\bv\d{2}\b", text_lower):
            score -= 6

        return score

    def _split_by_fiber_hint(self, text: str) -> tuple[Optional[str], Optional[str], Optional[str]]:
        """Split text using fiber words as hints for knot identification."""
        all_fiber_patterns = [pattern.strip("()") for pattern in _FIBER_PATTERNS.values()]
        combined_fiber_pattern = "|".join(all_fiber_patterns)
        fiber_matches = list(re.finditer(f"({combined_fiber_pattern})", text, re.IGNORECASE))
        if not fiber_matches:
            return None, None, None
        last_fiber_match = fiber_matches[-1]
        fiber_start = last_fiber_match.start()
        fiber_end = last_fiber_match.end()
        words = text.split()
        fiber_word_indices = self._find_fiber_word_indices(words, fiber_start, fiber_end)
        if not fiber_word_indices:
            return None, None, None
        first_fiber_word = fiber_word_indices[0]
        # Try each fiber-based splitting strategy in order
        handle, knot = self._fiber_handle_maker_split(words, first_fiber_word, text)
        if handle and knot:
            return handle, knot, "fiber_hint"
        handle, knot = self._fiber_knot_maker_split(text, fiber_start)
        if handle and knot:
            return handle, knot, "fiber_hint"
        handle, knot = self._fiber_word_split(words, first_fiber_word)
        if handle and knot:
            return handle, knot, "fiber_hint"
        return None, None, None

    def _find_fiber_word_indices(
        self, words: list[str], fiber_start: int, fiber_end: int
    ) -> list[int]:
        """Find indices of words that contain fiber information."""
        fiber_word_indices = []
        current_pos = 0
        for i, word in enumerate(words):
            word_start = current_pos
            word_end = current_pos + len(word)
            if (word_start <= fiber_start < word_end) or (word_start < fiber_end <= word_end):
                fiber_word_indices.append(i)
            current_pos = word_end + 1  # +1 for space
        return fiber_word_indices

    def _fiber_handle_maker_split(
        self, words: list[str], first_fiber_word: int, text: str
    ) -> tuple[Optional[str], Optional[str]]:
        """Split using handle maker patterns found before fiber words."""
        handle_maker_brands = [
            "Chisel & Hound",
            "Chisel and Hound",
            "Wolf Whiskers",
            "Elite",
            "Dogwood",
            "Declaration Grooming",
            "Grizzly Bay",
            "Paladin",
        ]
        text_before_fiber = " ".join(words[:first_fiber_word])
        for handle_maker in handle_maker_brands:
            if re.search(re.escape(handle_maker), text_before_fiber, re.IGNORECASE):
                handle_pattern = re.escape(handle_maker)
                match = re.search(handle_pattern, text, re.IGNORECASE)
                if match:
                    split_point = match.end()
                    handle_part = text[:split_point].strip()
                    knot_part = text[split_point:].strip()
                    if handle_part and knot_part:
                        return handle_part, knot_part
        return None, None

    def _fiber_knot_maker_split(
        self, text: str, fiber_start: int
    ) -> tuple[Optional[str], Optional[str]]:
        """Split using knot maker patterns found near fiber words."""
        knot_maker_patterns = [
            r"\b(Maggard|Oumo|Declaration|Zenith|Omega|Semogue|Simpson|Shavemac)\b"
        ]
        for pattern in knot_maker_patterns:
            matches = list(re.finditer(pattern, text, re.IGNORECASE))
            for match in matches:
                if abs(match.start() - fiber_start) <= 50:
                    split_point = match.start()
                    handle_part = text[:split_point].strip()
                    knot_part = text[split_point:].strip()
                    if handle_part and knot_part and len(handle_part) > 3:
                        return handle_part, knot_part
        return None, None

    def _fiber_word_split(
        self, words: list[str], first_fiber_word: int
    ) -> tuple[Optional[str], Optional[str]]:
        """Split at the fiber word boundary."""
        if first_fiber_word > 0 and len(words) > 2:
            handle_part = " ".join(words[:first_fiber_word])
            knot_part = " ".join(words[first_fiber_word:])
            if handle_part and knot_part:
                return handle_part, knot_part
        return None, None

    def _split_by_brand_context(
        self, text: str
    ) -> tuple[Optional[str], Optional[str], Optional[str]]:
        """Split text by recognizing brand context patterns when clear handle/knot makers
        are present.

        This handles cases like 'CH Circus B13' or 'B13 CH Circus' where:
        - B13 is a Declaration Grooming knot pattern
        - CH/Circus indicates Chisel & Hound handle
        - No explicit delimiters are present
        """
        # Look for Declaration Grooming knot patterns (B2, B3, B13, etc.)
        # Be conservative - only B followed by 1-2 digits, optionally followed by a single letter
        dg_knot_pattern = r"\b(B\d{1,2}[A-Z]?)\b"
        dg_matches = list(re.finditer(dg_knot_pattern, text, re.IGNORECASE))

        # Look for Chisel & Hound handle indicators
        ch_handle_patterns = [
            r"\bCH\b",  # "CH" as standalone word
            r"\bC&H\b",  # "C&H" abbreviation
            r"\bChisel\b",  # "Chisel" word
            r"\bCircus\b",  # "Circus" (known CH handle pattern)
            r"\bHound\b",  # "Hound" word
        ]

        # Find all CH pattern matches
        ch_matches = []
        for pattern in ch_handle_patterns:
            ch_matches.extend(re.finditer(pattern, text, re.IGNORECASE))

        # Only proceed if we found both DG knot and CH handle indicators
        # This is specifically for Chisel & Hound handles with Declaration Grooming knots
        if not dg_matches or not ch_matches:
            return None, None, None

        # Additional safety: Don't split if this appears to be a single Declaration Grooming brush
        # Check if "Declaration" appears in the text (indicating it might be "Declaration B3" not
        # "CH ... B3")
        declaration_indicators = [r"\bdeclaration\b", r"\bdg\b"]
        has_declaration_context = any(
            re.search(pattern, text, re.IGNORECASE) for pattern in declaration_indicators
        )

        # If we have Declaration context, only split if we also have clear CH context
        if has_declaration_context:
            # This looks like "Declaration B3" - treat as single brush, not handle/knot combo
            return None, None, None

        # Additional safety check: make sure this isn't already covered by delimiter splitting
        # If we have common delimiters, let the delimiter logic handle it
        common_delimiters = [" w/ ", " with ", " / ", "/", " - ", " in "]
        if any(delimiter in text for delimiter in common_delimiters):
            return None, None, None

        # Take the first DG knot match
        dg_match = dg_matches[0]
        knot_text = dg_match.group(1)  # Just the B13 part

        # Build handle text by removing the knot part and cleaning up
        handle_parts = []

        # Add text before the knot
        before_knot = text[: dg_match.start()].strip()
        if before_knot:
            handle_parts.append(before_knot)

        # Add text after the knot
        after_knot = text[dg_match.end() :].strip()
        if after_knot:
            handle_parts.append(after_knot)

        if not handle_parts:
            return None, None, None

        handle_text = " ".join(handle_parts).strip()

        # Validate that the handle part actually contains CH indicators
        has_ch_in_handle = any(
            re.search(pattern, handle_text, re.IGNORECASE) for pattern in ch_handle_patterns
        )

        if not has_ch_in_handle:
            return None, None, None

        # Additional validation: make sure we're not breaking up a legitimate single brush name
        # If the knot text is very short and the handle text is also very short, skip
        if len(knot_text) < 2 or len(handle_text.replace(" ", "")) < 2:
            return None, None, None

        return handle_text, knot_text, "brand_context"

    def _is_known_knot(self, text: str) -> bool:
        """Check if the text matches a known knot in the knots catalog."""
        if not self.strategies:
            return False

        # Try to match against knot strategies specifically
        for strategy in self.strategies:
            try:
                result = strategy.match(text)
                if result and (
                    (isinstance(result, dict) and result.get("matched"))
                    or (isinstance(result, dict) and result.get("brand"))
                ):
                    # Check if this strategy is specifically for knots
                    strategy_name = strategy.__class__.__name__.lower()
                    if "knot" in strategy_name:
                        # Additional check: make sure this isn't also a known brush
                        # If it's a known brush, it should be treated as a complete brush,
                        # not a knot
                        if not self._is_known_brush(text):
                            return True
            except (AttributeError, KeyError, TypeError, re.error):
                # Some strategies might fail on certain inputs - skip and continue
                continue
        return False

    def _is_known_handle(self, text: str) -> bool:
        """Check if the text matches a known handle in the handles catalog."""
        if not self.handle_matcher:
            return False

        try:
            handle_match = self.handle_matcher.match_handle_maker(text)
            return handle_match is not None
        except (AttributeError, KeyError, TypeError, re.error):
            return False

    def _is_known_brush(self, text: str) -> bool:
        """Check if the text matches a known brush in the catalog."""
        if not self.strategies:
            return False

        # Try to match against all strategies
        for strategy in self.strategies:
            try:
                result = strategy.match(text)
                if result and (
                    (isinstance(result, dict) and result.get("matched"))
                    or (isinstance(result, dict) and result.get("brand"))
                    or (hasattr(result, "matched") and getattr(result, "matched", None))
                ):
                    return True
            except (AttributeError, KeyError, TypeError, re.error):
                # Some strategies might fail on certain inputs - skip and continue
                continue
        return False
