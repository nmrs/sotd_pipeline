import json
import logging
import re
from collections import OrderedDict
from pathlib import Path
from typing import Optional

from sotd.extract.fields import extract_field_with_pattern, get_patterns
from sotd.extract.override_manager import OverrideManager
from sotd.utils.aliases import FIELD_ALIASES
from sotd.utils.extract_normalization import normalize_for_matching
from sotd.utils.text import preprocess_body

logger = logging.getLogger(__name__)


def parse_comment(
    comment: dict,
    override_manager: Optional[OverrideManager] = None,
    processing_month: Optional[str] = None,
) -> Optional[dict]:
    if "body" in comment:
        comment["body"] = preprocess_body(comment["body"])
    else:
        comment["body"] = None
    lines = comment["body"].splitlines() if comment["body"] else []

    lines = [re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", line) for line in lines]

    result = {}

    # Process fields with pattern priority: try each pattern across all lines
    # This ensures high-priority patterns (explicit markers) are checked before
    # low-priority patterns (ambiguous), regardless of line order
    # Pattern priority is enforced across all aliases, not per alias
    for field in ("razor", "blade", "brush", "soap"):
        if field in result:
            continue  # Already found this field

        # Get all aliases for this field
        aliases = FIELD_ALIASES.get(field, [field])

        # Get patterns grouped by priority level (pattern number)
        # This ensures pattern 0 for all aliases is tried before pattern 1 for any alias
        max_patterns = len(get_patterns(aliases[0])) if aliases else 0
        patterns_by_priority = [[] for _ in range(max_patterns)]

        for alias in aliases:
            alias_patterns = get_patterns(alias)
            for pattern_num, pattern in enumerate(alias_patterns):
                patterns_by_priority[pattern_num].append((alias, pattern))

        # Try each priority level across all aliases and all lines
        # Pattern priority ensures list items (* **alias:**) are tried before narrative (**alias:**)
        for priority_level, patterns_at_level in enumerate(patterns_by_priority):
            for alias, pattern in patterns_at_level:
                for line in lines:
                    value = extract_field_with_pattern(line, field, pattern)
                    if value:
                        # Found a match with this priority level - use it
                        normalized_value = normalize_for_matching(value, field=field)
                        result[field] = {"original": value, "normalized": normalized_value}
                        break  # Found match, move to next field
                if field in result:
                    break  # Found match for this field, try next field
            if field in result:
                break  # Found match for this field, try next field

    # Apply overrides if override manager is provided
    # Use processing_month if provided, otherwise fall back to extracting from created_utc
    if override_manager and comment.get("id"):
        if processing_month:
            month_str = processing_month
        else:
            # Fallback: extract month from created_utc timestamp
            month = comment.get("created_utc", "").split("-")[:2]
            if len(month) != 2:
                month_str = None
            else:
                month_str = f"{month[0]}-{month[1]:0>2}"

        if month_str:
            comment_id = comment["id"]

            for field in ("razor", "blade", "brush", "soap"):
                override_value = override_manager.get_override(month_str, comment_id, field)
                if override_value:
                    field_exists = field in result
                    result[field] = override_manager.apply_override(
                        result.get(field), override_value, field_exists
                    )

    ordered_comment = OrderedDict()
    for key in ("author", "body", "created_utc", "id", "thread_id", "thread_title", "url"):
        if key in comment:
            ordered_comment[key] = comment[key]

    for field in ("razor", "blade", "brush", "soap"):
        value = result.get(field)
        if value:
            ordered_comment[field] = value

    return ordered_comment if result else None


# Added function to run extraction for a month
# Skips extraction and logging a warning if input file is missing


def run_extraction_for_month(
    month: str, base_path: str = "data", override_manager: Optional[OverrideManager] = None
) -> Optional[dict]:
    input_path = Path(base_path) / "comments" / f"{month}.json"
    if not input_path.exists():
        logger.warning("Skipping extraction for missing input file: %s", input_path)
        return None

    with open(input_path, encoding="utf-8") as f:
        raw = json.load(f)
        comments = raw.get("data", [])

    extracted = []
    skipped = []

    for comment in comments:
        parsed = parse_comment(comment, override_manager, processing_month=month)
        if parsed:
            extracted.append(parsed)
        else:
            skipped.append(comment)

    field_coverage = {"razor": 0, "blade": 0, "brush": 0, "soap": 0}
    for entry in extracted:
        for field in field_coverage:
            if field in entry:
                field_coverage[field] += 1

    return {
        "meta": {
            "month": month,
            "comment_count": len(comments),
            "shave_count": len(extracted),
            "skipped_count": len(skipped),
            "field_coverage": field_coverage,
        },
        "data": extracted,
        "skipped": skipped,
    }
