# Enrich Phase Implementation Plan

This document tracks the step-by-step implementation of the SOTD Pipeline enrich phase. Each item can be checked off as completed, allowing us to stop and resume work at any point.

## Overview

The enrich phase performs sophisticated analysis requiring knowledge of matched products to extract detailed specifications and metadata that don't affect product identification.

**Key Architecture Decisions Made:**
- Enrich phase handles "sophisticated analysis requiring knowledge of the matched product first"
- Match phase focuses on "product identification"
- Self-determination pattern: each enricher decides its own applicability
- Field-focused routing: enrichers target specific fields ("blade", "razor", "brush", "soap")
- Fail-fast error handling for internal/logic errors
- Graceful handling for external/API errors

## Implementation Chunks

### Phase 1: Foundation Infrastructure
- [ ] **1.1** Create base enricher interface (`BaseEnricher`)
  - `target_field` property
  - `applies_to(record)` method
  - `enrich(field_data)` method
- [ ] **1.2** Create enricher registry/manager system
- [ ] **1.3** Set up basic testing framework for enrichers
- [ ] **1.4** Create core enrich module structure in `sotd/enrich/`

### Phase 2: Blade Count Enricher (Migration from Match)
- [ ] **2.1** Implement `BladeCountEnricher` class
- [ ] **2.2** Move blade count extraction regex patterns from `blade_matcher.py`
- [ ] **2.3** Add comprehensive tests for blade count extraction
- [ ] **2.4** Validate extraction accuracy against existing data

