from pathlib import Path
from typing import Any, Dict, Optional

# import yaml  # unused
from sotd.match.brush_matching_strategies.known_brush_strategy import (
    KnownBrushMatchingStrategy,
)
from sotd.match.brush_matching_strategies.known_knot_strategy import KnownKnotMatchingStrategy
from sotd.match.brush_matching_strategies.omega_semogue_strategy import (
    OmegaSemogueBrushMatchingStrategy,
)
from sotd.match.brush_matching_strategies.other_brushes_strategy import (
    OtherBrushMatchingStrategy,
)
from sotd.match.brush_matching_strategies.other_knot_strategy import OtherKnotMatchingStrategy
from sotd.match.brush_matching_strategies.zenith_strategy import ZenithBrushMatchingStrategy
from sotd.match.brush_splitter_enhanced import EnhancedBrushSplitter
from sotd.match.cache import MatchCache
from sotd.match.config import BrushMatcherConfig
from sotd.match.correct_matches import CorrectMatchesChecker
from sotd.match.fiber_processor_enhanced import FiberProcessorEnhanced
from sotd.match.handle_matcher_enhanced import EnhancedHandleMatcher
from sotd.match.knot_matcher_enhanced import EnhancedKnotMatcher
from sotd.match.loaders import CatalogLoader
from sotd.match.types import MatchResult


