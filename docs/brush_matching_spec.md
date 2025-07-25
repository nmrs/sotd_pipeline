# Brush Matching Specification

## Catalog Brushes vs. Combo Brushes

- **Catalog-driven brushes**: These are brushes that are explicitly defined in the catalog (e.g., `Simpson Chubby 2`, `Muninn Woodworks/EldrormR Industries / BFM`). They represent complete, commercially available products. For these, the matcher preserves the top-level `brand` and `model` fields AND populates the `handle` and `knot` subsections to reflect the complete brush. This provides both backward compatibility and the new unified structure.

- **Combo brushes**: These are user-assembled or dynamically split brushes that do **not** match any known brush in the catalog. The matcher splits the input into handle and knot components and matches each separately. For these, the matcher clears the top-level `brand` and `model` fields (sets them to `None`) and only populates the `handle` and `knot` subsections.

### Implementation Rule
- **For catalog-driven brushes**: Preserve top-level `brand`/`model` AND populate `handle`/`knot` sections with the same values to represent the complete brush.
- **For combo brushes**: Clear top-level `brand`/`model` (set to `None`) and only populate `handle`/`knot` sections.

This ensures that reporting, aggregation, and user-facing output are correct for both known products and user combos.

---

## Goal

Match and normalize shaving brush metadata from the `brush` field extracted during the extraction phase using a sophisticated strategy pattern with intelligent handle/knot separation.

## Input

A single `brush` string provided by the extraction phase. This string may contain:
- Simple brush descriptions: `"Simpson Chubby 2"`
- Complex handle/knot combinations: `"DG B15 w/ C&H Zebra"`
- Mixed specifications: `"Elite 26mm Boar handle w/ Declaration B10"`

## Matching Priority Order

1. **Correct Matches File**: If the input matches an entry in `data/correct_matches.yaml`, it is prioritized. The match result will have `match_type: exact` and will include all catalog fields for the matched brush.
2. **Regex Patterns**: If not found in the correct matches file, regex patterns from the YAML catalogs are used. These matches have `match_type: regex` and also include all catalog fields.
3. **Fallbacks**: Brand/alias/other fallback strategies as before.

### Enhanced Correct Matches Integration

The system now checks correct matches at multiple levels:

#### **Step 0: Full String Correct Matches**
- Check the entire input string against `brush` section in correct_matches.yaml
- Highest priority for complete brush matches

#### **Step 1: Split Component Correct Matches** 
- After splitting into handle and knot components, check each component individually
- Handle component checked against `handle` section in correct_matches.yaml
- Knot component checked against `knot` section in correct_matches.yaml
- Correct matches take priority over strategy-based matching for individual components

#### **Step 3: Dual Component Fallback Correct Matches**
- When attempting dual component matching on the entire string
- Check handle component against `handle` section in correct_matches.yaml
- Check knot component against `knot` section in correct_matches.yaml
- Correct matches take priority over strategy-based matching for individual components

### Correct Matches Priority Hierarchy
1. **Full String Correct Match** (Step 0) - Highest priority
2. **Split Component Correct Matches** (Step 1) - Component-level validation
3. **Dual Component Fallback Correct Matches** (Step 3) - Component-level validation
4. **Strategy-Based Matching** - Fallback when correct matches not found

## Output Structure

```python
{
    "original": "input_string",
    "matched": {
        "brand": str | None,
        "model": str | None, 
        "fiber": str | None,
        "knot_size_mm": float | None,
        # Removed redundant fields: handle_maker, knot_maker
        "handle": {
            "brand": str | None,
            "model": str | None,
            "source_text": str | None,
            "_matched_by": str | None,  # Strategy attribution
            "_pattern": str | None       # Pattern used for matching
        } | None,
        "knot": {
            "brand": str | None,
            "model": str | None,
            "fiber": str | None,
            "knot_size_mm": float | None,
            "source_text": str | None,
            "_matched_by": str | None,  # Strategy attribution
            "_pattern": str | None       # Pattern used for matching
        } | None,
        "user_intent": str | None,      # "handle_primary" | "knot_primary" | None
    } | None,
    "match_type": "exact|regex|alias|brand|fiber|knot|artisan|unmatched" | None,
    "pattern": str | None
}
```

**Note:**
- The `handle` and `knot` subsections are always present in the output (when information is available), regardless of whether the match was catalog-driven or split-driven.
- For catalog-driven matches (e.g., BFM), these subsections are populated directly from the catalog's nested `handle` and `knot` fields if present. For split/strategy matches, they are inferred from the input and matching logic.
- **New fields**: `source_text` provides the original text that was matched for each component, `_matched_by` indicates which strategy was used, and `_pattern` shows the specific pattern that matched.
- **Removed fields**: `handle_maker` and `knot_maker` are no longer included as they were redundant with the handle/knot section structure.

