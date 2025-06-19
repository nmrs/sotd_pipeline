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
from sotd.match.brush_matching_strategies.zenith_strategy import (
    ZenithBrushMatchingStrategy,
)
from sotd.match.brush_splitter_enhanced import EnhancedBrushSplitter
from sotd.match.fiber_processor_enhanced import FiberProcessorEnhanced
from sotd.match.handle_matcher_enhanced import EnhancedHandleMatcher
from sotd.match.knot_matcher_enhanced import EnhancedKnotMatcher


class BrushMatcher:
    def __init__(
        self,
        catalog_path: Path = Path("data/brushes.yaml"),
        handles_path: Path = Path("data/handles.yaml"),
    ):
        self.catalog_path = catalog_path
        self.handles_path = handles_path
        self.catalog_data = self._load_catalog(catalog_path)
        self.handle_matcher = EnhancedHandleMatcher(handles_path)
        self.fiber_processor = FiberProcessorEnhanced()
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
        self.knot_matcher = EnhancedKnotMatcher(self.strategies)
        self.brush_splitter = EnhancedBrushSplitter(self.handle_matcher, self.strategies)

    def _load_catalog(self, catalog_path: Path) -> dict:
        """Load brush catalog from YAML file."""
        try:
            with catalog_path.open("r", encoding="utf-8") as f:
                return yaml.safe_load(f) or {}
        except (FileNotFoundError, yaml.YAMLError):
            return {}

    def _split_handle_and_knot(
        self, text: str
    ) -> tuple[Optional[str], Optional[str], Optional[str]]:
        """Split handle and knot using various delimiters and fiber detection."""
        return self.brush_splitter.split_handle_and_knot(text)

    def _should_prioritize_knot(self, text: str) -> bool:
        """Determine if knot maker should take precedence based on delimiter semantics."""
        return self.knot_matcher.should_prioritize_knot(text, self._split_handle_and_knot)

    def _is_known_handle_maker(self, brand: str) -> bool:
        """Check if a brand is primarily known as a handle maker."""
        return self.knot_matcher.is_known_handle_maker(brand)

    def _try_knot_maker_fallback(self, value: str, handle_result: dict) -> dict | None:
        """Try to find a knot maker when full-text matching found a handle maker."""
        return self.knot_matcher.try_knot_maker_fallback(value, handle_result)

    def _process_fiber_info(self, value: str, match_dict: dict) -> None:
        """Process fiber information from the input value and update match dictionary."""
        self.fiber_processor.process_fiber_info(value, match_dict)

    def _process_handle_info(self, value: str, match_dict: dict) -> None:
        """Process handle information from the input value and update match dictionary."""
        handle, _knot, _ = self._split_handle_and_knot(value)
        if handle and not match_dict.get("handle_maker"):
            handle_match = self.handle_matcher.match_handle_maker(handle)
            if handle_match:
                match_dict["handle_maker"] = handle_match["handle_maker"]
                match_dict["handle_maker_metadata"] = {
                    "_matched_by_section": handle_match["_matched_by_section"],
                    "_pattern_used": handle_match["_pattern_used"],
                }

    def _enrich_match_result(self, value: str, match_dict: dict) -> None:
        """Enrich match dictionary with additional information from the input value."""
        self._process_fiber_info(value, match_dict)
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
        return self.knot_matcher.match_knot_priority(
            value, handle, knot, self._extract_match_dict, self._post_process_match
        )

    def _match_handle_priority(
        self, value: str, handle: Optional[str], knot: Optional[str]
    ) -> Optional[dict]:
        return self.knot_matcher.match_handle_priority(
            value, handle, knot, self._extract_match_dict, self._post_process_match
        )

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

        # Parse fiber from user input
        parsed_fiber = self.fiber_processor.match_fiber(value)

        self._resolve_fiber(updated, parsed_fiber)
        self._resolve_handle_maker(updated, value)

        result["matched"] = updated
        return result

    def _resolve_fiber(self, updated: dict, parsed_fiber: str | None) -> None:
        """Resolve fiber information in the match result."""
        self.fiber_processor.resolve_fiber(updated, parsed_fiber)

    def _resolve_handle_maker(self, updated: dict, value: str) -> None:
        if ("handle_maker" not in updated) or (updated["handle_maker"] is None):
            # Check if we have knot matching information to help exclude knot text
            handle_text = updated.get("_original_handle_text")
            matched_from = updated.get("_matched_from")

            # Strategy 1: If we matched from a knot part, try to find handle in handle part first
            if matched_from == "knot_part" and handle_text:
                handle_match = self.handle_matcher.match_handle_maker(handle_text)
                if handle_match:
                    updated["handle_maker"] = handle_match["handle_maker"]
                    updated["handle_maker_metadata"] = {
                        "_matched_by_section": handle_match["_matched_by_section"],
                        "_pattern_used": handle_match["_pattern_used"],
                        "_source_text": handle_match["_source_text"],
                    }
                    return

            # Strategy 2: If we matched from a handle part, try to find handle in handle part
            if matched_from == "handle_part" and handle_text:
                handle_match = self.handle_matcher.match_handle_maker(handle_text)
                if handle_match:
                    updated["handle_maker"] = handle_match["handle_maker"]
                    updated["handle_maker_metadata"] = {
                        "_matched_by_section": handle_match["_matched_by_section"],
                        "_pattern_used": handle_match["_pattern_used"],
                        "_source_text": handle_match["_source_text"],
                    }
                    return

            # Strategy 3: Try to find handle in the full value
            handle_match = self.handle_matcher.match_handle_maker(value)
            if handle_match:
                updated["handle_maker"] = handle_match["handle_maker"]
                updated["handle_maker_metadata"] = {
                    "_matched_by_section": handle_match["_matched_by_section"],
                    "_pattern_used": handle_match["_pattern_used"],
                    "_source_text": handle_match["_source_text"],
                }
                return

            # Strategy 4: Check if brand is a known handle maker
            brand = updated.get("brand", "").strip()
            if brand and self.handle_matcher.is_known_handle_maker(brand):
                updated["handle_maker"] = brand
                return

            # Strategy 5: Try to extract handle from model field
            model = updated.get("model", "").strip()
            if model:
                model_handle_match = self.handle_matcher.match_handle_maker(model)
                if model_handle_match:
                    updated["handle_maker"] = model_handle_match["handle_maker"]
                    updated["handle_maker_metadata"] = {
                        "_matched_by_section": model_handle_match["_matched_by_section"],
                        "_pattern_used": model_handle_match["_pattern_used"],
                        "_source_text": model_handle_match["_source_text"],
                    }
                    return
