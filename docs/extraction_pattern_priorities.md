# Extraction Pattern Priority Buckets

This document defines the priority system for extraction patterns used in the SOTD pipeline extract phase. Examples are shown for the "Razor" field, but patterns apply to all fields (razor, blade, brush, soap).

## Bucket 1 (High Priority - All Patterns with Explicit Markers)

These patterns have explicit field markers (colon `:` or dash `-`) and are unambiguous. All of these should be tried before the ambiguous pattern.

### Simple Formats
- `Razor: Value`
- `Razor : Value` (with space before colon)
- `Razor- Value` (no space before dash)
- `Razor - Value` (with space before dash)
- `* Razor: Value` (with bullet)
- `- Razor: Value` (with dash bullet)
- `* Razor - Value` (with bullet and dash separator)
- `- Razor - Value` (with dash bullet and dash separator)

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

## Bucket 2 (Low Priority - Ambiguous Pattern)

This pattern has NO explicit markers (no colon or dash) and is prone to false positives. Should only be tried after all explicit marker patterns fail.

- `Razor Value` (just space, no colon/dash - matches "Razor Game Changer" but also "Razor was still smooth")

## Notes

- Patterns are currently ordered 0-57 in the code
- Patterns 1-56: All have explicit markers (colon `:` or dash `-`) and should be high priority
- Pattern 57: Ambiguous space format (no explicit markers) - the only problematic pattern and should be lowest priority

## Current Problem Cases

- `Razor was still smooth but was not effective cutter` - Matches Bucket 2 pattern 57
- `Razor: WECK Hair Shaper - Pink Scales` - Should match Bucket 1 pattern 46, but gets skipped because Bucket 2 matched first

## Proposed Solution

Reorder patterns so all explicit marker patterns (Bucket 1) are tried first, then the ambiguous pattern (Bucket 2). This ensures explicit markers are always preferred over ambiguous patterns.

