# Aggregate Phase Implementation Plan

## Overview

This document outlines the implementation plan for rebuilding the Aggregate phase from scratch. The phase will process enriched SOTD data to generate statistical summaries for downstream reporting.

## File Organization

### Core Structure
```
sotd/aggregate/
├── __init__.py
├── cli.py              # CLI interface and argument parsing
├── run.py              # Main execution logic
├── load.py             # Data loading from enriched phase
├── engine.py           # Core aggregation engine
├── processor.py        # Data processing and validation
├── save.py             # Output saving and formatting
└── utils/
    ├── __init__.py
    ├── metrics.py      # Metric calculation functions
    └── validation.py   # Data validation functions
```

### Aggregator Categories
```
sotd/aggregate/aggregators/
├── __init__.py
├── core/               # Core product aggregations
│   ├── __init__.py
│   ├── razor_aggregator.py
│   ├── blade_aggregator.py
│   ├── brush_aggregator.py
│   └── soap_aggregator.py
├── manufacturers/      # Manufacturer-level aggregations
│   ├── __init__.py
│   ├── razor_manufacturer_aggregator.py
│   ├── blade_manufacturer_aggregator.py
│   └── soap_maker_aggregator.py
├── formats/           # Format-level aggregations
│   ├── __init__.py
│   └── razor_format_aggregator.py
├── brush_specialized/ # Brush component aggregations
│   ├── __init__.py
│   ├── handle_maker_aggregator.py
│   ├── knot_maker_aggregator.py
│   ├── fiber_aggregator.py
│   └── knot_size_aggregator.py
├── razor_specialized/ # Specialized razor aggregations
│   ├── __init__.py
│   ├── blackbird_plate_aggregator.py
│   ├── christopher_bradley_plate_aggregator.py
│   ├── game_changer_plate_aggregator.py
│   ├── super_speed_tip_aggregator.py
│   ├── straight_width_aggregator.py
│   ├── straight_grind_aggregator.py
│   └── straight_point_aggregator.py
├── users/             # User aggregations
│   ├── __init__.py
│   └── user_aggregator.py
└── cross_product/     # Cross-product aggregations
    ├── __init__.py
    ├── razor_blade_combo_aggregator.py
    └── highest_use_count_per_blade_aggregator.py
```

## Implementation Steps

### Phase 1: Core Infrastructure
- [x] **1.1 Basic Structure**
  - [x] Create directory structure
  - [x] Create `__init__.py` files
  - [x] Set up basic imports and exports

- [x] **1.2 CLI Interface (`cli.py`)**
  - [x] Implement argument parsing (month, year, range)
  - [x] Add validation for date formats
  - [x] Include debug and force options
  - [x] Follow existing CLI patterns from other phases

- [x] **1.3 Data Loading (`load.py`)**
  - [x] Implement enriched data loading from JSON files
  - [x] Add data validation for required fields
  - [x] Handle missing files gracefully
  - [x] Support for date range processing

- [x] **1.4 Core Engine (`engine.py`)**
  - [x] Implement main aggregation orchestration
  - [x] Add progress tracking with tqdm
  - [x] Implement sequential month processing
  - [x] Add error handling and logging

- [x] **1.5 Data Processing (`processor.py`)**
  - [x] Implement data validation and cleaning
  - [x] Add field normalization functions
  - [x] Handle null/missing values
  - [x] Implement data quality checks

- [x] **1.6 Output Saving (`save.py`)**
  - [x] Implement JSON output formatting
  - [x] Add metadata generation (total_shaves, unique_shavers, etc.)
  - [x] Ensure proper file structure and naming
  - [x] Add position field calculation and insertion

- [x] **1.7 Utilities (`utils/`)**
  - [x] **metrics.py**: Metric calculation functions (shaves, unique_users, etc.)
  - [x] **validation.py**: Data validation and quality check functions

**✅ Phase 1: Core Infrastructure - COMPLETE**

### Phase 2: Core Product Aggregators
- [x] **2.1 Razor Aggregator (`aggregators/core/razor_aggregator.py`)**
  - [x] Implement razor aggregation logic
  - [x] Handle brand/model/format combination
  - [x] Add position field calculation
  - [x] Sort by shaves desc, unique_users desc

- [x] **2.2 Blade Aggregator (`aggregators/core/blade_aggregator.py`)**
  - [x] Implement blade aggregation logic
  - [x] Handle brand/model/format combination
  - [x] Add position field calculation
  - [x] Sort by shaves desc, unique_users desc

- [x] **2.3 Brush Aggregator (`aggregators/core/brush_aggregator.py`)**
  - [x] Implement brush aggregation logic
  - [x] Handle brand/model/fiber combination
  - [x] Add position field calculation
  - [x] Sort by shaves desc, unique_users desc

