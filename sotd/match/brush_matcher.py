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
        Process correct match from handle_knot_section for composite brushes.
        Returns MatchResult structure in the new unified format.
        """
        # Legacy fields
        handle_maker = correct_match.get("handle_maker")
        handle_model = correct_match.get("handle_model")
        knot_info = correct_match.get("knot_info", {})
        # Split the input to get the actual handle and knot text
        handle_text, knot_text, _ = self.brush_splitter.split_handle_and_knot(value)
        matched = {
            "brand": None,
            "model": None,
            "handle": {
                "brand": handle_maker,
                "model": handle_model,
                "source_text": handle_text,
                "_matched_by": "CorrectMatches",
                "_pattern": "correct_matches_handle_knot",
            },
            "knot": {
                "brand": knot_info.get("brand"),
                "model": knot_info.get("model"),
                "fiber": knot_info.get("fiber"),
                "knot_size_mm": knot_info.get("knot_size_mm"),
                "source_text": knot_text,
                "_matched_by": "CorrectMatches",
                "_pattern": "correct_matches_handle_knot",
            },
        }
        from sotd.match.types import create_match_result

        return create_match_result(
            original=value,
            matched=matched,
            match_type="exact",
            pattern=None,
        )

    def _process_regular_correct_match(
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

        matched = {"brand": brand, "model": model}

        # Handle nested knot and handle structures
        if catalog_entry and "knot" in catalog_entry:
            # Extract knot information from nested structure
            knot_info = catalog_entry["knot"]
            matched["fiber"] = knot_info.get("fiber")
            matched["knot_size_mm"] = knot_info.get("knot_size_mm")
            # Set fiber_strategy to "yaml" if we have fiber data from catalog
            matched["fiber_strategy"] = "yaml" if knot_info.get("fiber") else None
        else:
            # Fall back to direct catalog fields for backward compatibility
            matched["fiber"] = catalog_entry.get("fiber", None) if catalog_entry else None
            matched["knot_size_mm"] = (
                catalog_entry.get("knot_size_mm", None) if catalog_entry else None
            )
            # Set fiber_strategy to "yaml" if we have fiber data from catalog, otherwise None
            matched["fiber_strategy"] = (
                "yaml" if (catalog_entry and catalog_entry.get("fiber")) else None
            )

        # Handle nested handle structure
        handle_maker = None
        if catalog_entry and "handle" in catalog_entry:
            handle_info = catalog_entry["handle"]
            handle_maker = handle_info.get("brand")  # handle.brand becomes handle_maker

        # --- Inject handle/knot fields for split input ---
        handle, knot, _ = self.brush_splitter.split_handle_and_knot(value)
        if handle or knot:
            # Always include handle and knot fields for split input
            matched["handle"] = (
                {
                    "brand": handle_maker,
                    "model": None,
                    "source_text": handle,
                    "_matched_by": "CorrectMatches",
                    "_pattern": "correct_matches_brush",
                }
                if handle
                else None
            )
            matched["knot"] = (
                {
                    "brand": brand,  # For single-brand brushes, knot brand is same as brush brand
                    "model": matched.get("model"),
                    "fiber": matched.get("fiber"),
                    "knot_size_mm": matched.get("knot_size_mm"),
                    "source_text": knot,
                    "_matched_by": "CorrectMatches",
                    "_pattern": "correct_matches_brush",
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

    def match(self, value: str) -> Optional["MatchResult"]:
        """
        Match a brush string against all available strategies.
        Returns MatchResult or None if no match found.
        """
        if not value:
            return None

        # Check correct matches first
        correct_match = self.correct_matches_checker.check(value)
        if correct_match:
            # Convert CorrectMatchData to dict if needed
            if isinstance(correct_match, dict):
                correct_match_dict = correct_match
            else:
                # Convert to dict format
                correct_match_dict = {
                    "match_type": getattr(correct_match, "match_type", None),
                    "matched": getattr(correct_match, "matched", {}),
                    "handle_maker": getattr(correct_match, "handle_maker", None),
                    "handle_model": getattr(correct_match, "handle_model", None),
                    "knot_info": getattr(correct_match, "knot_info", {}),
                }

            if correct_match_dict.get("match_type") == "handle_knot_section":
                return self._process_handle_knot_correct_match(value, correct_match_dict)
            else:
                return self._process_regular_correct_match(value, correct_match_dict)

        # Step 1: Try splitting first (composite brush)
        handle_text, knot_text, delimiter_type = self.brush_splitter.split_handle_and_knot(value)
        if handle_text and knot_text:
            # Handle split result - create composite brush structure
            # Match handle and knot separately
            handle_match = self.handle_matcher.match_handle_maker(handle_text)
            knot_match = None

            # Try to match knot with strategies
            for strategy in self.strategies:
                try:
                    result = strategy.match(knot_text)
                    if result and hasattr(result, "matched") and result.matched:
                        knot_match = result
                        break
                except Exception:
                    continue

            matched = {
                "brand": None,  # Composite brush
                "model": None,  # Composite brush
                "handle": {
                    "brand": handle_match.get("handle_maker") if handle_match else None,
                    "model": handle_match.get("handle_model") if handle_match else None,
                    "source_text": handle_text,
                    "_matched_by": "HandleMatcher" if handle_match else "BrushSplitter",
                    "_pattern": "split",
                },
                "knot": {
                    "brand": knot_match.matched.get("brand") if knot_match else None,
                    "model": knot_match.matched.get("model") if knot_match else None,
                    "fiber": knot_match.matched.get("fiber") if knot_match else None,
                    "knot_size_mm": knot_match.matched.get("knot_size_mm") if knot_match else None,
                    "source_text": knot_text,
                    "_matched_by": "BrushSplitter",
                    "_pattern": "split",
                },
            }

            from sotd.match.types import create_match_result

            return create_match_result(
                original=value,
                matched=matched,
                match_type="regex",
                pattern="split",
            )

        # Step 2: Try complete brush matching (single-brand brushes) - only use brush strategies
        for strategy in self.brush_strategies:
            try:
                result = strategy.match(value)
                if result and hasattr(result, "matched") and result.matched:
                    # Extract match data and ensure consistent format
                    match_dict = self._extract_match_dict(result, strategy)

                    if match_dict is not None:
                        # Ensure handle/knot sections are consistent
                        self._ensure_handle_knot_sections(
                            match_dict,
                            strategy,
                            getattr(result, "pattern", None),
                            getattr(result, "matched_from", None),
                            getattr(result, "handle", None),
                            getattr(result, "knot", None),
                        )

                        # Enrich with additional data
                        self._enrich_match_result(match_dict, value)

                        # Post-process to ensure consistency
                        self._post_process_match(match_dict)

                        # Final cleanup: remove any redundant top-level fields
                        self._final_cleanup(match_dict)

                        from sotd.match.types import create_match_result

                        return create_match_result(
                            original=value,
                            matched=match_dict,
                            match_type="regex",
                            pattern=getattr(result, "pattern", None),
                        )
            except Exception as e:
                print(f"Strategy {strategy.__class__.__name__} failed: {e}")
                continue

        # Step 3: Try both knot and handle matching, pick higher score
        from sotd.match.brush_matching_strategies.utils.pattern_utils import score_match_type

        best_match = None
        best_score = -1
        best_match_type = None

        # Try knot matching
        for strategy in self.strategies:
            try:
                result = strategy.match(value)
                if result and hasattr(result, "matched") and result.matched:
                    score = score_match_type(value, "knot", 5)  # Base score for knot match
                    if score > best_score:
                        best_score = score
                        best_match = result
                        best_match_type = "knot"
            except Exception as e:
                print(f"Knot strategy {strategy.__class__.__name__} failed: {e}")
                continue

        # Try handle matching
        handle_match = self.handle_matcher.match_handle_maker(value)
        if handle_match and handle_match.get("handle_maker"):
            handle_score = score_match_type(value, "handle", 5)  # Base score for handle match
            if handle_score > best_score:
                best_score = handle_score
                # Create a proper MatchResult-like object for handle match
                from sotd.match.types import create_match_result

                best_match = create_match_result(
                    original=value,
                    matched={
                        "brand": handle_match["handle_maker"],
                        "model": None,
                        "source_text": value,
                        "_matched_by": "HandleMatcher",
                        "_pattern": handle_match.get("_pattern_used", "handle_matching"),
                    },
                    match_type="regex",
                    pattern="handle_matching",
                )
                best_match_type = "handle"

        if best_match:
            # Process the best match
            if best_match_type == "handle":
                # Handle-only match - create composite structure
                matched = {
                    "brand": None,  # Composite brush
                    "model": None,  # Composite brush
                    "handle": {
                        "brand": best_match.matched["brand"],
                        "model": None,
                        "source_text": value,
                        "_matched_by": "HandleMatcher",
                        "_pattern": best_match.matched["_pattern"],
                    },
                    "knot": {
                        "brand": None,  # No knot information
                        "model": None,
                        "fiber": None,
                        "knot_size_mm": None,
                        "source_text": value,
                        "_matched_by": "HandleMatcher",
                        "_pattern": "handle_only",
                    },
                }
            else:
                # Knot match - extract and process
                match_dict = self._extract_match_dict(best_match, None)
                if match_dict is not None:
                    self._ensure_handle_knot_sections(
                        match_dict, None, getattr(best_match, "pattern", None), None, None, None
                    )
                    self._enrich_match_result(match_dict, value)
                    self._post_process_match(match_dict)
                    self._final_cleanup(match_dict)
                    matched = match_dict
                else:
                    # Fallback if extraction fails
                    matched = {
                        "brand": best_match.matched.get("brand"),
                        "model": best_match.matched.get("model"),
                        "source_text": value,
                        "_matched_by": "Unknown",
                        "_pattern": getattr(best_match, "pattern", "unknown"),
                    }

            from sotd.match.types import create_match_result

            return create_match_result(
                original=value,
                matched=matched,
                match_type="regex",
                pattern=getattr(best_match, "pattern", "handle_matching"),
            )

        return None

    def _final_cleanup(self, match_dict: dict) -> None:
        """Remove any redundant top-level fields from the final output."""
        # Remove redundant top-level fields that should only be in handle/knot sections
        redundant_fields = {
            "_matched_by_strategy",
            "_pattern_used",
            "source_text",
            "knot_size_mm",
            "fiber",
            "handle_maker",
            "knot_maker",
            "_original_knot_text",
            "_original_handle_text",
            "fiber_strategy",
            "fiber_conflict",
            "_matched_from",
            "_original_model",
        }

        for field in redundant_fields:
            if field in match_dict:
                del match_dict[field]

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

            # Remove redundant fields immediately
            m.pop("handle_maker", None)
            m.pop("knot_maker", None)
            m.pop("_original_knot_text", None)
            m.pop("_original_handle_text", None)
            m.pop("_matched_from", None)
            m.pop("_original_model", None)
            m.pop("fiber_strategy", None)
            m.pop("fiber_conflict", None)

            # Remove top-level fiber (only keep in knot section)
            m.pop("fiber", None)

            # Always create handle and knot sections with consistent structure
            self._ensure_handle_knot_sections(
                m, strategy, result.pattern or "unknown", matched_from, handle, knot
            )

            return m
        return None

    def _ensure_handle_knot_sections(
        self,
        m: dict,
        strategy,
        pattern: Optional[str],
        matched_from: Optional[str],
        handle: Optional[str],
        knot: Optional[str],
    ):
        """Ensure all brushes have consistent handle and knot sections."""
        brand = m.get("brand")
        model = m.get("model")

        # For single-brand brushes, create handle and knot sections
        # But if the input contains "handle" keyword and no knot information,
        # treat as composite
        source_text = m.get("source_text", "").lower()
        is_handle_only = "handle" in source_text and not m.get("model")
        if brand and not matched_from and not is_handle_only:
            # Single-brand brush - both handle and knot are from same brand
            m["handle"] = {
                "brand": brand,
                "model": model,
                "source_text": m.get("source_text", ""),
                "_matched_by": strategy.__class__.__name__,
                "_pattern": pattern or "unknown",
            }

            # Use correct values for fiber and knot_size_mm from m if present
            fiber = m.get("fiber")
            knot_size_mm = m.get("knot_size_mm")
            # If fiber is None, try to get from catalog
            if fiber is None:
                # Look up catalog entry
                catalog_entry = None
                for section in ["known_brushes", "declaration_grooming", "other_brushes"]:
                    section_data = self.catalog_data.get(section, {})
                    if brand in section_data:
                        brand_data = section_data[brand]
                        if model in brand_data:
                            catalog_entry = brand_data[model]
                            break
                if catalog_entry:
                    if isinstance(catalog_entry, dict) and "knot" in catalog_entry:
                        fiber = catalog_entry["knot"].get("fiber")
                    else:
                        fiber = catalog_entry.get("fiber")

                # If still no fiber, check knots catalog for default fiber
                if fiber is None and brand in self.knots_data:
                    knot_entry = self.knots_data[brand]
                    if isinstance(knot_entry, dict) and "default" in knot_entry:
                        fiber = knot_entry["default"]
                        print(f"DEBUG: Found default fiber '{fiber}' for brand '{brand}'")
            m["knot"] = {
                "brand": brand,
                "model": model,
                "fiber": fiber,
                "knot_size_mm": knot_size_mm,
                "source_text": m.get("source_text", ""),
                "_matched_by": strategy.__class__.__name__,
                "_pattern": pattern or "unknown",
            }

        elif matched_from in ["knot_part", "handle_part"]:
            # Composite brush - handle and knot from different sources
            handle_text = handle or ""
            knot_text = knot or ""

            # Determine handle brand and matcher info
            handle_brand = None
            handle_matched_by = "Unknown"
            handle_pattern = "unknown"
            if handle_text:
                handle_match = self.handle_matcher.match_handle_maker(handle_text)
                if handle_match and handle_match.get("handle_maker"):
                    handle_brand = handle_match["handle_maker"]
                    handle_matched_by = handle_match.get("_matched_by_section")
                    handle_pattern = handle_match.get("_pattern_used")
                else:
                    # Fall back to first word of handle text for unknown makers
                    handle_brand = handle_text.split()[0] if handle_text else None
                    handle_matched_by = None
                    handle_pattern = None
            else:
                handle_matched_by = None
                handle_pattern = None
            # Always set _matched_by and _pattern to non-None values
            if not handle_matched_by:
                handle_matched_by = "HandleMatcher"
            if not handle_pattern:
                handle_pattern = "handle_matching"

            # Determine knot brand
            knot_brand = None
            if knot_text:
                # Try to match the knot part using the available strategies
                for knot_strategy in self.strategies:
                    try:
                        knot_result = knot_strategy.match(knot_text)
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

            # Always include _matched_by and _pattern fields for both handle and knot
            m["handle"] = {
                "brand": handle_brand,
                "model": None,  # Could be extracted if needed
                "source_text": handle_text,
            }
            m["handle"]["_matched_by"] = handle_matched_by
            m["handle"]["_pattern"] = handle_pattern
            print("DEBUG handle dict:", m["handle"])  # DEBUG

            m["knot"] = {
                "brand": knot_brand,
                "model": None,  # Could be extracted if needed
                "fiber": None,  # Will be set by enrich phase
                "knot_size_mm": None,  # Will be set by enrich phase
                "source_text": knot_text,
                "_matched_by": strategy.__class__.__name__ if knot_brand else "Unknown",
                "_pattern": pattern or "unknown",
            }

            # Clear top-level brand/model for composite brushes
            m["brand"] = None
            m["model"] = None

        else:
            # Fallback for other cases - create minimal sections
            m["handle"] = {
                "brand": brand,
                "model": model,
                "source_text": m.get("source_text", ""),
                "_matched_by": strategy.__class__.__name__,
                "_pattern": pattern or "unknown",
            }

            m["knot"] = {
                "brand": brand,
                "model": model,
                "fiber": None,  # Will be set by enrich phase
                "knot_size_mm": None,  # Will be set by enrich phase
                "source_text": m.get("source_text", ""),
                "_matched_by": strategy.__class__.__name__,
                "_pattern": pattern or "unknown",
            }

    def _enrich_match_result(self, match_dict: dict, value: str) -> None:
        """Enrich match result with additional data."""
        # Add source text
        match_dict["source_text"] = value

        # Add fiber information if not already present
        if "fiber" not in match_dict:
            match_dict["fiber"] = None

    def _post_process_match(self, match_dict: dict) -> None:
        """Post-process match to ensure consistency."""
        # Remove any top-level fiber fields that should only be in knot section
        if "fiber" in match_dict:
            del match_dict["fiber"]

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
