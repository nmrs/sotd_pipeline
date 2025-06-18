"""Enrich phase for the SOTD Pipeline.

This phase performs sophisticated analysis requiring knowledge of matched products
to extract detailed specifications and metadata that don't affect product identification.
"""

from .enricher import BaseEnricher
from .registry import EnricherRegistry, enricher_registry

__all__ = ["BaseEnricher", "EnricherRegistry", "enricher_registry"]
