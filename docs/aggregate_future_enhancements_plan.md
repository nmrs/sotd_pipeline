# Aggregate Phase Future Enhancements Implementation Plan

## Project Overview
Implement specialized aggregation categories and cross-product analysis for the SOTD pipeline aggregate phase. This builds on the existing core aggregation functionality to provide deeper insights into specific razor types and product combinations.

## Implementation Checklist

### Phase 1: Specialized Razor Categories Foundation

#### Chunk 1: Blackbird Plates Aggregation
- [x] **Step 1.1: Create Blackbird Plates Function**
  - [x] Create `aggregate_blackbird_plates()` function in `sotd/aggregate/engine.py`
  - [x] Add filtering logic for Blackland Blackbird razors (`razor.matched.brand == "Blackland"` and `"Blackbird"` in model)
  - [x] Extract plate information from `razor.enriched.plate` (Standard, Lite, OC)
  - [x] Implement pandas-based aggregation with standard metrics
  - [x] Add proper error handling and validation
  - [x] Include type hints and docstrings
  - [x] Follow existing code patterns and style

- [x] **Step 1.2: Test Blackbird Plates**
  - [x] Create unit tests in `tests/aggregate/test_engine.py`
  - [x] Test with sample enriched data containing Blackland Blackbird razors
  - [x] Test edge cases (missing enriched data, unmatched razors)
  - [x] Test pandas aggregation operations
  - [x] Verify output structure matches existing patterns

#### Chunk 2: Christopher Bradley Plates Aggregation
- [ ] **Step 2.1: Create Christopher Bradley Plates Function**
  - [ ] Create `aggregate_christopher_bradley_plates()` function in `sotd/aggregate/engine.py`
  - [ ] Add filtering logic for Karve Christopher Bradley razors (`razor.matched.brand == "Karve"` and `model == "Christopher Bradley"`)
  - [ ] Extract plate information from `razor.enriched.plate` (AA-G levels)
  - [ ] Implement pandas-based aggregation with standard metrics
  - [ ] Add proper error handling and validation
  - [ ] Include type hints and docstrings
  - [ ] Follow existing code patterns

- [ ] **Step 2.2: Test Christopher Bradley Plates**
  - [ ] Create unit tests in `tests/aggregate/test_engine.py`
  - [ ] Test with sample enriched data containing Karve Christopher Bradley razors
  - [ ] Test edge cases and validation
  - [ ] Test pandas aggregation operations
  - [ ] Verify output structure matches existing patterns

#### Chunk 3: Game Changer Plates Aggregation
- [ ] **Step 3.1: Create Game Changer Plates Function**
  - [ ] Create `aggregate_game_changer_plates()` function in `sotd/aggregate/engine.py`
  - [ ] Add filtering logic for RazoRock Game Changer razors (`razor.matched.brand == "RazoRock"` and `"Game Changer"` in model)
  - [ ] Extract gap and variant information from `razor.enriched`
  - [ ] Handle different gap formats (.68, .76, .84, 1.05)
  - [ ] Implement pandas-based aggregation with standard metrics
  - [ ] Add proper error handling and validation
  - [ ] Include type hints and docstrings
  - [ ] Follow existing code patterns

- [ ] **Step 3.2: Test Game Changer Plates**
  - [ ] Create unit tests in `tests/aggregate/test_engine.py`
  - [ ] Test with sample enriched data containing RazoRock Game Changer razors
  - [ ] Test different gap formats and variants
  - [ ] Test edge cases and validation
  - [ ] Test pandas aggregation operations
  - [ ] Verify output structure matches existing patterns

#### Chunk 4: Super Speed Tips Aggregation
- [ ] **Step 4.1: Create Super Speed Tips Function**
  - [ ] Create `aggregate_super_speed_tips()` function in `sotd/aggregate/engine.py`
  - [ ] Add filtering logic for Gillette Super Speed razors (`razor.matched.brand == "Gillette"` and `model == "Super Speed"`)
  - [ ] Extract tip color and variant from `razor.enriched.super_speed_tip`
  - [ ] Handle color variants (Red, Blue, Black, Flare)
  - [ ] Implement pandas-based aggregation with standard metrics
  - [ ] Add proper error handling and validation
  - [ ] Include type hints and docstrings
  - [ ] Follow existing code patterns

- [ ] **Step 4.2: Test Super Speed Tips**
  - [ ] Create unit tests in `tests/aggregate/test_engine.py`
  - [ ] Test with sample enriched data containing Gillette Super Speed razors
  - [ ] Test different tip colors and variants
  - [ ] Test edge cases and validation
  - [ ] Test pandas aggregation operations
  - [ ] Verify output structure matches existing patterns

