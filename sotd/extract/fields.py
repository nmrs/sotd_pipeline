from typing import Optional
from re import escape
import re


def extract_razor_line(line: str) -> Optional[str]:
    return _extract_field_line(line, "razor")


def extract_blade_line(line: str) -> Optional[str]:
    return _extract_field_line(line, "blade")


def extract_brush_line(line: str) -> Optional[str]:
    return _extract_field_line(line, "brush")


def extract_soap_line(line: str) -> Optional[str]:
    return _extract_field_line(line, "soap")


def _extract_field_line(line: str, field: str) -> Optional[str]:
    pattern = rf"^\*\s*\*\*{field}:\*\*\s*(.+)$"
    match = re.match(pattern, line.strip(), flags=re.IGNORECASE)
    return match.group(1).strip() if match else None
