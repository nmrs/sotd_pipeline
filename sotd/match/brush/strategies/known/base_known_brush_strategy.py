import re
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional

from sotd.match.types import MatchResult, create_match_result
from sotd.utils.yaml_loader import UniqueKeyLoader, load_yaml_with_nfc

from ..base_brush_matching_strategy import (
    BaseBrushMatchingStrategy,
)
from ..utils.fiber_utils import match_fiber
from ..utils.knot_size_utils import parse_knot_size
from ..utils.pattern_cache import get_compiled_patterns
from ..utils.pattern_utils import (
    compile_catalog_patterns,
)


class BaseKnownBrushMatchingStrategy(BaseBrushMatchingStrategy, ABC):
    """
    Base strategy for matching known brush patterns from YAML catalog.

    This abstract base class provides common functionality for both
    known_brush and known_knot_based_brush strategies. The only differences
    between these strategies are:
    1. Different data sources (known_brushes vs known_knot_based_brushes sections)
    2. Different strategy names for scoring purposes
    3. Different scoring weights

    Subclasses must implement get_strategy_name() to return the appropriate
    strategy name for scoring.
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
        """Compile patterns using the unified pattern utilities with caching."""
        return get_compiled_patterns(
            self.catalog,
            "known_brush",
            lambda cat: compile_catalog_patterns(
                cat,
                pattern_field="patterns",
                metadata_fields=["fiber", "knot_size_mm", "handle_maker"],
            ),
        )

    def match(self, value: str, full_string: Optional[str] = None) -> MatchResult:
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
                    value,
                    result,
                    pattern_data.get("pattern", "unknown"),
                    "regex",
                )

        # No match found
        return self._create_match_result(
            value,
            None,
            None,
            None,
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

        # Handle nested knot structure if present
        knot_brand = pattern_data.get(
            "knot_brand", brand
        )  # Use knot brand if specified, otherwise brush brand
        knot_model = pattern_data.get(
            "knot_model", model
        )  # Use knot model if specified, otherwise brush model
        knot_fiber = pattern_data.get("knot_fiber") or fiber_info.get(
            "fiber"
        )  # Use knot fiber if specified
        knot_size = pattern_data.get("knot_size_mm") or size_info.get(
            "knot_size_mm"
        )  # Use knot size if specified

        # Handle nested handle structure if present
        handle_brand = pattern_data.get(
            "handle_brand", brand
        )  # Use handle brand if specified, otherwise brush brand
        handle_model = pattern_data.get("handle_model")  # Use handle model if specified

        # Create result with nested structure (no redundant root fields)
        result = {
            "brand": brand,
            "model": model,
            "_pattern_used": pattern_data.get("pattern", "unknown"),
            # Create nested handle section
            "handle": {
                "brand": handle_brand,
                "model": handle_model,
            },
            # Create nested knot section with fiber and size info
            "knot": {
                "brand": knot_brand,
                "model": knot_model,
                "fiber": knot_fiber,
                "knot_size_mm": knot_size,
            },
        }

        # Add strategy information to root level
        if fiber_info.get("fiber_strategy"):
            result["fiber_strategy"] = fiber_info["fiber_strategy"]
        if size_info.get("knot_size_strategy"):
            result["knot_size_strategy"] = size_info["knot_size_strategy"]

        return result

    def _detect_fiber_and_size(self, value: str, metadata: dict) -> tuple[dict, dict]:
        """Detect fiber and size information from input and metadata."""
        # Fiber detection
        fiber_info = {"fiber": None, "fiber_strategy": "none"}
        detected_fiber = match_fiber(value)
        if detected_fiber:
            fiber_info["fiber"] = detected_fiber
            fiber_info["fiber_strategy"] = "user_input"
        elif metadata.get("fiber"):
            fiber_info["fiber"] = metadata["fiber"]
            fiber_info["fiber_strategy"] = "yaml"

        # Size detection
        size_info = {"knot_size_mm": None, "knot_size_strategy": "none"}
        detected_size = parse_knot_size(value)
        if detected_size:
            size_info["knot_size_mm"] = detected_size
            size_info["knot_size_strategy"] = "user_input"
        elif metadata.get("knot_size_mm"):
            size_info["knot_size_mm"] = metadata["knot_size_mm"]
            size_info["knot_size_strategy"] = "yaml"

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
            strategy=self.get_strategy_name(),
        )

    @abstractmethod
    def get_strategy_name(self) -> str:
        """
        Return the strategy name for scoring purposes.

        Returns:
            Strategy name string (e.g., "known_brush" or "known_knot_based_brush")
        """
        pass
