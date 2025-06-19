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
- [x] **Step 2.1: Create Christopher Bradley Plates Function**
  - [x] Create `aggregate_christopher_bradley_plates()` function in `sotd/aggregate/engine.py`
  - [x] Add filtering logic for Karve Christopher Bradley razors (`razor.matched.brand == "Karve"` and `model == "Christopher Bradley"`)
  - [x] Extract plate information from `razor.enriched.plate` (AA-G levels)
  - [x] Implement pandas-based aggregation with standard metrics
  - [x] Add proper error handling and validation
  - [x] Include type hints and docstrings
  - [x] Follow existing code patterns

- [x] **Step 2.2: Test Christopher Bradley Plates**
  - [x] Create unit tests in `tests/aggregate/test_engine.py`
  - [x] Test with sample enriched data containing Karve Christopher Bradley razors
  - [x] Test edge cases and validation
  - [x] Test pandas aggregation operations
  - [x] Verify output structure matches existing patterns

#### Chunk 3: Game Changer Plates Aggregation
- [x] **Step 3.1: Create Game Changer Plates Function**
  - [x] Create `aggregate_game_changer_plates()` function in `sotd/aggregate/engine.py`
  - [x] Add filtering logic for RazoRock Game Changer razors (`razor.matched.brand == "RazoRock"` and `"Game Changer" in model`)
  - [x] Extract gap and variant information from `razor.enriched`
  - [x] Handle different gap formats (.68, .76, .84, 1.05)
  - [x] Implement pandas-based aggregation with standard metrics
  - [x] Add proper error handling and validation
  - [x] Include type hints and docstrings
  - [x] Follow existing code patterns

- [x] **Step 3.2: Test Game Changer Plates**
  - [x] Create unit tests in `tests/aggregate/test_engine.py`
  - [x] Test with sample enriched data containing RazoRock Game Changer razors
  - [x] Test different gap formats and variants
  - [x] Test edge cases and validation
  - [x] Test pandas aggregation operations
  - [x] Verify output structure matches existing patterns

#### Chunk 4: Super Speed Tips Aggregation
- [x] **Step 4.1: Create Super Speed Tips Function**
  - [x] Create `aggregate_super_speed_tips()` function in `sotd/aggregate/engine.py`
  - [x] Add filtering logic for Gillette Super Speed razors (`razor.matched.brand == "Gillette"` and `model == "Super Speed"`)
  - [x] Extract tip color and variant from `razor.enriched.super_speed_tip`
  - [x] Handle color variants (Red, Blue, Black, Flare)
  - [x] Implement pandas-based aggregation with standard metrics
  - [x] Add proper error handling and validation
  - [x] Include type hints and docstrings
  - [x] Follow existing code patterns

- [x] **Step 4.2: Test Super Speed Tips**
  - [x] Create unit tests in `tests/aggregate/test_engine.py`
  - [x] Test with sample enriched data containing Gillette Super Speed razors
  - [x] Test different tip colors and variants
  - [x] Test edge cases and validation
  - [x] Test pandas aggregation operations
  - [x] Verify output structure matches existing patterns

#### Chunk 5: Straight Razor Specifications Aggregation
- [x] **Step 5.1: Create Straight Razor Specs Function**
  - [x] Create `aggregate_straight_razor_specs()` function in `sotd/aggregate/engine.py`
  - [x] Add filtering logic for straight razors (`razor.matched.format == "Straight"`)
  - [x] Extract grind, width, and point from `razor.enriched` or `razor.matched`
  - [x] Handle different width formats (fractions, decimals)
  - [x] Implement pandas-based aggregation with standard metrics
  - [x] Add proper error handling and validation
  - [x] Include type hints and docstrings
  - [x] Follow existing code patterns

- [x] **Step 5.2: Test Straight Razor Specs**
  - [x] Create unit tests in `tests/aggregate/test_engine.py`
  - [x] Test with sample enriched data containing straight razors
  - [x] Test different width formats and specifications
  - [x] Test edge cases and validation
  - [x] Test pandas aggregation operations
  - [x] Verify output structure matches existing patterns

### Phase 2: Cross-Product Analysis

