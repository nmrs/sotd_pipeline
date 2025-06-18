import re
from pathlib import Path
from typing import Optional

import yaml

from sotd.match.brush_matching_strategies.chisel_and_hound_strategy import (
    ChiselAndHoundBrushMatchingStrategy,
)
from sotd.match.brush_matching_strategies.declaration_grooming_strategy import (
    DeclarationGroomingBrushMatchingStrategy,
)
from sotd.match.brush_matching_strategies.known_brush_strategy import (
    KnownBrushMatchingStrategy,
)
from sotd.match.brush_matching_strategies.omega_semogue_strategy import (
    OmegaSemogueBrushMatchingStrategy,
)
from sotd.match.brush_matching_strategies.other_brushes_strategy import (
    OtherBrushMatchingStrategy,
)
from sotd.match.brush_matching_strategies.utils.fiber_utils import (
    _FIBER_PATTERNS,
    match_fiber,
)
from sotd.match.brush_matching_strategies.zenith_strategy import (
    ZenithBrushMatchingStrategy,
)


class BrushMatcher:
    def __init__(
        self,
        catalog_path: Path = Path("data/brushes.yaml"),
        handles_path: Path = Path("data/handles.yaml"),
    ):
        self.catalog_path = catalog_path
        self.handles_path = handles_path
        self.catalog_data = self._load_catalog(catalog_path)
        self.handles_data = self._load_catalog(handles_path)
        self.handle_patterns = self._compile_handle_patterns()
        self.strategies = [
            KnownBrushMatchingStrategy(self.catalog_data.get("known_brushes", {})),
            DeclarationGroomingBrushMatchingStrategy(
                self.catalog_data.get("declaration_grooming", {})
            ),
            ChiselAndHoundBrushMatchingStrategy(),
            OmegaSemogueBrushMatchingStrategy(),
            ZenithBrushMatchingStrategy(),
            OtherBrushMatchingStrategy(self.catalog_data.get("other_brushes", {})),
        ]

    def _load_catalog(self, catalog_path: Path) -> dict:
        """Load brush catalog from YAML file."""
        try:
            with catalog_path.open("r", encoding="utf-8") as f:
                return yaml.safe_load(f) or {}
        except (FileNotFoundError, yaml.YAMLError):
            return {}

    def _compile_handle_patterns(self) -> list[dict]:
        """Compile handle patterns from the handles catalog in priority order."""
        patterns = []

        # Priority 1: artisan_handles
        artisan_handles = self.handles_data.get("artisan_handles", {})
        for handle_maker, data in artisan_handles.items():
            for pattern in data.get("patterns", []):
                try:
                    patterns.append(
                        {
                            "maker": handle_maker,
                            "pattern": pattern,
                            "regex": re.compile(pattern, re.IGNORECASE),
                            "section": "artisan_handles",
                            "priority": 1,
                        }
                    )
                except re.error:
                    continue

        # Priority 2: manufacturer_handles
        manufacturer_handles = self.handles_data.get("manufacturer_handles", {})
        for handle_maker, data in manufacturer_handles.items():
            for pattern in data.get("patterns", []):
                try:
                    patterns.append(
                        {
                            "maker": handle_maker,
                            "pattern": pattern,
                            "regex": re.compile(pattern, re.IGNORECASE),
                            "section": "manufacturer_handles",
                            "priority": 2,
                        }
                    )
                except re.error:
                    continue

        # Priority 3: other_handles
        other_handles = self.handles_data.get("other_handles", {})
        for handle_maker, data in other_handles.items():
            for pattern in data.get("patterns", []):
                try:
                    patterns.append(
                        {
                            "maker": handle_maker,
                            "pattern": pattern,
                            "regex": re.compile(pattern, re.IGNORECASE),
                            "section": "other_handles",
                            "priority": 3,
                        }
                    )
                except re.error:
                    continue

        # Sort by priority (lower = higher), then by pattern length (longer = more specific)
        patterns.sort(key=lambda x: (x["priority"], -len(x["pattern"])))
        return patterns

    def _match_handle_maker(self, text: str) -> Optional[dict]:
        """
        Match handle maker from text using the handle patterns.
        Returns dict with maker and metadata or None if no match.
        """
        if not text:
            return None

        for pattern_info in self.handle_patterns:
            if pattern_info["regex"].search(text):
                return {
                    "handle_maker": pattern_info["maker"],
                    "_matched_by_section": pattern_info["section"],
                    "_pattern_used": pattern_info["pattern"],
                    "_source_text": text,
                }

        return None

    def _split_handle_and_knot(
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
                    text, delimiter, "handle_primary", handle_first=False
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
        handle_match = self._match_handle_maker(text)
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
        if first_fiber_word > 0 and len(words) > 2:
            handle_part = " ".join(words[:first_fiber_word])
            knot_part = " ".join(words[first_fiber_word:])
            if handle_part and knot_part:
                return handle_part, knot_part
        return None, None

    def _should_prioritize_knot(self, text: str) -> bool:
        """Determine if knot maker should take precedence based on delimiter semantics."""
        handle_primary_delimiters = [" in "]  # Handle takes precedence

        # Check for handle-primary delimiters
        for delimiter in handle_primary_delimiters:
            if delimiter in text:
                return False

        # For all other delimiters, let the smart analysis determine priority
        # by checking if we successfully split and which part scored higher as handle
        handle, knot, delimiter_type = self._split_handle_and_knot(text)
        if handle and knot and delimiter_type == "smart_analysis":
            # If smart analysis was used, trust its determination
            # The smart analysis already put the handle first and knot second
            return True  # Process knot part first since it's usually more distinctive

        # Default behavior when no delimiters found
        return True  # Default to knot priority for backward compatibility

    def _is_known_handle_maker(self, brand: str) -> bool:
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

    def _try_knot_maker_fallback(self, value: str, handle_result: dict) -> dict | None:
        """Try to find a knot maker when full-text matching found a handle maker."""
        if not self._is_known_handle_maker(handle_result.get("brand", "")):
            return None

        # Try to find knot maker brands in the text
        for strategy in self.strategies:
            # Skip the strategy that already matched the handle
            if strategy.__class__.__name__ == handle_result.get("_matched_by_strategy"):
                continue

            if result := strategy.match(value):
                if isinstance(result, dict):
                    if "matched" in result and result.get("matched"):
                        knot_match = result["matched"]
                        # If we found a different brand, prioritize it as the knot maker
                        if knot_match.get("brand") != handle_result.get("brand"):
                            knot_match["_matched_by_strategy"] = strategy.__class__.__name__
                            knot_match["_pattern_used"] = result.get("pattern")
                            knot_match["_matched_from"] = "knot_fallback"
                            knot_match["handle_maker"] = handle_result.get("brand")
                            return knot_match
                    elif "brand" in result:
                        knot_match = result
                        # If we found a different brand, prioritize it as the knot maker
                        if knot_match.get("brand") != handle_result.get("brand"):
                            knot_match["_matched_by_strategy"] = strategy.__class__.__name__
                            knot_match["_pattern_used"] = result.get("_pattern_used", "unknown")
                            knot_match["_matched_from"] = "knot_fallback"
                            knot_match["handle_maker"] = handle_result.get("brand")
                            return knot_match
        return None

    def _process_fiber_info(self, value: str, match_dict: dict) -> None:
        """Process fiber information from the input value and update match dictionary."""
        user_fiber = None
        fiber_patterns = {
            "Boar": r"boar",
            "Badger": r"badger",
            "Synthetic": r"synthetic|syn|nylon|plissoft|tuxedo|cashmere",
        }
        for fiber, pat in fiber_patterns.items():
            if re.search(pat, value, re.IGNORECASE):
                user_fiber = fiber
                break

        if user_fiber:
            if match_dict.get("fiber") and match_dict["fiber"].lower() == user_fiber.lower():
                match_dict["fiber_strategy"] = "user_input"
            elif match_dict.get("fiber") and match_dict["fiber"].lower() != user_fiber.lower():
                match_dict["fiber_conflict"] = user_fiber
                match_dict["fiber_strategy"] = "yaml"
            else:
                match_dict["fiber"] = user_fiber
                match_dict["fiber_strategy"] = "user_input"
        else:
            if match_dict.get("fiber_strategy") is None:
                match_dict["fiber_strategy"] = "default" if "default" in value.lower() else "yaml"

    def _process_knot_size(self, value: str, match_dict: dict) -> None:
        """Process knot size information from the input value and update match dictionary."""
        user_knot = None
        knot_match = re.search(r"(\d{2})(\.\d+)?[\s-]*mm", value, re.IGNORECASE)
        if knot_match:
            user_knot = float(knot_match.group(1))

        if user_knot:
            if match_dict.get("knot_size_mm") and abs(match_dict["knot_size_mm"] - user_knot) < 0.1:
                match_dict["knot_size_strategy"] = "user_input"
            elif (
                match_dict.get("knot_size_mm")
                and abs(match_dict["knot_size_mm"] - user_knot) >= 0.1
            ):
                match_dict["knot_size_conflict"] = user_knot
                match_dict["knot_size_strategy"] = "yaml"
            else:
                match_dict["knot_size_mm"] = user_knot
                match_dict["knot_size_strategy"] = "user_input"
        else:
            if match_dict.get("knot_size_strategy") is None:
                match_dict["knot_size_strategy"] = (
                    "default" if "default" in value.lower() else "yaml"
                )

    def _process_handle_info(self, value: str, match_dict: dict) -> None:
        """Process handle information from the input value and update match dictionary."""
        handle, _knot, _ = self._split_handle_and_knot(value)
        if handle and not match_dict.get("handle_maker"):
            handle_match = self._match_handle_maker(handle)
            if handle_match:
                match_dict["handle_maker"] = handle_match["handle_maker"]
                match_dict["handle_maker_metadata"] = {
                    "_matched_by_section": handle_match["_matched_by_section"],
                    "_pattern_used": handle_match["_pattern_used"],
                }

    def _enrich_match_result(self, value: str, match_dict: dict) -> None:
        """Enrich match dictionary with additional information from the input value."""
        self._process_fiber_info(value, match_dict)
        self._process_knot_size(value, match_dict)
        self._process_handle_info(value, match_dict)

    def match(self, value: str) -> dict:
        """Match brush string to known patterns."""
        if not value:
            return {"original": value, "matched": None, "match_type": None, "pattern": None}

        handle, knot, _ = self._split_handle_and_knot(value)

        if knot and self._should_prioritize_knot(value):
            result = self._match_knot_priority(value, handle, knot)
            if result:
                return result
        elif handle and knot and not self._should_prioritize_knot(value):
            result = self._match_handle_priority(value, handle, knot)
            if result:
                return result

        result = self._match_main_strategies(value)
        if result:
            return result

        return {
            "original": value,
            "matched": None,
            "match_type": None,
            "pattern": None,
        }

    def _match_knot_priority(
        self, value: str, handle: Optional[str], knot: Optional[str]
    ) -> Optional[dict]:
        for strategy in self.strategies:
            if result := strategy.match(knot):
                m = self._extract_match_dict(result, strategy, "knot_part", handle, knot)
                if m:
                    return self._post_process_match(
                        {
                            "original": value,
                            "matched": m,
                            "match_type": (
                                result.get("match_type", "exact")
                                if isinstance(result, dict)
                                else m.get("source_type", "exact")
                            ),
                            "pattern": (
                                result.get("pattern")
                                if isinstance(result, dict)
                                else m.get("_pattern_used", "unknown")
                            ),
                        },
                        value,
                    )
        return None

    def _match_handle_priority(
        self, value: str, handle: Optional[str], knot: Optional[str]
    ) -> Optional[dict]:
        for strategy in self.strategies:
            if result := strategy.match(handle):
                m = self._extract_match_dict(result, strategy, "handle_part", handle, knot)
                if m:
                    return self._post_process_match(
                        {
                            "original": value,
                            "matched": m,
                            "match_type": (
                                result.get("match_type", "exact")
                                if isinstance(result, dict)
                                else m.get("source_type", "exact")
                            ),
                            "pattern": (
                                result.get("pattern")
                                if isinstance(result, dict)
                                else m.get("_pattern_used", "unknown")
                            ),
                        },
                        value,
                    )
        return None

    def _match_main_strategies(self, value: str) -> Optional[dict]:
        for strategy in self.strategies:
            if result := strategy.match(value):
                m = self._extract_match_dict(result, strategy)
                if m:
                    self._enrich_match_result(value, m)
                    return self._post_process_match(
                        {
                            "original": value,
                            "matched": m,
                            "match_type": (
                                result.get("match_type", "exact")
                                if isinstance(result, dict)
                                else m.get("source_type", "exact")
                            ),
                            "pattern": (
                                result.get("pattern")
                                if isinstance(result, dict)
                                else m.get("_pattern_used", "unknown")
                            ),
                        },
                        value,
                    )
        return None

    def _extract_match_dict(
        self,
        result,
        strategy,
        matched_from: Optional[str] = None,
        handle: Optional[str] = None,
        knot: Optional[str] = None,
    ):
        if isinstance(result, dict):
            if "matched" in result and result.get("matched"):
                m = result["matched"]
                m["_matched_by_strategy"] = strategy.__class__.__name__
                m["_pattern_used"] = result.get("pattern")
                if matched_from:
                    m["_matched_from"] = matched_from
                    m["_original_knot_text"] = knot
                    m["_original_handle_text"] = handle
                return m
            if "brand" in result:
                m = result
                m["_matched_by_strategy"] = strategy.__class__.__name__
                m["_pattern_used"] = result.get("_pattern_used", "unknown")
                if matched_from:
                    m["_matched_from"] = matched_from
                    m["_original_knot_text"] = knot
                    m["_original_handle_text"] = handle
                return m
        return None

    def _post_process_match(self, result: dict, value: str) -> dict:
        if not result.get("matched"):
            return result

        updated = result["matched"].copy()

        # Parse fiber and knot size from user input
        parsed_fiber = match_fiber(value)
        parsed_knot = None
        knot_match = re.search(r"(\d{2})(\.\d+)?[\s-]*mm", value, re.IGNORECASE)
        if knot_match:
            parsed_knot = float(knot_match.group(1))

        self._resolve_fiber(updated, parsed_fiber)
        self._resolve_knot_size(updated, parsed_knot)
        self._resolve_handle_maker(updated, value)

        result["matched"] = updated
        return result

    def _resolve_fiber(self, updated: dict, parsed_fiber: str | None) -> None:
        if "fiber_strategy" not in updated:
            fiber = updated.get("fiber")
            default_fiber = updated.get("default fiber")
            if fiber:
                updated["fiber_strategy"] = "yaml"
                if parsed_fiber and parsed_fiber.lower() != fiber.lower():
                    updated["fiber_conflict"] = f"user_input: {parsed_fiber}"
            elif parsed_fiber:
                updated["fiber"] = parsed_fiber
                updated["fiber_strategy"] = "user_input"
            elif default_fiber:
                updated["fiber"] = default_fiber
                updated["fiber_strategy"] = "default"
            else:
                updated["fiber_strategy"] = "unset"

    def _resolve_knot_size(self, updated: dict, parsed_knot: float | None) -> None:
        if "knot_size_strategy" not in updated:
            knot_size = updated.get("knot_size_mm")
            default_knot_size = updated.get("default_knot_size_mm")
            if knot_size is not None:
                updated["knot_size_strategy"] = "yaml"
            elif parsed_knot is not None:
                updated["knot_size_mm"] = parsed_knot
                updated["knot_size_strategy"] = "user_input"
            elif default_knot_size is not None:
                updated["knot_size_mm"] = default_knot_size
                updated["knot_size_strategy"] = "default"
            else:
                updated["knot_size_strategy"] = "unset"

    def _resolve_handle_maker(self, updated: dict, value: str) -> None:
        if ("handle_maker" not in updated) or (updated["handle_maker"] is None):
            # Check if we have knot matching information to help exclude knot text
            handle_text = updated.get("_original_handle_text")
            matched_from = updated.get("_matched_from")

            # Strategy 1: If we matched from a knot part, try to find handle in handle part first
            if matched_from == "knot_part" and handle_text:
                handle_match = self._match_handle_maker(handle_text)
                if handle_match:
                    updated["handle_maker"] = handle_match["handle_maker"]
                    updated["handle_maker_metadata"] = {
                        "_matched_by_section": handle_match["_matched_by_section"],
                        "_pattern_used": handle_match["_pattern_used"],
                        "_source_text": handle_match["_source_text"],
                        "_strategy": "non_knot_portion",
                    }
                    return

                # If no pattern match in handle text, use the handle text as-is
                updated["handle_maker"] = handle_text
                updated["handle_maker_metadata"] = {
                    "_matched_by_section": "split_fallback",
                    "_pattern_used": None,
                    "_source_text": handle_text,
                    "_strategy": "non_knot_portion",
                }
                return

            # Strategy 2: Try delimiter-based splitting for general cases
            handle, knot, _ = self._split_handle_and_knot(value)
            if handle:
                handle_match = self._match_handle_maker(handle)
                if handle_match:
                    updated["handle_maker"] = handle_match["handle_maker"]
                    updated["handle_maker_metadata"] = {
                        "_matched_by_section": handle_match["_matched_by_section"],
                        "_pattern_used": handle_match["_pattern_used"],
                        "_source_text": handle_match["_source_text"],
                        "_strategy": "delimiter_split",
                    }
                    return
                else:
                    # No pattern match, but we have a handle part from splitting
                    updated["handle_maker"] = handle
                    updated["handle_maker_metadata"] = {
                        "_matched_by_section": "split_fallback",
                        "_pattern_used": None,
                        "_source_text": handle,
                        "_strategy": "delimiter_split",
                    }
                    if knot:
                        updated["knot_maker"] = knot
                    return

            # Strategy 3: Fallback to full string matching
            handle_match = self._match_handle_maker(value)
            if handle_match:
                updated["handle_maker"] = handle_match["handle_maker"]
                updated["handle_maker_metadata"] = {
                    "_matched_by_section": handle_match["_matched_by_section"],
                    "_pattern_used": handle_match["_pattern_used"],
                    "_source_text": handle_match["_source_text"],
                    "_strategy": "full_string_fallback",
                }

    def _split_by_brand_context(
        self, text: str
    ) -> tuple[Optional[str], Optional[str], Optional[str]]:
        """Split text by recognizing brand context patterns when clear handle/knot makers are present.

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
        # Check if "Declaration" appears in the text (indicating it might be "Declaration B3" not "CH ... B3")
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
