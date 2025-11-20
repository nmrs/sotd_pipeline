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
    Get extraction patterns for a field alias, ordered by frequency/priority.
    
    Patterns are tried in order (0=highest priority, last=lowest priority).
    Patterns 0-13 have explicit markers (colon : or dash -).
    Pattern 14 is ambiguous (no explicit markers) and must remain last.
    
    Order is based on actual usage frequency from 2020-2025 data analysis.
    See docs/extraction_pattern_priorities.md for priority details.
    """
    return [
        # Pattern 0: Markdown bold: * **alias:** value (73.17% usage - most common)
        # Colon/dash BEFORE second ** (e.g., * **Razor:** Blackbird)
        # BUG FIX: Require colon/dash (changed from optional [-:]? to required [-:])
        rf"^(?:[-*]\s*)?\*\*\b{alias}\b\s*[-:]\s*\*\*\s*(.+)$",  # * **alias:** value
        # Pattern 1: Simple explicit: Field: Value (20.66% usage - second most common)
        rf"^(?:[-*•‣⁃▪‧·~+]*\s*)?\b{alias}\b\s*[-:]\s*(.+)$",  # * alias: value (word boundary)
        # Pattern 2: Markdown bold: * **alias**: value (2.67% usage)
        # Colon/dash AFTER second ** (e.g., * **Razor**: Blackbird)
        rf"^(?:[-*]\s*)?\*\*\b{alias}\b\*\*\s*[-:]\s*(.+)$",  # * **alias**: value
        # Pattern 3: Emoji-prefixed: *alias:* value (0.50% usage)
        rf"^[^\w\s]?\s*\*\b{alias}\b\*\s*[-:]\s*(.+)$",  # emoji-prefixed *alias:* value
        # Pattern 5: Emoji-prefixed: *alias:* value variant 2 (0.43% usage)
        rf"^[^\w\s]\s*\*+\s*\b{alias}\b\s*\*+[-:]\s*(.*)$",  # emoji-prefixed *alias:* value (variant 2)
        # Pattern 6: Markdown bold: * **Field** Value no separator (0.20% usage)
        # No colon/dash, handles both **razor** and **razor ** (space before closing **)
        # (e.g., * **Razor** Blackbird, * **Razor**Blackbird, * **razor ** value, - **Razor** Blackbird, **Razor** Blackbird)
        rf"^(?:[-*]\s*)?\*\*\b{alias}\b\s*\*\*\s*(.+)$",  # * **Field** Value (no separator, space optional before closing **)
        # Pattern 7: Emoji-prefixed: *alias:* value variant (0.16% usage)
        rf"^[^\w\s]\s*\*+\s*\b{alias}\b[-:]\s*\*+\s*(.*)$",  # emoji-prefixed *alias:* value (variant)
        # Pattern 8: Markdown bold: * **alias - value** (0.07% usage)
        rf"^(?:[-*]\s*)?\*\*\b{alias}\b\s*[-:]\s*(.+)\*\*$",  # * **alias - value**
        # Pattern 9: Underscore: __alias:__ value (0.04% usage)
        rf"^(?:[-*]\s*)?__{alias}:\__\s*(.+)$",  # __alias:__ value
        # Pattern 10: Forward slash: **alias //** value (0.02% usage)
        rf"^(?:[-*]\s*)?\*\*\b{alias}\b\s*//\*\*\s*(.+)$",  # **alias //** value
        # Pattern 11: Checkmark: ✓Field: Value (0.00% usage)
        rf"^✓\s*\b{alias}\b\s*[-:]\s*(.+)$",  # ✓Field: Value or ✓ Field: Value
        # Pattern 12: Double hash: ##alias## - value (0.00% usage)
        rf"^(?:[-*•‣⁃▪‧·~+]\s*)?\#\#\b{alias}\b\#\#\s*[-:]\s*(.+)$",  # ##alias## - value
        # Pattern 13: Simple explicit: Field - Value (0.00% usage)
        rf"^(?:[-*•‣⁃▪‧·~+]*\s*)?\b{alias}\b\s+[-:]\s*(.+)$",  # * alias - value (word boundary)
        # Pattern 14: Ambiguous format (0.08% usage - MUST REMAIN LAST)
        # This pattern is tried last and only matches if no explicit markers found
        rf"^\b{alias}\b\s+(?![^:]*:)(?![^\-]*\-)(.+)$",  # Field product (no colon/dash)
    ]