#### Chunk 5: Straight Razor Specifications Aggregation
- [ ] **Step 5.1: Create Straight Razor Specs Function**
  - [ ] Create `aggregate_straight_razor_specs()` function in `sotd/aggregate/engine.py`
  - [ ] Add filtering logic for straight razors (`razor.matched.format == "Straight"`)
  - [ ] Extract grind, width, and point from `razor.enriched` or `razor.matched`
  - [ ] Handle different width formats (fractions, decimals)
  - [ ] Implement pandas-based aggregation with standard metrics
  - [ ] Add proper error handling and validation
  - [ ] Include type hints and docstrings
  - [ ] Follow existing code patterns

- [ ] **Step 5.2: Test Straight Razor Specs**
  - [ ] Create unit tests in `tests/aggregate/test_engine.py`
  - [ ] Test with sample enriched data containing straight razors
  - [ ] Test different width formats and specifications
  - [ ] Test edge cases and validation
  - [ ] Test pandas aggregation operations
  - [ ] Verify output structure matches existing patterns

### Phase 2: Cross-Product Analysis

#### Chunk 6: Razor-Blade Combinations Aggregation
- [ ] **Step 6.1: Create Razor-Blade Combinations Function**
  - [ ] Create `aggregate_razor_blade_combinations()` function in `sotd/aggregate/engine.py`
  - [ ] Group by both razor name and blade name from matched data
  - [ ] Calculate metrics for most popular combinations
  - [ ] Handle edge cases (missing either razor or blade data)
  - [ ] Sort by usage frequency
  - [ ] Implement pandas-based aggregation with standard metrics
  - [ ] Add proper error handling and validation
  - [ ] Include type hints and docstrings
  - [ ] Follow existing code patterns

- [ ] **Step 6.2: Test Razor-Blade Combinations**
  - [ ] Create unit tests in `tests/aggregate/test_engine.py`
  - [ ] Test with sample enriched data containing razor and blade combinations
  - [ ] Test edge cases (missing data)
  - [ ] Test pandas aggregation operations
  - [ ] Verify output structure matches existing patterns

#### Chunk 7: Per-User Blade Usage Aggregation
- [ ] **Step 7.1: Create Per-User Blade Usage Function**
  - [ ] Create `aggregate_user_blade_usage()` function in `sotd/aggregate/engine.py`
  - [ ] Extract blade use count from `blade.enriched.use_count`
  - [ ] Group by user and blade, calculate average use count
  - [ ] Identify users who maximize blade usage
  - [ ] Handle missing use count data gracefully
  - [ ] Implement pandas-based aggregation with standard metrics
  - [ ] Add proper error handling and validation
  - [ ] Include type hints and docstrings
  - [ ] Follow existing code patterns

- [ ] **Step 7.2: Test Per-User Blade Usage**
  - [ ] Create unit tests in `tests/aggregate/test_engine.py`
  - [ ] Test with sample enriched data containing blade use count information
  - [ ] Test edge cases and missing data
  - [ ] Test pandas aggregation operations
  - [ ] Verify output structure matches existing patterns

### Phase 3: Integration & Testing

#### Chunk 8: Engine Integration
- [ ] **Step 8.1: Update Main Processing Function**
  - [ ] Update `process_month()` function in `sotd/aggregate/run.py` to include new categories
  - [ ] Add new categories to the aggregations dictionary
  - [ ] Update summary statistics to include new category counts
  - [ ] Add proper error handling for each category
  - [ ] Maintain backward compatibility
  - [ ] Include type hints and docstrings

- [ ] **Step 8.2: Test Engine Integration**
  - [ ] Create integration tests for end-to-end processing
  - [ ] Test with sample enriched data containing all specialized information
  - [ ] Test error handling for each category
  - [ ] Verify all categories are included in results
  - [ ] Test backward compatibility

#### Chunk 9: Save Module Updates
- [ ] **Step 9.1: Update Save Function**
  - [ ] Update `save_aggregated_data()` function in `sotd/aggregate/save.py`
  - [ ] Add new categories to the categories list in metadata
  - [ ] Add new categories to the data section structure
  - [ ] Update validation function to check for new categories
  - [ ] Maintain backward compatibility
  - [ ] Include proper error handling
  - [ ] Add type hints and docstrings

- [ ] **Step 9.2: Test Save Module Updates**
  - [ ] Create unit tests for updated save functionality
  - [ ] Test with sample aggregated data containing new categories
  - [ ] Test validation function with new categories
  - [ ] Test backward compatibility
  - [ ] Verify JSON output structure

#### Chunk 10: CLI Integration
- [ ] **Step 10.1: Update CLI Interface**
  - [ ] Update argument parser in `sotd/aggregate/run.py`
  - [ ] Add optional flags for enabling/disabling specialized aggregations
  - [ ] Update help text and documentation
  - [ ] Include proper error handling
  - [ ] Add type hints and docstrings

