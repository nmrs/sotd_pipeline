import re
from typing import Optional

from sotd.utils.aliases import FIELD_ALIASES


def extract_field(line: str, field: str) -> Optional[str]:
    return _extract_field_line(line, field)


def _extract_field_line(line: str, field: str) -> Optional[str]:
    # Special handling for soap field: ignore "lather" when followed by "games"
    if field == "soap" and re.match(r"^lather\s+games", line, flags=re.IGNORECASE):
        return None

    # Special handling for razor field: ignore "razor" when followed by "test"
    if field == "razor" and re.match(r"^razor\s+test", line, flags=re.IGNORECASE):
        return None

    aliases = FIELD_ALIASES.get(field, [field])

    patterns = []
    for alias in aliases:
        patterns.extend(get_patterns(alias))

    for pattern in patterns:
        match = re.match(pattern, line, flags=re.IGNORECASE)
        if match:
            value = match.group(1).strip()
            return value

    return None


def get_patterns(alias: str) -> list[str]:
    return [
        # Checkmark format: ✓Field: Value
        rf"^✓\s*\b{alias}\b\s*[-:]\s*(.+)$",  # ✓Field: Value or ✓ Field: Value
        # Emoji bold format: * **Field** Value
        rf"^\*\s*\*\*\b{alias}\b\*\*\s*[-:]\s*(.+)$",  # * **Field** - Value
        rf"^\*\s*\*\*\b{alias}\b\*\*\s*(.+)$",  # * **Field** Value (no separator)
        # common more generic cases
        rf"^(?:[-*]\s*)?\*\*\b{alias}\b\*\*\s*[-:]?\s*(.+)$",  # * **alias**: value
        rf"^(?:[-*]\s*)?\*\*\b{alias}\b\s*[-:]?\*\*\s*(.+)$",  # * **alias:** value
        rf"^(?:[-*]\s*)?\*\*\b{alias}\b\s*[-:]\s*(.+)\*\*$",  # * **alias - value**
        rf"^(?:[-*•‣⁃▪‧·~+]*\s*)?\b{alias}\b\s*[-:]\s*(.+)$",  # * alias: value (word boundary)
        rf"^(?:[-*•‣⁃▪‧·~+]*\s*)?\b{alias}\b\s+[-:]\s*(.+)$",  # * alias - value (word boundary)
        rf"^[^\w\s]?\s*\*\b{alias}\b\*\s*[-:]\s*(.+)$",  # emoji-prefixed *alias:* value
        rf"^(?:[-*•‣⁃▪‧·~+]\s*)?\#\#\b{alias}\b\#\#\s*[-:]\s*(.+)$",  # ##alias## - value
        rf"^(?:[-*]\s*)?__{alias}:\__\s*(.+)$",  # __alias:__ value
        rf"^(?:[-*]\s*)?\*\*\b{alias}\b\s*//\*\*\s*(.+)$",  # **alias //** value
        # more specific cases
        rf"^[^\w\s]\s*\*+\s*\b{alias}\b[-:]\s*\*+\s*(.*)$",  # emoji-prefixed *alias:* value
        rf"^[^\w\s]\s*\*+\s*\b{alias}\b\s*\*+[-:]\s*(.*)$",  # emoji-prefixed *alias:* value
        # simple space format: Field product name (no colon/dash) - only
        # when no other words between field and value
        rf"^\b{alias}\b\s+(?![^:]*:)(?![^\-]*\-)(.+)$",  # Field product
        # name (no colon/dash, no other words)
    ]
