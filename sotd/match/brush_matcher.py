from pathlib import Path
from typing import Any, Dict, Optional

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
from sotd.utils.yaml_loader import load_yaml_with_nfc

from .base_matcher import MatchType


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
        correct_matches_path: Optional[Path] = None,
    ):
        self.catalog_path = catalog_path
        self.handles_path = handles_path
        self.correct_matches_path = correct_matches_path or Path("data/correct_matches.yaml")
        self.catalog_data = self._load_catalog(catalog_path)
        self.correct_matches = self._load_correct_matches()

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
        # Add cache for expensive operations
        self._match_cache = {}

    def _load_catalog(self, catalog_path: Path) -> dict:
        """Load brush catalog from YAML file."""
        try:
            with catalog_path.open("r", encoding="utf-8") as f:
                return yaml.safe_load(f) or {}
        except (FileNotFoundError, yaml.YAMLError):
            return {}

    def _load_correct_matches(self) -> Dict[str, Dict[str, Any]]:
        """Load correct matches for brush field from correct_matches.yaml (or injected path)."""
        if not self.correct_matches_path.exists():
            return {}

        try:
            data = load_yaml_with_nfc(self.correct_matches_path)
            return data.get("brush", {})
        except Exception:
            # If correct matches file is corrupted or can't be loaded, continue without it
            return {}

    def _check_correct_matches(self, value: str) -> Optional[Dict[str, Any]]:
        """
        Check if value matches any correct matches entry using canonical normalization.

        Returns match data if found, None otherwise.
        """
        # Check cache first
        cache_key = f"correct_matches:{value}"
        if cache_key in self._match_cache:
            return self._match_cache[cache_key]

        from sotd.utils.match_filter_utils import normalize_for_matching

        if not value or not self.correct_matches:
            self._match_cache[cache_key] = None
            return None

        # All correct match lookups must use normalize_for_matching
        # (see docs/product_matching_validation.md)
        normalized_value = normalize_for_matching(value, field="brush")
        if not normalized_value:
            self._match_cache[cache_key] = None
            return None

        # Search through correct matches structure
        for brand, brand_data in self.correct_matches.items():
            if not isinstance(brand_data, dict):
                continue

            for model, strings in brand_data.items():
                if not isinstance(strings, list):
                    continue

                # Check if normalized value matches any of the correct strings
                for correct_string in strings:
                    normalized_correct = normalize_for_matching(correct_string, field="brush")
                    if normalized_correct == normalized_value:
                        # Return match data in the expected format
                        result = {
                            "brand": brand,
                            "model": model,
                        }
                        self._match_cache[cache_key] = result
                        return result

        self._match_cache[cache_key] = None
        return None

    def match(self, value: str) -> dict:
        """
        Main orchestration method for brush matching.

        Coordinates the matching workflow by:
        1. Check correct matches first (highest priority)
        2. Splitting input into handle and knot components
        3. Determining matching priority based on delimiter semantics
        4. Attempting priority-based matching strategies
        5. Falling back to main strategy matching
        6. Post-processing results with fiber and handle information
        """
        if not value:
            return {"original": value, "matched": None, "match_type": None, "pattern": None}

        # Step 1: Check correct matches first (highest priority)
        correct_match = self._check_correct_matches(value)
        if correct_match:
            # Merge in all catalog fields if available
            brand = correct_match["brand"]
            model = correct_match["model"]

            # Search for catalog entry in different sections
            catalog_entry = None
            for section in ["known_brushes", "declaration_grooming", "other_brushes"]:
                section_data = self.catalog_data.get(section, {})
                if brand in section_data:
                    brand_data = section_data[brand]
                    if model in brand_data:
                        catalog_entry = brand_data[model]
                        break

            matched = {"brand": brand, "model": model}

            # Handle nested knot and handle structures
            if catalog_entry and "knot" in catalog_entry:
                # Extract knot information from nested structure
                knot_info = catalog_entry["knot"]
                matched["fiber"] = knot_info.get("fiber")
                matched["knot_size_mm"] = knot_info.get("knot_size_mm")
                matched["knot_maker"] = knot_info.get("brand")  # knot.brand becomes knot_maker
                # Set fiber_strategy to "yaml" if we have fiber data from catalog
                matched["fiber_strategy"] = "yaml" if knot_info.get("fiber") else None
            else:
                # Fall back to direct catalog fields for backward compatibility
                matched["fiber"] = catalog_entry.get("fiber", None) if catalog_entry else None
                matched["knot_size_mm"] = (
                    catalog_entry.get("knot_size_mm", None) if catalog_entry else None
                )
                matched["knot_maker"] = (
                    catalog_entry.get("knot_maker", None) if catalog_entry else None
                )
                # Set fiber_strategy to "yaml" if we have fiber data from catalog, otherwise None
                matched["fiber_strategy"] = (
                    "yaml" if (catalog_entry and catalog_entry.get("fiber")) else None
                )

            # Handle nested handle structure
            if catalog_entry and "handle" in catalog_entry:
                handle_info = catalog_entry["handle"]
                matched["handle_maker"] = handle_info.get(
                    "brand"
                )  # handle.brand becomes handle_maker

            return {
                "original": value,
                "matched": matched,
                "match_type": "exact",
                "pattern": None,
            }

        # Step 2: Split input into components
        handle, knot, _ = self.brush_splitter.split_handle_and_knot(value)

        # Step 3: Attempt priority-based matching
        if knot and self.knot_matcher.should_prioritize_knot(
            value, self.brush_splitter.split_handle_and_knot
        ):
            result = self.knot_matcher.match_knot_priority(
                value, handle, knot, self._extract_match_dict, self._post_process_match
            )
            if result:
                # Update match type to REGEX for regex-based matches
                if result.get("match_type") == "exact":
                    result["match_type"] = "regex"
                # Ensure required keys
                for k in ("brand", "model", "fiber", "knot_size_mm", "fiber_strategy"):
                    if k not in result["matched"]:
                        result["matched"][k] = None
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
                # Update match type to REGEX for regex-based matches
                if result.get("match_type") == "exact":
                    result["match_type"] = "regex"
                # Ensure required keys
                for k in ("brand", "model", "fiber", "knot_size_mm", "fiber_strategy"):
                    if k not in result["matched"]:
                        result["matched"][k] = None
                return result

        # Step 4: Fall back to main strategy matching
        result = self._match_main_strategies(value)
        if result and result.get("matched"):
            for k in ("brand", "model", "fiber", "knot_size_mm", "fiber_strategy"):
                if k not in result["matched"]:
                    result["matched"][k] = None
            return result

        return {
            "original": value,
            "matched": None,
            "match_type": None,  # Keep None for backward compatibility
            "pattern": None,
        }

    def _match_main_strategies(self, value: str) -> Optional[dict]:
        """Orchestrate matching using main brush strategies."""
        for strategy in self.strategies:
            if result := strategy.match(value):
                m = self._extract_match_dict(result, strategy)
                if m:
                    self._enrich_match_result(value, m)
                    match_type = (
                        result.get("match_type", "exact")
                        if isinstance(result, dict)
                        else m.get("source_type", "exact")
                    )
                    # Update match type to REGEX for regex-based matches
                    if match_type == "exact":
                        match_type = MatchType.REGEX
                    return self._post_process_match(
                        {
                            "original": value,
                            "matched": m,
                            "match_type": match_type,
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
                # --- Begin nested knot/handle extraction ---
                # Try to extract nested knot/handle fields from the catalog entry if present
                brand = m.get("brand")
                model = m.get("model")
                # Only attempt if both are present
                if brand and model:
                    for section in ["known_brushes", "declaration_grooming", "other_brushes"]:
                        section_data = self.catalog_data.get(section, {})
                        if brand in section_data:
                            brand_data = section_data[brand]
                            if model in brand_data:
                                catalog_entry = brand_data[model]
                                # Extract knot info
                                if isinstance(catalog_entry, dict) and "knot" in catalog_entry:
                                    knot_info = catalog_entry["knot"]
                                    m["fiber"] = knot_info.get("fiber")
                                    m["knot_size_mm"] = knot_info.get("knot_size_mm")
                                    m["knot_maker"] = knot_info.get("brand")
                                    m["fiber_strategy"] = (
                                        "yaml"
                                        if knot_info.get("fiber")
                                        else m.get("fiber_strategy")
                                    )
                                # Extract handle info
                                if isinstance(catalog_entry, dict) and "handle" in catalog_entry:
                                    handle_info = catalog_entry["handle"]
                                    m["handle_maker"] = handle_info.get("brand")
                                break
                # --- End nested knot/handle extraction ---
                return m
            if "brand" in result:
                m = result
                m["_matched_by_strategy"] = strategy.__class__.__name__
                m["_pattern_used"] = result.get("_pattern_used", "unknown")
                if matched_from:
                    m["_matched_from"] = matched_from
                    m["_original_knot_text"] = knot
                    m["_original_handle_text"] = handle
                # --- Begin nested knot/handle extraction (brand/model dict case) ---
                brand = m.get("brand")
                model = m.get("model")
                if brand and model:
                    for section in ["known_brushes", "declaration_grooming", "other_brushes"]:
                        section_data = self.catalog_data.get(section, {})
                        if brand in section_data:
                            brand_data = section_data[brand]
                            if model in brand_data:
                                catalog_entry = brand_data[model]
                                if isinstance(catalog_entry, dict) and "knot" in catalog_entry:
                                    knot_info = catalog_entry["knot"]
                                    m["fiber"] = knot_info.get("fiber")
                                    m["knot_size_mm"] = knot_info.get("knot_size_mm")
                                    m["knot_maker"] = knot_info.get("brand")
                                    m["fiber_strategy"] = (
                                        "yaml"
                                        if knot_info.get("fiber")
                                        else m.get("fiber_strategy")
                                    )
                                if isinstance(catalog_entry, dict) and "handle" in catalog_entry:
                                    handle_info = catalog_entry["handle"]
                                    m["handle_maker"] = handle_info.get("brand")
                                break
                # --- End nested knot/handle extraction ---
                return m
        return None

    def _enrich_match_result(self, value: str, match_dict: dict) -> None:
        """Enrich match result with fiber and handle information."""
        # Check cache first
        cache_key = f"enrich:{value}"
        if cache_key in self._match_cache:
            cached_result = self._match_cache[cache_key]
            match_dict.update(cached_result)
            return

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

        # Cache the enrichment result
        self._match_cache[cache_key] = {
            "fiber": match_dict.get("fiber"),
            "handle_maker": match_dict.get("handle_maker"),
            "handle_maker_metadata": match_dict.get("handle_maker_metadata"),
        }

    def _post_process_match(self, result: dict, value: str) -> dict:
        """Post-process match result with fiber and handle resolution."""
        # Check cache first
        cache_key = f"post_process:{value}"
        if cache_key in self._match_cache:
            cached_result = self._match_cache[cache_key]
            result["matched"].update(cached_result)
            return result

        if not result.get("matched"):
            return result

        updated = result["matched"].copy()

        # Resolve fiber information
        parsed_fiber = self.fiber_processor.match_fiber(value)
        self.fiber_processor.resolve_fiber(updated, parsed_fiber)

        # Resolve handle maker information
        self._resolve_handle_maker(updated, value)

        # Add handle and knot subsections if we have split information
        self._add_handle_knot_subsections(updated, value)

        # Cache the post-processing result
        self._match_cache[cache_key] = {
            "fiber": updated.get("fiber"),
            "handle_maker": updated.get("handle_maker"),
            "handle_maker_metadata": updated.get("handle_maker_metadata"),
            "handle": updated.get("handle"),
            "knot": updated.get("knot"),
        }

        result["matched"] = updated
        return result

    def _add_handle_knot_subsections(self, updated: dict, value: str) -> None:
        """Add handle and knot subsections to the match result if available."""
        # Prefer catalog-driven info if available
        brand = updated.get("brand")
        model = updated.get("model")
        catalog_entry = None
        if brand and model:
            for section in ["known_brushes", "declaration_grooming", "other_brushes"]:
                section_data = self.catalog_data.get(section, {})
                if brand in section_data:
                    brand_data = section_data[brand]
                    if model in brand_data:
                        catalog_entry = brand_data[model]
                        break
        # Handle subsection from catalog
        if catalog_entry and isinstance(catalog_entry, dict) and "handle" in catalog_entry:
            handle_info = catalog_entry["handle"]
            updated["handle"] = {
                "brand": handle_info.get("brand"),
                "model": handle_info.get("model"),
                "source_text": value,  # Catalog-driven, so use full input
            }
        # Knot subsection from catalog
        if catalog_entry and isinstance(catalog_entry, dict) and "knot" in catalog_entry:
            knot_info = catalog_entry["knot"]
            updated["knot"] = {
                "brand": knot_info.get("brand"),
                "model": knot_info.get("model"),
                "fiber": knot_info.get("fiber"),
                "knot_size_mm": knot_info.get("knot_size_mm"),
                "source_text": value,  # Catalog-driven, so use full input
            }
        # If not present in catalog, fall back to split/strategy logic
        if ("handle" not in updated) or (updated["handle"] is None):
            # Get the original split information if available
            handle_text = updated.get("_original_handle_text")
            knot_text = updated.get("_original_knot_text")
            # If we don't have split text, try to split now
            if not handle_text and not knot_text:
                handle_text, knot_text, _ = self.brush_splitter.split_handle_and_knot(value)
            # Add handle subsection if we have handle information
            if handle_text:
                handle_match = self.handle_matcher.match_handle_maker(handle_text)
                if handle_match:
                    updated["handle"] = {
                        "brand": handle_match["handle_maker"],
                        "model": None,  # Could be extracted from handle_text if needed
                        "source_text": handle_text,
                    }
        if ("knot" not in updated) or (updated["knot"] is None):
            if not ("knot" in updated and updated["knot"]):
                knot_text = updated.get("_original_knot_text")
                if not knot_text:
                    _, knot_text, _ = self.brush_splitter.split_handle_and_knot(value)
                if knot_text:
                    # Try to match the knot against our strategies
                    knot_match = None
                    for strategy in self.strategies:
                        try:
                            result = strategy.match(knot_text)
                            if result and (
                                (isinstance(result, dict) and result.get("matched"))
                                or (isinstance(result, dict) and result.get("brand"))
                            ):
                                if isinstance(result, dict) and result.get("matched"):
                                    knot_match = result["matched"]
                                elif isinstance(result, dict) and result.get("brand"):
                                    knot_match = result
                                break
                        except (AttributeError, KeyError, TypeError):
                            continue
                    if knot_match:
                        updated["knot"] = {
                            "brand": knot_match.get("brand"),
                            "model": knot_match.get("model"),
                            "fiber": knot_match.get("fiber"),
                            "knot_size_mm": knot_match.get("knot_size_mm"),
                            "source_text": knot_text,
                        }
                    else:
                        updated["knot"] = {
                            "brand": None,
                            "model": None,
                            "fiber": None,
                            "knot_size_mm": None,
                            "source_text": knot_text,
                        }

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