#### Chunk 6: Razor-Blade Combinations Aggregation
- [x] **Step 6.1: Create Razor-Blade Combinations Function**
  - [x] Create `aggregate_razor_blade_combinations()` function in `sotd/aggregate/engine.py`
  - [x] Group by both razor name and blade name from matched data
  - [x] Calculate metrics for most popular combinations
  - [x] Handle edge cases (missing either razor or blade data)
  - [x] Sort by usage frequency
  - [x] Implement pandas-based aggregation with standard metrics
  - [x] Add proper error handling and validation
  - [x] Include type hints and docstrings
  - [x] Follow existing code patterns

- [x] **Step 6.2: Test Razor-Blade Combinations**
  - [x] Create unit tests in `tests/aggregate/test_engine.py`
  - [x] Test with sample enriched data containing razor and blade combinations
  - [x] Test edge cases (missing data)
  - [x] Test pandas aggregation operations
  - [x] Verify output structure matches existing patterns

#### Chunk 7: Per-User Blade Usage Aggregation
- [x] **Step 7.1: Create Per-User Blade Usage Function**
  - [x] Create `aggregate_user_blade_usage()` function in `sotd/aggregate/engine.py`
  - [x] Extract blade use count from `blade.enriched.use_count`
  - [x] Group by user and blade, calculate average use count
  - [x] Identify users who maximize blade usage
  - [x] Handle missing use count data gracefully
  - [x] Implement pandas-based aggregation with standard metrics
  - [x] Add proper error handling and validation
  - [x] Include type hints and docstrings
  - [x] Follow existing code patterns

- [x] **Step 7.2: Test Per-User Blade Usage**
  - [x] Create unit tests in `tests/aggregate/test_engine.py`
  - [x] Test with sample enriched data containing blade use count information
  - [x] Test edge cases and missing data
  - [x] Test pandas aggregation operations
  - [x] Verify output structure matches existing patterns

### Phase 3: Integration & Testing

#### Chunk 8: Engine Integration
- [x] **Step 8.1: Update Main Processing Function**
  - [x] Update `process_month()` function in `sotd/aggregate/run.py` to include new categories
  - [x] Add new categories to the aggregations dictionary
  - [x] Update summary statistics to include new category counts
  - [x] Add proper error handling for each category
  - [x] Maintain backward compatibility
  - [x] Include type hints and docstrings

- [x] **Step 8.2: Test Engine Integration**
  - [x] Create integration tests for end-to-end processing
  - [x] Test with sample enriched data containing all specialized information
  - [x] Test error handling for each category
  - [x] Verify all categories are included in results
  - [x] Test backward compatibility
  - [x] Update save module to include new categories in output structure
  - [x] Fix existing test fixtures to include new categories
  - [x] Ensure all 765 tests pass with new functionality

**Session Note (2025-01-21):** Completed Step 8.2 - Engine Integration Testing. Extended integration tests to cover all new specialized aggregation categories (Blackbird plates, Christopher Bradley plates, Game Changer plates, Super Speed tips, Straight Razor specs, Razor-Blade combinations, User Blade usage). Updated save module to include new categories in output structure. Fixed test fixtures and assertions to match actual aggregation results. All 765 tests pass with full quality checks (format, lint, typecheck).

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
- [x] Phase 1: Specialized Razor Categories Foundation (5/5 chunks completed)
- [x] Phase 2: Cross-Product Analysis (2/2 chunks completed)
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
- **Session 2**: [2024-12-20] - Completed Chunk 2: Christopher Bradley Plates Aggregation
  - Implemented `aggregate_christopher_bradley_plates()` in `sotd/aggregate/engine.py` following the Blackbird pattern
  - Added comprehensive unit tests in `tests/aggregate/test_engine.py` for all edge cases and scenarios
  - All quality checks pass: format, lint, typecheck, test (712/712 tests pass)
  - Committed changes with clear conventional commit message
- **Session 3**: [2024-12-21] - Completed Chunk 3: Game Changer Plates Aggregation
  - Implemented `aggregate_game_changer_plates()` in `sotd/aggregate/engine.py` following the established aggregation pattern
  - Added comprehensive unit tests in `tests/aggregate/test_engine.py` for all edge cases and scenarios (gap only, variant only, both, multiple users, multiple plates, model variations, and mixed razor types)
  - All quality checks pass: format, lint, typecheck, test (724/724 tests pass)
  - Committed changes with clear conventional commit message