class BrushMatcher:
    """
    Orchestrator for brush matching that coordinates specialized components.

    This class acts as a lightweight coordinator that delegates specific tasks
    to specialized components while maintaining the overall matching workflow.
    """

    def __init__(
        self,
        config: Optional[BrushMatcherConfig] = None,
        catalog_path: Optional[Path] = None,
        handles_path: Optional[Path] = None,
        knots_path: Optional[Path] = None,
        correct_matches_path: Optional[Path] = None,
        debug: Optional[bool] = None,
    ):
        # Handle backward compatibility: if config is None, create from individual parameters
        if config is None:
            config = BrushMatcherConfig.create_custom(
                catalog_path=catalog_path,
                handles_path=handles_path,
                knots_path=knots_path,
                correct_matches_path=correct_matches_path,
                debug=debug if debug is not None else False,
            )

        self.config = config
        self.catalog_path = config.catalog_path
        self.handles_path = config.handles_path
        self.knots_path = config.knots_path
        self.correct_matches_path = config.correct_matches_path
        self.debug = config.debug

        # Use CatalogLoader to load all catalog data
        self.catalog_loader = CatalogLoader(config)
        catalogs = self.catalog_loader.load_all_catalogs()
        self.catalog_data = catalogs["brushes"]
        self.knots_data = catalogs["knots"]
        self.correct_matches = catalogs["correct_matches"]

        # Initialize specialized components
        self.correct_matches_checker = CorrectMatchesChecker(config, self.correct_matches)
        self.handle_matcher = EnhancedHandleMatcher(config.handles_path)
        self.fiber_processor = FiberProcessorEnhanced()

        # Register brush strategies in order of preference:
        # 1. Known brushes (catalog-driven, highest priority)
        # 2. Brand-specific strategies (Omega/Semogue, Zenith) for uncataloged models
        # 3. Other brushes (generic fallback, lowest priority)
        self.brush_strategies = [
            KnownBrushMatchingStrategy(self.catalog_data.get("known_brushes", {})),
            OmegaSemogueBrushMatchingStrategy(),
            ZenithBrushMatchingStrategy(),
            OtherBrushMatchingStrategy(self.catalog_data.get("other_brushes", {})),
        ]
        # Add knot strategies from knots.yaml
        self.knot_strategies = [
            KnownKnotMatchingStrategy(self.knots_data.get("known_knots", {})),
            OtherKnotMatchingStrategy(self.knots_data.get("other_knots", {})),
        ]
        # For handle/knot matching, use both sets of strategies
        self.strategies = self.brush_strategies + self.knot_strategies
        self.knot_matcher = EnhancedKnotMatcher(self.strategies)
        self.brush_splitter = EnhancedBrushSplitter(self.handle_matcher, self.strategies)
        # Centralized cache for expensive operations
        self._cache = MatchCache(
            max_size=config.cache_max_size,
            enabled=config.cache_enabled,
        )

    def _check_correct_matches(self, value: str) -> Optional[Dict[str, Any]]:
        """
        Check if value matches any correct matches entry using canonical normalization.

        Returns match data if found, None otherwise.
        Supports both brush section (simple brushes) and handle/knot sections (combo brushes).
        """
        # Check cache first
        cache_key = f"correct_matches:{value}"
        cached = self._cache.get(cache_key)
        if cached is not None:
            return cached

        # Use the CorrectMatchesChecker component
        result = self.correct_matches_checker.check(value)

        # Convert CorrectMatchData to dictionary for backward compatibility
        if result is not None:
            result_dict = {
                "brand": result.brand,
                "model": result.model,
                "handle_maker": result.handle_maker,
                "handle_model": result.handle_model,
                "knot_info": result.knot_info,
                "match_type": result.match_type,
            }
            self._cache.set(cache_key, result_dict)
            return result_dict

        self._cache.set(cache_key, None)
        return None

    def _process_handle_knot_correct_match(
        self, value: str, correct_match: Dict[str, Any]
    ) -> "MatchResult":
        """
        Process correct match from handle/knot section for combo brushes.

        Returns MatchResult structure maintaining existing behavior.
        """
        handle_maker = correct_match.get("handle_maker")
        handle_model = correct_match.get("handle_model")
        knot_info = correct_match.get("knot_info", {})

        # Split the input to get the actual handle and knot text
        handle_text, knot_text, _ = self.brush_splitter.split_handle_and_knot(value)

        matched = {
            "brand": None,  # No top-level brand for handle/knot combos
            "model": None,  # No top-level model for handle/knot combos
            "fiber": None,  # Only in knot dict
            # No top-level handle_maker, knot_maker, knot_size_mm for combos
            "handle": (
                {
                    "brand": handle_maker,
                    "model": handle_model,
                    "source_text": handle_text,
                }
                if handle_maker or handle_model or handle_text
                else None
            ),
            "knot": (
                {
                    "brand": knot_info.get("brand"),
                    "model": knot_info.get("model"),
                    "fiber": knot_info.get("fiber"),
                    "knot_size_mm": knot_info.get("knot_size_mm"),
                    "source_text": knot_text,
                }
                if knot_info or knot_text
                else None
            ),
            "fiber_strategy": "yaml" if knot_info.get("fiber") else None,
            "_matched_by_strategy": "CorrectMatches",
            "_pattern_used": "correct_matches_handle_knot",
        }

        from sotd.match.types import create_match_result

        return create_match_result(
            original=value,
            matched=matched,
            match_type="exact",
            pattern=None,
        )

    def _process_brush_correct_match(
        self, value: str, correct_match: Dict[str, Any]
    ) -> "MatchResult":
        """
        Process correct match from brush section for simple brushes (backward compatibility).

        Returns MatchResult structure maintaining existing behavior.
        """
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

        matched = {"brand": brand, "model": model, "handle_maker": None}

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
            matched["knot_maker"] = catalog_entry.get("knot_maker", None) if catalog_entry else None
            # Set fiber_strategy to "yaml" if we have fiber data from catalog, otherwise None
            matched["fiber_strategy"] = (
                "yaml" if (catalog_entry and catalog_entry.get("fiber")) else None
            )

        # Handle nested handle structure
        if catalog_entry and "handle" in catalog_entry:
            handle_info = catalog_entry["handle"]
            matched["handle_maker"] = handle_info.get("brand")  # handle.brand becomes handle_maker

        # --- Inject handle/knot fields for split input ---
        handle, knot, _ = self.brush_splitter.split_handle_and_knot(value)
        if handle or knot:
            # Always include handle and knot fields for split input
            matched["handle"] = (
                {
                    "brand": matched.get("handle_maker"),
                    "model": None,
                    "source_text": handle,
                }
                if handle
                else None
            )
            matched["knot"] = (
                {
                    "brand": matched.get("knot_maker"),
                    "model": matched.get("model"),
                    "fiber": matched.get("fiber"),
                    "knot_size_mm": matched.get("knot_size_mm"),
                    "source_text": knot,
                }
                if knot
                else None
            )

        from sotd.match.types import create_match_result

        return create_match_result(
            original=value,
            matched=matched,
            match_type="exact",
            pattern=None,
        )

    def _get_normalized_text(self, value: str) -> str:
        """
        Return normalized text directly.

        Args:
            value: Normalized text string

        Returns:
            Normalized text string
        """
        return value

    def _get_original_text(self, value: str) -> str:
        """
        Return original text directly.

        Args:
            value: Original text string

        Returns:
            Original text string
        """
        return value

    def match(self, value: str, original: str | None = None) -> "MatchResult":
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
        # Use provided original text or default to normalized text
        original_text = original if original is not None else value
        normalized_text = value

        handle_maker_name = None
        knot_maker_name = None
        if not normalized_text:
            from sotd.match.types import create_match_result

            return create_match_result(
                original=original_text, matched=None, match_type=None, pattern=None
            )

        # Step 1: Check correct matches first (highest priority)
        correct_match = self._check_correct_matches(normalized_text)
        if correct_match:
            if correct_match.get("match_type") == "handle_knot_section":
                # Handle combo brush/handle brushes with handle/knot sections
                return self._process_handle_knot_correct_match(original_text, correct_match)
            else:
                # Handle simple brushes with brush section (backward compatibility)
                return self._process_brush_correct_match(original_text, correct_match)

        # Step 2: Split input into components
        handle, knot, _ = self.brush_splitter.split_handle_and_knot(normalized_text)
        # (No fallback dicts here)

        # Step 2.5: Compare makers if both handle and knot are present
        if handle and knot:
            handle_maker = self.handle_matcher.match_handle_maker(handle)
            # Find knot maker by trying all strategies
            knot_maker = None
            for strategy in self.strategies:
                result = strategy.match(knot)
                # Defensive: handle both MatchResult and dict
                if hasattr(result, "matched") and result.matched:
                    if "brand" in result.matched:
                        knot_maker = result.matched
                        break
                elif isinstance(result, dict) and result.get("matched"):
                    if "brand" in result["matched"]:
                        knot_maker = result["matched"]
                        break
            handle_maker_name = (
                handle_maker.get("brand")
                if handle_maker and "brand" in handle_maker
                else (
                    handle_maker.get("handle_maker")
                    if handle_maker and "handle_maker" in handle_maker
                    else None
                )
            )
            knot_maker_name = knot_maker["brand"] if knot_maker and "brand" in knot_maker else None
            if self.debug:
                print(
                    f"DEBUG: handle_maker_name={handle_maker_name}, "
                    f"knot_maker_name={knot_maker_name}"
                )
            norm_handle = (
                self._normalize_maker_name(handle_maker_name) if handle_maker_name else None
            )
            norm_knot = self._normalize_maker_name(knot_maker_name) if knot_maker_name else None
            if self.debug:
                print(f"DEBUG: norm_handle={norm_handle}, norm_knot={norm_knot}")
            # If both makers are present and the same, treat as a complete brush
            if handle_maker_name and knot_maker_name and norm_handle == norm_knot:
                # For same-maker combinations, create a complete brush result
                if self.debug:
                    print("DEBUG: Entered same-maker comparison block")
                normalized_maker = norm_handle
                from sotd.match.types import create_match_result

                result = create_match_result(
                    original=original_text,
                    matched={
                        "brand": normalized_maker,
                        "model": None,
                        "fiber": None,
                        "knot_size_mm": None,
                        "fiber_strategy": None,
                        "_matched_by_strategy": "MakerComparison",
                        "_pattern_used": "same_maker_comparison",
                    },
                    match_type="complete_brush",
                    pattern="same_maker_comparison",
                )
                if self.debug:
                    print(f"DEBUG: Constructed result: {result}")
                return self._post_process_match(result, original_text)

        # Step 3: Attempt priority-based matching
        if knot and self.knot_matcher.should_prioritize_knot(
            normalized_text, self.brush_splitter.split_handle_and_knot
        ):
            result = self.knot_matcher.match_knot_priority(
                normalized_text, handle, knot, self._extract_match_dict, self._post_process_match
            )
            if result and result.matched:
                # Update match type to REGEX for regex-based matches
                if result.match_type == "exact":
                    result.match_type = "regex"
                # Ensure required keys
                for k in ("brand", "model", "fiber", "knot_size_mm", "fiber_strategy"):
                    if k not in result.matched:
                        result.matched[k] = None
                return result
        elif (
            handle
            and knot
            and not self.knot_matcher.should_prioritize_knot(
                normalized_text, self.brush_splitter.split_handle_and_knot
            )
        ):
            result = self.knot_matcher.match_handle_priority(
                normalized_text, handle, knot, self._extract_match_dict, self._post_process_match
            )
            if result and result.matched:
                # Update match type to REGEX for regex-based matches
                if result.match_type == "exact":
                    result.match_type = "regex"
                # Ensure required keys
                for k in ("brand", "model", "fiber", "knot_size_mm", "fiber_strategy"):
                    if k not in result.matched:
                        result.matched[k] = None
                return result

        # Step 4: Fall back to main strategy matching
        result = self._match_main_strategies(normalized_text)
        if result and result.matched:
            for k in ("brand", "model", "fiber", "knot_size_mm", "fiber_strategy"):
                if k not in result.matched:
                    result.matched[k] = None
            return result

        # Ensure handle_maker_name and knot_maker_name are always defined
        if "handle_maker_name" not in locals():
            handle_maker_name = None
        if "knot_maker_name" not in locals():
            knot_maker_name = None

        # If both handle and knot are present but no makers found, return minimal structure
        if handle and knot:
            # Extract fiber and size from knot text even when maker is unknown
            fiber = self.fiber_processor.match_fiber(knot)
            knot_size_mm = None

            # Try to extract size from knot text
            import re

            size_match = re.search(r"(\d+)\s*mm", knot, re.IGNORECASE)
            if size_match:
                knot_size_mm = float(size_match.group(1))

            # Extract likely maker name from handle string (first word)
            handle_brand = None
            if handle_maker_name is None and handle:
                handle_brand = handle.split()[0]
            elif handle_maker_name:
                handle_brand = handle_maker_name

            from sotd.match.types import create_match_result

            minimal = create_match_result(
                original=original_text,
                matched={
                    "brand": None,
                    "model": None,
                    "fiber": fiber,
                    # No top-level handle_maker, knot_maker, knot_size_mm for combos
                    "handle": {
                        "brand": handle_brand,
                        "model": None,
                        "source_text": handle,
                    },
                    "knot": {
                        "brand": knot_maker_name,
                        "model": None,
                        "fiber": fiber,
                        "knot_size_mm": knot_size_mm,
                        "source_text": knot,
                    },
                    "fiber_strategy": None,
                    "_matched_by_strategy": "MinimalFallback",
                    "_pattern_used": None,
                },
                match_type=None,
                pattern=None,
            )
            return self._post_process_match(minimal, original_text)

        from sotd.match.types import create_match_result

        return create_match_result(
            original=original_text, matched=None, match_type=None, pattern=None
        )

    def _match_main_strategies(self, value: str) -> Optional["MatchResult"]:
        """Orchestrate matching using main brush strategies."""
        for strategy in self.strategies:
            result = strategy.match(value)
            # All strategies now return MatchResult objects
            if result.matched:
                m = self._extract_match_dict(result, strategy)
                if m:
                    self._enrich_match_result(value, m)
                    match_type = result.match_type or "exact"
                    # Update match type to REGEX for regex-based matches
                    if match_type == "exact":
                        match_type = "regex"
                    # Ensure knot_maker is set if brand is present
                    if m.get("brand") and not m.get("knot_maker"):
                        m["knot_maker"] = m["brand"]

                    from sotd.match.types import create_match_result

                    match_result = create_match_result(
                        original=value,
                        matched=m,
                        match_type=match_type,
                        pattern=result.pattern,
                    )
                    return self._post_process_match(match_result, value)
        return None

    def _extract_match_dict(
        self,
        result: MatchResult,
        strategy,
        matched_from: Optional[str] = None,
        handle: Optional[str] = None,
        knot: Optional[str] = None,
    ):
        """Extract and standardize match dictionary from strategy results."""
        if result.matched:
            m = result.matched.copy()
            m["_matched_by_strategy"] = strategy.__class__.__name__
            m["_pattern_used"] = result.pattern
            if matched_from:
                m["_matched_from"] = matched_from
                m["_original_knot_text"] = knot
                m["_original_handle_text"] = handle
                # For handle/knot combos, clear the brand/model (should be None)
                # But preserve the original values for subsections
                if matched_from in ["knot_part", "handle_part"]:
                    # Store the original model for subsections
                    m["_original_model"] = m.get("model")
                    # Clear top-level brand/model for handle/knot combos
                    m["brand"] = None
                    m["model"] = None
            # --- Begin nested knot/handle extraction ---
            # Try to extract nested knot/handle fields from the catalog entry if present
            brand = m.get("brand")
            model = m.get("model")

            # Only attempt if both are present
            if brand and model:
                # Check in known_brushes section first
                known_brushes_data = self.catalog_data.get("known_brushes", {})
                if brand in known_brushes_data:
                    brand_data = known_brushes_data[brand]
                    if brand_data and model in brand_data:
                        catalog_entry = brand_data[model]
                        # Extract knot info
                        if isinstance(catalog_entry, dict) and "knot" in catalog_entry:
                            knot_info = catalog_entry["knot"]
                            m["fiber"] = knot_info.get("fiber")
                            m["knot_size_mm"] = knot_info.get("knot_size_mm")
                            m["knot_maker"] = knot_info.get("brand")
                            m["fiber_strategy"] = (
                                "yaml" if knot_info.get("fiber") else m.get("fiber_strategy")
                            )
                        # Extract handle info
                        if isinstance(catalog_entry, dict) and "handle" in catalog_entry:
                            handle_info = catalog_entry["handle"]
                            m["handle_maker"] = handle_info.get("brand")
                        return m
                # Fallback to other_brushes section
                other_brushes_data = self.catalog_data.get("other_brushes", {})
                if brand in other_brushes_data:
                    brand_data = other_brushes_data[brand]
                    if brand_data and model in brand_data:
                        catalog_entry = brand_data[model]
                        # Extract knot info
                        if isinstance(catalog_entry, dict) and "knot" in catalog_entry:
                            knot_info = catalog_entry["knot"]
                            m["fiber"] = knot_info.get("fiber")
                            m["knot_size_mm"] = knot_info.get("knot_size_mm")
                            m["knot_maker"] = knot_info.get("brand")
                            m["fiber_strategy"] = (
                                "yaml" if knot_info.get("fiber") else m.get("fiber_strategy")
                            )
                        # Extract handle info
                        if isinstance(catalog_entry, dict) and "handle" in catalog_entry:
                            handle_info = catalog_entry["handle"]
                            m["handle_maker"] = handle_info.get("brand")
                        return m

            # --- Inject handle/knot fields for split input ---
            if matched_from in ["knot_part", "handle_part"]:
                # For handle/knot combos, always include handle and knot fields
                handle_text = handle
                knot_text = knot

                # Set handle brand - use handle_maker if available, otherwise try to match
                # handle_text
                handle_brand = None
                if m.get("handle_maker"):
                    handle_brand = m["handle_maker"]
                elif handle_text:
                    # Try to match the handle part using the handle matcher
                    handle_match = self.handle_matcher.match_handle_maker(handle_text)
                    if handle_match and handle_match.get("handle_maker"):
                        handle_brand = handle_match["handle_maker"]
                    else:
                        # Fall back to first word of handle text for unknown makers
                        handle_brand = handle_text.split()[0] if handle_text else None

                # Set knot brand - use knot_maker only.
                knot_brand = m.get("knot_maker")
                if not knot_brand and knot_text:
                    # Try to match the knot part using the available strategies
                    for strategy in self.strategies:
                        try:
                            knot_result = strategy.match(knot_text)
                            if not isinstance(knot_result, dict):
                                if hasattr(knot_result, "matched") and knot_result.matched:
                                    knot_brand = knot_result.matched.get("brand")
                                    break
                            else:
                                if knot_result.get("matched"):
                                    knot_brand = knot_result["matched"].get("brand")
                                    break
                        except Exception:
                            continue

                m["handle"] = (
                    {
                        "brand": handle_brand,
                        "model": m.get("_original_model") if handle_brand != knot_brand else None,
                        "source_text": handle_text,
                        "_matched_by_strategy": m.get("_matched_by_strategy"),
                        "_pattern_used": m.get("_pattern_used"),
                        "_matched_from": "handle_part",
                    }
                    if handle_text
                    else None
                )
                # Only set knot['model'] if a true model is matched (not just a fiber match)
                knot_model = m.get("_original_model")
                if knot_model and knot_model.lower() in ["boar", "badger", "synthetic"]:
                    knot_model = None
                m["knot"] = (
                    {
                        "brand": knot_brand,
                        "model": knot_model,
                        "fiber": m.get("fiber"),
                        "knot_size_mm": m.get("knot_size_mm"),
                        "source_text": knot_text,
                        "_matched_by_strategy": m.get("_matched_by_strategy"),
                        "_pattern_used": m.get("_pattern_used"),
                        "_matched_from": "knot_part",
                    }
                    if knot_text
                    else None
                )
                # Remove redundant top-level fields for all combos
                m.pop("handle_maker", None)
                m.pop("knot_maker", None)
            # --- End nested knot/handle extraction ---
            return m
        return None

    def _enrich_match_result(self, value: str, match_dict: dict) -> None:
        """Enrich match result with fiber and handle information."""
        # Check cache first
        cache_key = f"enrich:{value}"
        cached = self._cache.get(cache_key)
        if cached is not None:
            match_dict.update(cached)
            return

        # Process fiber information
        self.fiber_processor.process_fiber_info(value, match_dict)

        # Process handle information only for complete brushes (brand/model set)
        handle, _knot, _ = self.brush_splitter.split_handle_and_knot(value)
        if (
            handle
            and match_dict.get("brand") is not None
            and match_dict.get("model") is not None
            and not match_dict.get("handle_maker")
        ):
            handle_match = self.handle_matcher.match_handle_maker(handle)
            if handle_match:
                match_dict["handle_maker"] = handle_match["handle_maker"]
                match_dict["handle_maker_metadata"] = {
                    "_matched_by_section": handle_match["_matched_by_section"],
                    "_pattern_used": handle_match["_pattern_used"],
                }

        # Cache the enrichment result
        self._cache.set(
            cache_key,
            {
                "fiber": match_dict.get("fiber"),
                "handle_maker": (
                    match_dict.get("handle_maker")
                    if match_dict.get("brand") is not None and match_dict.get("model") is not None
                    else None
                ),
                "handle_maker_metadata": (
                    match_dict.get("handle_maker_metadata")
                    if match_dict.get("brand") is not None and match_dict.get("model") is not None
                    else None
                ),
            },
        )

    def _post_process_match(self, result: "MatchResult", value: str) -> "MatchResult":
        """Post-process match result with fiber and handle resolution."""
        # Check cache first
        cache_key = f"post_process:{value}"
        cached = self._cache.get(cache_key)
        if cached is not None:
            # Update the matched dict with cached data
            if result.matched:
                result.matched.update(cached)
            return result

        if not result.matched:
            return result

        # Create a copy of the matched dict for processing
        updated = result.matched.copy()

        # Resolve fiber information
        parsed_fiber = self.fiber_processor.match_fiber(value)
        self.fiber_processor.resolve_fiber(updated, parsed_fiber)

        # Add handle and knot subsections if we have split information
        # (This should be done before resolving makers to avoid conflicts)
        self._add_handle_knot_subsections(updated, value)

        # Resolve handle/knot maker only for complete brushes
        if updated.get("brand") is not None and updated.get("model") is not None:
            self._resolve_handle_maker(updated, value)
            self._resolve_knot_maker(updated, value)

        # Cache the post-processing result
        self._cache.set(
            cache_key,
            {
                "fiber": updated.get("fiber"),
                "handle_maker": (
                    updated.get("handle_maker")
                    if updated.get("brand") is not None and updated.get("model") is not None
                    else None
                ),
                "handle_maker_metadata": (
                    updated.get("handle_maker_metadata")
                    if updated.get("brand") is not None and updated.get("model") is not None
                    else None
                ),
                "handle": updated.get("handle"),
                "knot": updated.get("knot"),
            },
        )

        # Ensure all required fields are present
        required_fields = [
            "fiber",
            "knot_size_mm",
            "handle_maker",
            "knot_maker",
            "fiber_strategy",
            "_matched_by_strategy",
            "_pattern_used",
            "handle",
            "knot",
        ]
        for field in required_fields:
            if field not in updated:
                if field == "_matched_by_strategy":
                    updated[field] = "MinimalFallback"
                else:
                    updated[field] = None

        # Update the MatchResult with the processed data
        result.matched = updated
        return result

    def _add_handle_knot_subsections(self, updated: dict, value: str) -> None:
        """Add handle and knot subsections to the match result if available.

        - For known (catalog) brushes, preserve top-level brand/model even if
          handle/knot are present.
        - For dynamic/user combos (not found in catalog), clear top-level brand/model if both
          handle and knot are present.
        """
        # Prefer catalog-driven info if available
        brand = updated.get("brand")
        model = updated.get("model")
        catalog_entry = None
        if brand and model:
            # Check in the known_brushes section first
            known_brushes_data = self.catalog_data.get("known_brushes", {})
            if brand in known_brushes_data:
                brand_data = known_brushes_data[brand]
                if model in brand_data:
                    catalog_entry = brand_data[model]
            # Fallback to other_brushes section
            if not catalog_entry:
                other_brushes_data = self.catalog_data.get("other_brushes", {})
                if brand in other_brushes_data:
                    brand_data = other_brushes_data[brand]
                    if brand_data and model in brand_data:
                        catalog_entry = brand_data[model]
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
            # Extract fiber and knot_size_mm from nested knot info for top-level fields
            if knot_info.get("fiber") and not updated.get("fiber"):
                updated["fiber"] = knot_info["fiber"]
            if knot_info.get("knot_size_mm") and not updated.get("knot_size_mm"):
                updated["knot_size_mm"] = knot_info["knot_size_mm"]
            if knot_info.get("brand") and not updated.get("knot_maker"):
                updated["knot_maker"] = knot_info["brand"]
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
                updated["handle"] = {
                    "brand": handle_match["handle_maker"] if handle_match else None,
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
                            # Handle both MatchResult objects and dictionaries
                            if hasattr(result, "matched") and result.matched:
                                knot_match = result.matched
                                break
                            elif isinstance(result, dict) and result.get("matched"):
                                knot_match = result["matched"]
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
        # Clear top-level brand/model for handle/knot combos (different makers)
        # Only preserve brand/model for complete brushes (same maker or catalog-driven)
        if (
            updated.get("handle")
            and updated.get("knot")
            and catalog_entry is None
            and updated.get("_matched_by_strategy")
            not in ["MakerComparison", "KnownBrushMatchingStrategy"]
        ):
            updated["brand"] = None
            updated["model"] = None

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
        brand = (updated.get("brand") or "").strip()
        if brand:
            updated["handle_maker"] = brand
            return True
        return False

    def _resolve_knot_maker(self, updated: dict, value: str) -> None:
        """Resolve knot maker using multiple strategies."""
        if ("knot_maker" not in updated) or (updated["knot_maker"] is None):
            # For complete brushes, knot maker is often the same as the brand
            # But don't override if it's already been set from catalog
            brand = updated.get("brand")
            if brand and not updated.get("knot_maker"):
                updated["knot_maker"] = brand
            else:
                # Try to find knot maker from split text or full text
                knot_text = updated.get("_original_knot_text")
                if not knot_text:
                    _, knot_text, _ = self.brush_splitter.split_handle_and_knot(value)

                if knot_text:
                    # Try to match the knot against our strategies
                    for strategy in self.strategies:
                        try:
                            result = strategy.match(knot_text)
                            # Handle both MatchResult objects and dictionaries
                            if hasattr(result, "matched") and result.matched:
                                updated["knot_maker"] = result.matched.get("brand")
                                break
                            elif isinstance(result, dict) and result.get("matched"):
                                updated["knot_maker"] = result["matched"].get("brand")
                                break
                        except (AttributeError, KeyError, TypeError):
                            continue
                else:
                    updated["knot_maker"] = None

    def _normalize_maker_name(self, maker_name: str) -> str:
        """Normalize maker name for comparison by removing common suffixes."""
        if not maker_name:
            return ""

        # Remove common suffixes that don't affect maker identity
        normalized = maker_name
        suffixes_to_remove = [
            " (batch not specified)",
            " (batch unspecified)",
            " batch",
            " (default)",
        ]

        for suffix in suffixes_to_remove:
            if normalized.endswith(suffix):
                normalized = normalized[: -len(suffix)]
                break

        return normalized.strip()

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
