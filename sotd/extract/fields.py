import re
from typing import Optional

from sotd.utils.aliases import FIELD_ALIASES


def extract_field(line: str, field: str) -> Optional[str]:
    return _extract_field_line(line, field)


def extract_field_with_pattern(line: str, field: str, pattern: str) -> Optional[str]:
    """
    Try a specific pattern on a line for a field.

    Args:
        line: The line to check
        field: The field name (razor, blade, brush, soap)
        pattern: The regex pattern to try

    Returns:
        Extracted value if pattern matches, None otherwise
    """
    # Check exclusions first
    if field == "soap" and re.match(r"^lather\s+games", line, flags=re.IGNORECASE):
        return None
    if field == "razor" and re.match(r"^razor\s+test", line, flags=re.IGNORECASE):
        return None

    match = re.match(pattern, line, flags=re.IGNORECASE)
    if match:
        value = match.group(1).strip()
        return value
    return None


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
    """
    Get extraction patterns for a field alias, ordered by priority.

    Patterns are tried in order (0=highest priority, last=lowest priority).
    High-priority patterns (0-13) have explicit markers (colon : or dash -).
    Low-priority pattern (14) is ambiguous (no explicit markers).

    See docs/extraction_pattern_priorities.md for priority details.
    """
    return [
        # Pattern 0: Checkmark format: ✓Field: Value
        rf"^✓\s*\b{alias}\b\s*[-:]\s*(.+)$",  # ✓Field: Value or ✓ Field: Value
        # Pattern 1: Emoji bold format: * **Field** - Value
        rf"^\*\s*\*\*\b{alias}\b\*\*\s*[-:]\s*(.+)$",  # * **Field** - Value
        # Pattern 2: Emoji bold format: * **Field** Value (no separator)
        rf"^\*\s*\*\*\b{alias}\b\*\*\s*(.+)$",  # * **Field** Value (no separator)
        # Patterns 3-5: Markdown bold formats with explicit markers
        rf"^(?:[-*]\s*)?\*\*\b{alias}\b\*\*\s*[-:]?\s*(.+)$",  # * **alias**: value
        rf"^(?:[-*]\s*)?\*\*\b{alias}\b\s*[-:]?\*\*\s*(.+)$",  # * **alias:** value
        rf"^(?:[-*]\s*)?\*\*\b{alias}\b\s*[-:]\s*(.+)\*\*$",  # * **alias - value**
        # Pattern 6: Simple explicit format: Field: Value (HIGHEST PRIORITY for explicit markers)
        rf"^(?:[-*•‣⁃▪‧·~+]*\s*)?\b{alias}\b\s*[-:]\s*(.+)$",  # * alias: value (word boundary)
        # Pattern 7: Simple explicit format: Field - Value
        rf"^(?:[-*•‣⁃▪‧·~+]*\s*)?\b{alias}\b\s+[-:]\s*(.+)$",  # * alias - value (word boundary)
        # Patterns 8-13: Other formats with explicit markers
        rf"^[^\w\s]?\s*\*\b{alias}\b\*\s*[-:]\s*(.+)$",  # emoji-prefixed *alias:* value
        rf"^(?:[-*•‣⁃▪‧·~+]\s*)?\#\#\b{alias}\b\#\#\s*[-:]\s*(.+)$",  # ##alias## - value
        rf"^(?:[-*]\s*)?__{alias}:\__\s*(.+)$",  # __alias:__ value
        rf"^(?:[-*]\s*)?\*\*\b{alias}\b\s*//\*\*\s*(.+)$",  # **alias //** value
        rf"^[^\w\s]\s*\*+\s*\b{alias}\b[-:]\s*\*+\s*(.*)$",  # emoji-prefixed *alias:* value
        rf"^[^\w\s]\s*\*+\s*\b{alias}\b\s*\*+[-:]\s*(.*)$",  # emoji-prefixed *alias:* value
        # Pattern 14: Ambiguous format (LOWEST PRIORITY - no explicit markers)
        # This pattern is tried last and only matches if no explicit markers found
        rf"^\b{alias}\b\s+(?![^:]*:)(?![^\-]*\-)(.+)$",  # Field product (no colon/dash)
    ]
