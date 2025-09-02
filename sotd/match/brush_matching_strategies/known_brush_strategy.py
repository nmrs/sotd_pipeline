import re
from pathlib import Path

from sotd.match.brush_matching_strategies.base_brush_matching_strategy import (
    BaseBrushMatchingStrategy,
)
from sotd.match.brush_matching_strategies.utils.pattern_utils import (
    compile_catalog_patterns,
)
from sotd.match.brush_matching_strategies.utils.fiber_utils import match_fiber
from sotd.match.brush_matching_strategies.utils.knot_size_utils import parse_knot_size
from sotd.match.types import MatchResult, create_match_result
from sotd.utils.yaml_loader import UniqueKeyLoader, load_yaml_with_nfc


class KnownBrushMatchingStrategy(BaseBrushMatchingStrategy):
    """
    Strategy for matching known brush patterns from YAML catalog.

    Provides YAML loading, pattern matching, and fiber/size detection logic.
    """

    def __init__(self, catalog_data, handle_matcher=None):
        if isinstance(catalog_data, Path):
            self.catalog = load_yaml_with_nfc(catalog_data, loader_cls=UniqueKeyLoader)
        else:
            self.catalog = catalog_data or {}

        self.handle_matcher = handle_matcher

        # Compile patterns during initialization
        self.patterns = self._compile_patterns()

    def _compile_patterns(self) -> list[dict]:
        """Compile patterns using the unified pattern utilities."""
        return compile_catalog_patterns(
            self.catalog,
            pattern_field="patterns",
            metadata_fields=["fiber", "knot_size_mm", "handle_maker"],
        )

    def match(self, value: str) -> MatchResult:
        """
        Common pattern matching logic for known brush strategies.

        Args:
            value: String to match against patterns

        Returns:
            MatchResult with strategy name set
        """
        # Use compiled patterns from subclass
        for pattern_data in self.patterns:
            if self._pattern_matches(value, pattern_data):
                result = self._create_match_result_from_pattern(value, pattern_data)
                return self._create_match_result(
                    value=value,
                    matched_data=result,
                    pattern=pattern_data.get("pattern", "unknown"),
                    match_type="regex",
                )

        # No match found
        return self._create_match_result(
            value=value,
            matched_data=None,
            pattern=None,
            match_type=None,
        )

    def _pattern_matches(self, value: str, pattern_data: dict) -> bool:
        """Check if value matches the pattern."""
        pattern = pattern_data.get("compiled") or pattern_data.get("pattern")
        if pattern is not None and hasattr(pattern, "search"):
            return pattern.search(value)
        elif isinstance(pattern, str):
            return bool(re.search(pattern, value, re.IGNORECASE))
        return False

    def _create_match_result_from_pattern(self, value: str, pattern_data: dict) -> dict:
        """Create matched data from pattern data with nested structure."""
        # Get basic brush information
        brand = pattern_data.get("brand")
        model = pattern_data.get("model")

        # Apply fiber and size detection logic
        fiber_info, size_info = self._detect_fiber_and_size(value, pattern_data)

        # Create result with nested structure (no redundant root fields)
        result = {
            "brand": brand,
            "model": model,
            "_pattern_used": pattern_data.get("pattern", "unknown"),
            # Create nested handle section
            "handle": {
                "brand": brand,  # Handle brand same as brush brand for complete brushes
                "model": None,  # Handle model not specified in catalog
            },
            # Create nested knot section with fiber and size info
            "knot": {
                "brand": brand,  # Knot brand same as brush brand for complete brushes
                "model": model,  # Knot model same as brush model for complete brushes
                "fiber": fiber_info.get("fiber"),
                "knot_size_mm": size_info.get("knot_size_mm"),
            },
        }

        # Add strategy information to root level
        if fiber_info.get("fiber_strategy"):
            result["fiber_strategy"] = fiber_info["fiber_strategy"]
        if size_info.get("knot_size_strategy"):
            result["knot_size_strategy"] = size_info["knot_size_strategy"]

        return result

    def _detect_fiber_and_size(self, value: str, metadata: dict) -> tuple[dict, dict]:
        """
        Detect fiber and size information with priority-based logic.

        Args:
            value: Input string to analyze
            metadata: Pattern metadata

        Returns:
            Tuple of (fiber_info, size_info) dictionaries
        """
        fiber_info = {}
        size_info = {}

        # Fiber detection with priority
        if "fiber" in metadata:
            fiber_info["fiber"] = metadata["fiber"]
            fiber_info["fiber_strategy"] = "yaml"
        else:
            # Priority 2: Parsed from user input
            fiber = match_fiber(value)
            if fiber:
                fiber_info["fiber"] = fiber
                fiber_info["fiber_strategy"] = "parsed"
            else:
                # Priority 3: Default field in YAML
                if "default fiber" in metadata:
                    fiber_info["fiber"] = metadata["default fiber"]
                    fiber_info["fiber_strategy"] = "yaml_default"

        # Size detection with priority
        if "knot_size_mm" in metadata:
            size_info["knot_size_mm"] = metadata["knot_size_mm"]
            size_info["knot_size_strategy"] = "yaml"
        else:
            # Priority 2: Parsed from user input
            size = parse_knot_size(value)
            if size is not None:
                size_info["knot_size_mm"] = size
                size_info["knot_size_strategy"] = "parsed"
            else:
                # Priority 3: Default field in YAML
                if "default_knot_size_mm" in metadata:
                    size_info["knot_size_mm"] = metadata["default_knot_size_mm"]
                    size_info["knot_size_strategy"] = "yaml_default"

        return fiber_info, size_info

    def _create_match_result(
        self, value: str, matched_data: dict | None, pattern: str | None, match_type: str | None
    ) -> MatchResult:
        """
        Create a MatchResult with the correct strategy name.

        Args:
            value: Original input string
            matched_data: Matched data or None
            pattern: Pattern that matched or None
            match_type: Type of match or None

        Returns:
            MatchResult with strategy name set
        """
        return create_match_result(
            original=value,
            matched=matched_data,
            pattern=pattern,
            match_type=match_type,
            strategy="known_brush",
        )