- [x] **2.4 Soap Aggregator (`aggregators/core/soap_aggregator.py`)**
  - [x] Implement soap aggregation logic
  - [x] Handle maker/scent combination
  - [x] Add position field calculation
  - [x] Sort by shaves desc, unique_users desc

### Phase 3: Manufacturer Aggregators
- [x] **3.1 Razor Manufacturer Aggregator (`aggregators/manufacturers/razor_manufacturer_aggregator.py`)**
  - [x] Implement razor manufacturer aggregation
  - [x] Extract brand from razor.matched.brand
  - [x] Add position field calculation
  - [x] Sort by shaves desc, unique_users desc

- [ ] **3.2 Blade Manufacturer Aggregator (`aggregators/manufacturers/blade_manufacturer_aggregator.py`)**
  - [ ] Implement blade manufacturer aggregation
  - [ ] Extract brand from blade.matched.brand
  - [ ] Add position field calculation
  - [ ] Sort by shaves desc, unique_users desc

- [ ] **3.3 Soap Maker Aggregator (`aggregators/manufacturers/soap_maker_aggregator.py`)**
  - [ ] Implement soap maker aggregation
  - [ ] Extract maker from soap.matched.maker
  - [ ] Add position field calculation
  - [ ] Sort by shaves desc, unique_users desc

### Phase 4: Format Aggregators
- [ ] **4.1 Razor Format Aggregator (`aggregators/formats/razor_format_aggregator.py`)**
  - [ ] Implement razor format aggregation
  - [ ] Extract format from razor.matched.format
  - [ ] Add position field calculation
  - [ ] Sort by shaves desc, unique_users desc

### Phase 5: Brush Specialized Aggregators
- [ ] **5.1 Handle Maker Aggregator (`aggregators/brush_specialized/handle_maker_aggregator.py`)**
  - [ ] Implement handle maker aggregation
  - [ ] Extract handle_maker from brush.matched.handle_maker
  - [ ] Add position field calculation
  - [ ] Sort by shaves desc, unique_users desc

- [ ] **5.2 Knot Maker Aggregator (`aggregators/brush_specialized/knot_maker_aggregator.py`)**
  - [ ] Implement knot maker aggregation
  - [ ] Extract knot_maker from brush.matched.knot_maker
  - [ ] Add position field calculation
  - [ ] Sort by shaves desc, unique_users desc

- [ ] **5.3 Fiber Aggregator (`aggregators/brush_specialized/fiber_aggregator.py`)**
  - [ ] Implement fiber aggregation
  - [ ] Extract fiber from brush.matched.fiber (fallback to brush.enriched.fiber)
  - [ ] Add position field calculation
  - [ ] Sort by shaves desc, unique_users desc

- [ ] **5.4 Knot Size Aggregator (`aggregators/brush_specialized/knot_size_aggregator.py`)**
  - [ ] Implement knot size aggregation
  - [ ] Extract knot_size_mm from brush.matched.knot_size_mm (fallback to brush.enriched.knot_size_mm)
  - [ ] Add position field calculation
  - [ ] Sort by shaves desc, unique_users desc

### Phase 6: Razor Specialized Aggregators
- [ ] **6.1 Blackbird Plate Aggregator (`aggregators/razor_specialized/blackbird_plate_aggregator.py`)**
  - [ ] Implement Blackbird plate aggregation
  - [ ] Extract plate from razor.enriched.plate
  - [ ] Add position field calculation
  - [ ] Sort by shaves desc, unique_users desc

- [ ] **6.2 Christopher Bradley Plate Aggregator (`aggregators/razor_specialized/christopher_bradley_plate_aggregator.py`)**
  - [ ] Implement Christopher Bradley plate aggregation
  - [ ] Extract plate_type and plate_level from razor.enriched
  - [ ] Combine into composite key
  - [ ] Add position field calculation
  - [ ] Sort by shaves desc, unique_users desc

- [ ] **6.3 Game Changer Plate Aggregator (`aggregators/razor_specialized/game_changer_plate_aggregator.py`)**
  - [ ] Implement Game Changer plate aggregation
  - [ ] Extract gap from razor.enriched.gap
  - [ ] Add position field calculation
  - [ ] Sort by shaves desc, unique_users desc

- [ ] **6.4 Super Speed Tip Aggregator (`aggregators/razor_specialized/super_speed_tip_aggregator.py`)**
  - [ ] Implement Super Speed tip aggregation
  - [ ] Extract super_speed_tip from razor.enriched.super_speed_tip
  - [ ] Add position field calculation
  - [ ] Sort by shaves desc, unique_users desc