### Phase 3: Straight Razor Enricher
- [ ] **3.1** Implement `StraightRazorEnricher` class
- [ ] **3.2** Create grind extraction patterns (wedge, quarter hollow, half hollow, full hollow, etc.)
- [ ] **3.3** Create width extraction patterns (4/8", 5/8", 6/8", 7/8", 8/8")
- [ ] **3.4** Create point type extraction patterns (round, square, French, Spanish, etc.)
- [ ] **3.5** Add comprehensive tests with real comment examples
- [ ] **3.6** Handle multiple specification formats and edge cases

### Phase 4: DE Plate Enrichers
- [ ] **4.1** Implement `GameChangerEnricher` class
  - Gap detection (.68, .84, etc.)
  - Variant detection (Game Changer, Game Changer 2.0, Game Changer Jaws)
- [ ] **4.2** Implement `ChristopherBradleyEnricher` class  
  - Plate number extraction (A1-A9, B1-B10, C1-C8, D1-D8, E1-E4, F1-F4)
  - Material detection (stainless steel, titanium)
- [ ] **4.3** Add comprehensive tests for both enrichers
- [ ] **4.4** Validate against known product specifications

### Phase 5: CLI and I/O Infrastructure
- [ ] **5.1** Create `sotd/enrich/run.py` with CLI interface
  - `--month` flag support
  - `--range` flag support  
  - `--debug` flag for verbose output
  - `--force` flag to overwrite existing files
- [ ] **5.2** Create `sotd/enrich/save.py` for file I/O operations
  - Read from `data/matched/YYYY-MM.json`
  - Write to `data/enriched/YYYY-MM.json`
  - Include comprehensive metadata
- [ ] **5.3** Add enrich command to main CLI (`cli.py`)
- [ ] **5.4** Update Makefile with enrich phase targets

### Phase 6: Integration and Migration
- [ ] **6.1** Wire all enrichers into main enrich controller
- [ ] **6.2** Remove blade count extraction from `sotd/match/blade_matcher.py`
- [ ] **6.3** Update existing tests that rely on blade count in match phase
- [ ] **6.4** Integration testing with full pipeline
- [ ] **6.5** Performance validation and optimization

## Detailed Implementation Prompts

### Prompt 1: Foundation Infrastructure
- [ ] **P1** Create base enricher interface and registry system
  - BaseEnricher abstract class with required methods
  - EnricherRegistry for managing enricher instances
  - Basic error handling and logging infrastructure
  - Initial test framework structure

### Prompt 2: Blade Count Enricher Implementation  
- [ ] **P2** Implement BladeCountEnricher with migration from match phase
  - Move regex patterns from blade_matcher.py
  - Implement extraction logic with comprehensive patterns
  - Add tests covering various count formats (numbers, words, ranges)
  - Ensure no functionality regression

### Prompt 3: Straight Razor Enricher Implementation
- [ ] **P3** Implement StraightRazorEnricher with comprehensive specification extraction
  - Grind type extraction (wedge, hollow variants)
  - Width extraction (fractional and decimal formats)
  - Point type extraction (multiple naming conventions)
  - Robust pattern matching and error handling

### Prompt 4: Game Changer Enricher Implementation
- [ ] **P4** Implement GameChangerEnricher for RazoRock Game Changer variants
  - Gap detection with decimal parsing
  - Variant identification (Game Changer vs 2.0 vs Jaws)
  - Product applicability logic (brand == "RazoRock" AND "Game Changer" in model)
  - Comprehensive test coverage

### Prompt 5: Christopher Bradley Enricher Implementation
- [ ] **P5** Implement ChristopherBradleyEnricher for Karve plates
  - Plate number extraction (A1-A9, B1-B10, C1-C8, D1-D8, E1-E4, F1-F4)
  - Material detection (stainless steel, titanium)  
  - Product applicability logic (brand == "Karve" AND "Christopher Bradley" in model)
  - Handle various naming formats and abbreviations

### Prompt 6: CLI Interface Implementation
- [ ] **P6** Create CLI interface following existing phase patterns
  - `sotd/enrich/run.py` with argument parsing
  - Support for --month, --range, --debug, --force flags
  - Integration with main CLI (`cli.py`)
  - Consistent help text and error messages

### Prompt 7: File I/O Implementation  
- [ ] **P7** Create file I/O operations with metadata generation
  - `sotd/enrich/save.py` for reading matched data and writing enriched data
  - Comprehensive metadata including processing timestamps
  - Statistics on enricher application (records processed, fields enriched)
  - Error handling for file operations

### Prompt 8: Integration and Final Migration
- [ ] **P8** Complete integration and clean up match phase
  - Wire all enrichers into main controller
  - Remove blade count extraction from match phase
  - Update affected tests and documentation
  - Final validation and performance testing

## Testing Strategy

### Unit Tests Required
- [ ] Test each enricher in isolation with mock data
- [ ] Test enricher registry and management system
- [ ] Test CLI argument parsing and validation
- [ ] Test file I/O operations and error handling
- [ ] Test metadata generation and statistics

### Integration Tests Required  
- [ ] Test full enrich phase with real matched data
- [ ] Test pipeline integration (match → enrich)
- [ ] Test CLI integration with main application
- [ ] Validate output format compatibility

### Validation Tests Required
- [ ] Compare blade count extraction accuracy before/after migration
- [ ] Validate enricher applicability logic with edge cases
- [ ] Test performance with large datasets
- [ ] Validate metadata completeness and accuracy

## Data Structure Changes

### Input Format (from match phase)
```json
{
  "metadata": {...},
  "comments": [
    {
      "comment_id": "...",
      "blade": {"brand": "...", "model": "..."},
      "razor": {"brand": "...", "model": "..."},
      "brush": {"brand": "...", "model": "..."},
      "soap": {"brand": "...", "model": "..."}
    }
  ]
}
```

### Output Format (enriched data)
```json
{
  "metadata": {...},
  "comments": [
    {
      "comment_id": "...",
      "blade": {"brand": "...", "model": "..."},
      "razor": {"brand": "...", "model": "..."},
      "brush": {"brand": "...", "model": "..."},
      "soap": {"brand": "...", "model": "..."},
      "enriched": {
        "blade": {
          "use_count": 3,
          "_enriched_by": "BladeCountEnricher",
          "_extraction_source": "user_comment"
        },
        "razor": {
          "grind": "full_hollow",
          "width": "6/8",
          "point_type": "round",
          "_enriched_by": "StraightRazorEnricher", 
          "_extraction_source": "user_comment"
        }
      }
    }
  ]
}
```

## Files to be Created/Modified

### New Files
- [ ] `sotd/enrich/enricher.py` - Base enricher interface
- [ ] `sotd/enrich/registry.py` - Enricher registry system
- [ ] `sotd/enrich/blade_enricher.py` - Blade count enricher
- [ ] `sotd/enrich/straight_razor_enricher.py` - Straight razor enricher
- [ ] `sotd/enrich/game_changer_enricher.py` - Game Changer enricher
- [ ] `sotd/enrich/christopher_bradley_enricher.py` - Christopher Bradley enricher
- [ ] `sotd/enrich/run.py` - CLI interface
- [ ] `sotd/enrich/save.py` - File I/O operations
- [ ] `tests/enrich/test_*.py` - Comprehensive test suite

### Modified Files
- [ ] `sotd/match/blade_matcher.py` - Remove blade count extraction
- [ ] `cli.py` - Add enrich command
- [ ] `Makefile` - Add enrich targets
- [ ] Affected test files in `tests/match/`

## Success Criteria

- [ ] All enrichers successfully extract their target specifications
- [ ] No regression in blade count extraction accuracy after migration
- [ ] CLI interface matches existing phase patterns and conventions
- [ ] File I/O operations handle errors gracefully
- [ ] Comprehensive test coverage (>90%) for all new code
- [ ] Integration with existing pipeline phases works seamlessly
- [ ] Performance meets pipeline standards (reasonable processing time)
- [ ] Documentation is complete and accurate

## Notes and Decisions Made

- **Architecture Philosophy**: Enrich phase handles sophisticated analysis requiring knowledge of matched products, while match phase focuses on product identification
- **Error Handling**: Fail fast for internal/logic errors, handle gracefully for external/API errors  
- **Self-Determination Pattern**: Each enricher decides its own applicability rather than complex routing logic
- **Metadata Standards**: Always include `_enriched_by` and `_extraction_source` fields
- **Partial Extraction**: Include successfully extracted fields, set missing fields to null
- **Field-Focused Routing**: Each enricher targets specific field types

---

**Last Updated**: Initial creation
**Current Phase**: Ready to begin Phase 1 - Foundation Infrastructure
**Next Prompt**: P1 - Create base enricher interface and registry system 