import re

from sotd.match.brush_matching_strategies.utils.fiber_utils import match_fiber
from sotd.match.brush_matching_strategies.utils.knot_size_utils import parse_knot_size
from sotd.match.brush_matching_strategies.utils.pattern_utils import (
    validate_catalog_structure,
)
from sotd.match.brush_matching_strategies.yaml_backed_strategy import (
    YamlBackedBrushMatchingStrategy,
)
from sotd.match.types import MatchResult, create_match_result


class OtherBrushMatchingStrategy(YamlBackedBrushMatchingStrategy):
    def __init__(self, catalog: dict):
        super().__init__(catalog)
        self._validate_catalog()
        self.compiled_patterns = self._compile_patterns()

    def _validate_catalog(self):
        """Validate that all other_brushes entries have required fields."""
        validate_catalog_structure(
            self.catalog,
            required_fields=["patterns", "default"],
            catalog_name="other_brushes catalog",
        )

    def _compile_patterns(self) -> list[dict]:
        """Pre-compile patterns for performance optimization."""
        compiled_patterns = []
        for brand, metadata in self.catalog.items():
            patterns = sorted(metadata["patterns"], key=len, reverse=True)
            for pattern in patterns:
                compiled_patterns.append(
                    {
                        "brand": brand,
                        "metadata": metadata,
                        "pattern": pattern,
                        "compiled": re.compile(pattern, re.IGNORECASE),
                    }
                )
        return compiled_patterns

    def match(self, value: str) -> MatchResult:
        # Use precompiled patterns for performance optimization
        for pattern_data in self.compiled_patterns:
            if pattern_data["compiled"].search(value):
                brand = pattern_data["brand"]
                metadata = pattern_data["metadata"]
                pattern = pattern_data["pattern"]

                # Extract fiber from user input or use default
                user_fiber = match_fiber(value)
                default_fiber = metadata["default"]
                final_fiber = user_fiber or default_fiber

                # Extract knot size from user input or use default
                user_knot_size = parse_knot_size(value)
                default_knot_size = metadata.get("knot_size_mm")

                # Set model to just the fiber type
                if user_fiber:
                    model = user_fiber.title()
                else:
                    model = default_fiber

                result = {
                    "brand": brand,
                    "model": model,
                    "fiber": final_fiber,
                    "_pattern_used": pattern,
                    "fiber_strategy": "user_input" if user_fiber else "default",
                    "_matched_by_strategy": self.__class__.__name__,
                }

                # Add knot size - preserve catalog data for enrich phase
                if user_knot_size is not None:
                    result["knot_size_mm"] = user_knot_size
                elif default_knot_size is not None:
                    result["knot_size_mm"] = default_knot_size

                return create_match_result(
                    original=value,
                    matched=result,
                    pattern=pattern,
                    match_type="brand_default",
                )

        return create_match_result(
            original=value,
            matched=None,
            pattern="",
            match_type="",
        )
