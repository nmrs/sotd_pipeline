import re
from pathlib import Path
from typing import Any, Dict, Optional

from sotd.match.brush_matching_strategies.fiber_fallback_strategy import FiberFallbackStrategy
from sotd.match.brush_matching_strategies.knot_size_fallback_strategy import (
    KnotSizeFallbackStrategy,
)

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
from sotd.match.brush_splits_loader import BrushSplitsLoader
from sotd.match.brush_splitter import BrushSplitter
from sotd.match.cache import MatchCache
from sotd.match.config import BrushMatcherConfig
from sotd.match.correct_matches import CorrectMatchesChecker
from sotd.match.fiber_processor import FiberProcessor
from sotd.match.handle_matcher import HandleMatcher
from sotd.match.knot_matcher import KnotMatcher
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

        # DEBUG: Print correct_matches_path and loaded correct_matches
        if self.debug:
            print(f"[BrushMatcher DEBUG] correct_matches_path: {self.correct_matches_path}")
            print(f"[BrushMatcher DEBUG] loaded correct_matches: {self.correct_matches}")

        # Initialize specialized components
        self.correct_matches_checker = CorrectMatchesChecker(config, self.correct_matches)
        self.handle_matcher = HandleMatcher(config.handles_path)
        self.fiber_processor = FiberProcessor()

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
            FiberFallbackStrategy(),  # After existing strategies
            KnotSizeFallbackStrategy(),  # After FiberFallbackStrategy
        ]
        # For handle/knot matching, use both sets of strategies
        self.strategies = self.brush_strategies + self.knot_strategies
        self.knot_matcher = KnotMatcher(self.knot_strategies)
        self.brush_splitter = BrushSplitter(self.handle_matcher, self.strategies)
        # Centralized cache for expensive operations
        self._cache = MatchCache(
            max_size=config.cache_max_size,
            enabled=config.cache_enabled,
        )

        # Load human-curated brush splits
        self.brush_splits_loader = BrushSplitsLoader()

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
            result_dict = {}
            if hasattr(result, "brand"):
                result_dict["brand"] = result.brand
            if hasattr(result, "model"):
                result_dict["model"] = result.model
            if hasattr(result, "handle_maker"):
                result_dict["handle_maker"] = result.handle_maker
            if hasattr(result, "handle_model"):
                result_dict["handle_model"] = result.handle_model
            if hasattr(result, "knot_info"):
                result_dict["knot_info"] = result.knot_info
            result_dict["match_type"] = result.match_type
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
        # Handle both CorrectMatchData objects and dictionaries
        if hasattr(correct_match, "brand"):
            # It's a CorrectMatchData object
            brand = correct_match.brand
            model = correct_match.model
        else:
            # It's a dictionary
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

        # For simple brushes, create unified format with nested sections AND preserve top-level
        # fields
        matched = {
            "brand": brand,  # Top-level brand for simple brushes
            "model": model,  # Top-level model for simple brushes
            "handle": {
                "brand": brand,  # Handle brand is the brush brand
                "model": model,  # Handle model is the brush model
                "source_text": value,  # Full text as source
                "_matched_by": "CorrectMatches",
                "_pattern": "correct_matches_brush",
            },
            "knot": {
                "brand": brand,  # Knot brand is the brush brand
                "model": model,  # Knot model is the brush model
                "fiber": None,  # Will be populated from catalog if available
                "knot_size_mm": None,  # Will be populated from catalog if available
                "source_text": value,  # Full text as source
                "_matched_by": "CorrectMatches",
                "_pattern": "correct_matches_brush",
            },
        }

        # Populate fiber and knot_size_mm from catalog if available
        if catalog_entry:
            if "knot" in catalog_entry:
                # Extract knot information from nested structure
                knot_info = catalog_entry["knot"]
                matched["knot"]["fiber"] = knot_info.get("fiber")
                matched["knot"]["knot_size_mm"] = knot_info.get("knot_size_mm")
            else:
                # Fall back to direct catalog fields for backward compatibility
                matched["knot"]["fiber"] = catalog_entry.get("fiber")
                matched["knot"]["knot_size_mm"] = catalog_entry.get("knot_size_mm")

        # Handle nested handle structure for handle maker
        if catalog_entry and "handle" in catalog_entry:
            handle_info = catalog_entry["handle"]
            handle_maker = handle_info.get("brand")  # handle.brand becomes handle_maker
            if handle_maker:
                matched["handle"]["brand"] = handle_maker

        from sotd.match.types import create_match_result

        result = create_match_result(
            original=value,
            matched=matched,
            match_type="exact",
            pattern=None,
        )

        # Apply complete brush handle matching if enabled
        if correct_match.get("handle_match_enabled", False):
            self._complete_brush_handle_matching(matched, value)

        return result

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

    def _process_split_brush_correct_match(
        self, value: str, correct_match: Dict[str, Any]
    ) -> "MatchResult":
        """
        Process correct match from split_brush section for split brushes.
        Returns MatchResult structure in the new unified format.
        """
        # Get handle and knot components from the split brush mapping
        # Handle both CorrectMatchData objects and raw split data dictionaries
        if hasattr(correct_match, "handle_component"):
            # CorrectMatchData object
            handle_component = correct_match.handle_component
            knot_component = correct_match.knot_component
        else:
            # Raw split data dictionary
            handle_component = correct_match.get("handle")
            knot_component = correct_match.get("knot")

        # Look up handle component in handle section
        handle_match = None
        if handle_component:
            handle_correct_match = self.correct_matches_checker.check(handle_component)
            if handle_correct_match:
                handle_match = {
                    "handle_maker": handle_correct_match.handle_maker,
                    "handle_model": handle_correct_match.handle_model,
                    "_matched_by": "CorrectMatches",
                    "_pattern": "correct_matches_handle",
                }
            else:
                # Fall back to handle matcher
                handle_match = self.handle_matcher.match_handle_maker(handle_component)

        # Look up knot component in knot section
        knot_match = None
        if knot_component:
            knot_correct_match = self.correct_matches_checker.check(knot_component)
            if knot_correct_match:
                # Extract knot info safely
                knot_info = knot_correct_match.knot_info or {}
                knot_match = {
                    "brand": knot_info.get("brand"),
                    "model": knot_info.get("model"),
                    "fiber": knot_info.get("fiber"),
                    "knot_size_mm": knot_info.get("knot_size_mm"),
                    "_matched_by": "CorrectMatches",
                    "_pattern": "correct_matches_knot",
                }
            else:
                # Fall back to knot matcher strategies
                for strategy in self.strategies:
                    try:
                        result = strategy.match(knot_component)
                        if result and hasattr(result, "matched") and result.matched:
                            knot_match = result.matched
                            break
                    except Exception:
                        continue

        # Create unified format with nested sections
        matched = {
            "brand": None,  # Split brushes have no top-level brand
            "model": None,  # Split brushes have no top-level model
            "handle": {
                "brand": handle_match.get("handle_maker") if handle_match else None,
                "model": handle_match.get("handle_model") if handle_match else None,
                "source_text": handle_component,
                "_matched_by": "CorrectMatches",
                "_pattern": "correct_matches_split_brush",
            },
            "knot": {
                "brand": knot_match.get("brand") if knot_match else None,
                "model": knot_match.get("model") if knot_match else None,
                "fiber": knot_match.get("fiber") if knot_match else None,
                "knot_size_mm": knot_match.get("knot_size_mm") if knot_match else None,
                "source_text": knot_component,
                "_matched_by": "CorrectMatches",
                "_pattern": "correct_matches_split_brush",
            },
        }

        from sotd.match.types import create_match_result

        return create_match_result(
            original=value,
            matched=matched,
            match_type="exact",
            pattern="correct_matches_split_brush",
        )

    def match(self, value: str) -> Optional["MatchResult"]:
        """
        Match a brush string against all available strategies.
        Returns MatchResult or None if no match found.
        """
        if not value:
            return None

        # Handle case where value might be a dict (from correct_matches.yaml structure)
        if isinstance(value, dict):
            # Extract the key (brush name) from the dictionary
            brush_name = list(value.keys())[0]
            value = brush_name

        # Define strategies in priority order
        strategies = [
            self._match_correct_complete_brush,
            self._match_correct_split_brush,
            self._match_known_split,
            self._match_high_priority_automated_split,
            self._match_complete_brush,
            self._match_dual_component,
            self._match_medium_priority_automated_split,
            self._match_single_component_fallback,
        ]

        # Try each strategy in order
        for strategy in strategies:
            result = strategy(value)
            if result is not None:
                return result

        return None

    def _match_correct_complete_brush(self, value: str) -> Optional["MatchResult"]:
        """Strategy 1: Check brush section in correct_matches.yaml (fastest)."""
        normalized_text = value.lower().strip()
        brush_correct_matches = self.correct_matches_checker.correct_matches.get("brush", {})

        # Check if this is a known brush (exact match)
        for brand, brand_data in brush_correct_matches.items():
            for model, patterns in brand_data.items():
                # Check if normalized_text matches any pattern (handle both strings and dicts)
                pattern_matched = False
                handle_match_enabled = False

                for pattern in patterns:
                    if isinstance(pattern, dict):
                        # Dictionary with handle_match flag
                        pattern_text = list(pattern.keys())[0]  # Get the key
                        if normalized_text == pattern_text:
                            pattern_matched = True
                            handle_match_enabled = pattern[pattern_text].get("handle_match", False)
                            break
                    else:
                        # Simple string pattern
                        if normalized_text == pattern:
                            pattern_matched = True
                            break

                if pattern_matched:
                    return self._process_regular_correct_match(
                        value,
                        {
                            "match_type": "brush_section",
                            "brand": brand,
                            "model": model,
                            "matched": {"brand": brand, "model": model},
                            "handle_match_enabled": handle_match_enabled,
                        },
                    )
        return None

    def _match_correct_split_brush(self, value: str) -> Optional["MatchResult"]:
        """Strategy 2: Check split_brush section in correct_matches.yaml (fast lookup)."""
        normalized_text = value.lower().strip()
        split_brush_correct_matches = self.correct_matches_checker.correct_matches.get(
            "split_brush", {}
        )
        if normalized_text in split_brush_correct_matches:
            split_data = split_brush_correct_matches[normalized_text]
            return self._process_split_brush_correct_match(
                value,
                {
                    "match_type": "split_brush_section",
                    "handle": split_data.get("handle", ""),
                    "knot": split_data.get("knot", ""),
                },
            )
        return None

    def _match_known_split(self, value: str) -> Optional["MatchResult"]:
        """Strategy 3: Check other correct matches sections."""
        correct_match = self.correct_matches_checker.check(value)
        if correct_match:
            # Convert CorrectMatchData to dict if needed
            if isinstance(correct_match, dict):
                correct_match_dict = correct_match
            else:
                # Convert to dict format
                correct_match_dict = {
                    "match_type": getattr(correct_match, "match_type", None),
                    "brand": getattr(correct_match, "brand", None),
                    "model": getattr(correct_match, "model", None),
                    "matched": getattr(correct_match, "matched", {}),
                    "handle_maker": getattr(correct_match, "handle_maker", None),
                    "handle_model": getattr(correct_match, "handle_model", None),
                    "knot_info": getattr(correct_match, "knot_info", {}),
                    "handle_component": getattr(correct_match, "handle_component", None),
                    "knot_component": getattr(correct_match, "knot_component", None),
                }

            if correct_match_dict.get("match_type") == "split_brush_section":
                return self._process_split_brush_correct_match(value, correct_match_dict)
            elif correct_match_dict.get("match_type") == "handle_knot_section":
                return self._process_handle_knot_correct_match(value, correct_match_dict)
            else:
                return self._process_regular_correct_match(value, correct_match_dict)
        return None

    def _match_high_priority_automated_split(self, value: str) -> Optional["MatchResult"]:
        """Strategy 4: Check brush_splits.yaml and high-priority automated splitting."""
        # Check if this brush should not be split (human-curated decision)
        if self.brush_splits_loader.should_not_split(value):
            # Treat as complete brush, skip splitting
            handle_text, knot_text, delimiter_type = None, None, None
        else:
            # Check human-curated brush splits first (highest priority)
            curated_split = self.brush_splits_loader.get_handle_and_knot(value)
            if curated_split:
                handle_text, knot_text = curated_split
                delimiter_type = "curated_split"
            else:
                # Try automated splitting with high-priority delimiters only
                handle_text, knot_text, delimiter_type = self._try_high_priority_splitting(value)

        if handle_text and knot_text:
            return self._process_split_result(handle_text, knot_text, delimiter_type, value)
        return None

    def _match_complete_brush(self, value: str) -> Optional["MatchResult"]:
        """Strategy 5: Try complete brush matching strategies."""
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

                        # Apply complete brush handle matching
                        self._complete_brush_handle_matching(match_dict, value)

                        from sotd.match.types import create_match_result

                        return create_match_result(
                            original=value,
                            matched=match_dict,
                            match_type="regex",
                            pattern=getattr(result, "pattern", None),
                        )
            except Exception as e:
                # Only print strategy failures in debug mode or for unexpected errors
                if self.debug or "Handle matching failed" not in str(e):
                    print(f"Strategy {strategy.__class__.__name__} failed: {e}")
                continue
        return None

    def _match_dual_component(self, value: str) -> Optional["MatchResult"]:
        """Strategy 6: Try dual component matching (both handle and knot)."""
        dual_result = self._try_dual_component_match(value)
        if dual_result is not None:
            handle_match, knot_match = dual_result

            # Detect user intent based on component order in original string
            handle_text = handle_match.get("handle_maker", "") if handle_match else ""
            knot_text = (
                knot_match.matched.get("model", "") if knot_match and knot_match.matched else ""
            )
            user_intent = self.detect_user_intent(value, handle_text, knot_text)

            # Create dual component result
            result = self.create_dual_component_result(handle_match, knot_match, value, user_intent)
            return result
        return None

    def _match_medium_priority_automated_split(self, value: str) -> Optional["MatchResult"]:
        """Strategy 7: Try medium-priority automated splitting."""
        # Try automated splitting with medium-priority delimiters
        handle_text, knot_text, delimiter_type = self._try_medium_priority_splitting(value)

        if handle_text and knot_text:
            return self._process_split_result(handle_text, knot_text, delimiter_type, value)
        return None

    def _match_single_component_fallback(self, value: str) -> Optional["MatchResult"]:
        """Strategy 8: Try single component fallback (handle or knot only)."""
        from sotd.match.brush_matching_strategies.utils.pattern_utils import score_match_type

        best_match = None
        best_score = -1
        best_match_type = None

        # Try knot matching
        for strategy in self.strategies:
            try:
                result = strategy.match(value)
                if result and hasattr(result, "matched") and result.matched:
                    score = score_match_type(
                        value,
                        "knot",
                        5,
                        knot_matcher=self.knot_matcher,
                        handle_matcher=self.handle_matcher,
                    )  # Base score for knot match
                    if score > best_score:
                        best_score = score
                        best_match = result
                        best_match_type = "knot"
            except Exception as e:
                # Only print strategy failures in debug mode or for unexpected errors
                if self.debug or "Handle matching failed" not in str(e):
                    print(f"Knot strategy {strategy.__class__.__name__} failed: {e}")
                continue

        # Try handle matching
        handle_match = self.handle_matcher.match_handle_maker(value)
        if handle_match and handle_match.get("handle_maker"):
            handle_score = score_match_type(
                value,
                "handle",
                5,
                knot_matcher=self.knot_matcher,
                handle_matcher=self.handle_matcher,
            )  # Base score for handle match
            if handle_score > best_score:
                best_score = handle_score
                # Create a proper MatchResult-like object for handle match
                from sotd.match.types import create_match_result

                best_match = create_match_result(
                    original=value,
                    matched={
                        "brand": handle_match["handle_maker"],
                        "model": handle_match.get("handle_model"),
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
                # Knot-only match - create composite structure
                matched = {
                    "brand": None,  # Composite brush
                    "model": None,  # Composite brush
                    "handle": {
                        "brand": None,  # No handle information
                        "model": None,
                        "source_text": value,
                        "_matched_by": "KnotMatcher",
                        "_pattern": "knot_only",
                    },
                    "knot": {
                        "brand": best_match.matched.get("brand"),
                        "model": best_match.matched.get("model"),
                        "fiber": best_match.matched.get("fiber"),
                        "knot_size_mm": best_match.matched.get("knot_size_mm"),
                        "source_text": value,
                        "_matched_by": best_match.matched.get(
                            "_matched_by_strategy", "KnotMatcher"
                        ),
                        "_pattern": best_match.matched.get(
                            "_pattern_used", best_match.pattern or "knot_only"
                        ),
                    },
                }

            from sotd.match.types import create_match_result

            # Use the pattern from the best match if available
            overall_pattern = (
                best_match.pattern
                if best_match and best_match.pattern
                else "single_component_fallback"
            )
            return create_match_result(
                original=value,
                matched=matched,
                match_type="regex",
                pattern=overall_pattern,
            )
        # No match found - return MatchResult with matched=None
        from sotd.match.types import create_match_result

        return create_match_result(
            original=value,
            matched=None,
            match_type=None,
            pattern=None,
        )

    def _try_high_priority_splitting(
        self, value: str
    ) -> tuple[Optional[str], Optional[str], Optional[str]]:
        """Try splitting with high-priority delimiters only."""
        # Use the brush splitter's logic instead of duplicating it
        return self.brush_splitter._split_by_high_priority_delimiters(value)

    def _try_medium_priority_splitting(
        self, value: str
    ) -> tuple[Optional[str], Optional[str], Optional[str]]:
        """Try splitting with medium-priority delimiters only."""
        # Extract medium-priority delimiter logic from brush splitter
        medium_reliability_delimiters = [" - ", " + "]

        for delimiter in medium_reliability_delimiters:
            if delimiter in value:
                return self._split_by_delimiter_smart(value, delimiter, "smart_analysis")

        return None, None, None

    def _split_by_delimiter_simple(
        self, text: str, delimiter: str, delimiter_type: str
    ) -> tuple[Optional[str], Optional[str], Optional[str]]:
        """Simple splitting for high-reliability delimiters."""
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
                if part1_handle_score > part2_handle_score and part2_knot_score > part1_knot_score:
                    return part1, part2, delimiter_type
                elif (
                    part2_handle_score > part1_handle_score and part1_knot_score > part2_knot_score
                ):
                    return part2, part1, delimiter_type
                else:
                    # Fall back to handle score comparison
                    if part1_handle_score > part2_handle_score:
                        return part1, part2, delimiter_type
                    else:
                        return part2, part1, delimiter_type
        return None, None, None

    def _split_by_delimiter_positional(
        self, text: str, delimiter: str, delimiter_type: str
    ) -> tuple[Optional[str], Optional[str], Optional[str]]:
        """Positional splitting for handle-primary delimiters."""
        parts = text.split(delimiter, 1)
        if len(parts) == 2:
            handle = parts[0].strip()
            knot = parts[1].strip()
            if handle and knot:
                return handle, knot, delimiter_type
        return None, None, None

    def _split_by_delimiter_smart(
        self, text: str, delimiter: str, delimiter_type: str
    ) -> tuple[Optional[str], Optional[str], Optional[str]]:
        """Smart splitting for medium-priority delimiters."""
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

            # Score the split
            score = self._score_split(part1, part2)
            if score > best_score:
                best_score = score
                best_split = (part1, part2)

        if best_split:
            return best_split[0], best_split[1], delimiter_type
        return None, None, None

    def _score_split(self, handle: str, knot: str) -> float:
        """Score a handle/knot split based on content analysis."""
        handle_score = self._score_as_handle(handle)
        knot_score = self._score_as_knot(knot)
        return handle_score + knot_score

    def _score_as_handle(self, text: str) -> int:
        """Score text as a handle component using actual matcher results with priority."""
        score = 0

        # Check for handle indicators
        if "handle" in text.lower():
            score += 10

        # Check if it matches handle patterns using the actual handle matcher
        handle_result = self.handle_matcher.match(text)
        if handle_result and handle_result.matched:
            # Base score for successful handle match
            score += 20

            # Use priority information for scoring (lower priority = higher score)
            if handle_result.has_section_info:
                # Priority 1 (artisan_handles) = highest score
                # Priority 2 (manufacturer_handles) = medium score
                # Priority 3 (other_handles) = lowest score
                if handle_result.priority == 1:
                    score += 15  # Artisan handles get highest bonus
                elif handle_result.priority == 2:
                    score += 10  # Manufacturer handles get medium bonus
                elif handle_result.priority == 3:
                    score += 5  # Other handles get lowest bonus
            else:
                # Fallback for backward compatibility
                score += 10

        # Check for handle-related terms
        handle_terms = ["stock", "custom", "artisan", "turned"]
        for term in handle_terms:
            if term in text.lower():
                score += 2

        # Check for handle model patterns (like "Zebra", "Jeffington", etc.)
        handle_model_patterns = [r"\b(zebra|jeffington|washington|bulldog)\b", r"\b(handle|grip)\b"]
        for pattern in handle_model_patterns:
            if re.search(pattern, text.lower()):
                score += 5

        return score

    def _score_as_knot(self, text: str) -> int:
        """Score text as a knot component using actual matcher results with priority."""
        score = 0

        # Check for fiber types
        fiber_types = ["badger", "boar", "synthetic"]
        for fiber in fiber_types:
            if fiber in text.lower():
                score += 8

        # Check if it matches knot patterns using the actual knot matcher
        knot_result = self.knot_matcher.match(text)
        if knot_result and knot_result.matched:
            # Base score for successful knot match
            score += 20

            # Use priority information for scoring (lower priority = higher score)
            if knot_result.has_section_info:
                # Priority 1 (known_knots) = highest score
                # Priority 2 (other_knots) = medium score
                # Priority 3+ (fallback strategies) = lowest score
                if knot_result.priority == 1:
                    score += 15  # Known knots get highest bonus
                elif knot_result.priority == 2:
                    score += 10  # Other knots get medium bonus
                else:
                    score += 5  # Fallback strategies get lowest bonus
            else:
                # Fallback for backward compatibility
                score += 10

        # Check for size patterns
        if re.search(r"\d+mm", text):
            score += 6

        # Check for versioning patterns
        if re.search(r"[vV]\d+", text):
            score += 6

        # Check for knot model patterns (B15, B16, etc.)
        if re.search(r"\bB(?:[1-8]|9[ab]|1[0-8])\b", text):
            score += 12  # High score for knot model patterns

        return score

    def _process_split_result(
        self, handle_text: str, knot_text: str, delimiter_type: str, value: str
    ) -> Optional["MatchResult"]:
        """Process a split result into a MatchResult."""
        # Check correct matches for handle component first
        handle_correct_match = self.correct_matches_checker.check(handle_text)
        if handle_correct_match:
            # Use correct match for handle
            handle_match = {
                "handle_maker": handle_correct_match.handle_maker,
                "handle_model": handle_correct_match.handle_model,
                "_matched_by": "CorrectMatches",
                "_pattern": "correct_matches_handle",
            }
        else:
            # Fall back to handle matcher
            handle_match = self.handle_matcher.match_handle_maker(handle_text)

        # Check correct matches for knot component first
        knot_correct_match = self.correct_matches_checker.check(knot_text)
        if knot_correct_match:
            # Use correct match for knot
            from sotd.match.types import create_match_result

            # Extract knot info safely
            knot_info = knot_correct_match.knot_info or {}
            knot_match = create_match_result(
                original=knot_text,
                matched={
                    "brand": knot_info.get("brand"),
                    "model": knot_info.get("model"),
                    "fiber": knot_info.get("fiber"),
                    "knot_size_mm": knot_info.get("knot_size_mm"),
                    "_matched_by": "CorrectMatches",
                    "_pattern": "correct_matches_knot",
                },
                match_type="exact",
                pattern="correct_matches_knot",
            )
        else:
            # Fall back to knot matcher using unified MatchResult structure
            knot_match = self.knot_matcher.match(knot_text)
            # Debug: Print knot match info
            if knot_match:
                print(
                    f"DEBUG: Knot match from unified matcher: "
                    f"{knot_match.section}, {knot_match.priority}, {knot_match.pattern}"
                )
            else:
                print(f"DEBUG: No knot match from unified matcher for: {knot_text}")

        # If no knot match found, check if it's a generic knot reference
        if not knot_match and knot_text:
            # Check if knot text contains the same brand as the handle
            handle_brand = handle_match.get("handle_maker") if handle_match else None
            if handle_brand and handle_brand.lower() in knot_text.lower():
                # Generic knot reference - create a synthetic match
                from sotd.match.types import create_match_result

                knot_match = create_match_result(
                    original=knot_text,
                    matched={
                        "brand": handle_brand,
                        "model": None,  # Generic knot, no specific model
                        "fiber": None,
                        "knot_size_mm": None,
                        "source_text": knot_text,
                        "_matched_by": "GenericKnotReference",
                        "_pattern": "generic_knot",
                    },
                    match_type="regex",
                    pattern="generic_knot",
                )

        # Get actual patterns from individual matchers
        handle_pattern = handle_match.get("_pattern_used") if handle_match else "split"
        knot_pattern = knot_match.pattern if knot_match else "split"

        matched = {
            "brand": None,  # Composite brush
            "model": None,  # Composite brush
            "handle": {
                "brand": handle_match.get("handle_maker") if handle_match else None,
                "model": handle_match.get("handle_model") if handle_match else None,
                "source_text": handle_text,
                "_matched_by": "HandleMatcher" if handle_match else "BrushSplitter",
                "_pattern": handle_pattern,
            },
            "knot": {
                "brand": (
                    knot_match.matched.get("brand") if knot_match and knot_match.matched else None
                ),
                "model": (
                    knot_match.matched.get("model") if knot_match and knot_match.matched else None
                ),
                "fiber": (
                    knot_match.matched.get("fiber") if knot_match and knot_match.matched else None
                ),
                "knot_size_mm": (
                    knot_match.matched.get("knot_size_mm")
                    if knot_match and knot_match.matched
                    else None
                ),
                "source_text": knot_text,
                "_matched_by": "BrushSplitter",
                "_pattern": knot_pattern,
            },
        }

        # Apply the same fallback logic for unmatched handles
        if not handle_match and handle_text:
            # Extract the brand from handle_text if no match found
            handle_words = handle_text.lower().split()
            if "handle" in handle_words:
                handle_words.remove("handle")
            if handle_words:
                # Use the first word as the brand (e.g., "UnknownMaker")
                matched["handle"]["brand"] = handle_text.split()[0]  # Use original case
                matched["handle"]["_matched_by"] = "BrushSplitter"

        # Extract model from handle text if not provided by handle matcher
        if not matched["handle"]["model"] and handle_text:
            matched["handle"]["model"] = self._extract_model_from_handle_text(handle_text)

        # Check if both handle and knot are from the same maker
        if self._is_same_maker_split(matched["handle"]["brand"], matched["knot"]["brand"]):
            # Same maker - treat as complete brush with shared brand but no global model
            matched["brand"] = matched["handle"]["brand"]
            matched["model"] = None  # No global model for composite brushes

        from sotd.match.types import create_match_result

        return create_match_result(
            original=value,
            matched=matched,
            match_type="regex",
            pattern="split",
        )

    def _final_cleanup(self, match_dict: dict) -> None:
        """Remove any redundant top-level fields from the final output."""
        # Remove redundant top-level fields that should only be in handle/knot sections
        redundant_fields = {
            "_matched_by_strategy",
            "_pattern_used",
            "source_text",
            "knot_size_mm",
            "fiber",
            # Don't remove brand/model for simple brushes - they should be preserved
            "handle_maker",  # Remove redundant handle_maker field
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

    def _complete_brush_handle_matching(self, match_dict: dict, value: str) -> None:
        """
        Apply complete brush handle matching to enhance brush matches with handle information.

        This method checks if a complete brush match has handle_matching enabled and attempts
        to match the handle on the full brush text using the brush brand's handle patterns.

        Args:
            match_dict: The brush match result dictionary to enhance
            value: The original brush text being matched
        """
        # Only apply to complete brushes (where "model" is set at top level)
        if not match_dict or "model" not in match_dict:
            return

        # Get the brush brand and model
        brand = match_dict.get("brand")
        model = match_dict.get("model")

        if not brand or not model:
            return

        # Check if handle_matching is enabled for this brush
        handle_matching_enabled = self._is_handle_matching_enabled(brand, model)
        if not handle_matching_enabled:
            return

        # Attempt handle matching on the full brush text
        try:
            handle_match = self._attempt_handle_matching_for_brand(value, brand)
            if handle_match:
                # Replace the handle section with the new handle match
                match_dict["handle"] = handle_match
        except Exception as e:
            # Fail fast with exception for debugging
            error_msg = (
                f"Handle matching failed for brush '{value}' ({brand} {model}) - "
                f"attempted handle text '{value}' did not match any handle patterns"
            )
            raise ValueError(error_msg) from e

    def _is_handle_matching_enabled(self, brand: str, model: str) -> bool:
        """
        Check if handle_matching is enabled for the given brand and model.

        Implements hierarchical logic: brand-level setting applies to all models unless
        overridden at model level. Model-level setting overrides brand-level setting.

        Args:
            brand: The brush brand
            model: The brush model

        Returns:
            True if handle_matching is enabled, False otherwise
        """
        # Check known_brushes first
        known_brushes = self.catalog_data.get("known_brushes", {})
        if brand in known_brushes:
            brand_data = known_brushes[brand]

            # Check model-level setting first (overrides brand-level)
            if model in brand_data:
                model_data = brand_data[model]
                if "handle_matching" in model_data:
                    return bool(model_data["handle_matching"])

            # Check brand-level setting
            if "handle_matching" in brand_data:
                return bool(brand_data["handle_matching"])

        # Check other_brushes
        other_brushes = self.catalog_data.get("other_brushes", {})
        if brand in other_brushes:
            brand_data = other_brushes[brand]

            # Check model-level setting first (overrides brand-level)
            if model in brand_data:
                model_data = brand_data[model]
                if "handle_matching" in model_data:
                    return bool(model_data["handle_matching"])

            # Check brand-level setting
            if "handle_matching" in brand_data:
                return bool(brand_data["handle_matching"])

        # Default to False if not specified
        return False

    def _attempt_handle_matching_for_brand(
        self, value: str, brand: str
    ) -> Optional[Dict[str, Any]]:
        """
        Attempt handle matching on the full brush text using only the brush brand's handle patterns.

        Args:
            value: The full brush text to match against
            brand: The brush brand to get handle patterns for

        Returns:
            Handle match dictionary if found, None otherwise

        Raises:
            ValueError: If handle matching fails (no patterns match)
        """
        # Get handle patterns for this specific brand
        handle_patterns = self._get_handle_patterns_for_brand(brand)
        if not handle_patterns:
            raise ValueError(f"No handle patterns found for brand: {brand}")

        # Try to match against each pattern
        for pattern_info in handle_patterns:
            pattern = pattern_info["pattern"]
            match_data = pattern_info["match_data"]

            # Use case-insensitive matching
            if pattern.search(value.lower()):
                return {
                    "brand": match_data.get("brand"),
                    "model": match_data.get("model"),
                    "source_text": value,
                    "_matched_by": "HandleMatchingStrategy",
                    "_pattern": pattern_info["original_pattern"],
                }

        # No match found
        raise ValueError(f"No handle patterns matched for brand: {brand}")

    def _get_handle_patterns_for_brand(self, brand: str) -> list[dict]:
        """
        Get handle patterns for a specific brand from the handles catalog.

        Args:
            brand: The brand to get handle patterns for

        Returns:
            List of pattern dictionaries with compiled patterns and match data
        """
        import re

        patterns = []
        handles_data = self.catalog_loader.load_catalog(self.handles_path, "handles")

        # Search through all handle sections for the brand
        for section_name, section_data in handles_data.items():
            if section_data and brand in section_data:
                brand_data = section_data[brand]
                if not brand_data:
                    continue

                # Get all models for this brand
                for model_name, model_data in brand_data.items():
                    if not model_data:
                        continue

                    if model_name == "Unspecified":
                        # Handle unspecified models
                        for pattern in model_data.get("patterns", []):
                            patterns.append(
                                {
                                    "pattern": re.compile(pattern, re.IGNORECASE),
                                    "original_pattern": pattern,
                                    "match_data": {
                                        "brand": brand,
                                        "model": model_name,
                                    },
                                }
                            )
                    else:
                        # Handle specific models
                        for pattern in model_data.get("patterns", []):
                            patterns.append(
                                {
                                    "pattern": re.compile(pattern, re.IGNORECASE),
                                    "original_pattern": pattern,
                                    "match_data": {
                                        "brand": brand,
                                        "model": model_name,
                                    },
                                }
                            )

        return patterns

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

            # Use knot-specific information if available
            # Use knot model if available, otherwise brush model
            knot_model = m.get("knot_model", model)
            # Use knot fiber if available, otherwise brush fiber
            knot_fiber = m.get("knot_fiber", fiber)
            # Use knot brand if available, otherwise brush brand
            knot_brand = m.get("knot_brand", brand)

            m["knot"] = {
                "brand": knot_brand,
                "model": knot_model,
                "fiber": knot_fiber,
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
                # Extract the brand from handle_text if no match found
                # This handles cases like "UnknownMaker handle" where UnknownMaker isn't in the
                # catalog
                handle_brand = None
                if handle_match:
                    handle_brand = handle_match["handle_maker"]
                else:
                    # Try to extract brand from handle_text (e.g., "UnknownMaker handle" ->
                    # "UnknownMaker")
                    # Remove common handle-related words to get the brand
                    handle_words = handle_text.lower().split()
                    if "handle" in handle_words:
                        handle_words.remove("handle")
                    if handle_words:
                        # Use the first word as the brand (e.g., "UnknownMaker")
                        handle_brand = handle_text.split()[0]  # Use original case

                updated["handle"] = {
                    "brand": handle_brand,
                    "model": handle_match.get("handle_model") if handle_match else None,
                    "source_text": handle_text,
                    "_matched_by": "HandleMatcher" if handle_match else "BrushSplitter",
                    "_pattern": handle_match.get("_pattern_used") if handle_match else "split",
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
                            "_matched_by": "BrushSplitter",
                            "_pattern": knot_match.get("_pattern_used", "split"),
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

            # If no strategy succeeded, set to None to ensure field exists
            updated["handle_maker"] = None

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
            updated["handle_model"] = handle_match["handle_model"]
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

            # If no strategy succeeded, set to None to ensure field exists
            if "knot_maker" not in updated:
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

    def _is_same_maker_split(self, handle_brand: Optional[str], knot_brand: Optional[str]) -> bool:
        """Check if handle and knot are from the same maker brand."""
        if not handle_brand or not knot_brand:
            return False
        return handle_brand == knot_brand

    def _extract_model_from_handle_text(self, handle_text: str) -> Optional[str]:
        """Extract model from handle text (e.g., 'Simpson Chubby 2' -> 'Chubby 2')."""
        if not handle_text:
            return None

        # Split into words and look for model patterns
        words = handle_text.split()
        if len(words) < 2:
            return None

        # Skip the first word (brand) and join the rest as the model
        model_words = words[1:]
        if model_words:
            return " ".join(model_words)

        return None

    def _try_dual_component_match(self, value: str) -> Optional[tuple]:
        """
        Try to match both handle and knot components in the input string.

        Returns:
            Optional[tuple]: (handle_match, knot_match) if both found, None otherwise
        """
        if not value or not isinstance(value, str):
            return None

        try:
            # Try handle matching on the entire string first (cheaper than knot matching)
            # Check correct matches first, then fall back to handle matcher
            handle_correct_match = self.correct_matches_checker.check(value)
            if handle_correct_match and handle_correct_match.handle_maker:
                # Use correct match for handle
                handle_match = {
                    "handle_maker": handle_correct_match.handle_maker,
                    "handle_model": handle_correct_match.handle_model,
                    "_matched_by": "CorrectMatches",
                    "_pattern": "correct_matches_handle",
                }
            else:
                # Fall back to handle matcher
                handle_match = self.handle_matcher.match_handle_maker(value)

            # Try knot matching on the entire string
            # Check correct matches first, then fall back to knot matcher
            knot_correct_match = self.correct_matches_checker.check(value)
            if knot_correct_match and knot_correct_match.knot_info:
                # Use correct match for knot
                from sotd.match.types import create_match_result

                knot_info = knot_correct_match.knot_info
                knot_match = create_match_result(
                    original=value,
                    matched={
                        "brand": knot_info.get("brand"),
                        "model": knot_info.get("model"),
                        "fiber": knot_info.get("fiber"),
                        "knot_size_mm": knot_info.get("knot_size_mm"),
                        "_matched_by": "CorrectMatches",
                        "_pattern": "correct_matches_knot",
                    },
                    match_type="exact",
                    pattern="correct_matches_knot",
                )
            else:
                # Fall back to knot matcher
                knot_match = self.knot_matcher.match(value)

            # Validate dual component match
            if self._validate_dual_component_match(handle_match, knot_match):
                return (handle_match, knot_match)

            return None

        except Exception as e:
            if self.debug:
                print(f"Dual component match failed for '{value}': {e}")
            return None

    def detect_user_intent(self, value: str, handle_text: str, knot_text: str) -> str:
        """
        Detect user intent based on component order in the original string.

        Args:
            value: Original input string
            handle_text: Extracted handle text
            knot_text: Extracted knot text

        Returns:
            str: "handle_primary" or "knot_primary"
        """
        if not value or not handle_text or not knot_text:
            return "handle_primary"  # Default behavior

        # Find positions of handle and knot text in original string
        handle_pos = value.find(handle_text)
        knot_pos = value.find(knot_text)

        # If either component not found, default to handle_primary
        if handle_pos == -1 or knot_pos == -1:
            return "handle_primary"

        # If positions are identical (same text), default to handle_primary
        if handle_pos == knot_pos:
            return "handle_primary"

        # Return based on which component appears first
        return "handle_primary" if handle_pos < knot_pos else "knot_primary"

    def _validate_dual_component_match(
        self, handle_match: Optional[dict], knot_match: Optional["MatchResult"]
    ) -> bool:
        """
        Validate that a dual component match is valid.

        Args:
            handle_match: Handle match result or None
            knot_match: Knot match result or None

        Returns:
            bool: True if valid dual component match, False otherwise
        """
        # Both components must be found
        if not handle_match or not knot_match:
            return False

        # Handle match must have handle_maker
        if not handle_match.get("handle_maker"):
            return False

        # Knot match must have valid matched data
        if not knot_match.matched:
            return False

        # For fallback strategies, brand can be None (they only detect partial information)
        knot_brand = knot_match.matched.get("brand")
        if knot_brand is None:
            # Check if this is a fallback strategy (they set brand to None)
            if knot_match.matched.get("_matched_by_strategy") in [
                "KnotSizeFallbackStrategy",
                "FiberFallbackStrategy",
            ]:
                # Fallback strategies are valid even with brand: None
                pass
            else:
                # Non-fallback strategies must have a brand
                return False

        # Check if handle maker is only a handle maker (not also a knot maker)
        handle_maker = handle_match.get("handle_maker")
        knot_brand = knot_match.matched.get("brand")

        # If handle maker is only a handle maker and knot brand is "Unspecified",
        # reject the dual-component match to avoid false positives
        if (
            handle_maker
            and self._is_only_handle_maker(handle_maker)
            and knot_brand == "Unspecified"
        ):
            return False

        # Same brand is valid for makers that are both handle and knot makers (e.g., Zenith)
        # We don't reject same-brand matches as they can be legitimate dual component scenarios

        return True

    def _is_only_handle_maker(self, brand: str) -> bool:
        """
        Check if a brand is only a handle maker (not also a knot maker).

        Args:
            brand: Brand name to check

        Returns:
            bool: True if brand is only a handle maker, False if it's also a knot maker
        """
        if not brand:
            return False

        # Check if brand is in handles catalog
        is_handle_maker = self.handle_matcher.is_known_handle_maker(brand)

        # Check if brand is in knots catalog
        is_knot_maker = self._is_knot_maker(brand)

        # Return True if it's a handle maker but NOT a knot maker
        return is_handle_maker and not is_knot_maker

    def _is_knot_maker(self, brand: str) -> bool:
        """
        Check if a brand is a knot maker.

        Args:
            brand: Brand name to check

        Returns:
            bool: True if brand is a knot maker, False otherwise
        """
        if not brand:
            return False

        # Check known_knots section
        known_knots = self.knots_data.get("known_knots", {})
        if brand in known_knots:
            return True

        # Check other_knots section
        other_knots = self.knots_data.get("other_knots", {})
        if brand in other_knots:
            return True

        return False

    def create_dual_component_result(
        self, handle_match: dict, knot_match: "MatchResult", value: str, user_intent: str
    ) -> "MatchResult":
        """
        Create a dual component result with composite brush structure.

        Args:
            handle_match: Handle match result
            knot_match: Knot match result
            value: Original input string
            user_intent: User intent ("handle_primary" or "knot_primary")

        Returns:
            MatchResult: Composite brush result
        """
        from sotd.match.types import create_match_result

        # Create composite brush structure
        matched = {
            "brand": None,  # Composite brush
            "model": None,  # Composite brush
            "user_intent": user_intent,
            "handle": {
                "brand": handle_match.get("handle_maker"),
                "model": handle_match.get("handle_model"),
                "source_text": value,
                "_matched_by": "HandleMatcher",
                "_pattern": "dual_component_fallback",
            },
            "knot": {
                "brand": knot_match.matched.get("brand"),
                "model": knot_match.matched.get("model"),
                "fiber": knot_match.matched.get("fiber"),
                "knot_size_mm": knot_match.matched.get("knot_size_mm"),
                "source_text": value,
                "_matched_by": "KnotMatcher",
                "_pattern": "dual_component_fallback",
            },
        }

        return create_match_result(
            original=value,
            matched=matched,
            match_type="regex",
            pattern="dual_component_fallback",
        )
