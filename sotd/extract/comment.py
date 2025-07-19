import json
import logging
import re
from collections import OrderedDict
from pathlib import Path
from typing import Optional

from sotd.extract.fields import extract_field
from sotd.utils.text import preprocess_body

logger = logging.getLogger(__name__)


def parse_comment(comment: dict) -> Optional[dict]:
    if "body" in comment:
        comment["body"] = preprocess_body(comment["body"])
    else:
        comment["body"] = None
    lines = comment["body"].splitlines() if comment["body"] else []

    lines = [re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", line) for line in lines]

    result = {}
    seen_fields = set()

    for line in lines:
        for field in ("razor", "blade", "brush", "soap"):
            if field not in seen_fields:
                value = extract_field(line, field)
                if value:
                    # Preserve all extracted values - no filtering
                    result[field] = value
                    seen_fields.add(field)

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


def run_extraction_for_month(month: str, base_path: str = "data") -> Optional[dict]:
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
        parsed = parse_comment(comment)
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