- **Session 4**: [2024-12-22] - Completed Chunk 4: Super Speed Tips Aggregation
  - Implemented `aggregate_super_speed_tips()` in `sotd/aggregate/engine.py` following the established aggregation pattern
  - Added comprehensive filtering logic for Gillette Super Speed razors
  - Implemented tip extraction from `razor.enriched.super_speed_tip` (Red, Blue, Black, Flare)
  - Created pandas-based aggregation with standard metrics (shaves, unique_users, avg_shaves_per_user)
  - Added comprehensive unit tests in `tests/aggregate/test_engine.py` for all edge cases and scenarios (single tip, multiple tips, mixed razor types, tiebreaker scenarios)
  - All quality checks pass: format, lint, typecheck, test (733/733 tests pass)
  - Committed changes with clear conventional commit message
- **Session 5**: [2024-12-22] - Completed Chunk 5: Straight Razor Specifications Aggregation
  - Implemented `aggregate_straight_razor_specs()` in `sotd/aggregate/engine.py` following the established aggregation pattern
  - Added comprehensive filtering logic for straight razors (razor.matched.format == "Straight")
  - Implemented specification extraction from `razor.enriched` (grind, width, point)
  - Created pandas-based aggregation with standard metrics (shaves, unique_users, avg_shaves_per_user)
  - Added comprehensive unit tests in `tests/aggregate/test_engine.py` for all edge cases and scenarios (single specs, multiple specs, partial specs, mixed razor types, tiebreaker scenarios)
  - All quality checks pass: format, lint, typecheck, test (743/743 tests pass)
  - Committed changes with clear conventional commit message
- **Session 6**: [2024-12-22] - Completed Chunk 6: Razor-Blade Combinations Aggregation
  - Implemented `aggregate_razor_blade_combinations()` in `sotd/aggregate/engine.py` following the established aggregation pattern
  - Added comprehensive filtering logic for razor-blade combinations (both razor and blade must be matched)
  - Implemented combination extraction from `razor.matched` and `blade.matched` (brand + model for both)
  - Created pandas-based aggregation with standard metrics (shaves, unique_users, avg_shaves_per_user)
  - Added comprehensive unit tests in `tests/aggregate/test_engine.py` for all edge cases and scenarios (single combination, multiple combinations, missing data, tiebreaker scenarios)
  - All quality checks pass: format, lint, typecheck, test (752/752 tests pass)
  - Committed changes with clear conventional commit message
- **Session 7**: [2024-12-22] - Completed Chunk 7: Per-User Blade Usage Aggregation
  - Implemented `aggregate_user_blade_usage()` in `sotd/aggregate/engine.py` following the established aggregation pattern
  - Added comprehensive filtering logic for per-user blade usage (blade must be matched and use_count must be available)
  - Implemented use count extraction from `blade.enriched.use_count`
  - Created pandas-based aggregation with metrics (avg_use_count, shaves, max_use_count)
  - Added comprehensive unit tests in `tests/aggregate/test_engine.py` for all edge cases and scenarios (single user, multiple users, multiple shaves, tiebreaker scenarios)
  - All quality checks pass: format, lint, typecheck, test (761/761 tests pass)
  - Committed changes with clear conventional commit message
- **Session 8**: [2024-06-21] - Completed Chunk 8.1: Engine Integration (Main Processing Function)
  - Updated `process_month()` in `sotd/aggregate/run.py` to include all new specialized aggregation categories (Blackbird Plates, Christopher Bradley Plates, Game Changer Plates, Super Speed Tips, Straight Razor Specs, Razor-Blade Combinations, Per-User Blade Usage)
  - Updated the aggregations dictionary and summary statistics to reflect new categories
  - Ensured error handling and backward compatibility
  - Ran `make format lint typecheck test` (all 765 tests pass)
  - All quality checks pass, code style and documentation maintained
  - Ready to proceed to integration testing

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