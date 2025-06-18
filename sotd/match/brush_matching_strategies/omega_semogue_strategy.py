import re


class OmegaSemogueBrushMatchingStrategy:
    def match(self, value: str) -> dict:
        if not isinstance(value, str):
            return {"original": value, "matched": None, "pattern": None, "strategy": "OmegaSemogue"}

        # Normalize and fix common typo
        normalized = value.strip().lower().replace("semouge", "semogue")

        brand_match = re.search(r"(omega|semogue)", normalized, re.IGNORECASE)
        # Match e.g. 'omega 10049', 'semogue c3', etc.
        model_match = re.search(
            r"(omega|semogue)[^\]\n\d]*(c\d{1,3}|\d{3,6})", normalized, re.IGNORECASE
        )

        if brand_match and model_match:
            brand = brand_match.group(1).title()
            model_num = model_match.group(2)

            matched = {
                "brand": brand,
                "model": model_num,
                "fiber": "boar",
                "knot_size_mm": None,
                "handle_maker": None,
                "knot_maker": None,
                "source_text": model_match.group(0),
                "source_type": "exact",
            }

            return {
                "original": value,
                "matched": matched,
                "pattern": model_match.re.pattern,
                "strategy": "OmegaSemogue",
            }

        return {"original": value, "matched": None, "pattern": None, "strategy": "OmegaSemogue"}

    def _get_default_match(self) -> dict:
        return {
            "brand": None,
            "model": None,
            "fiber": None,
            "knot_size_mm": None,
            "handle_maker": None,
            "source_text": None,
            "source_type": None,
        }
