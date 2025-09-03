from ..utils.pattern_utils import (
    create_strategy_result,
    validate_string_input,
)
from ..utils.knot_size_utils import parse_knot_size
from sotd.match.types import MatchResult
from sotd.match.utils.regex_error_utils import compile_regex_with_context, create_context_dict


class KnownKnotMatchingStrategy:
    """Strategy for matching known knot models from knots.yaml."""

    def __init__(self, catalog_data):
        self.catalog = catalog_data or {}
        self.patterns = self._compile_known_knot_patterns()

    def _compile_known_knot_patterns(self) -> list[dict]:
        """Compile patterns from the nested catalog structure."""
        all_patterns = []

        for brand, models in self.catalog.items():
            if not isinstance(models, dict):
                continue

            # Get brand-level defaults
            brand_default_fiber = models.get("fiber")
            brand_default_knot_size = models.get("knot_size_mm")

            # Handle regular patterns
            for model, metadata in models.items():
                # Skip non-model entries (like brand-level defaults)
                if model in ["fiber", "knot_size_mm", "default"]:
                    continue

                if not isinstance(metadata, dict):
                    continue

                patterns = metadata.get("patterns", [])
                if not patterns:
                    continue

                # Use model-level fiber/size if available, otherwise brand defaults
                fiber = metadata.get("fiber", brand_default_fiber)
                knot_size_mm = metadata.get("knot_size_mm", brand_default_knot_size)

                for pattern in patterns:
                    context = create_context_dict(
                        file_path="data/knots.yaml",
                        brand=brand,
                        model=model,
                        strategy="KnownKnotMatchingStrategy",
                    )
                    compiled_pattern = compile_regex_with_context(pattern, context)

                    all_patterns.append(
                        {
                            "pattern": pattern,
                            "compiled": compiled_pattern,
                            "brand": brand,
                            "model": model,
                            "fiber": fiber,
                            "knot_size_mm": knot_size_mm,
                            "metadata": metadata,
                        }
                    )

        # Sort by pattern length (longest first) for proper prioritization
        all_patterns.sort(key=lambda x: len(x["pattern"]), reverse=True)
        return all_patterns

    def match(self, value: str) -> MatchResult:
        """Match input against known knot patterns. Always returns a MatchResult."""
        if not validate_string_input(value):
            return create_strategy_result(
                original_value=value,
                matched_data=None,
                pattern=None,
                strategy_name="KnownKnotMatchingStrategy",
            )

        for pattern_data in self.patterns:
            if pattern_data["compiled"].search(value):
                # Extract size from input text if available
                extracted_size = parse_knot_size(value)

                # Use extracted size if found, otherwise fall back to catalog size
                final_size = (
                    extracted_size if extracted_size is not None else pattern_data["knot_size_mm"]
                )
                return create_strategy_result(
                    original_value=value,
                    matched_data={
                        "brand": pattern_data["brand"],
                        "model": pattern_data["model"],
                        "fiber": pattern_data["fiber"],
                        "knot_size_mm": final_size,
                    },
                    pattern=pattern_data["pattern"],
                    strategy_name="KnownKnotMatchingStrategy",
                    match_type="regex",
                )

        return create_strategy_result(
            original_value=value,
            matched_data=None,
            pattern=None,
            strategy_name="KnownKnotMatchingStrategy",
        )