### Example Output (Simple Catalog Brush, e.g., Simpson Chubby 2)
```python
{
    "original": "Simpson Chubby 2",
    "matched": {
        "brand": "Simpson",
        "model": "Chubby 2",
        "fiber": "Badger",
        "knot_size_mm": 27,
        "handle": {
            "brand": "Simpson",
            "model": "Chubby 2",
            "source_text": "Simpson Chubby 2",
            "_matched_by": "known_brush",
            "_pattern": "\\bchubby\\s*2\\b"
        },
        "knot": {
            "brand": "Simpson", 
            "model": "Chubby 2",
            "fiber": "Badger",
            "knot_size_mm": 27,
            "source_text": "Simpson Chubby 2",
            "_matched_by": "known_brush",
            "_pattern": "\\bchubby\\s*2\\b"
        }
    },
    "match_type": "regex",
    "pattern": "\\bchubby\\s*2\\b"
}
```

### Example Output (Complex Catalog Brush, e.g., BFM)
```python
{
    "original": "Muninn Woodworks BFM",
    "matched": {
        "brand": "Muninn Woodworks/EldrormR Industries",
        "model": "BFM",
        "fiber": "Synthetic",
        "knot_size_mm": 50,
        "handle": {
            "brand": "Muninn Woodworks",
            "model": None,
            "source_text": "Muninn Woodworks BFM",
            "_matched_by": "known_brush",
            "_pattern": "\\bbfm\\b"
        },
        "knot": {
            "brand": "Moti",
            "model": "Motherlode",
            "fiber": "Synthetic",
            "knot_size_mm": 50,
            "source_text": "Muninn Woodworks BFM",
            "_matched_by": "known_brush",
            "_pattern": "\\bbfm\\b"
        }
    },
    "match_type": "regex",
    "pattern": "\\bbfm\\b(.*50mm)?"
}
```

## Integration with correct_matches.yaml

- The file `data/correct_matches.yaml` contains manually confirmed brush matches.
- If a brush string matches an entry in this file, it is matched directly, and all catalog fields are included in the output.
- This takes precedence over all regex and fallback strategies.
- The `match_type` will be `exact` for these matches.

## Architecture

The system uses a **Strategy Pattern** with multiple specialized matching strategies tried in priority order, combined with intelligent handle/knot splitting and content analysis.

### Matching Steps (Sequential Processing)

1. **Step 0: Correct Matches Check** - Check entire input against `brush` section in correct_matches.yaml
2. **Step 1: Composite Brush Splitting** - Split input into handle and knot components using delimiters
   - Check handle component against `handle` section in correct_matches.yaml
   - Check knot component against `knot` section in correct_matches.yaml
   - Fall back to strategy-based matching for individual components
3. **Step 2: Complete Brush Matching** - Apply brush-specific strategies to full string
4. **Step 3: Dual Component Fallback** - Run handle and knot matchers on entire string
   - Check handle component against `handle` section in correct_matches.yaml
   - Check knot component against `knot` section in correct_matches.yaml
   - Fall back to strategy-based matching for individual components
   - Create composite brush if both components match

### Strategy Priority Order (Within Each Step)

1. **Correct Matches File** (highest priority within each step)
2. **KnownBrushMatchingStrategy** - Exact catalog matches from `known_brushes` section
3. **DeclarationGroomingBrushMatchingStrategy** - DG-specific patterns with smart brand detection
4. **ChiselAndHoundBrushMatchingStrategy** - C&H versioned knots (V10-V27)
5. **OmegaSemogueBrushMatchingStrategy** - Omega/Semogue brand patterns
6. **ZenithBrushMatchingStrategy** - Zenith brand patterns  
7. **OtherBrushMatchingStrategy** - Generic brand patterns from `other_brushes` section

## Intelligent Handle/Knot Splitting

### Delimiter Recognition
The system recognizes various delimiters and applies semantic understanding:

- **`" w/ "`, `" with "`** - Knot-ambiguous delimiters (requires content analysis)
- **`" in "`** - Handle-primary delimiter  
- **`" / "`, `"/"`, `" - "`** - Neutral delimiters

### Data-Driven Validation and Real-World Patterns

The brush splitter logic has been validated against real SOTD data to ensure it handles actual community usage patterns correctly.

#### Real-World Data Analysis
- **Analyzed 5+ months of real SOTD data** (9+ years available)
- **Found 0 cases** where both " in " and " x " appear together in the same brush string
- **Confirmed realistic patterns** from actual community data

#### Common Real-World Patterns

