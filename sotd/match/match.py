from pathlib import Path

from sotd.utils.filtered_entries import load_filtered_entries, save_filtered_entries

from .blade_matcher import BladeMatcher
from .brush_matcher import BrushMatcher  # placeholder
from .razor_matcher import RazorMatcher
from .soap_matcher import SoapMatcher

# Load filtered entries at module level for performance
_filtered_entries_manager = None


def _get_filtered_entries_manager():
    """Get or create filtered entries manager."""
    global _filtered_entries_manager
    if _filtered_entries_manager is None:
        filtered_file = Path("data/intentionally_unmatched.yaml")
        try:
            _filtered_entries_manager = load_filtered_entries(filtered_file)
        except Exception:
            # If filtered file doesn't exist or is corrupted, create empty manager
            from sotd.utils.filtered_entries import FilteredEntriesManager

            _filtered_entries_manager = FilteredEntriesManager(filtered_file)
            _filtered_entries_manager.load()
    return _filtered_entries_manager


def add_filtered_entry(
    category: str, entry_name: str, comment_id: str, file_path: str, source: str = "pipeline"
):
    """Add a new filtered entry from the pipeline."""
    manager = _get_filtered_entries_manager()
    manager.add_entry(category, entry_name, comment_id, file_path, source)
    save_filtered_entries(manager)


razor_matcher = RazorMatcher()
blade_matcher = BladeMatcher()
soap_matcher = SoapMatcher()
brush_matcher = BrushMatcher()


def match_record(record: dict) -> dict:
    result = record.copy()
    filtered_manager = _get_filtered_entries_manager()

    # Match razor first (required for blade matching)
    if "razor" in result:
        # Check if razor is filtered
        if filtered_manager.is_filtered("razor", result["razor"]):
            # Mark as intentionally unmatched
            result["razor"] = {
                "original": result["razor"],
                "matched": None,
                "match_type": "intentionally_unmatched",
                "pattern": None,
            }
        else:
            razor_result = razor_matcher.match(result["razor"])
            # Convert MatchResult to dict for consistency
            result["razor"] = {
                "original": razor_result.original,
                "matched": razor_result.matched,
                "match_type": razor_result.match_type,
                "pattern": razor_result.pattern,
            }

    # Blade matching requires razor context
    if "blade" in result:
        # Check if blade is filtered
        if filtered_manager.is_filtered("blade", result["blade"]):
            # Mark as intentionally unmatched
            result["blade"] = {
                "original": result["blade"],
                "matched": None,
                "match_type": "intentionally_unmatched",
                "pattern": None,
            }
        else:
            # Get razor result - handle both dict and MatchResult types
            razor_result = result.get("razor", {})
            if hasattr(razor_result, "matched"):
                # It's a MatchResult object
                razor_matched = razor_result.matched or {}
            else:
                # It's a dict
                razor_matched = razor_result.get("matched", {})

            # If no razor context, match blade normally (fallback behavior)
            if not razor_matched:
                blade_result = blade_matcher.match(result["blade"])
                result["blade"] = {
                    "original": blade_result.original,
                    "matched": blade_result.matched,
                    "match_type": blade_result.match_type,
                    "pattern": blade_result.pattern,
                }
            else:
                razor_format = razor_matched.get("format", "").upper()

                # Skip blade matching for formats where blade is irrelevant
                irrelevant_formats = ["SHAVETTE (DISPOSABLE)", "CARTRIDGE", "STRAIGHT"]

                if razor_format in irrelevant_formats:
                    # Clear blade info since it's irrelevant for these razor formats
                    result["blade"] = {
                        "original": result["blade"],
                        "matched": None,
                        "match_type": None,
                        "pattern": None,
                    }
                else:
                    # For other formats, try context-aware matching
                    blade_result = blade_matcher.match_with_context(result["blade"], razor_format)
                    result["blade"] = {
                        "original": blade_result.original,
                        "matched": blade_result.matched,
                        "match_type": blade_result.match_type,
                        "pattern": blade_result.pattern,
                    }

    if "soap" in result:
        # Check if soap is filtered
        if filtered_manager.is_filtered("soap", result["soap"]):
            # Mark as intentionally unmatched
            result["soap"] = {
                "original": result["soap"],
                "matched": None,
                "match_type": "intentionally_unmatched",
                "pattern": None,
            }
        else:
            soap_result = soap_matcher.match(result["soap"])
            result["soap"] = {
                "original": soap_result.original,
                "matched": soap_result.matched,
                "match_type": soap_result.match_type,
                "pattern": soap_result.pattern,
            }

    if "brush" in result:
        # Check if brush is filtered
        if filtered_manager.is_filtered("brush", result["brush"]):
            # Mark as intentionally unmatched
            result["brush"] = {
                "original": result["brush"],
                "matched": None,
                "match_type": "intentionally_unmatched",
                "pattern": None,
            }
        else:
            brush_result = brush_matcher.match(result["brush"])
            result["brush"] = {
                "original": brush_result.original,
                "matched": brush_result.matched,
                "match_type": brush_result.match_type,
                "pattern": brush_result.pattern,
            }

    return result
