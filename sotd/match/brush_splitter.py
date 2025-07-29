import re
from typing import Optional

from sotd.match.brush_matching_strategies.utils.fiber_utils import _FIBER_PATTERNS, match_fiber
from sotd.match.brush_matching_strategies.utils.knot_size_utils import parse_knot_size


class BrushSplitter:
    """Brush splitting functionality extracted from BrushMatcher."""

    def __init__(self, handle_matcher=None, strategies=None):
        self.handle_matcher = handle_matcher
        self.strategies = strategies or []

    def split_handle_and_knot(
        self, text: str
    ) -> tuple[Optional[str], Optional[str], Optional[str]]:
        """Split handle and knot using various delimiters and fiber detection."""
        if not text:
            return None, None, None

        # Step 1: Try delimiter-based splitting (highest priority)
        result = self._try_delimiter_splitting(text)
        if result[0] and result[1]:
            return result

        # Step 2: Check if it's a known brush (medium priority)
        result = self._try_known_brush_check(text)
        if result[0] is None and result[1] is None:
            return result  # Known brush - don't split

        # Step 3: Try fiber hint splitting (lower priority)
        result = self._try_fiber_hint_splitting(text)
        if result[0] and result[1]:
            return result

        # Step 4: Final fallback - try all splitting methods again
        result = self._try_fallback_splitting(text)
        return result

    def _try_delimiter_splitting(
        self, text: str
    ) -> tuple[Optional[str], Optional[str], Optional[str]]:
        """Step 1: Try delimiter-based splitting (highest priority)."""
        return self._split_by_delimiters(text)

    def _try_known_brush_check(
        self, text: str
    ) -> tuple[Optional[str], Optional[str], Optional[str]]:
        """Step 2: Check if it's a known brush (medium priority)."""
        if self._is_known_brush(text):
            # It's a known complete brush, don't split it
            return None, None, None
        else:
            # Not a known brush, continue with other methods
            return None, None, "not_known_brush"

    def _try_fiber_hint_splitting(
        self, text: str
    ) -> tuple[Optional[str], Optional[str], Optional[str]]:
        """Step 3: Try fiber hint splitting (lower priority)."""
        return self._split_by_fiber_hint(text)

    def _try_fallback_splitting(
        self, text: str
    ) -> tuple[Optional[str], Optional[str], Optional[str]]:
        """Step 4: Final fallback - try all splitting methods again."""
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

        # If no splitting methods worked, return None to indicate no splitting
        return None, None, None

    def _split_by_delimiters(self, text: str) -> tuple[Optional[str], Optional[str], Optional[str]]:
        """Split text using known delimiters and return parts and delimiter type.

        - `/` is treated as a high-reliability delimiter regardless of spaces
          (e.g., 'A/B', 'A / B', 'A/ B', 'A /B').
        - Always check for ' w/ ' and ' with ' delimiters before '/' to avoid
          mis-splitting 'w/' as '/'.
        - Other delimiters retain their original logic.
        - " x " is only treated as a non-delimiter when it's part of dimension specifications.
        """
        # High-reliability delimiters (always trigger splitting with simple logic)
        high_reliability_delimiters = [" w/ ", " w/", " with "]
        # Handle-primary delimiters (first part is handle)
        handle_primary_delimiters = [" in "]
        # Medium-reliability delimiters (need smart analysis)
        medium_reliability_delimiters = [" + ", " - "]

        # Check if " x " is part of a dimension specification - if so, don't treat as delimiter
        if " x " in text and self._is_specification_x(text):
            # " x " is part of a dimension specification, so ignore it as a delimiter
            # Continue with other delimiter detection
            pass
        elif " x " in text:
            # " x " is present but NOT part of a dimension specification
            # This could be a legitimate delimiter, so don't block other delimiter detection
            pass

        # Check if text contains " & " - only treat as non-delimiter if it's not part of a brand
        # name
        if " & " in text:
            # Check if " & " is followed by a space and another word (likely a brand name)
            # or if it's followed immediately by another word (likely a delimiter)
            if re.search(r" &\s+\w", text):
                # " & " is followed by space + word, likely a brand name, so don't treat as
                # non-delimiter
                pass
            else:
                # " & " is followed immediately by word, likely a delimiter
                return None, None, None

        # Always check for ' w/ ' and ' with ' first to avoid misinterpreting 'w/' as '/'
        for delimiter in high_reliability_delimiters:
            if delimiter in text:
                return self._split_by_delimiter_simple(text, delimiter, "high_reliability")

        # Special handling for `/` as high-reliability delimiter (any spaces, not part of 'w/')
        # But first check if `/` is part of a specification rather than a delimiter
        if self._is_specification_slash(text):
            return None, None, None

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
                # For " - " delimiter, be extra smart about brand aliases and logical grouping
                if delimiter == " - ":
                    return self._split_by_delimiter_smart(text, delimiter, "smart_analysis")
                else:
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

        Analyzes both sides to determine which is handle vs knot using relative scoring.
        """
        parts = text.split(delimiter, 1)
        if len(parts) == 2:
            part1 = parts[0].strip()
            part2 = parts[1].strip()
            if part1 and part2:
                # Score each part as both handle and knot
                part1_handle_score = self._score_as_handle(part1)
                part1_knot_score = self._score_as_knot(part1)
                part2_handle_score = self._score_as_handle(part2)
                part2_knot_score = self._score_as_knot(part2)

                # Determine which part should be handle and which should be knot
                # based on relative scoring
                if part1_handle_score > part2_handle_score and part2_knot_score > part1_knot_score:
                    # part1 is better handle, part2 is better knot
                    return part1, part2, delimiter_type
                elif (
                    part2_handle_score > part1_handle_score and part1_knot_score > part2_knot_score
                ):
                    # part2 is better handle, part1 is better knot
                    return part2, part1, delimiter_type
                else:
                    # Fall back to handle score comparison (original logic)
                    if part1_handle_score > part2_handle_score:
                        return part1, part2, delimiter_type
                    else:
                        return part2, part1, delimiter_type
        return None, None, None

    def _split_by_delimiter_smart(
        self, text: str, delimiter: str, delimiter_type: str
    ) -> tuple[Optional[str], Optional[str], Optional[str]]:
        """Smart splitting for ambiguous delimiters by analyzing content."""
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

        # Try each delimiter position and score the results
        best_split = None
        best_score = -float("inf")

        for pos in delimiter_positions:
            part1 = text[:pos].strip()
            part2 = text[pos + len(delimiter) :].strip()

            if not part1 or not part2:
                continue

            # Check if part2 contains another delimiter (for " - " cases)
            if delimiter == " - " and " - " in part2:
                # This looks like "Brand - Alias - Size Fiber" or
                # "Brand Handle - Size Fiber" pattern
                sub_parts = part2.split(" - ", 1)
                if len(sub_parts) == 2:
                    middle_part = sub_parts[0].strip()
                    size_fiber_part = sub_parts[1].strip()

                    # Check if middle_part looks like a brand alias (not a handle description)
                    if self._looks_like_brand_alias(middle_part, size_fiber_part):
                        # This is likely "Brand - Alias - Size Fiber" pattern
                        # Handle should be part1, knot should be the combined alias + size/fiber
                        score = self._score_split(part1, part2)
                        if score > best_score:
                            best_score = score
                            best_split = (part1, part2, delimiter_type)
                    elif self._looks_like_handle_description(middle_part):
                        # This is likely "Brand Handle - Size Fiber" pattern
                        # Try splitting on the second delimiter instead
                        # This means part1 + middle_part should be handle,
                        # size_fiber_part should be knot
                        combined_handle = f"{part1} - {middle_part}"
                        score = self._score_split(combined_handle, size_fiber_part)
                        if score > best_score:
                            best_score = score
                            best_split = (combined_handle, size_fiber_part, delimiter_type)
            else:
                # No second delimiter, check if part2 looks like a complete knot description
                if delimiter == " - " and self._looks_like_complete_knot(part2):
                    # This looks like "Brand - Complete Knot Description"
                    score = self._score_split(part1, part2)
                    if score > best_score:
                        best_score = score
                        best_split = (part1, part2, delimiter_type)
                else:
                    # Regular smart analysis for other delimiters
                    # Score each part as both handle and knot
                    part1_handle_score = self._score_as_handle(part1)
                    part1_knot_score = self._score_as_knot(part1)
                    part2_handle_score = self._score_as_handle(part2)
                    part2_knot_score = self._score_as_knot(part2)

                    # Calculate the score difference for the best handle/knot assignment
                    if (
                        part1_handle_score > part2_handle_score
                        and part2_knot_score > part1_knot_score
                    ):
                        # part1 is better handle, part2 is better knot
                        score = part1_handle_score + part2_knot_score
                        potential_split = (part1, part2, delimiter_type)
                    elif (
                        part2_handle_score > part1_handle_score
                        and part1_knot_score > part2_knot_score
                    ):
                        # part2 is better handle, part1 is better knot
                        score = part2_handle_score + part1_knot_score
                        potential_split = (part2, part1, delimiter_type)
                    else:
                        # Fall back to handle score comparison (original logic)
                        if part1_handle_score > part2_handle_score:
                            score = part1_handle_score
                            potential_split = (part1, part2, delimiter_type)
                        else:
                            score = part2_handle_score
                            potential_split = (part2, part1, delimiter_type)

                    # Choose the split with the best score
                    if score > best_score:
                        best_score = score
                        best_split = potential_split

        return best_split if best_split else (None, None, None)

    def _score_split(self, handle: str, knot: str) -> float:
        """Score a potential handle/knot split."""
        handle_score = self._score_as_handle(handle)
        knot_score = self._score_as_knot(knot)
        return handle_score + knot_score

    def _looks_like_brand_alias(self, alias_part: str, size_fiber_part: str) -> bool:
        """Check if a part looks like a brand alias followed by size/fiber info."""
        # Check if size_fiber_part contains size and fiber information
        has_size = parse_knot_size(size_fiber_part) is not None
        has_fiber = match_fiber(size_fiber_part) is not None

        # If the second part has size/fiber info, the first part is likely a brand alias
        return has_size or has_fiber

    def _looks_like_handle_description(self, text: str) -> bool:
        """Check if text looks like a handle description rather than a brand alias."""
        text_lower = text.lower()

        # Handle-specific terms that indicate this is a handle description
        handle_terms = ["handle", "custom", "artisan", "turned", "wood", "resin", "zebra", "burl"]
        for term in handle_terms:
            if term in text_lower:
                return True

        # If it contains size/fiber info, it's likely not a handle description
        if parse_knot_size(text) is not None:
            return False
        if match_fiber(text) is not None:
            return False

        return False

    def _looks_like_complete_knot(self, text: str) -> bool:
        """Check if text looks like a complete knot description."""
        text_lower = text.lower()

        # Check for size patterns using knot_size_utils
        has_size = parse_knot_size(text) is not None

        # Check for fiber types using fiber_utils
        has_fiber = match_fiber(text) is not None

        # Check for version patterns (like B15, V20, etc.)
        has_version = bool(re.search(r"\b[bv]\d{1,2}\b", text_lower))

        # Check for knot-specific terms
        has_knot_terms = bool(re.search(r"\b(knot|tip|density)\b", text_lower))

        return has_size or has_fiber or has_version or has_knot_terms

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

    def _score_as_knot(self, text: str) -> int:
        """Score how likely a text is to be a knot (higher = more likely knot)."""
        score = 0

        # Strong knot indicators
        if "knot" in text.lower():
            score += 10

        # Test against brush strategies to see if this looks like a knot
        knot_strategy_matches = 0
        known_knot_matches = 0
        other_knot_matches = 0

        for strategy in self.strategies:
            try:
                result = strategy.match(text)
                if result and result.matched:
                    knot_strategy_matches += 1
                    # Check if this is a known knot vs other knot
                    brand = result.matched.get("brand", "")
                    model = result.matched.get("model", "")
                    strategy_name = result.strategy_name

                    # Known knots have specific brand/model combinations from known_knots section
                    if brand and model and "KnownKnot" in strategy_name:
                        known_knot_matches += 1
                    # Other knots are from other_knots section
                    elif brand and "OtherKnot" in strategy_name:
                        other_knot_matches += 1
            except (AttributeError, KeyError, TypeError, re.error):
                # Some strategies might fail on certain inputs due to regex errors,
                # missing attributes, or type issues - skip and continue
                continue

        # If multiple strategies match this as a knot, increase knot score
        if knot_strategy_matches >= 2:
            score += 12
        elif knot_strategy_matches == 1:
            score += 8

        # Known knots get much higher scores than other knots
        if known_knot_matches >= 1:
            score += 25  # Significant bonus for known knots
        elif other_knot_matches >= 1:
            score += 5  # Small bonus for other knots

        # Knot-related terms
        knot_terms = ["syn", "mm", "knot", "badger", "boar", "synthetic"]
        for term in knot_terms:
            if term in text.lower():
                score += 3

        # Fiber type patterns (strong knot indicators) - use fiber_utils
        fiber_type = match_fiber(text)
        if fiber_type:
            score += 10

        # Size patterns (knot indicators)
        if re.search(r"\d{2}\s*mm", text, re.IGNORECASE):
            score += 8

        # Chisel & Hound versioning patterns (knot indicators)
        if re.search(r"\bv\d{2}\b", text, re.IGNORECASE):
            score += 8

        # Declaration Grooming patterns (B2, B15, etc.)
        if re.search(r"B\d{1,2}[A-Z]?\b", text, re.IGNORECASE):
            score += 10

        # Handle indicators (negative score for knot likelihood)
        handle_terms = [
            "handle",
            "stock",
            "custom",
            "artisan",
            "turned",
            "wood",
            "resin",
            "zebra",
            "burl",
        ]
        for term in handle_terms:
            if term in text.lower():
                score -= 5

        # Test against actual handle patterns from handles.yaml (negative for knot)
        if self.handle_matcher:
            handle_match = self.handle_matcher.match_handle_maker(text)
            if handle_match:
                # Found a handle pattern match - reduce knot score
                section = handle_match.get("_matched_by_section", "")
                if section == "artisan_handles":
                    score -= 12  # Artisan handles are most specific
                elif section == "manufacturer_handles":
                    score -= 10
                elif section == "other_handles":
                    score -= 8
                else:
                    score -= 6

        return score

    def _split_by_fiber_hint(self, text: str) -> tuple[Optional[str], Optional[str], Optional[str]]:
        """Split text using fiber words as hints for knot identification."""
        # Check if `/` is part of a specification rather than a delimiter
        if self._is_specification_slash(text):
            return None, None, None

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

    def _is_specification_slash(self, text: str) -> bool:
        """Check if `/` is part of a specification rather than a delimiter.

        Examples of specifications that should NOT be split:
        - "50/50" (50% horse mane, 50% horse tail)
        - "70/30" (70% badger, 30% boar)
        - "80/20" (80% synthetic, 20% badger)
        - "25/75" (25% horse, 75% badger)
        - "r/wetshaving" (Reddit subreddit reference)
        """
        # Look for percentage specifications like "50/50", "70/30", etc.
        # These are typically found in parentheses or as part of fiber descriptions
        percentage_patterns = [
            r"\(\s*\d{1,2}/\d{1,2}\s*\)",  # (50/50), (70/30)
            r"\b\d{1,2}/\d{1,2}\b",  # 50/50, 70/30
            r"\d{1,2}/\d{1,2}\s*(?:horse|badger|boar|synthetic)",  # 50/50 horse mane
            r"(?:horse|badger|boar|synthetic).*?\d{1,2}/\d{1,2}",  # horse mane/tail 50/50
        ]

        for pattern in percentage_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return True

        # Look for Reddit subreddit references like "r/wetshaving"
        reddit_patterns = [
            r"\br/\w+\b",  # r/wetshaving, r/something
        ]

        for pattern in reddit_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return True

        return False

    def _is_specification_x(self, text: str) -> bool:
        """Check if ' x ' is part of a specification (e.g., dimensions) rather than a delimiter.

        Examples:
        - '1 in. x 3 in. x 5 in. Handle' (should NOT split on ' x ')
        - '24mm x 50mm' (should NOT split on ' x ')
        """
        import re

        # Match patterns like '1 in. x 3 in. x 5 in.' or '24mm x 50mm'
        dimension_pattern = re.compile(
            r"(\d+\s*(mm|in\.|in|cm)\s*x\s*){1,}\d+\s*(mm|in\.|in|cm)", re.IGNORECASE
        )
        return bool(dimension_pattern.search(text))

    def _is_same_maker_split(self, handle: str, knot: str) -> bool:
        """Check if the handle and knot are from the same maker brand."""
        if not self.handle_matcher:
            return False

        handle_match = self.handle_matcher.match_handle_maker(handle)
        knot_match = self.handle_matcher.match_handle_maker(knot)

        if handle_match and knot_match:
            handle_maker = handle_match.get("_matched_by_section", "")
            knot_maker = knot_match.get("_matched_by_section", "")

            # Check if both are from the same maker brand
            return handle_maker == knot_maker

        return False

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
