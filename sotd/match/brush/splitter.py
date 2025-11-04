import re
from typing import Optional

from .delimiter_patterns import BrushDelimiterPatterns
from .strategies.utils.fiber_utils import _FIBER_PATTERNS, match_fiber
from .strategies.utils.knot_size_utils import parse_knot_size


class BrushSplitter:
    """Brush splitting functionality extracted from BrushMatcher."""

    # Class-level cache for brands with slashes to avoid repeated YAML loading
    _brands_with_slash_cache = None

    @classmethod
    def clear_brands_cache(cls):
        """Clear the brands with slash cache."""
        cls._brands_with_slash_cache = None

    def __init__(self, handle_matcher=None, strategies=None):
        self.handle_matcher = handle_matcher
        self.strategies = strategies or []
        # Pre-load brands with slash to avoid repeated YAML loading during matching
        self._brands_with_slash = self._get_brands_with_slash()

    @classmethod
    def _get_brands_with_slash(cls) -> set:
        """Get cached set of brand and model names that contain '/'."""
        if cls._brands_with_slash_cache is None:
            cls._brands_with_slash_cache = cls._load_brands_with_slash()
        return cls._brands_with_slash_cache

    @classmethod
    def _load_brands_with_slash(cls) -> set:
        """Load brands and models with '/' from brushes.yaml."""
        try:
            from pathlib import Path

            import yaml

            # Load brushes.yaml to find brands/models with "/"
            brushes_path = Path("data/brushes.yaml")
            if not brushes_path.exists():
                return set()

            with open(brushes_path, "r", encoding="utf-8") as f:
                brushes_data = yaml.safe_load(f)

            brands_with_slash = set()

            # Search through known_brushes and other_brushes sections
            sections_to_check = ["known_brushes", "other_brushes"]

            for section_name in sections_to_check:
                section_data = brushes_data.get(section_name, {})
                if not isinstance(section_data, dict):
                    continue

                # Check brand names (top level keys)
                for brand_name in section_data.keys():
                    if "/" in brand_name:
                        brands_with_slash.add(brand_name.lower())

                    # Check model names under each brand
                    brand_data = section_data[brand_name]
                    if isinstance(brand_data, dict):
                        for model_name in brand_data.keys():
                            if "/" in model_name:
                                brands_with_slash.add(model_name.lower())

            return brands_with_slash

        except Exception:
            # If there's any error loading the YAML or processing, fall back to empty set
            return set()

    def split_handle_and_knot(
        self, text: str
    ) -> tuple[Optional[str], Optional[str], Optional[str]]:
        """Split handle and knot using various delimiters and fiber detection."""
        if not text:
            return None, None, None

        # Step 1: Try high-priority delimiter-based splitting (w/, with, in)
        result = self._try_delimiter_splitting(text)
        if result[0] and result[1]:
            return result

        # Step 2: Check if it's a known brush (medium priority)
        result = self._try_known_brush_check(text)
        if result[0] is None and result[1] is None and result[2] is None:
            return result  # Known brush - don't split

        # Step 3: Try medium-priority delimiter-based splitting (-, +)
        result = self._try_medium_priority_delimiter_splitting(text)
        if result[0] and result[1]:
            return result

        # Step 4: Fiber hint splitting removed - fiber words are for scoring only, not splitting
        # Fiber words should only be used in _score_as_handle() and _score_as_knot() methods

        # Step 5: Final fallback - try all splitting methods again
        result = self._try_fallback_splitting(text)
        return result

    def _try_delimiter_splitting(
        self, text: str
    ) -> tuple[Optional[str], Optional[str], Optional[str]]:
        """Step 1: Try high-priority delimiter-based splitting."""
        return self._split_by_high_priority_delimiters(text)

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

    def _try_medium_priority_delimiter_splitting(
        self, text: str
    ) -> tuple[Optional[str], Optional[str], Optional[str]]:
        """Step 3: Try medium-priority delimiter-based splitting."""
        return self._split_by_medium_priority_delimiters(text)

    # _try_fiber_hint_splitting method removed - fiber words are for scoring only, not splitting

    def _try_fallback_splitting(
        self, text: str
    ) -> tuple[Optional[str], Optional[str], Optional[str]]:
        """Step 5: Final fallback - try all splitting methods again."""
        # Try high-priority delimiters first
        handle, knot, delimiter_type = self._split_by_high_priority_delimiters(text)
        if handle and knot:
            return handle, knot, delimiter_type

        # Try medium-priority delimiters
        handle, knot, delimiter_type = self._split_by_medium_priority_delimiters(text)
        if handle and knot:
            return handle, knot, delimiter_type

        # Fiber hint splitting removed - fiber words are for scoring only, not splitting

        # If no splitting methods worked, return None to indicate no splitting
        return None, None, None

    def _split_by_high_priority_delimiters(
        self, text: str
    ) -> tuple[Optional[str], Optional[str], Optional[str]]:
        """Split text using high-priority delimiters.

        These delimiters are always treated as splitting indicators and are checked
        before known brush validation.
        """
        # High-reliability delimiters (always trigger splitting with simple logic)
        high_reliability_delimiters = BrushDelimiterPatterns.get_smart_splitting_delimiters()
        # Handle-primary delimiters (first part is handle)
        handle_primary_delimiters = BrushDelimiterPatterns.get_positional_splitting_delimiters()
        # Other high-priority delimiters
        other_high_priority_delimiters = []  # "+" requires smart analysis, not high-priority splitting

        # Always check for ' w/ ' and ' with ' first to avoid misinterpreting 'w/' as '/'
        # These delimiters use smart splitting to determine handle vs knot based on content
        for delimiter in high_reliability_delimiters:
            if delimiter in text:
                return self._split_by_delimiter_smart(text, delimiter, "high_reliability")

        # Check handle-primary delimiters (first part is knot, second part is handle)
        for delimiter in handle_primary_delimiters:
            if delimiter in text:
                return self._split_by_delimiter_positional(text, delimiter, "handle_primary")

        # Check other high-priority delimiters
        for delimiter in other_high_priority_delimiters:
            if delimiter in text:
                return self._split_by_delimiter_simple(text, delimiter, "high_priority")

        return None, None, None

    def _split_by_medium_priority_delimiters(
        self, text: str
    ) -> tuple[Optional[str], Optional[str], Optional[str]]:
        """Split text using medium-priority delimiters.

        These delimiters are checked after known brush validation and may not always
        indicate a split (e.g., "Zenith - MOAR BOAR" should not split).
        """
        # Medium-reliability delimiters (need smart analysis)
        medium_reliability_delimiters = [
            d for d in BrushDelimiterPatterns.get_medium_priority_delimiters() if d != "/"
        ]

        # Check medium-reliability delimiters (use smart analysis)
        for delimiter in medium_reliability_delimiters:
            if delimiter in text:
                # Special handling for parentheses
                if delimiter == " (":
                    return self._split_by_parentheses(text, "medium_reliability")
                # For " - " and " + " delimiters, use smart analysis
                elif delimiter in [" - ", " + "]:
                    return self._split_by_delimiter_smart(text, delimiter, "smart_analysis")
                else:
                    return self._split_by_delimiter_smart(text, delimiter, "smart_analysis")

        # Special handling for `/` as medium-priority delimiter (any spaces, not part of 'w/')
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
                    return part1, part2, "medium_reliability"
                else:
                    return part2, part1, "medium_reliability"

        return None, None, None

    def _split_by_delimiter_positional(
        self, text: str, delimiter: str, delimiter_type: str
    ) -> tuple[Optional[str], Optional[str], Optional[str]]:
        """Positional splitting for delimiters.

        For 'in' delimiter: first part = knot, second part = handle
        For other delimiters: first part = handle, second part = knot
        """
        parts = text.split(delimiter, 1)
        if len(parts) == 2:
            part1 = parts[0].strip()
            part2 = parts[1].strip()
            if part1 and part2:
                if delimiter == " in ":
                    # For "in" delimiter: first part = knot, second part = handle
                    return part2, part1, delimiter_type  # handle, knot
                else:
                    # For other delimiters: first part = handle, second part = knot
                    return part1, part2, delimiter_type  # handle, knot
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
                    # Handle scores are equal or conflicting - prioritize knot scores
                    if part2_knot_score > part1_knot_score:
                        # part2 is better knot, so part1 should be handle
                        return part1, part2, delimiter_type
                    elif part1_knot_score > part2_knot_score:
                        # part1 is better knot, so part2 should be handle
                        return part2, part1, delimiter_type
                    else:
                        # Knot scores are also equal - fall back to handle score comparison
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
                        # Handle scores are equal or conflicting - prioritize knot scores
                        if part2_knot_score > part1_knot_score:
                            # part2 is better knot, so part1 should be handle
                            score = part1_handle_score + part2_knot_score
                            potential_split = (part1, part2, delimiter_type)
                        elif part1_knot_score > part2_knot_score:
                            # part1 is better knot, so part2 should be handle
                            score = part2_handle_score + part1_knot_score
                            potential_split = (part2, part1, delimiter_type)
                        else:
                            # Knot scores are also equal - fall back to handle score comparison
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

        # Declaration Grooming patterns (B2, B15, etc.) - HIGH PRIORITY
        if re.search(r"B\d{1,2}[A-Z]?\b", text, re.IGNORECASE):
            score += 25  # Increased from 10 to 25 for high priority

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
        # BUT give lower priority to handle matches when strong knot indicators are present
        if self.handle_matcher:
            handle_match = self.handle_matcher.match_handle_maker(text)
            if handle_match:
                # Check if we have strong knot indicators that should override handle match
                has_strong_knot_indicators = (
                    re.search(r"B\d{1,2}[A-Z]?\b", text, re.IGNORECASE)
                    or re.search(r"\d{2}\s*mm", text, re.IGNORECASE)
                    or match_fiber(text)
                )

                if has_strong_knot_indicators:
                    # Reduce the penalty when strong knot indicators are present
                    section = handle_match.get("_matched_by_section", "")
                    if section == "artisan_handles":
                        score -= 4  # Reduced from 12 to 4
                    elif section == "manufacturer_handles":
                        score -= 3  # Reduced from 10 to 3
                    elif section == "other_handles":
                        score -= 2  # Reduced from 8 to 2
                    else:
                        score -= 1  # Reduced from 6 to 1
                else:
                    # Normal penalty when no strong knot indicators
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
        - "EldrormR Industries/Muninn Woodworks" (known brand with "/")
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

        # Look for mixed fiber specifications like "Mixed Badger/Boar"
        mixed_fiber_patterns = [
            r"mixed\s+(?:badger|boar|synthetic|horse)/\s*(?:badger|boar|synthetic|horse)",
            r"(?:badger|boar|synthetic|horse)/\s*(?:badger|boar|synthetic|horse)\s+mixed",
        ]

        for pattern in mixed_fiber_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return True

        # Look for Reddit subreddit references like "r/wetshaving"
        reddit_patterns = [
            r"\br/\w+\b",  # r/wetshaving, r/something
        ]

        for pattern in reddit_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return True

        # Check if the text contains a known brand or model name with "/"
        # This prevents splitting on "/" when it's part of a known brand name
        # Performance optimization: only check if text contains "/"
        if "/" in text and self._contains_known_brand_with_slash(text):
            return True

        return False

    def _contains_known_brand_with_slash(self, text: str) -> bool:
        """Check if the text contains a known brand or model name that includes '/'."""
        if not self._brands_with_slash:
            return False

        text_lower = text.lower()

        # Cast to list to satisfy linter
        for brand_name in list(self._brands_with_slash):
            if brand_name in text_lower:
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

    def _split_by_parentheses(
        self, text: str, delimiter_type: str
    ) -> tuple[Optional[str], Optional[str], Optional[str]]:
        """Split text using parentheses pattern: handle (knot) or knot (handle).

        Uses content-based scoring to determine which part is handle vs knot.
        Expects format: "Part1 (Part2)" or "Part1 (Part2 with spaces)"
        """
        # Match pattern: text before '(' and text between '(' and ')'
        # Handle cases where closing paren might be missing or have extra text after
        match = re.search(r"^(.+?)\s+\(([^)]+)\)", text)
        if not match:
            return None, None, None

        part1 = match.group(1).strip()  # Outside parentheses
        part2 = match.group(2).strip()  # Inside parentheses

        if not part1 or not part2:
            return None, None, None

        # Use content-based scoring to determine handle vs knot
        part1_handle_score = self._score_as_handle(part1)
        part1_knot_score = self._score_as_knot(part1)
        part2_handle_score = self._score_as_handle(part2)
        part2_knot_score = self._score_as_knot(part2)

        # Determine best assignment based on scores
        if part1_handle_score > part2_handle_score and part2_knot_score > part1_knot_score:
            return part1, part2, delimiter_type  # part1=handle, part2=knot
        elif part2_handle_score > part1_handle_score and part1_knot_score > part2_knot_score:
            return part2, part1, delimiter_type  # part2=handle, part1=knot
        else:
            # Tie-breaking: prioritize knot scores
            if part2_knot_score > part1_knot_score:
                return part1, part2, delimiter_type
            else:
                return part2, part1, delimiter_type

    def _is_known_brush(self, text: str) -> bool:
        """Check if the text matches a known brush in the catalog.

        This method should only return True for complete, single brush descriptions
        that match patterns in the brush catalog.
        """
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
