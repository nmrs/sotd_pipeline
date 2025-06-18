# Brush Matching Phase Specification

## Goal

Match and normalize shaving brush metadata from the `brush` field extracted during the extraction phase using a sophisticated strategy pattern with intelligent handle/knot separation.

## Input

A single `brush` string provided by the extraction phase. This string may contain:
- Simple brush descriptions: `"Simpson Chubby 2"`
- Complex handle/knot combinations: `"DG B15 w/ C&H Zebra"`
- Mixed specifications: `"Elite 26mm Boar handle w/ Declaration B10"`

## Architecture

The system uses a **Strategy Pattern** with multiple specialized matching strategies tried in priority order, combined with intelligent handle/knot splitting and content analysis.

### Strategy Priority Order (Most to Least Specific)

1. **KnownBrushMatchingStrategy** - Exact catalog matches from `known_brushes` section
2. **DeclarationGroomingBrushMatchingStrategy** - DG-specific patterns with smart brand detection
3. **ChiselAndHoundBrushMatchingStrategy** - C&H versioned knots (V10-V27)
4. **OmegaSemogueBrushMatchingStrategy** - Omega/Semogue brand patterns
5. **ZenithBrushMatchingStrategy** - Zenith brand patterns  
6. **OtherBrushMatchingStrategy** - Generic brand patterns from `other_brushes` section

## Intelligent Handle/Knot Splitting

### Delimiter Recognition
The system recognizes various delimiters and applies semantic understanding:

- **`" w/ "`, `" with "`** - Knot-ambiguous delimiters (requires content analysis)
- **`" in "`** - Handle-primary delimiter  
- **`" / "`, `"/"`, `" - "`** - Neutral delimiters

### Content Analysis Scoring
Uses `_score_as_handle()` to determine which part is likely the handle:

**Handle Indicators (+points):**
- Contains "handle" keyword (+10)
- Matches `handles.yaml` patterns (+6 to +12 based on section)
- Handle-related terms: "stock", "custom", "artisan", "turned" (+2 each)

**Knot Indicators (-points):**
- Fiber types: "badger", "boar", "synthetic" (-8)
- Size patterns: "26mm" (-6)
- Versioning patterns: "V20" (-6)
- Multiple brush strategy matches (-4 to -8)

### Example Processing
```
Input: "DG B15 w/ C&H Zebra"
1. Split on " w/ " → ["DG B15", "C&H Zebra"]  
2. Score "DG B15" as handle: -4 (brush strategy match)
3. Score "C&H Zebra" as handle: +8 (handle pattern match)
4. Result: Handle="C&H Zebra", Knot="DG B15"
5. Match knot against strategies → Declaration Grooming B15
6. Match handle against handles.yaml → Chisel & Hound
```

## Fiber and Knot Size Strategy Tracking

The system tracks the **source** of each attribute:

### Strategy Types
- **`"user_input"`** - Explicitly specified by user (e.g., "26mm Boar")
- **`"yaml"`** - From catalog data (authoritative)
- **`"default"`** - Brand default values
- **`"conflict"`** - User input conflicts with catalog (both recorded)

### Resolution Priority
1. **YAML exact fields** (highest priority - authoritative manufacturer data)
2. **Parsed user input** (if no YAML field present)
3. **YAML default fields** (fallback only)
4. **Unset** (if no information available)

### Conflict Handling
When user input conflicts with catalog data:
```python
# User says "Synthetic", catalog says "Badger"
{
    "fiber": "Badger",  # YAML wins
    "fiber_strategy": "yaml",
    "fiber_conflict": "user_input: Synthetic"  # Conflict recorded
}
```

## Output Schema

