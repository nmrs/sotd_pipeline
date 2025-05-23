from typing import Optional
from sotd.extract.fields import (
    extract_razor_line,
    extract_blade_line,
    extract_brush_line,
    extract_soap_line,
)


def parse_comment(comment: dict) -> Optional[dict]:
    body = comment.get("body", "")
    lines = body.splitlines()

    result = {}
    seen_fields = set()

    for line in lines:
        if "razor" not in seen_fields:
            value = extract_razor_line(line)
            if value:
                result["razor"] = value
                seen_fields.add("razor")

        if "blade" not in seen_fields:
            value = extract_blade_line(line)
            if value:
                result["blade"] = value
                seen_fields.add("blade")

        if "brush" not in seen_fields:
            value = extract_brush_line(line)
            if value:
                result["brush"] = value
                seen_fields.add("brush")

        if "soap" not in seen_fields:
            value = extract_soap_line(line)
            if value:
                result["soap"] = value
                seen_fields.add("soap")

    return result if result else None
