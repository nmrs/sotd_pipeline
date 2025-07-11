"""Main enrich module that coordinates all enrichers."""

from .blackbird_plate_enricher import BlackbirdPlateEnricher
from .blade_enricher import BladeCountEnricher
from .brush_enricher import BrushEnricher
from .christopher_bradley_enricher import ChristopherBradleyEnricher
from .game_changer_enricher import GameChangerEnricher
from .registry import enricher_registry
from .straight_razor_enricher import StraightRazorEnricher
from .super_speed_tip_enricher import SuperSpeedTipEnricher

# Track if enrichers have been set up to avoid repeated setup
_enrichers_setup = False


def setup_enrichers():
    """Set up all enrichers in the registry."""
    global _enrichers_setup
    if _enrichers_setup:
        return  # Already set up, skip

    # Register all enrichers
    enricher_registry.register(BladeCountEnricher())
    enricher_registry.register(BrushEnricher())
    enricher_registry.register(StraightRazorEnricher())
    enricher_registry.register(GameChangerEnricher())
    enricher_registry.register(ChristopherBradleyEnricher())
    enricher_registry.register(BlackbirdPlateEnricher())
    enricher_registry.register(SuperSpeedTipEnricher())

    _enrichers_setup = True


def enrich_comments(comments: list[dict], original_comments: list[str]) -> list[dict]:
    """Enrich a list of comments with all applicable enrichers.

    Args:
        comments: List of comment records with matched product data
        original_comments: List of original user comment texts

    Returns:
        List of enriched comment records
    """
    # Ensure enrichers are set up (will be skipped if already done)
    setup_enrichers()

    # Enrich all comments
    return enricher_registry.enrich_records(comments, original_comments)
