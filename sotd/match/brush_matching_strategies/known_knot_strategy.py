import re

from sotd.match.brush_matching_strategies.utils.pattern_utils import (
    create_strategy_result,
    validate_string_input,
)


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

            # Handle template patterns first
            template_patterns = self._compile_template_patterns(
                brand, models, brand_default_fiber, brand_default_knot_size
            )
            all_patterns.extend(template_patterns)

            # Handle regular patterns
            for model, metadata in models.items():
                # Skip non-model entries (like brand-level defaults and template patterns)
                if model in ["fiber", "knot_size_mm", "default", "batch_patterns"]:
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
                    all_patterns.append(
                        {
                            "pattern": pattern,
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

    def _compile_template_patterns(
        self,
        brand: str,
        models: dict,
        brand_default_fiber: str | None,
        brand_default_knot_size: float | None,
    ) -> list[dict]:
        """Compile template patterns with batch substitution."""
        all_patterns = []

        batch_patterns = models.get("batch_patterns", [])
        for batch_pattern in batch_patterns:
            patterns = batch_pattern["patterns"]  # Use plural 'patterns'
            valid_batches = batch_pattern["valid_batches"]
            model_name_template = batch_pattern["name"]

            # Use pattern-level defaults or fall back to brand defaults
            fiber = batch_pattern.get("fiber", brand_default_fiber)
            knot_size_mm = batch_pattern.get("knot_size_mm", brand_default_knot_size)

            for batch in valid_batches:
                # Substitute {batch} placeholder in model name
                model_name = model_name_template.replace("{batch}", str(batch))

                # Process each pattern in the patterns list
                for pattern_template in patterns:
                    # Substitute {batch} placeholder in pattern
                    pattern = pattern_template.replace("{batch}", str(batch))

                    all_patterns.append(
                        {
                            "pattern": pattern,
                            "brand": brand,
                            "model": model_name,
                            "fiber": fiber,
                            "knot_size_mm": knot_size_mm,
                            "metadata": batch_pattern,
                        }
                    )

        return all_patterns

    def match(self, value: str) -> dict:
        """Match input against known knot patterns."""
        if not validate_string_input(value):
            return create_strategy_result(
                original_value=value, matched_data=None, pattern=None, strategy_name="KnownKnot"
            )

        for pattern_data in self.patterns:
            pattern = pattern_data["pattern"]
            if re.search(pattern, value, re.IGNORECASE):
                return create_strategy_result(
                    original_value=value,
                    matched_data={
                        "brand": pattern_data["brand"],
                        "model": pattern_data["model"],
                        "fiber": pattern_data["fiber"],
                        "knot_size_mm": pattern_data["knot_size_mm"],
                    },
                    pattern=pattern,
                    strategy_name="KnownKnot",
                    match_type="regex",
                )

        return create_strategy_result(
            original_value=value, matched_data=None, pattern=None, strategy_name="KnownKnot"
        )
