"""Main enrich module that coordinates all enrichers."""

from .blade_enricher import BladeCountEnricher
from .brush_enricher import BrushEnricher
from .registry import enricher_registry
from .straight_razor_enricher import StraightRazorEnricher


def setup_enrichers():
    """Set up all enrichers in the registry."""
    # Register all enrichers
    enricher_registry.register(BladeCountEnricher())
    enricher_registry.register(BrushEnricher())
    enricher_registry.register(StraightRazorEnricher())


def enrich_comments(comments: list[dict], original_comments: list[str]) -> list[dict]:
    """Enrich a list of comments with all applicable enrichers.

    Args:
        comments: List of comment records with matched product data
        original_comments: List of original user comment texts

    Returns:
        List of enriched comment records
    """
    # Ensure enrichers are set up
    setup_enrichers()

    # Enrich all comments
    return enricher_registry.enrich_records(comments, original_comments)
