# Extraction Pattern Priority Buckets

This document defines the priority system for extraction patterns used in the SOTD pipeline extract phase. Examples are shown for the "Razor" field, but patterns apply to all fields (razor, blade, brush, soap).

## Bucket 1 (High Priority - Patterns 0-14 with Explicit Markers)

These patterns have explicit field markers (colon `:` or dash `-`) and are unambiguous. All of these should be tried before the ambiguous pattern (pattern 15).

**Pattern Priority Within Bucket 1:**
- **Pattern 0**: Requires list item prefix (`*` or `-`) - highest priority for list items
- **Pattern 0b**: No list item prefix - lower priority for narrative text
- **Patterns 1-14**: Other explicit marker patterns

## Bucket 1.5 (Medium Priority - Patterns 14a-14b with Equals Sign)

These patterns have explicit field markers using equals sign (`=`) and have medium priority (after `:` and `-` but before ambiguous patterns).

**Pattern Priority Within Bucket 1.5:**
- **Pattern 14a**: Requires list item prefix (`*` or `-`) with equals sign - `* Field = Value`
- **Pattern 14b**: No list item prefix with equals sign - `Field = Value`

### Simple Formats
- `Razor: Value`
- `Razor : Value` (with space before colon)
- `Razor- Value` (no space before dash)
- `Razor - Value` (with space before dash)
- `* Razor: Value` (with bullet)
- `- Razor: Value` (with dash bullet)
- `* Razor - Value` (with bullet and dash separator)
- `- Razor - Value` (with dash bullet and dash separator)
- `* Razor = Value` (with bullet and equals sign - medium priority)
- `Razor = Value` (with equals sign - medium priority)

### Markdown/Formatting Formats
- `* **Razor:** Value` (markdown bold with colon)
- `* **Razor**: Value` (markdown bold with colon, space before colon)
- `* **Razor** - Value` (markdown bold with dash)
- `**Razor:** Value` (markdown bold, no bullet)
- `**Razor**: Value` (markdown bold, no bullet, space before colon)
- `* **Razor - Value**` (markdown bold with dash, value also bold)
- `- **Razor:** Value` (dash bullet with markdown bold)
- `* **Razor** Value` (markdown bold, no separator - still has markdown formatting)
- `##Razor## - Value` (double hash format)
- `* ##Razor## - Value` (bullet with double hash)
- `__Razor:__ Value` (underscore format)
- `* __Razor:__ Value` (bullet with underscore)
- `* **Razor //** Value` (forward slash separator)
- `🪒 *Razor:* Value` (emoji-prefixed with markdown)
- `*Razor:* Value` (markdown italic with colon)
- `*Razor - Value*` (markdown italic with dash)

### Special Formats
- `✓Razor: Value` (checkmark format - single pattern handles both `✓Razor:` and `✓ Razor:`)
- `✓Razor - Value` (checkmark with dash - single pattern handles both `✓Razor -` and `✓ Razor -`)

## Bucket 2 (Low Priority - Pattern 15, Ambiguous)

This pattern has NO explicit markers (no colon, dash, or equals sign) and is prone to false positives. Should only be tried after all explicit marker patterns fail.

- Pattern 15: `Razor Value` (just space, no colon/dash/equals - matches "Razor Game Changer" but also "Razor was still smooth")

## Notes

- Patterns are currently ordered 0-15 in the code (18 patterns total)
- Patterns 0-14: All have explicit markers (colon `:` or dash `-`) and are high priority
  - Pattern 0: Requires list item prefix (`*` or `-`) - preferred for structured lists
  - Pattern 0b: No list item prefix - matches narrative text with explicit markers
- Patterns 14a-14b: Have explicit markers with equals sign (`=`) and are medium priority
  - Pattern 14a: Requires list item prefix (`*` or `-`) with equals sign
  - Pattern 14b: No list item prefix with equals sign
- Pattern 15: Ambiguous space format (no explicit markers) - the only problematic pattern and is lowest priority

## Implementation Status

✅ **COMPLETED**: Pattern priority system has been implemented. The extraction logic now iterates patterns first, then lines, ensuring high-priority patterns (0-14) are checked across all lines before low-priority pattern (15). Pattern 0 (with list item prefix) is tried before pattern 0b (without prefix), ensuring list items are preferred over narrative text.

## Previous Problem Cases (Now Fixed)

- `Razor was still smooth but was not effective cutter` - Previously matched Bucket 2 pattern 15
- `Razor: WECK Hair Shaper - Pink Scales` - Now correctly matches Bucket 1 pattern 6 (explicit marker), even when narrative text appears earlier

## Solution Implemented

The extraction logic now processes patterns in priority order:
- For each field, try pattern 0 on all lines, then pattern 0b on all lines, then pattern 1 on all lines, etc.
- Pattern 0 (with list item prefix) is tried before pattern 0b (without prefix), ensuring list items are preferred over narrative text
- Patterns with `:` and `-` markers (0-14) are tried before patterns with `=` markers (14a-14b)
- This ensures explicit markers (patterns 0-14, 14a-14b) are always preferred over ambiguous patterns (pattern 15), regardless of line order

### Cross-Alias Priority Enforcement

**IMPORTANT**: Pattern priority is enforced **across all aliases**, not per alias. This means:
- All pattern 0s (highest priority) for all aliases are tried before any pattern 1s
- All pattern 1s are tried before pattern 2s, etc.
- Patterns 14a-14b (equals sign, medium priority) are tried after patterns 0-14 but before pattern 15
- Pattern 15 (ambiguous, lowest priority) is only tried after all explicit patterns (0-14, 14a-14b) have been tried for all aliases

**Example**: For the soap field with aliases "soap" and "lather":
- Pattern 0 for "soap" is tried
- Pattern 0 for "lather" is tried
- Pattern 1 for "soap" is tried
- Pattern 1 for "lather" is tried
- ... (continues through all priority levels)
- Pattern 14a for "soap" is tried (equals sign with list prefix)
- Pattern 14a for "lather" is tried
- Pattern 14b for "soap" is tried (equals sign without list prefix)
- Pattern 14b for "lather" is tried
- Pattern 15 for "soap" is tried (only after all explicit patterns fail)
- Pattern 15 for "lather" is tried

This ensures that an explicit "Lather:" pattern (pattern 0) will always win over an equals sign pattern (pattern 14a/14b) or an ambiguous "Soap" pattern (pattern 15), even if the lower priority pattern appears earlier in the comment or earlier in the alias list.

