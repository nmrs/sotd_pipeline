import re
from typing import Optional

from sotd.match.brush_matching_strategies.utils.fiber_utils import _FIBER_PATTERNS


class BrushSplitter:
    """Handles splitting of brush text into handle and knot components."""

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
        return self._split_by_brand_context(text)

    def _split_by_delimiters(self, text: str) -> tuple[Optional[str], Optional[str], Optional[str]]:
        """Split text using known delimiters and return parts and delimiter type."""
        handle_primary_delimiters = [" in "]  # Handle takes precedence
        other_delimiters = [" w/ ", " with ", " / ", "/", " - "]  # All use smart analysis

        for delimiter in handle_primary_delimiters:
            if delimiter in text:
                return self._split_by_delimiter(
                    text, delimiter, "handle_primary", handle_first=True
                )
        for delimiter in other_delimiters:
            if delimiter in text:
                return self._split_by_delimiter_smart(text, delimiter, "smart_analysis")
        return None, None, None

    def _split_by_delimiter_smart(
        self, text: str, delimiter: str, delimiter_type: str
    ) -> tuple[Optional[str], Optional[str], Optional[str]]:
        """Smart splitting for ambiguous delimiters like 'w/' by analyzing content."""
        parts = text.split(delimiter, 1)
        if len(parts) != 2:
            return None, None, None

        part1 = parts[0].strip()
        part2 = parts[1].strip()

        if not part1 or not part2:
            return None, None, None

        # Analyze which part is more likely to be the handle
        part1_handle_score = self._score_as_handle(part1)
        part2_handle_score = self._score_as_handle(part2)

        if part1_handle_score > part2_handle_score:
            # Part 1 is more likely the handle
            return part1, part2, delimiter_type
        else:
            # Part 2 is more likely the handle (or they're equal, default to part 2)
            return part2, part1, delimiter_type

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
        knot_terms = ["badger", "boar", "synthetic", "syn", "mm", "knot"]
        for term in knot_terms:
            if term in text_lower:
                score -= 5

        # Fiber type patterns (strong knot indicators)
        if any(fiber in text_lower for fiber in ["badger", "boar", "synthetic"]):
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
        """Split based on known handle maker brands before fiber words."""
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
        """Split based on knot maker brands near fiber words."""
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
        """Split at the first fiber word position."""
        if first_fiber_word > 0 and len(words) > 2:
            handle_part = " ".join(words[:first_fiber_word])
            knot_part = " ".join(words[first_fiber_word:])
            if handle_part and knot_part:
                return handle_part, knot_part
        return None, None

    def should_prioritize_knot(self, text: str) -> bool:
        """Determine if knot maker should take precedence based on delimiter semantics."""
        handle_primary_delimiters = [" in "]  # Handle takes precedence

        # Check for handle-primary delimiters
        for delimiter in handle_primary_delimiters:
            if delimiter in text:
                return False

        # For all other delimiters, let the smart analysis determine priority
        # by checking if we successfully split and which part scored higher as handle
        handle, knot, delimiter_type = self.split_handle_and_knot(text)
        if handle and knot and delimiter_type == "smart_analysis":
            # If smart analysis was used, trust its determination
            # The smart analysis already put the handle first and knot second
            return True  # Process knot part first since it's usually more distinctive

        # Default behavior when no delimiters found
        return True  # Default to knot priority for backward compatibility

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
