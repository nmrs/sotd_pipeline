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
    """
    Orchestrator for brush matching that coordinates specialized components.

    This class acts as a lightweight coordinator that delegates specific tasks
    to specialized components while maintaining the overall matching workflow.
    """

    def __init__(
        self,
        catalog_path: Path = Path("data/brushes.yaml"),
        handles_path: Path = Path("data/handles.yaml"),
    ):
        self.catalog_path = catalog_path
        self.handles_path = handles_path
        self.catalog_data = self._load_catalog(catalog_path)

        # Initialize specialized components
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

    def match(self, value: str) -> dict:
        """
        Main orchestration method for brush matching.

        Coordinates the matching workflow by:
        1. Splitting input into handle and knot components
        2. Determining matching priority based on delimiter semantics
        3. Attempting priority-based matching strategies
        4. Falling back to main strategy matching
        5. Post-processing results with fiber and handle information
        """
        if not value:
            return {"original": value, "matched": None, "match_type": None, "pattern": None}

        # Step 1: Split input into components
        handle, knot, _ = self.brush_splitter.split_handle_and_knot(value)

        # Step 2: Attempt priority-based matching
        if knot and self.knot_matcher.should_prioritize_knot(
            value, self.brush_splitter.split_handle_and_knot
        ):
            result = self.knot_matcher.match_knot_priority(
                value, handle, knot, self._extract_match_dict, self._post_process_match
            )
            if result:
                return result
        elif (
            handle
            and knot
            and not self.knot_matcher.should_prioritize_knot(
                value, self.brush_splitter.split_handle_and_knot
            )
        ):
            result = self.knot_matcher.match_handle_priority(
                value, handle, knot, self._extract_match_dict, self._post_process_match
            )
            if result:
                return result

        # Step 3: Fall back to main strategy matching
        result = self._match_main_strategies(value)
        if result:
            return result

        return {
            "original": value,
            "matched": None,
            "match_type": None,
            "pattern": None,
        }

    def _match_main_strategies(self, value: str) -> Optional[dict]:
        """Orchestrate matching using main brush strategies."""
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
        """Extract and standardize match dictionary from strategy results."""
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

    def _enrich_match_result(self, value: str, match_dict: dict) -> None:
        """Enrich match result with fiber and handle information."""
        # Process fiber information
        self.fiber_processor.process_fiber_info(value, match_dict)

        # Process handle information
        handle, _knot, _ = self.brush_splitter.split_handle_and_knot(value)
        if handle and not match_dict.get("handle_maker"):
            handle_match = self.handle_matcher.match_handle_maker(handle)
            if handle_match:
                match_dict["handle_maker"] = handle_match["handle_maker"]
                match_dict["handle_maker_metadata"] = {
                    "_matched_by_section": handle_match["_matched_by_section"],
                    "_pattern_used": handle_match["_pattern_used"],
                }

    def _post_process_match(self, result: dict, value: str) -> dict:
        """Post-process match result with fiber and handle resolution."""
        if not result.get("matched"):
            return result

        updated = result["matched"].copy()

        # Resolve fiber information
        parsed_fiber = self.fiber_processor.match_fiber(value)
        self.fiber_processor.resolve_fiber(updated, parsed_fiber)

        # Resolve handle maker information
        self._resolve_handle_maker(updated, value)

        result["matched"] = updated
        return result

    def _resolve_handle_maker(self, updated: dict, value: str) -> None:
        """Resolve handle maker using multiple strategies."""
        if ("handle_maker" not in updated) or (updated["handle_maker"] is None):
            # Try strategies in order of preference
            strategies = [
                self._try_handle_from_split_text,
                self._try_handle_from_full_text,
                self._try_handle_from_brand,
                self._try_handle_from_model,
            ]

            for strategy in strategies:
                if strategy(updated, value):
                    return

    def _try_handle_from_split_text(self, updated: dict, value: str) -> bool:
        """Try to find handle maker from split text components."""
        handle_text = updated.get("_original_handle_text")
        matched_from = updated.get("_matched_from")

        if handle_text and matched_from in ["knot_part", "handle_part"]:
            handle_match = self.handle_matcher.match_handle_maker(handle_text)
            if handle_match:
                updated["handle_maker"] = handle_match["handle_maker"]
                updated["handle_maker_metadata"] = {
                    "_matched_by_section": handle_match["_matched_by_section"],
                    "_pattern_used": handle_match["_pattern_used"],
                    "_source_text": handle_match["_source_text"],
                }
                return True
        return False

    def _try_handle_from_full_text(self, updated: dict, value: str) -> bool:
        """Try to find handle maker from full input text."""
        handle_match = self.handle_matcher.match_handle_maker(value)
        if handle_match:
            updated["handle_maker"] = handle_match["handle_maker"]
            updated["handle_maker_metadata"] = {
                "_matched_by_section": handle_match["_matched_by_section"],
                "_pattern_used": handle_match["_pattern_used"],
                "_source_text": handle_match["_source_text"],
            }
            return True
        return False

    def _try_handle_from_brand(self, updated: dict, value: str) -> bool:
        """Try to use brand as handle maker if it's known."""
        brand = updated.get("brand", "").strip()
        if brand and self.handle_matcher.is_known_handle_maker(brand):
            updated["handle_maker"] = brand
            return True
        return False

    def _try_handle_from_model(self, updated: dict, value: str) -> bool:
        """Try to extract handle maker from model field."""
        model = updated.get("model")
        if model and isinstance(model, str):
            model = model.strip()
            if model:
                model_handle_match = self.handle_matcher.match_handle_maker(model)
                if model_handle_match:
                    updated["handle_maker"] = model_handle_match["handle_maker"]
                    updated["handle_maker_metadata"] = {
                        "_matched_by_section": model_handle_match["_matched_by_section"],
                        "_pattern_used": model_handle_match["_pattern_used"],
                        "_source_text": model_handle_match["_source_text"],
                    }
                    return True
        return False
