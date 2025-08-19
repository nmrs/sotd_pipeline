from typing import Any, Dict, List

import pandas as pd

from ..base_aggregator import BaseAggregator


class RazorBladeComboAggregator(BaseAggregator):
    """Aggregator for razor-blade combination data from enriched records."""

    def _extract_data(self, records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Extract razor-blade combination data from records."""
        combo_data = []
        for record in records:
            razor = record.get("razor", {})
            blade = record.get("blade", {})

            # Skip if no razor or blade data
            if not razor or not blade:
                continue

            razor_matched = razor.get("matched", {})
            blade_matched = blade.get("matched", {})

            # Skip if no matched data
            if not razor_matched or not blade_matched:
                continue

            # Construct names from brand and model if name not directly available
            razor_name = razor_matched.get("name")
            if not razor_name or not isinstance(razor_name, str):
                razor_name = ""
            razor_name = razor_name.strip()
            if not razor_name:
                brand = razor_matched.get("brand")
                model = razor_matched.get("model")
                if brand and isinstance(brand, str) and model and isinstance(model, str):
                    razor_name = f"{brand.strip()} {model.strip()}"
                else:
                    brand_str = brand if isinstance(brand, str) else ""
                    model_str = model if isinstance(model, str) else ""
                    razor_name = brand_str or model_str or "Unknown Razor"

            blade_name = blade_matched.get("name")
            if not blade_name or not isinstance(blade_name, str):
                blade_name = ""
            blade_name = blade_name.strip()
            if not blade_name:
                brand = blade_matched.get("brand")
                model = blade_matched.get("model")
                if brand and isinstance(brand, str) and model and isinstance(model, str):
                    blade_name = f"{brand.strip()} {model.strip()}"
                else:
                    brand_str = brand if isinstance(brand, str) else ""
                    model_str = model if isinstance(model, str) else ""
                    blade_name = brand_str or model_str or "Unknown Blade"

            # Skip if no names
            if not razor_name or not blade_name:
                continue

            author = record.get("author", "").strip()

            if razor_name and blade_name and author:
                combo_data.append(
                    {"razor_name": razor_name, "blade_name": blade_name, "author": author}
                )

        return combo_data

    def _create_composite_name(self, df: pd.DataFrame) -> pd.Series:
        """Create composite name from razor and blade data."""
        return df["razor_name"] + " + " + df["blade_name"]

    def _get_group_columns(self, df: pd.DataFrame) -> List[str]:
        """Get columns to use for grouping."""
        return ["name"]


# Legacy function interface for backward compatibility
def aggregate_razor_blade_combos(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Legacy function interface for backward compatibility."""
    aggregator = RazorBladeComboAggregator()
    return aggregator.aggregate(records)