- [ ] **Step 10.2: Test CLI Integration**
  - [ ] Create CLI tests for new functionality
  - [ ] Test with various CLI argument combinations
  - [ ] Test help text and documentation
  - [ ] Test backward compatibility
  - [ ] Verify CLI behavior

#### Chunk 11: Comprehensive Testing
- [ ] **Step 11.1: Unit Testing**
  - [ ] Create unit tests for each specialized aggregation function
  - [ ] Test with sample enriched data containing specialized information
  - [ ] Test edge cases and error conditions
  - [ ] Test pandas aggregation operations
  - [ ] Add test data fixtures

- [ ] **Step 11.2: Integration Testing**
  - [ ] Create integration tests for end-to-end processing
  - [ ] Test cross-product analysis features
  - [ ] Test performance with large datasets
  - [ ] Test error handling scenarios
  - [ ] Add comprehensive test documentation

- [ ] **Step 11.3: Performance Testing**
  - [ ] Test with large datasets containing specialized information
  - [ ] Monitor memory usage during specialized aggregations
  - [ ] Test performance impact of new categories
  - [ ] Compare performance with existing categories
  - [ ] Document performance characteristics

#### Chunk 12: Documentation Updates
- [ ] **Step 12.1: Update Technical Documentation**
  - [ ] Update aggregate phase specification in `docs/aggregate_phase_spec.md`
  - [ ] Update implementation plan in `docs/aggregate_implementation_plan.md`
  - [ ] Update Cursor rules for aggregate phase
  - [ ] Include examples of new functionality
  - [ ] Maintain consistency with existing documentation

- [ ] **Step 12.2: Update User Documentation**
  - [ ] Update CLI documentation
  - [ ] Update test documentation
  - [ ] Include sample output structures
  - [ ] Add usage examples
  - [ ] Verify documentation accuracy against implementation

## Progress Tracking

### Current Status
- [x] Phase 1: Specialized Razor Categories Foundation (1/5 chunks completed)
- [ ] Phase 2: Cross-Product Analysis (0/2 chunks completed)
- [ ] Phase 3: Integration & Testing (0/4 chunks completed)

### Session Notes
- **Session 1**: [2024-12-19] - Completed Chunk 1: Blackbird Plates Aggregation
  - Successfully implemented `aggregate_blackbird_plates()` function in `sotd/aggregate/engine.py`
  - Added comprehensive filtering logic for Blackland Blackbird razors
  - Implemented plate extraction from `razor.enriched.plate` (Standard, Lite, OC)
  - Created pandas-based aggregation with standard metrics (shaves, unique_users, avg_shaves_per_user)
  - Added proper error handling and validation following existing patterns
  - Created comprehensive unit tests covering all edge cases and scenarios
  - All quality checks pass: format, lint, typecheck, test (702/702 tests pass)
  - Committed changes with clear conventional commit message
- **Session 2**: [Date] - [Notes on what was completed]
- **Session 3**: [Date] - [Notes on what was completed]
- **Session 4**: [Date] - [Notes on what was completed]
- **Session 5**: [Date] - [Notes on what was completed]

### Next Steps
- [x] Start with Chunk 1: Blackbird Plates Aggregation
- [ ] Continue with Chunk 2: Christopher Bradley Plates Aggregation
- [ ] Complete each chunk before moving to the next
- [ ] Run `make format lint typecheck test` after each chunk
- [ ] Commit changes with clear messages after each chunk
- [ ] Update progress tracking after each session

### Notes
- Each chunk builds on the previous
- Test thoroughly before moving to next chunk
- Follow existing code patterns and style
- Maintain proper error handling throughout
- Document any deviations from the plan
- Keep this file updated with progress

## Success Criteria

### Functionality
- [ ] All specialized categories work correctly with sample data
- [ ] Cross-product analysis provides meaningful insights
- [ ] New categories integrate seamlessly with existing functionality
- [ ] CLI supports enabling/disabling specialized aggregations

### Performance
- [ ] New categories don't significantly impact overall performance
- [ ] Memory usage remains reasonable with large datasets
- [ ] Processing time scales appropriately with data size

### Quality
- [ ] Comprehensive test coverage for all new functionality
- [ ] All tests pass consistently
- [ ] Code follows existing patterns and style
- [ ] Proper error handling throughout

### Documentation
- [ ] Updated documentation reflects new capabilities
- [ ] Examples and usage instructions are clear
- [ ] Technical specifications are accurate
- [ ] Backward compatibility is maintained

## Future Considerations

### Potential Enhancements
- [ ] Parallel processing for multiple months (if needed)
- [ ] Streaming/batching for very large datasets
- [ ] Additional specialized categories based on user feedback
- [ ] Advanced cross-product analysis features

### Maintenance
- [ ] Monitor performance with real-world data
- [ ] Gather user feedback on new categories
- [ ] Plan for additional specialized categories
- [ ] Consider optimization opportunities 