```yaml
brand: string | null                    # Brush manufacturer
model: string | null                    # Brush model/name
fiber: "Badger" | "Boar" | "Synthetic" | null  # Knot fiber type
knot_size_mm: float | null             # Knot diameter in millimeters
handle_maker: string | null            # Handle manufacturer (if different from brush brand)
_matched_by_strategy: string           # Which strategy produced the match
_pattern_used: string                  # Regex pattern that matched
fiber_strategy: "user_input" | "yaml" | "default"    # Source of fiber information
knot_size_strategy: "user_input" | "yaml" | "default"  # Source of knot size
fiber_conflict: string | null          # User input if conflicted with catalog
knot_size_conflict: float | null       # User input if conflicted with catalog
match_type: "exact" | "alias" | "brand" | "fiber" | "knot" | "artisan" | "unmatched"
source_text: string                    # Original input text
```

## Brand-Specific Intelligence

### Declaration Grooming Strategy
- **Default matching**: Standalone patterns like `"B2"`, `"B15"` default to Declaration Grooming
- **Brand rejection**: Explicit other brands prevent false matches: `"Zenith B2"` → Zenith (not DG)
- **Context awareness**: `"DG B2"` → Declaration Grooming (explicit context)

### Chisel & Hound Strategy  
- **Version range**: Handles V10-V27 versioned knots
- **Abbreviation support**: "C&H", "Chisel & Hound", "chis hou"
- **Boundary validation**: V9 and V28 rejected (outside known range)

### Zenith/Omega/Semogue Strategies
- **Brand-specific defaults**: Zenith → Boar default, Omega → Boar default
- **Series recognition**: B-series patterns, model number patterns
- **Fiber inference**: Uses brand-typical fiber types when not specified

## Data Sources

### Primary Catalogs
- **`data/brushes.yaml`** - Main brush catalog with known_brushes, declaration_grooming, other_brushes sections
- **`data/handles.yaml`** - Handle maker patterns (artisan_handles, manufacturer_handles, other_handles)

### Catalog Structure Requirements
```yaml
# brushes.yaml
known_brushes:
  Brand Name:
    Model Name:
      fiber: "Badger|Boar|Synthetic"
      knot_size_mm: 26
      patterns:
        - "regex_pattern"

other_brushes:
  Brand Name:
    default: "Badger|Boar|Synthetic"    # Default fiber for brand
    knot_size_mm: 26                    # Optional default knot size  
    patterns:
      - "regex_pattern"

# handles.yaml  
artisan_handles:      # Highest priority
  Handle Maker:
    patterns:
      - "regex_pattern"
```

## Error Handling and Resilience

### Graceful Degradation
- **Missing catalogs**: Empty catalog handling
- **Invalid regex**: Pattern compilation errors logged and excluded
- **Strategy failures**: Continue to next strategy on exception
- **Malformed YAML**: Safe loading with error reporting

### Performance Optimizations
- **Pattern compilation**: Regex patterns compiled once at initialization
- **Strategy caching**: Results cached where appropriate
- **Priority ordering**: Most specific strategies tried first

## Testing Requirements

### Unit Test Coverage
- All regex patterns with positive/negative cases
- Boundary conditions (version ranges, size limits)
- Handle/knot splitting with various delimiters
- Fiber/knot size conflict detection and resolution
- Strategy priority order with overlapping patterns
- Error handling and edge cases

### Integration Test Coverage  
- Real catalog compatibility testing
- Production data validation
- Catalog change regression testing
- End-to-end workflow validation

## Future Enhancements

### Planned Improvements
- **Partial match extraction**: Return matched substrings rather than full input
- **Enhanced handle detection**: More sophisticated handle maker inference
- **Synonym expansion**: Handle common abbreviations and variations
- **Machine learning integration**: Pattern learning from user corrections

### Backwards Compatibility
- All changes maintain existing API contracts
- Legacy pattern support preserved
- Gradual migration strategies for breaking changes

## Assumptions and Limitations

### Current Assumptions
- Only one brush matched per comment
- Input restricted to structured `brush` field from extraction
- Regex-based matching sufficient for current accuracy requirements

### Known Limitations
- Complex multi-brush descriptions may not parse perfectly
- Regional naming variations may require pattern updates
- New brush releases require catalog maintenance

This specification reflects the current implementation as of the latest codebase review and should be maintained as the system evolves.
