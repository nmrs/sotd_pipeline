from .utils.fiber_utils import match_fiber
from .utils.knot_size_utils import parse_knot_size
from .utils.pattern_utils import (
    validate_catalog_structure,
)
from .base_brush_matching_strategy import (
    BaseBrushMatchingStrategy,
)

from sotd.match.types import MatchResult, create_match_result
from sotd.match.utils.regex_error_utils import compile_regex_with_context, create_context_dict


class OtherBrushMatchingStrategy(BaseBrushMatchingStrategy):
    @property
    def strategy_name(self) -> str:
        return "other_brush"

    def __init__(self, catalog: dict):
        self.catalog = catalog
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
                context = create_context_dict(
                    file_path="data/brushes.yaml",
                    brand=brand,
                    model=metadata.get("default"),
                    strategy="OtherBrushMatchingStrategy",
                )
                compiled_pattern = compile_regex_with_context(pattern, context)

                compiled_patterns.append(
                    {
                        "brand": brand,
                        "metadata": metadata,
                        "pattern": pattern,
                        "compiled": compiled_pattern,
                    }
                )
        return compiled_patterns

    def match(self, value: str | dict) -> MatchResult:
        # Handle both string and field data object inputs
        if isinstance(value, dict):
            # Extract normalized text from field data object
            text = value.get("normalized", value.get("original", ""))
        else:
            # Direct string input
            text = value

        # Use precompiled patterns for performance optimization
        for pattern_data in self.compiled_patterns:
            if pattern_data["compiled"].search(text):
                brand = pattern_data["brand"]
                metadata = pattern_data["metadata"]
                pattern = pattern_data["pattern"]

                # Extract fiber from user input or use default
                user_fiber = match_fiber(text)
                default_fiber = metadata["default"]
                final_fiber = user_fiber or default_fiber

                # Extract knot size from user input or use default
                user_knot_size = parse_knot_size(text)
                default_knot_size = metadata.get("knot_size_mm")

                # Set model to just the fiber type
                if user_fiber:
                    model = user_fiber.title()
                else:
                    model = default_fiber

                # Create result with nested structure (no redundant root fields)
                result = {
                    "brand": brand,
                    "model": model,
                    "_pattern_used": pattern,
                    "fiber_strategy": "user_input" if user_fiber else "default",
                    "_matched_by_strategy": self.__class__.__name__,
                    # Create nested handle section
                    "handle": {
                        "brand": brand,  # Handle brand same as brush brand for other brushes
                        "model": None,  # Handle model not specified for other brushes
                    },
                    # Create nested knot section with fiber and size info
                    "knot": {
                        "brand": brand,  # Knot brand same as brush brand for other brushes
                        "model": model,  # Knot model same as brush model for other brushes
                        "fiber": final_fiber,
                        "knot_size_mm": (
                            user_knot_size if user_knot_size is not None else default_knot_size
                        ),
                    },
                }

                return create_match_result(
                    original=value.get("original", text) if isinstance(value, dict) else value,
                    matched=result,
                    pattern=pattern,
                    match_type="brand_default",
                    strategy="other_brush",
                )

        return create_match_result(
            original=value.get("original", text) if isinstance(value, dict) else value,
            matched=None,
            pattern=None,  # type: ignore
            match_type=None,  # type: ignore
            strategy="other_brush",
        )
