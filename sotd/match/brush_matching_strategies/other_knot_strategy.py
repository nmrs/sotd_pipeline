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
            pattern_metadata = {
                "brand": brand,
                "model": None,  # Other knots don't have specific models
                "fiber": metadata.get("default"),  # Use default fiber
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

    def match(self, value: str) -> dict:
        # Use unified string validation
        normalized_text = validate_string_input(value)
        if normalized_text is None:
            return create_strategy_result(
                original_value=value, matched_data=None, pattern=None, strategy_name="OtherKnot"
            )

        # Use pattern matching
        for entry in self.patterns:
            if entry["compiled"].search(normalized_text):
                entry_result = {
                    "brand": entry.get("brand"),
                    "model": entry.get("model"),
                    "fiber": entry.get("fiber"),
                    "knot_size_mm": entry.get("knot_size_mm"),
                    "source_text": value,
                }
                return create_strategy_result(
                    original_value=value,
                    matched_data=entry_result,
                    pattern=entry["pattern"],
                    strategy_name="OtherKnot",
                    match_type="brand",
                )

        return create_strategy_result(
            original_value=value, matched_data=None, pattern=None, strategy_name="OtherKnot"
        )
