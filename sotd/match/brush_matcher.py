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
from sotd.match.brush_matching_strategies.utils.fiber_utils import match_fiber
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
        """Split handle and knot using various delimiters and fiber detection.

        Returns:
            tuple: (handle_part, knot_part, delimiter_type)
            delimiter_type: "knot_primary" for "with"/"w/", "handle_primary" for "in",
                           "neutral" for "/", "fiber_hint" for fiber-based detection
        """
        if not text:
            return None, None, None

        # Define delimiters with their semantic meaning
        knot_primary_delimiters = [" w/ ", " with "]  # Knot takes precedence
        handle_primary_delimiters = [" in "]  # Handle takes precedence
        neutral_delimiters = [" / ", "/", " - "]  # No semantic preference

        # Check knot-primary delimiters first
        for delimiter in knot_primary_delimiters:
            if delimiter in text:
                parts = text.split(delimiter, 1)
                if len(parts) == 2:
                    handle = parts[0].strip()
                    knot = parts[1].strip()
                    if handle and knot:
                        return handle, knot, "knot_primary"

        # Check handle-primary delimiters
        for delimiter in handle_primary_delimiters:
            if delimiter in text:
                parts = text.split(delimiter, 1)
                if len(parts) == 2:
                    # For "in" delimiter: "knot_description in handle_description"
                    # So parts[0] is knot, parts[1] is handle
                    knot = parts[0].strip()
                    handle = parts[1].strip()
                    if handle and knot:
                        return handle, knot, "handle_primary"

        # Check neutral delimiters
        for delimiter in neutral_delimiters:
            if delimiter in text:
                parts = text.split(delimiter, 1)
                if len(parts) == 2:
                    handle = parts[0].strip()
                    knot = parts[1].strip()
                    if handle and knot:
                        return handle, knot, "neutral"

        # If no delimiters found, try fiber detection as a hint
        # Look for fiber words (badger, boar, synthetic, etc.) to identify knot part
        return self._split_by_fiber_hint(text)

    def _split_by_fiber_hint(self, text: str) -> tuple[Optional[str], Optional[str], Optional[str]]:
        """Split text using fiber words as hints for knot identification."""
        from sotd.match.brush_matching_strategies.utils.fiber_utils import _FIBER_PATTERNS

        # Build a comprehensive fiber pattern from all fiber types
        all_fiber_patterns = []
        for fiber_type, pattern in _FIBER_PATTERNS.items():
            # Remove outer parentheses if present
            clean_pattern = pattern.strip("()")
            all_fiber_patterns.append(clean_pattern)

        # Combine all fiber patterns
        combined_fiber_pattern = "|".join(all_fiber_patterns)

        # Find fiber words in the text
        import re

        fiber_matches = list(re.finditer(f"({combined_fiber_pattern})", text, re.IGNORECASE))

        if not fiber_matches:
            return None, None, None

        # Find the last fiber match (often the most specific)
        last_fiber_match = fiber_matches[-1]
        fiber_start = last_fiber_match.start()
        fiber_end = last_fiber_match.end()

        # Try to identify a reasonable split point around the fiber
        # Look for brand/maker boundaries before the fiber
        words = text.split()
        fiber_word_indices = []

        # Find which word indices contain the fiber
        current_pos = 0
        for i, word in enumerate(words):
            word_start = current_pos
            word_end = current_pos + len(word)

            # Check if this word overlaps with the fiber match
            if (word_start <= fiber_start < word_end) or (word_start < fiber_end <= word_end):
                fiber_word_indices.append(i)

            current_pos = word_end + 1  # +1 for space

        if not fiber_word_indices:
            return None, None, None

        # Try different split strategies
        first_fiber_word = fiber_word_indices[0]

        # Strategy 1: Look for known handle makers before the fiber
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

        # Check if any handle maker appears before the fiber
        text_before_fiber = " ".join(words[:first_fiber_word])
        for handle_maker in handle_maker_brands:
            if re.search(re.escape(handle_maker), text_before_fiber, re.IGNORECASE):
                # Found a handle maker before fiber - split after the handle maker
                handle_pattern = re.escape(handle_maker)
                match = re.search(handle_pattern, text, re.IGNORECASE)
                if match:
                    split_point = match.end()
                    handle_part = text[:split_point].strip()
                    knot_part = text[split_point:].strip()
                    if handle_part and knot_part:
                        return handle_part, knot_part, "fiber_hint"

        # Strategy 2: Look for brand names that might be knot makers near the fiber
        # This is more heuristic - split before a potential knot maker brand
        knot_maker_patterns = [
            r"\b(Maggard|Oumo|Declaration|Zenith|Omega|Semogue|Simpson|Shavemac)\b"
        ]

        for pattern in knot_maker_patterns:
            matches = list(re.finditer(pattern, text, re.IGNORECASE))
            for match in matches:
                # If the knot maker is reasonably close to the fiber, try splitting before it
                if abs(match.start() - fiber_start) <= 50:  # Within 50 characters
                    split_point = match.start()
                    handle_part = text[:split_point].strip()
                    knot_part = text[split_point:].strip()
                    if handle_part and knot_part and len(handle_part) > 3:
                        return handle_part, knot_part, "fiber_hint"

        # Strategy 3: If we have multiple words, try splitting before the fiber word
        # This is a fallback for cases where we can't identify specific brands
        if first_fiber_word > 0 and len(words) > 2:
            # Split before the word containing the fiber
            handle_part = " ".join(words[:first_fiber_word])
            knot_part = " ".join(words[first_fiber_word:])
            if handle_part and knot_part:
                return handle_part, knot_part, "fiber_hint"

        return None, None, None

    def _should_prioritize_knot(self, text: str) -> bool:
        """Determine if knot maker should take precedence based on delimiter semantics."""
        knot_primary_delimiters = [" w/ ", " with "]
        handle_primary_delimiters = [" in "]

        # Check for knot-primary delimiters
        for delimiter in knot_primary_delimiters:
            if delimiter in text:
                return True

        # Check for handle-primary delimiters
        for delimiter in handle_primary_delimiters:
            if delimiter in text:
                return False

        # Default behavior for neutral delimiters (/, etc.)
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

    def match(self, value: str) -> dict:
        """Match brush string to known patterns."""
        if not value:
            return {"original": value, "matched": None, "match_type": None, "pattern": None}

        # Check if we can split into handle and knot parts
        handle, knot, _ = self._split_handle_and_knot(value)

        # If we have a knot part and knot should take precedence, try matching it first
        if knot and self._should_prioritize_knot(value):
            for strategy in self.strategies:
                if result := strategy.match(knot):
                    # Found a match for the knot part - this takes precedence
                    if isinstance(result, dict):
                        if "matched" in result and result.get("matched"):
                            m = result["matched"]
                            m["_matched_by_strategy"] = strategy.__class__.__name__
                            m["_pattern_used"] = result.get("pattern")
                            m["_matched_from"] = "knot_part"
                            m["_original_knot_text"] = knot
                            m["_original_handle_text"] = handle

                            # Add handle maker if we can identify it
                            if handle:
                                handle_match = self._match_handle_maker(handle)
                                if handle_match:
                                    m["handle_maker"] = handle_match["handle_maker"]
                                    m["handle_maker_metadata"] = {
                                        "_matched_by_section": handle_match["_matched_by_section"],
                                        "_pattern_used": handle_match["_pattern_used"],
                                    }

                            return self._post_process_match(
                                {
                                    "original": value,
                                    "matched": m,
                                    "match_type": result.get("match_type", "exact"),
                                    "pattern": result.get("pattern"),
                                },
                                value,
                            )
                        elif "brand" in result:
                            m = result
                            m["_matched_by_strategy"] = strategy.__class__.__name__
                            m["_pattern_used"] = result.get("_pattern_used", "unknown")
                            m["_matched_from"] = "knot_part"
                            m["_original_knot_text"] = knot
                            m["_original_handle_text"] = handle

                            # Add handle maker if we can identify it
                            if handle:
                                handle_match = self._match_handle_maker(handle)
                                if handle_match:
                                    m["handle_maker"] = handle_match["handle_maker"]
                                    m["handle_maker_metadata"] = {
                                        "_matched_by_section": handle_match["_matched_by_section"],
                                        "_pattern_used": handle_match["_pattern_used"],
                                    }

                            return self._post_process_match(
                                {
                                    "original": value,
                                    "matched": m,
                                    "match_type": m.get("source_type", "exact"),
                                    "pattern": m.get("_pattern_used", "unknown"),
                                },
                                value,
                            )

        # If we have handle and knot parts but handle should take precedence (e.g., "in" delimiter)
        elif handle and knot and not self._should_prioritize_knot(value):
            for strategy in self.strategies:
                if result := strategy.match(handle):
                    # Found a match for the handle part - this takes precedence
                    if isinstance(result, dict):
                        if "matched" in result and result.get("matched"):
                            m = result["matched"]
                            m["_matched_by_strategy"] = strategy.__class__.__name__
                            m["_pattern_used"] = result.get("pattern")
                            m["_matched_from"] = "handle_part"
                            m["_original_handle_text"] = handle
                            m["_original_knot_text"] = knot

                            return self._post_process_match(
                                {
                                    "original": value,
                                    "matched": m,
                                    "match_type": result.get("match_type", "exact"),
                                    "pattern": result.get("pattern"),
                                },
                                value,
                            )
                        elif "brand" in result:
                            m = result
                            m["_matched_by_strategy"] = strategy.__class__.__name__
                            m["_pattern_used"] = result.get("_pattern_used", "unknown")
                            m["_matched_from"] = "handle_part"
                            m["_original_handle_text"] = handle
                            m["_original_knot_text"] = knot

                            return self._post_process_match(
                                {
                                    "original": value,
                                    "matched": m,
                                    "match_type": m.get("source_type", "exact"),
                                    "pattern": m.get("_pattern_used", "unknown"),
                                },
                                value,
                            )

        # No knot/handle match found, proceed with normal full-text matching
        # Try each strategy in order
        for strategy in self.strategies:
            if result := strategy.match(value):
                # Handle different return formats from strategies
                if isinstance(result, dict):
                    # Check if it's already wrapped (new format)
                    if "matched" in result and result.get("matched"):
                        m = result["matched"]
                        m["_matched_by_strategy"] = strategy.__class__.__name__
                        m["_pattern_used"] = result.get("pattern")
                        # Fiber strategy
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
                            if m.get("fiber") and m["fiber"].lower() == user_fiber.lower():
                                m["fiber_strategy"] = "user_input"
                            elif m.get("fiber") and m["fiber"].lower() != user_fiber.lower():
                                m["fiber_conflict"] = user_fiber
                                m["fiber_strategy"] = "yaml"
                            else:
                                m["fiber"] = user_fiber
                                m["fiber_strategy"] = "user_input"
                        else:
                            if m.get("fiber_strategy") is None:
                                m["fiber_strategy"] = (
                                    "default" if "default" in value.lower() else "yaml"
                                )
                        # Knot size strategy
                        user_knot = None
                        knot_match = re.search(r"(\d{2})(?:\s*)mm", value.lower())
                        if knot_match:
                            user_knot = float(knot_match.group(1))
                        if user_knot:
                            if m.get("knot_size_mm") and abs(m["knot_size_mm"] - user_knot) < 0.1:
                                m["knot_size_strategy"] = "user_input"
                            elif (
                                m.get("knot_size_mm") and abs(m["knot_size_mm"] - user_knot) >= 0.1
                            ):
                                m["knot_size_conflict"] = user_knot
                                m["knot_size_strategy"] = "yaml"
                            else:
                                m["knot_size_mm"] = user_knot
                                m["knot_size_strategy"] = "user_input"
                        else:
                            if m.get("knot_size_strategy") is None:
                                m["knot_size_strategy"] = (
                                    "default" if "default" in value.lower() else "yaml"
                                )
                        # Handle/knot splitting
                        handle, _knot, _ = self._split_handle_and_knot(value)
                        if handle and not m.get("handle_maker"):
                            handle_match = self._match_handle_maker(handle)
                            if handle_match:
                                m["handle_maker"] = handle_match["handle_maker"]
                                m["handle_maker_metadata"] = {
                                    "_matched_by_section": handle_match["_matched_by_section"],
                                    "_pattern_used": handle_match["_pattern_used"],
                                }
                        enriched_result = self._post_process_match(
                            {
                                "original": value,
                                "matched": m,
                                "match_type": result.get("match_type", "exact"),
                                "pattern": result.get("pattern"),
                            },
                            value,
                        )
                        return enriched_result
                    # Handle direct result format (ChiselAndHound, OmegaSemogue, Zenith)
                    elif "brand" in result:
                        m = result
                        m["_matched_by_strategy"] = strategy.__class__.__name__
                        m["_pattern_used"] = result.get("_pattern_used", "unknown")
                        # Fiber strategy
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
                            if m.get("fiber") and m["fiber"].lower() == user_fiber.lower():
                                m["fiber_strategy"] = "user_input"
                            elif m.get("fiber") and m["fiber"].lower() != user_fiber.lower():
                                m["fiber_conflict"] = user_fiber
                                m["fiber_strategy"] = "yaml"
                            else:
                                m["fiber"] = user_fiber
                                m["fiber_strategy"] = "user_input"
                        else:
                            if m.get("fiber_strategy") is None:
                                m["fiber_strategy"] = (
                                    "default" if "default" in value.lower() else "yaml"
                                )
                        # Knot size strategy
                        user_knot = None
                        knot_match = re.search(r"(\d{2})(?:\s*)mm", value.lower())
                        if knot_match:
                            user_knot = float(knot_match.group(1))
                        if user_knot:
                            if m.get("knot_size_mm") and abs(m["knot_size_mm"] - user_knot) < 0.1:
                                m["knot_size_strategy"] = "user_input"
                            elif (
                                m.get("knot_size_mm") and abs(m["knot_size_mm"] - user_knot) >= 0.1
                            ):
                                m["knot_size_conflict"] = user_knot
                                m["knot_size_strategy"] = "yaml"
                            else:
                                m["knot_size_mm"] = user_knot
                                m["knot_size_strategy"] = "user_input"
                        else:
                            if m.get("knot_size_strategy") is None:
                                m["knot_size_strategy"] = (
                                    "default" if "default" in value.lower() else "yaml"
                                )
                        # Handle/knot splitting
                        handle, _knot, _ = self._split_handle_and_knot(value)
                        if handle and not m.get("handle_maker"):
                            handle_match = self._match_handle_maker(handle)
                            if handle_match:
                                m["handle_maker"] = handle_match["handle_maker"]
                                m["handle_maker_metadata"] = {
                                    "_matched_by_section": handle_match["_matched_by_section"],
                                    "_pattern_used": handle_match["_pattern_used"],
                                }
                        enriched_result = self._post_process_match(
                            {
                                "original": value,
                                "matched": m,
                                "match_type": m.get("source_type", "exact"),
                                "pattern": m.get("_pattern_used", "unknown"),
                            },
                            value,
                        )
                        return enriched_result

        # No match found
        return {"original": value, "matched": None, "match_type": None, "pattern": None}

    def _post_process_match(self, result: dict, value: str) -> dict:
        if not result.get("matched"):
            return result

        updated = result["matched"].copy()

        # Try to parse fiber and knot size from user input
        parsed_fiber = match_fiber(value)
        parsed_knot = None
        knot_match = re.search(r"(\d{2}(\.\d+)?)[\s-]*mm", value, re.IGNORECASE)
        if knot_match:
            parsed_knot = float(knot_match.group(1))

        # Handle fiber resolution priority (only if not already set by strategy)
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

        # Handle knot_size_mm resolution priority (only if not already set by strategy)
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

        # Extract handle_maker if not already set or is None
        if ("handle_maker" not in updated) or (updated["handle_maker"] is None):
            # Strategy 1: Try split-based parsing first (higher priority)
            handle, knot, _ = self._split_handle_and_knot(value)
            if handle:
                # Try to match the parsed handle part
                handle_match = self._match_handle_maker(handle)
                if handle_match:
                    updated["handle_maker"] = handle_match["handle_maker"]
                    updated["handle_maker_metadata"] = {
                        "_matched_by_section": handle_match["_matched_by_section"],
                        "_pattern_used": handle_match["_pattern_used"],
                        "_source_text": handle_match["_source_text"],
                    }
                else:
                    updated["handle_maker"] = handle
                    updated["handle_maker_metadata"] = {
                        "_matched_by_section": "split_fallback",
                        "_pattern_used": None,
                        "_source_text": handle,
                    }
                if knot:
                    updated["knot_maker"] = knot
            # Strategy 2: Fallback to full text matching (always try if handle_maker is still None)
            if ("handle_maker" not in updated) or (updated["handle_maker"] is None):
                handle_match = self._match_handle_maker(value)
                if handle_match:
                    updated["handle_maker"] = handle_match["handle_maker"]
                    updated["handle_maker_metadata"] = {
                        "_matched_by_section": handle_match["_matched_by_section"],
                        "_pattern_used": handle_match["_pattern_used"],
                        "_source_text": handle_match["_source_text"],
                    }

        result["matched"] = updated
        return result
