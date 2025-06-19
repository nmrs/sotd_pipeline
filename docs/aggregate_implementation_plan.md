# Aggregate Phase Implementation Plan

## Project Overview
Build the aggregate phase of the SOTD pipeline that processes enriched data to generate statistical summaries for downstream reporting. The phase will calculate metrics for core categories (razors, blades, brushes, soaps, etc.) and output structured JSON data.

## Proposed File Organization

```
sotd/aggregate/
├── __init__.py                    # Package initialization
├── run.py                         # Main CLI entry point (Step 1)
├── load.py                        # Data loading module (Step 2)
├── engine.py                      # Core aggregation engine (Step 3)
├── processor.py                   # Orchestration pipeline (Step 8)
├── save.py                        # Output generation (Step 9)
├── aggregators/                   # Category-specific aggregators
│   ├── __init__.py
│   ├── base.py                    # Base aggregator class
│   ├── core/                      # Core product aggregators (Step 4)
│   │   ├── __init__.py
│   │   ├── razor_aggregator.py
│   │   ├── blade_aggregator.py
│   │   ├── brush_aggregator.py
│   │   └── soap_aggregator.py
│   ├── manufacturers/             # Manufacturer aggregators (Step 4)
│   │   ├── __init__.py
│   │   ├── razor_manufacturer_aggregator.py
│   │   ├── blade_manufacturer_aggregator.py
│   │   └── soap_maker_aggregator.py
│   ├── formats/                   # Format aggregators (Step 4)
│   │   ├── __init__.py
│   │   └── razor_format_aggregator.py
│   ├── brush/                     # Brush specialized aggregators (Step 5)
│   │   ├── __init__.py
│   │   ├── brush_handle_maker_aggregator.py
│   │   ├── brush_knot_maker_aggregator.py
│   │   ├── brush_fiber_aggregator.py
│   │   └── brush_knot_size_aggregator.py
│   ├── razor_specialized/         # Razor specialized aggregators (Step 6)
│   │   ├── __init__.py
│   │   ├── blackbird_plate_aggregator.py
│   │   ├── christopher_bradley_plate_aggregator.py
│   │   ├── game_changer_plate_aggregator.py
│   │   ├── super_speed_tip_aggregator.py
│   │   └── straight_razor/        # Straight razor specs
│   │       ├── __init__.py
│   │       ├── straight_width_aggregator.py
│   │       ├── straight_grind_aggregator.py
│   │       └── straight_point_aggregator.py
│   └── users/                     # User aggregators (Step 7)
│       ├── __init__.py
│       └── user_aggregator.py
└── utils/                         # Shared utilities
    ├── __init__.py
    ├── field_extractor.py         # Nested field access utilities
    ├── data_validator.py          # Data validation utilities
    └── normalizer.py              # Field normalization utilities
```

### Key Organizational Principles

#### 1. Clear Separation of Concerns
- **CLI Layer**: `run.py` - Entry point and argument handling
- **Data Layer**: `load.py`, `save.py` - I/O operations
- **Processing Layer**: `engine.py`, `processor.py` - Core logic
- **Aggregation Layer**: `aggregators/` - Category-specific logic

#### 2. Logical Grouping by Category
- **Core**: Basic product aggregations (razors, blades, brushes, soaps)
- **Manufacturers**: Brand-level aggregations
- **Formats**: Format-based aggregations
- **Brush**: Brush component aggregations
- **Razor Specialized**: Specialized razor aggregations
- **Users**: User-based aggregations

#### 3. Hierarchical Specialization
- **Base Class**: `aggregators/base.py` - Common functionality
- **Category Groups**: Logical groupings (core, manufacturers, etc.)
- **Specialized Subgroups**: Further specialization (straight_razor under razor_specialized)

#### 4. Utility Organization
- **Field Extraction**: Handle nested field access patterns
- **Data Validation**: Input validation and quality checks
- **Normalization**: Field value normalization

### Implementation Benefits

#### Maintainability
- Clear file organization makes it easy to find specific aggregators
- Logical grouping helps understand relationships between components
- Base class reduces code duplication

#### Extensibility
- Easy to add new aggregators by following the established pattern
- Clear structure for adding new categories
- Utility functions can be shared across aggregators

#### Testing
- Each aggregator can be tested independently
- Clear separation makes unit testing straightforward
- Utilities can be tested separately from business logic

#### Performance
- Can easily implement lazy loading of aggregators
- Clear structure for optimization opportunities
- Easy to add caching or parallel processing later

## Implementation Checklist

### Phase 1: Foundation & Core Structure

- [ ] **Step 1: Basic CLI Structure**
  - [ ] Create `sotd/aggregate/run.py` with main CLI entry point
  - [ ] Follow same argument pattern as other phases (--month, --year, --range, --start, --end, --out-dir, --debug, --force)
  - [ ] Add basic argument parsing and validation
  - [ ] Add placeholder for main processing logic
  - [ ] Include proper imports and error handling

