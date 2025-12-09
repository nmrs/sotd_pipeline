from typing import Optional

from sotd.match.utils.regex_error_utils import compile_regex_with_context, create_context_dict

from .utils.fiber_utils import match_fiber
from .utils.pattern_utils import (
    create_strategy_result,
    validate_string_input,
)


class OtherKnotMatchingStrategy:
    """Strategy for matching other knot makers from knots.yaml."""

    def __init__(self, catalog_data):
        self.catalog = catalog_data or {}
        self.patterns = self._compile_other_knot_patterns()

    def _compile_other_knot_patterns(self) -> list[dict]:
        """Compile patterns from the flat catalog structure."""
        all_patterns = []

        for brand, metadata in self.catalog.items():
            if not isinstance(metadata, dict):
                continue

            patterns = metadata.get("patterns", [])
            if not patterns:
                continue

            # Extract metadata fields
            default_fiber = metadata.get("default")
            pattern_metadata = {
                "brand": brand,
                "default_fiber": default_fiber,  # Store default for later use
                "knot_size_mm": metadata.get("knot_size_mm"),
            }

            # Create pattern entries
            for pattern in patterns:
                context = create_context_dict(
                    file_path="data/knots.yaml",
                    brand=brand,
                    model=default_fiber,
                    strategy="OtherKnotMatchingStrategy",
                )
                compiled_pattern = compile_regex_with_context(pattern, context)

                pattern_entry = {
                    "pattern": pattern,
                    "compiled": compiled_pattern,
                    **pattern_metadata,
                }
                all_patterns.append(pattern_entry)

        # Sort by pattern length (longest first)
        all_patterns.sort(key=lambda x: len(x["pattern"]), reverse=True)
        return all_patterns

    def match(self, value: str, full_string: Optional[str] = None):
        """Match input against other knot patterns. Always returns a MatchResult.
        
        Args:
            value: The text to match against (may be a split portion)
            full_string: The full original string (unused by this strategy, but required for interface consistency)
        """
        if not validate_string_input(value):
            return create_strategy_result(
                original_value=value,
                matched_data=None,
                pattern=None,
                strategy_name="OtherKnotMatchingStrategy",
            )

        for pattern_data in self.patterns:
            if pattern_data["compiled"].search(value):
                brand = pattern_data["brand"]
                default_fiber = pattern_data["default_fiber"]

                # Extract fiber from user input or use default
                # (same logic as OtherBrushMatchingStrategy)
                user_fiber = match_fiber(value)
                final_fiber = user_fiber or default_fiber

                # Set model to fiber type (user-provided or default)
                if user_fiber:
                    model = user_fiber.title()
                else:
                    model = default_fiber

                return create_strategy_result(
                    original_value=value,
                    matched_data={
                        "brand": brand,
                        "model": model,  # Use detected fiber or default fiber
                        "fiber": final_fiber,  # Use detected fiber or default fiber
                        "knot_size_mm": pattern_data["knot_size_mm"],
                        "fiber_strategy": "user_input" if user_fiber else "default",
                        "_pattern_used": pattern_data["pattern"],
                    },
                    pattern=pattern_data["pattern"],
                    strategy_name="OtherKnotMatchingStrategy",
                    match_type="regex",
                )

        return create_strategy_result(
            original_value=value,
            matched_data=None,
            pattern=None,
            strategy_name="OtherKnotMatchingStrategy",
        )