- [ ] **6.5 Straight Razor Spec Aggregators**
  - [ ] **Width Aggregator**: Extract width from razor.enriched.width
  - [ ] **Grind Aggregator**: Extract grind from razor.enriched.grind
  - [ ] **Point Aggregator**: Extract point from razor.enriched.point
  - [ ] Each with position field and proper sorting

### Phase 7: User Aggregators
- [ ] **7.1 User Aggregator (`aggregators/users/user_aggregator.py`)**
  - [ ] Implement user aggregation
  - [ ] Extract author from comment data
  - [ ] Calculate shaves and missed_days
  - [ ] Add position field calculation
  - [ ] Sort by shaves desc, missed_days desc

### Phase 8: Cross-Product Aggregators
- [ ] **8.1 Razor Blade Combo Aggregator (`aggregators/cross_product/razor_blade_combo_aggregator.py`)**
  - [ ] Implement razor blade combination aggregation
  - [ ] Combine razor and blade data
  - [ ] Create composite keys
  - [ ] Add position field calculation
  - [ ] Sort by shaves desc, unique_users desc

- [ ] **8.2 Highest Use Count per Blade Aggregator (`aggregators/cross_product/highest_use_count_per_blade_aggregator.py`)**
  - [ ] Implement highest use count per blade aggregation
  - [ ] Track per-user blade usage
  - [ ] Extract use_count from blade.enriched.use_count
  - [ ] Add position field calculation
  - [ ] Sort by uses desc

### Phase 9: Integration and Testing
- [ ] **9.1 Main Runner Integration (`run.py`)**
  - [ ] Integrate all aggregators into main engine
  - [ ] Implement proper orchestration
  - [ ] Add error handling and logging
  - [ ] Ensure all categories are processed

- [ ] **9.2 Unit Tests**
  - [ ] Test each aggregator individually
  - [ ] Test metric calculation functions
  - [ ] Test position field generation
  - [ ] Test sorting logic
  - [ ] Test data validation

- [ ] **9.3 Integration Tests**
  - [ ] Test end-to-end processing
  - [ ] Test CLI interface
  - [ ] Test file I/O with sample data
  - [ ] Test error handling scenarios

- [ ] **9.4 Data Quality Tests**
  - [ ] Test with edge cases (empty data, single records)
  - [ ] Test error conditions
  - [ ] Validate output structure
  - [ ] Verify position field correctness

### Phase 10: Documentation and Cleanup
- [ ] **10.1 Documentation**
  - [ ] Update docstrings for all functions
  - [ ] Add type hints throughout
  - [ ] Document aggregator interfaces
  - [ ] Update README if needed

- [ ] **10.2 Code Quality**
  - [ ] Run Black formatting
  - [ ] Run Ruff linting
  - [ ] Run Pyright type checking
  - [ ] Ensure all tests pass

- [ ] **10.3 Performance Optimization**
  - [ ] Profile memory usage
  - [ ] Optimize pandas operations
  - [ ] Add progress tracking
  - [ ] Consider parallel processing if needed

## Key Requirements

### Position Field
- Every aggregation output must include a "position" field
- Position is 1-based rank within the sorted list
- Enables robust delta calculations in report phase

### Sort Orders
- **Default**: shaves desc, unique_users desc
- **Users**: shaves desc, missed_days desc  
- **Highest Use Count per Blade**: uses desc

### Data Structure
- Follow exact field names specified in aggregate phase spec
- Include all required fields for each category
- Ensure consistent output structure

### Error Handling
- Fail fast for internal errors
- Handle external failures gracefully
- Validate data early and clearly

## Dependencies

### New Dependencies
- `pandas`: For efficient data aggregation and manipulation

### Existing Dependencies
- `tqdm`: Progress bars
- `pathlib`: File path handling
- `json`: JSON I/O operations
- `argparse`: CLI argument parsing

## Testing Strategy

### Unit Tests
- Test each aggregator in isolation
- Test metric calculation functions
- Test data validation functions
- Test sorting and position field logic

### Integration Tests
- Test complete aggregation pipeline
- Test CLI interface with various arguments
- Test file I/O with sample data
- Test error handling scenarios

### Test Data
- Sample enriched data files
- Edge cases (empty data, single records)
- Error conditions (missing fields, malformed data)

## Success Criteria

- [ ] All aggregations produce correct output structure
- [ ] Position fields are correctly calculated and sequential
- [ ] Sort orders match specification exactly
- [ ] All tests pass (unit, integration, data quality)
- [ ] Code quality checks pass (Black, Ruff, Pyright)
- [ ] Performance is acceptable for typical datasets
- [ ] Error handling is robust and informative
- [ ] Documentation is complete and accurate