- [ ] **Step 2: Data Loading Module**
  - [ ] Create `sotd/aggregate/load.py` for loading enriched data
  - [ ] Implement JSON loading with error handling
  - [ ] Add data validation for required fields
  - [ ] Add filtering for records with matched data
  - [ ] Include metadata extraction (total records, valid records, etc.)

- [ ] **Step 3: Core Aggregation Engine**
  - [ ] Create `sotd/aggregate/engine.py` with main aggregation logic
  - [ ] Implement base aggregator class with common functionality
  - [ ] Add field extraction utilities for nested data structures
  - [ ] Implement basic counting and grouping logic
  - [ ] Add sorting and limiting capabilities

- [ ] **Step 4: Category-Specific Aggregators**
  - [ ] Create `sotd/aggregate/aggregators/` directory
  - [ ] Implement core product aggregators:
    - [ ] `razor_aggregator.py` - aggregates `razor.matched.brand` + `razor.matched.model`
    - [ ] `blade_aggregator.py` - aggregates `blade.matched.brand` + `blade.matched.model`
    - [ ] `brush_aggregator.py` - aggregates `brush.matched.brand` + `brush.matched.model`
    - [ ] `soap_aggregator.py` - aggregates `soap.matched.maker` + `soap.matched.scent`
  - [ ] Implement manufacturer aggregators:
    - [ ] `razor_manufacturer_aggregator.py` - aggregates `razor.matched.brand`
    - [ ] `blade_manufacturer_aggregator.py` - aggregates `blade.matched.brand`
    - [ ] `soap_maker_aggregator.py` - aggregates `soap.matched.maker`
  - [ ] Implement format aggregators:
    - [ ] `razor_format_aggregator.py` - aggregates `razor.matched.format`

- [ ] **Step 5: Brush Specialized Aggregators**
  - [ ] Implement brush component aggregators:
    - [ ] `brush_handle_maker_aggregator.py` - aggregates `brush.matched.handle_maker`
    - [ ] `brush_knot_maker_aggregator.py` - aggregates `brush.matched.knot_maker`
    - [ ] `brush_fiber_aggregator.py` - aggregates `brush.matched.fiber` (fallback to `brush.enriched.fiber`)
    - [ ] `brush_knot_size_aggregator.py` - aggregates `brush.matched.knot_size_mm` (fallback to `brush.enriched.knot_size_mm`)

- [ ] **Step 6: Razor Specialized Aggregators**
  - [ ] Implement specialized razor aggregators:
    - [ ] `blackbird_plate_aggregator.py` - aggregates `razor.enriched.plate` for Blackland Blackbird
    - [ ] `christopher_bradley_plate_aggregator.py` - aggregates `razor.enriched.plate_type` + `razor.enriched.plate_level` for Karve CB
    - [ ] `game_changer_plate_aggregator.py` - aggregates `razor.enriched.gap` for RazoRock Game Changer
    - [ ] `super_speed_tip_aggregator.py` - aggregates `razor.enriched.super_speed_tip` for Gillette Super Speed
    - [ ] `straight_razor_spec_aggregator.py` - aggregates straight razor specifications:
      - [ ] `straight_width_aggregator.py` - aggregates `razor.enriched.width`
      - [ ] `straight_grind_aggregator.py` - aggregates `razor.enriched.grind`
      - [ ] `straight_point_aggregator.py` - aggregates `razor.enriched.point`

- [ ] **Step 7: User Aggregator**
  - [ ] Implement `user_aggregator.py` - aggregates `author` field
  - [ ] Add user statistics (total shaves per user)

### Phase 2: Data Processing & Output

- [ ] **Step 8: Data Processing Pipeline**
  - [ ] Create `sotd/aggregate/processor.py` to orchestrate aggregation
  - [ ] Implement sequential processing of all aggregators
  - [ ] Add progress tracking and logging
  - [ ] Include error handling for individual aggregators
  - [ ] Add data validation between steps

- [ ] **Step 9: Output Generation**
  - [ ] Create `sotd/aggregate/save.py` for output handling
  - [ ] Implement JSON output with proper formatting
  - [ ] Add metadata generation (timestamp, processing stats)
  - [ ] Include data validation before saving
  - [ ] Add backup/overwrite handling

- [ ] **Step 10: Integration & Testing**
  - [ ] Integrate all components in main CLI
  - [ ] Add comprehensive error handling
  - [ ] Implement debug logging
  - [ ] Add performance monitoring
  - [ ] Create integration tests

### Phase 3: Advanced Features

- [ ] **Step 11: Data Quality & Validation**
  - [ ] Add input data validation
  - [ ] Implement field normalization (case, whitespace)
  - [ ] Add null/missing value handling
  - [ ] Include data quality metrics in output

