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
        razor_text = result["razor"]
        # Check if razor is filtered
        if filtered_manager.is_filtered("razor", razor_text):
            # Mark as intentionally unmatched
            result["razor"] = {
                "original": razor_text,
                "matched": None,
                "match_type": "intentionally_unmatched",
                "pattern": None,
            }
        else:
            # Match using normalized string only
            razor_result = razor_matcher.match(razor_text)
            # Convert MatchResult to dict for consistency
            if razor_result is not None:
                result["razor"] = {
                    "original": razor_result.original,
                    "matched": razor_result.matched,
                    "match_type": razor_result.match_type,
                    "pattern": razor_result.pattern,
                }
            else:
                result["razor"] = {
                    "original": razor_text,
                    "matched": None,
                    "match_type": None,
                    "pattern": None,
                }

    # Blade matching requires razor context
    if "blade" in result:
        blade_text = result["blade"]
        # Check if blade is filtered
        if filtered_manager.is_filtered("blade", blade_text):
            # Mark as intentionally unmatched
            result["blade"] = {
                "original": blade_text,
                "matched": None,
                "match_type": "intentionally_unmatched",
                "pattern": None,
            }
        else:
            # Match using normalized string only
            blade_result = blade_matcher.match(blade_text)
            # Convert MatchResult to dict for consistency
            if blade_result is not None:
                result["blade"] = {
                    "original": blade_result.original,
                    "matched": blade_result.matched,
                    "match_type": blade_result.match_type,
                    "pattern": blade_result.pattern,
                }
            else:
                result["blade"] = {
                    "original": blade_text,
                    "matched": None,
                    "match_type": None,
                    "pattern": None,
                }

    # Soap matching
    if "soap" in result:
        soap_text = result["soap"]
        # Check if soap is filtered
        if filtered_manager.is_filtered("soap", soap_text):
            # Mark as intentionally unmatched
            result["soap"] = {
                "original": soap_text,
                "matched": None,
                "match_type": "intentionally_unmatched",
                "pattern": None,
            }
        else:
            # Match using normalized string only
            soap_result = soap_matcher.match(soap_text)
            # Convert MatchResult to dict for consistency
            if soap_result is not None:
                result["soap"] = {
                    "original": soap_result.original,
                    "matched": soap_result.matched,
                    "match_type": soap_result.match_type,
                    "pattern": soap_result.pattern,
                }
            else:
                result["soap"] = {
                    "original": soap_text,
                    "matched": None,
                    "match_type": None,
                    "pattern": None,
                }

    # Brush matching
    if "brush" in result:
        brush_text = result["brush"]
        # Check if brush is filtered
        if filtered_manager.is_filtered("brush", brush_text):
            # Mark as intentionally unmatched
            result["brush"] = {
                "original": brush_text,
                "matched": None,
                "match_type": "intentionally_unmatched",
                "pattern": None,
            }
        else:
            # Match using normalized string only
            brush_result = brush_matcher.match(brush_text)
            # Convert MatchResult to dict for consistency
            if brush_result is not None:
                result["brush"] = {
                    "original": brush_result.original,
                    "matched": brush_result.matched,
                    "match_type": brush_result.match_type,
                    "pattern": brush_result.pattern,
                }
            else:
                result["brush"] = {
                    "original": brush_text,
                    "matched": None,
                    "match_type": None,
                    "pattern": None,
                }

    return result
