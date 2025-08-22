# SOTD Pipeline Test Suite TODO

**Generated**: 2025-08-22  
**Total Tests**: 3,447  
**Failures**: 13  
**Categories**: 4 groups  
**Status**: Analysis Complete

## Summary by Category
- **Test Drift**: 6 failures (46%)
- **Regression**: 4 failures (31%)  
- **Incomplete Implementation**: 2 failures (15%)
- **Performance Issue**: 1 failure (8%)

---

## Group 1: Delta Calculation System Issues
**Category**: Regression  
**Root Cause**: Delta calculation system requires rank fields that are missing from test data  
**Files Involved**: `tests/report/test_delta_calculator.py`, `tests/report/test_annual_delta_integration.py`, `sotd/report/table_generators/`

### Tasks

- [ ] **Fix specialized table delta integration for Christopher Bradley plates**
  - **Category**: Regression
  - **Failing tests**: `test_christopher_bradley_plates_table_delta_integration`
  - **Files involved**: `tests/report/test_delta_calculator.py:402`, `sotd/report/table_generators/specialized_tables.py`
  - **Observed error**: Table shows "n/a" for all delta columns instead of proper delta values
  - **Quick next steps**:
    - Check if Christopher Bradley plates table generator properly implements delta calculation
    - Verify that historical data transformation preserves rank information
    - Ensure delta calculation logic works with the table structure
  - **Notes/links**: Debug output shows "Historical item missing plate or rank" - rank field not being preserved

- [ ] **Fix specialized table delta integration for Straight Razor tables**
  - **Category**: Regression
  - **Failing tests**: `test_straight_grinds_table_delta_integration`, `test_straight_points_table_delta_integration`, `test_straight_widths_table_delta_integration`
  - **Files involved**: `tests/report/test_delta_calculator.py:445,502,554`, `sotd/report/table_generators/specialized_tables.py:91`
  - **Observed error**: `ValueError: Historical data missing ranks for {category} - aggregator must assign ranks before delta calculations`
  - **Quick next steps**:
    - Check if specialized table generators properly assign ranks to historical data
    - Verify that rank field is preserved during data transformation
    - Ensure aggregators assign ranks before delta calculations
  - **Notes/links**: All straight razor specialized tables failing with same rank missing error

- [ ] **Fix specialized table delta integration for Game Changer and Super Speed tables**
  - **Category**: Regression
  - **Failing tests**: `test_game_changer_plates_table_delta_integration`, `test_super_speed_tips_table_delta_integration`
  - **Files involved**: `tests/report/test_delta_calculator.py:607,665`, `sotd/report/table_generators/specialized_tables.py:91`
  - **Observed error**: Same rank missing error as straight razor tables
  - **Quick next steps**:
    - Check if these table generators inherit from proper base classes
    - Verify rank assignment in specialized table generators
    - Ensure consistent rank handling across all specialized tables
  - **Notes/links**: Same pattern as straight razor tables - rank field not preserved

- [ ] **Fix Blackbird plates table delta integration**
  - **Category**: Regression
  - **Failing tests**: `test_blackbird_plates_table_delta_integration`
  - **Files involved**: `tests/report/test_delta_calculator.py:723`, `sotd/report/table_generators/specialized_tables.py:91`
  - **Observed error**: Same rank missing error despite inheriting from DataTransformingTableGenerator
  - **Quick next steps**:
    - Check if BlackbirdPlatesTableGenerator properly implements rank assignment
    - Verify data transformation logic preserves rank information
    - Ensure base class inheritance is working correctly
  - **Notes/links**: Should work since it inherits from DataTransformingTableGenerator, but still failing

- [ ] **Fix annual delta integration rank requirements**
  - **Category**: Regression
  - **Failing tests**: `test_delta_column_integration`, `test_formatting_and_alignment`
  - **Files involved**: `tests/report/test_annual_delta_integration.py:62,115`, `sotd/report/table_generators/base.py:819`
  - **Observed error**: `ValueError: Historical data missing ranks for razors - aggregator must assign ranks before delta calculations`
  - **Quick next steps**:
    - Check if annual aggregators properly assign ranks to output data
    - Verify that rank field is included in annual aggregation output
    - Ensure rank assignment happens before delta calculation attempts
  - **Notes/links**: Annual delta system requires ranks but aggregators aren't providing them

---

## Group 2: Report Integration and Table Generation
**Category**: Test Drift  
**Root Cause**: Report structure and table generation changes  
**Files Involved**: `tests/report/test_integration.py`, `sotd/report/monthly_generator.py`

### Tasks

- [ ] **Fix software report table generation**
  - **Category**: Test Drift
  - **Failing tests**: `test_software_report_generation`
  - **Files involved**: `tests/report/test_integration.py:193`, `sotd/report/monthly_generator.py`
  - **Observed error**: Expected "| Name" table header but not found in generated report
  - **Quick next steps**:
    - Check if software report template was changed
    - Verify table generation logic for software reports
    - Update test to match current report structure
  - **Notes/links**: Report structure appears to have changed, missing expected tables

