import re

from sotd.match.brush_matching_strategies.utils.pattern_utils import (
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
                "model": default_fiber,  # Use default fiber as model name
                "fiber": default_fiber,  # Use default fiber
                "knot_size_mm": metadata.get("knot_size_mm"),
            }

            # Create pattern entries
            for pattern in patterns:
                pattern_entry = {
                    "pattern": pattern,
                    "compiled": re.compile(pattern, re.IGNORECASE),
                    **pattern_metadata,
                }
                all_patterns.append(pattern_entry)

        # Sort by pattern length (longest first)
        all_patterns.sort(key=lambda x: len(x["pattern"]), reverse=True)
        return all_patterns

    def match(self, value: str):
        """Match input against other knot patterns. Always returns a MatchResult."""
        if not validate_string_input(value):
            return create_strategy_result(
                original_value=value,
                matched_data=None,
                pattern=None,
                strategy_name="OtherKnotMatchingStrategy",
            )

        for pattern_data in self.patterns:
            if pattern_data["compiled"].search(value):
                return create_strategy_result(
                    original_value=value,
                    matched_data={
                        "brand": pattern_data["brand"],
                        "model": pattern_data["model"],  # Now uses fiber as model
                        "fiber": pattern_data["fiber"],
                        "knot_size_mm": pattern_data["knot_size_mm"],
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
