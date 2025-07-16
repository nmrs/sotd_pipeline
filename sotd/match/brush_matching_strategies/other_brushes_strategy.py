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

    def _validate_catalog(self):
        """Validate that all other_brushes entries have required fields."""
        validate_catalog_structure(
            self.catalog,
            required_fields=["patterns", "default"],
            catalog_name="other_brushes catalog",
        )

    def match(self, value: str) -> MatchResult:
        # Handle other_brushes format: brand -> {default: fiber, patterns: []}
        for brand, metadata in self.catalog.items():
            patterns = sorted(metadata["patterns"], key=len, reverse=True)
            for pattern in patterns:
                if re.search(pattern, value, re.IGNORECASE):
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
            pattern=None,
            match_type=None,
        )