- [ ] **Fix report delta calculation integration**
  - **Category**: Test Drift
  - **Failing tests**: `test_report_with_delta_calculations`
  - **Files involved**: `tests/report/test_integration.py:255`, `sotd/report/table_generators/base.py:819`
  - **Observed error**: `ValueError: Historical data missing ranks for razors - aggregator must assign ranks before delta calculations`
  - **Quick next steps**:
    - Check if monthly aggregators properly assign ranks to output data
    - Verify that rank field is included in monthly aggregation output
    - Ensure rank assignment happens before delta calculation attempts
  - **Notes/links**: Monthly delta system also requires ranks but aggregators aren't providing them

---

## Group 3: Rank Formatter and Table Output
**Category**: Test Drift  
**Root Cause**: Rank formatting and table generation behavior changes  
**Files Involved**: `tests/report/test_rank_formatter.py`, `sotd/report/utils/rank_formatter.py`

### Tasks

- [ ] **Fix rank formatter tie handling in table output**
  - **Category**: Test Drift
  - **Failing tests**: `test_rank_column_in_table_output`
  - **Files involved**: `tests/report/test_rank_formatter.py:211`, `sotd/report/utils/rank_formatter.py`
  - **Observed error**: Expected "2=" tied rank indicator but got "n/a" for all ranks
  - **Quick next steps**:
    - Check if rank formatter is properly processing rank data
    - Verify that tie detection logic is working correctly
    - Ensure rank field is being populated before formatting
  - **Notes/links**: Rank formatter appears to be returning "n/a" instead of proper rank values

---

## Group 4: Performance and Dependency Issues
**Category**: Performance Issue  
**Root Cause**: Handle/knot dependency system performance overhead  
**Files Involved**: `tests/match/brush_scoring_components/test_handle_knot_dependency_performance.py`

### Tasks

- [ ] **Fix handle/knot dependency performance overhead**
  - **Category**: Performance Issue
  - **Failing tests**: `test_dependency_performance_impact`
  - **Files involved**: `tests/match/brush_scoring_components/test_handle_knot_dependency_performance.py:73`
  - **Observed error**: Performance overhead too high: 50.89% (threshold: 50%)
  - **Quick next steps**:
    - Profile the dependency system to identify performance bottlenecks
    - Optimize dependency calculation logic
    - Consider caching or memoization for dependency results
  - **Notes/links**: Dependency system adds 50.89% overhead, slightly above acceptable 50% threshold

---

## Next Runner Guidance

### Priority Order (Highest Leverage/Lowest Effort First)

1. **Group 1: Delta Calculation System Issues** - Core functionality affecting multiple table types
2. **Group 2: Report Integration and Table Generation** - Core reporting functionality
3. **Group 3: Rank Formatter and Table Output** - Core table formatting functionality
4. **Group 4: Performance and Dependency Issues** - Performance optimization, lower priority

### Environment Setup Hints

- **Virtual Environment**: Ensure `.venv` is activated (`source .venv/bin/activate`)
- **Dependencies**: Run `pip install -r requirements-dev.txt` for development dependencies
- **Test Execution**: Use `make test` for full suite, `pytest tests/specific_file.py` for targeted testing
- **Debug Mode**: Add `--debug` flag to pytest for verbose output
- **Data Files**: Ensure `data/aggregated/2025-06.json` exists for real data tests

### Investigation Approach

1. **Start with Group 1** - Delta calculation is fundamental to reporting system
2. **Check aggregator output** - Verify that all aggregators include rank fields
3. **Examine specialized table generators** - Check inheritance and rank assignment logic
4. **Verify data transformation** - Ensure ranks are preserved during historical data processing
5. **Update tests or fix implementation** - Based on intended behavior

### Notes

- **13 failures** represent approximately **0.4%** of total test suite (down from 0.9%)
- **19 tests fixed** since last TODO generation - significant progress made
- **Test Drift** failures suggest intentional implementation changes that need test updates
- **Regression** failures suggest recent changes broke delta calculation functionality
- **Performance Issue** is minor - just above threshold, likely easy to optimize
- Focus on **delta calculation system** first as it affects multiple table types

### Recent Progress

- **Manufacturer Aggregator Field Mismatches**: ✅ RESOLVED
- **Tier-Based Ranking System Integration**: ✅ RESOLVED  
- **Report Table Generator Issues**: ✅ RESOLVED
- **Enhanced Table Generation System**: ✅ RESOLVED
- **Template Processor Table Substitution**: ✅ RESOLVED
- **Ranking and Table Size Limiting**: ✅ RESOLVED

The test suite has improved significantly with 19 failures resolved. The remaining 13 failures are primarily related to delta calculation system requirements for rank fields.
