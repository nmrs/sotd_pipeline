from typing import Optional

from sotd.enrich.handle_enricher import HandleEnrichmentPipeline


class BrushEnricher:
    def __init__(self):
        self.strategies = [
            self._parse_w_split,
        ]
        self.handle_enricher = HandleEnrichmentPipeline()

    def enrich(self, original: str, matched: Optional[dict]) -> dict:
        result = self.handle_enricher.enrich(original, matched)

        for strategy in self.strategies:
            parsed = strategy(original, matched)
            if parsed:
                parsed["handle_knot_strategy"] = strategy.__name__
                result.update(parsed)
                break

        return result

    def _parse_w_split(self, original: str, matched: Optional[dict]) -> Optional[dict]:
        lowered = original.lower()
        if " w/ " in lowered:
            parts = original.split(" w/ ", 1)
            if len(parts) == 2:
                handle = parts[0].strip()
                knot = parts[1].strip()
                return {"handle_maker": handle, "knot_maker": knot}
        return None