**Handle/Knot Combinations:**
- `"Dogwood Handcrafts/Zenith B2 Boar"` → Handle: "Dogwood Handcrafts", Knot: "Zenith B2 Boar"
- `"Mozingo/Declaration B2"` → Handle: "Mozingo", Knot: "Declaration B2"
- `"Declaration B2 in Mozingo handle"` → Handle: "Mozingo handle", Knot: "Declaration B2"

**Brand Collaborations:**
- `"Druidia x Mammoth 26mm SHD"` → Brand collaboration (not handle/knot split)
- `"AP Shaveco x Declaration Grooming B10"` → Brand collaboration (not handle/knot split)

**Size Specifications:**
- `"24mm x 51mm"`, `"65mm x 30mm"` → Size specifications (not delimiters)
- `"28mm x 52mm"` → Knot specifications (diameter x loft)

#### Test Case Validation
**Before (unrealistic test cases):**
- ❌ `"Declaration B2 in 26mm x 52mm x 48mm"` (doesn't exist in real data)
- ❌ `"Zenith B2 / 28mm x 52mm"` (unrealistic pattern)

**After (realistic test cases):**
- ✅ `"Declaration B2 in Mozingo handle"` → `('Mozingo handle', 'Declaration B2', 'handle_primary')`
- ✅ `"Dogwood Handcrafts/Zenith B2 Boar"` → `('Dogwood Handcrafts', 'Zenith B2 Boar', 'high_reliability')`

#### Key Insights from Real Data
1. **"Zenith B2"** = Zenith brand B2 knot (not Declaration Grooming)
2. **"28mm x 52mm"** = knot specifications (diameter x loft), not a handle
3. **Real data patterns** are much simpler and more predictable than contrived test cases
4. **Brand collaborations** use " x " but are not handle/knot splits
5. **Size specifications** with " x " are not delimiters

#### Implementation Impact
- **Test cases updated** to use realistic patterns from actual SOTD data
- **Delimiter detection** works correctly with real-world patterns
- **All 33 brush splitter tests pass** with realistic data validation
- **No breaking changes** to existing functionality

### Dual Component Fallback Enhancement

When splitting fails or no clear delimiter is present, the system now includes an enhanced fallback mechanism:

#### **Step 3: Dual Component Fallback**
- **Purpose**: Handle cases where both handle and knot components are present without clear delimiters
- **Example**: `"Rad Dinosaur G5C"` (Rad Dinosaur handle + AP Shave Co G5C knot)
- **Process**: 
  1. Run handle matcher on entire string
  2. Run knot matcher on entire string  
  3. If both return valid matches, create composite brush structure
  4. Detect user intent based on component order in original string

#### **User Intent Tracking**
- **`"handle_primary"`**: Handle component appears first in input string
- **`"knot_primary"`**: Knot component appears first in input string
- **Application**: Tracks user's primary focus for both split and fallback scenarios
- **Example**: `"G5C Rad Dinosaur"` → `"knot_primary"`, `"Rad Dinosaur G5C"` → `"handle_primary"`

#### **Dual Component Validation**
- **Same-brand makers**: Valid dual component matches (e.g., "Zenith Boar" with Zenith handle and knot)
- **Different-brand makers**: Standard dual component validation
- **Priority**: Dual component matches always take priority over single component matches in fallback

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

## Fiber Strategy Tracking

The system tracks the **source** of fiber information:

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

**Note**: Knot size processing has been moved to the enrich phase for better conflict resolution and catalog data preservation.

## Output Schema

```yaml
brand: string | null                    # Brush manufacturer
model: string | null                    # Brush model/name
fiber: "Badger" | "Boar" | "Synthetic" | null  # Knot fiber type
knot_size_mm: float | null             # Knot diameter in millimeters
# Removed redundant fields: handle_maker, knot_maker
handle:                                 # Handle subsection (if available)
  brand: string | null
  model: string | null
  source_text: string | null            # Original text that was matched
  _matched_by: string | null           # Strategy that produced the match
  _pattern: string | null              # Regex pattern that matched
knot:                                   # Knot subsection (if available)
  brand: string | null
  model: string | null
  fiber: string | null
  knot_size_mm: float | null
  source_text: string | null            # Original text that was matched
  _matched_by: string | null           # Strategy that produced the match
  _pattern: string | null              # Regex pattern that matched
user_intent: "handle_primary" | "knot_primary" | null  # User's primary focus
fiber_strategy: "user_input" | "yaml" | "default"    # Source of fiber information
match_type: "exact" | "regex" | "alias" | "brand" | "fiber" | "knot" | "artisan" | "unmatched"
pattern: string | null                  # Overall pattern that matched
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