- [ ] **Step 12: Performance Optimization**
  - [ ] Optimize aggregation algorithms
  - [ ] Add memory usage monitoring
  - [ ] Implement efficient data structures
  - [ ] Add progress reporting for large datasets

- [ ] **Step 13: Configuration & Flexibility**
  - [ ] Add configurable aggregation parameters
  - [ ] Implement custom field mappings
  - [ ] Add aggregation rule customization
  - [ ] Include output format options

## Technical Requirements

### Data Access Patterns
- **Nested Field Access**: Handle `razor.matched.brand`, `brush.enriched.fiber` patterns
- **Fallback Logic**: Use `brush.matched.fiber` with fallback to `brush.enriched.fiber`
- **Conditional Aggregation**: Only aggregate specialized fields when parent conditions are met
- **Null Handling**: Properly handle null values and missing fields

### Output Requirements
- **Consistent Structure**: All aggregations follow same output format
- **Field Names**: Match exactly what report phase expects
- **Sorting**: Results sorted by count descending
- **Metadata**: Include processing metadata and statistics

### Error Handling
- **Graceful Degradation**: Continue processing if individual aggregators fail
- **Data Validation**: Validate input data structure and required fields
- **Logging**: Comprehensive logging for debugging and monitoring
- **Recovery**: Ability to resume from failures

## Field Mapping Reference

### Core Product Aggregations
- **Razors**: `razor.matched.brand` + `razor.matched.model` → `{"name": "Brand Model", "shaves": N}`
- **Blades**: `blade.matched.brand` + `blade.matched.model` → `{"name": "Brand Model", "shaves": N}`
- **Brushes**: `brush.matched.brand` + `brush.matched.model` → `{"name": "Brand Model", "shaves": N}`
- **Soaps**: `soap.matched.maker` + `soap.matched.scent` → `{"name": "Maker - Scent", "shaves": N}`

### Manufacturer Aggregations
- **Razor Manufacturers**: `razor.matched.brand` → `{"brand": "Brand", "shaves": N}`
- **Blade Manufacturers**: `blade.matched.brand` → `{"brand": "Brand", "shaves": N}`
- **Soap Makers**: `soap.matched.maker` → `{"maker": "Maker", "shaves": N}`

### Format Aggregations
- **Razor Formats**: `razor.matched.format` → `{"format": "Format", "shaves": N}`

### Brush Component Aggregations
- **Handle Makers**: `brush.matched.handle_maker` → `{"handle_maker": "Maker", "shaves": N}`
- **Knot Makers**: `brush.matched.knot_maker` → `{"brand": "Brand", "shaves": N}`
- **Fibers**: `brush.matched.fiber` (fallback: `brush.enriched.fiber`) → `{"fiber": "Fiber", "shaves": N}`
- **Knot Sizes**: `brush.matched.knot_size_mm` (fallback: `brush.enriched.knot_size_mm`) → `{"knot_size_mm": N, "shaves": N}`

### Specialized Razor Aggregations
- **Blackbird Plates**: `razor.enriched.plate` → `{"plate": "Plate", "shaves": N}`
- **Christopher Bradley Plates**: `razor.enriched.plate_type` + `razor.enriched.plate_level` → `{"plate_type": "Type", "plate_level": "Level", "shaves": N}`
- **Game Changer Plates**: `razor.enriched.gap` → `{"gap": "Gap", "shaves": N}`
- **Super Speed Tips**: `razor.enriched.super_speed_tip` → `{"super_speed_tip": "Tip", "shaves": N}`
- **Straight Widths**: `razor.enriched.width` → `{"width": "Width", "shaves": N}`
- **Straight Grinds**: `razor.enriched.grind` → `{"grind": "Grind", "shaves": N}`
- **Straight Points**: `razor.enriched.point` → `{"point": "Point", "shaves": N}`

### User Aggregations
- **Users**: `author` → `{"name": "Username", "shaves": N}`

## Progress Tracking

### Current Status
- [ ] Phase 1: Foundation & Core Structure (0/7 steps completed)
- [ ] Phase 2: Data Processing & Output (0/3 steps completed)
- [ ] Phase 3: Advanced Features (0/3 steps completed)

### Next Steps
- Start with Step 1: Basic CLI Structure
- Follow the plan systematically
- Test each step before moving to the next

### Notes
- Each step builds on the previous
- Test thoroughly before moving to next step
- Follow existing code patterns and style
- Maintain proper error handling throughout
- Document any deviations from the plan

## Future Enhancements (TODO)

### Cross-Product Analysis
- [ ] Most Used Blades in Most Used Razors: Top razor+blade combinations
- [ ] Highest Use Count per Blade: Per-user blade usage tracking

### Performance Optimizations
- [ ] Parallel processing for multiple months (if needed) 