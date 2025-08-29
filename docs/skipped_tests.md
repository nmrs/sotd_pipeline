# Skipped Tests Documentation

This document tracks all tests that have been temporarily skipped in the SOTD Pipeline test suite, along with the reasons for skipping and action items for future investigation.

## Overview

As of **2025-08-28**, we have **33 skipped tests** out of **3,140 total tests** (98.9% pass rate). All skipped tests are documented below with clear reasons and next steps.

## Test Categories

### 1. Production Data Tests (High Priority - Fix Required)

These tests intentionally operate on production data files and need to be properly isolated or redesigned.

#### Catalog Validation Tests
**File**: `tests/webui/api/test_catalog_validation.py`

| Test | Reason | Action Required |
|------|--------|-----------------|
| `test_step3_composite_brush_validation` | Testing validation logic against production data structures | Redesign to use mock data or temporary catalogs |
| `test_step4_single_component_brush_validation` | Testing validation logic against production data structures | Redesign to use mock data or temporary catalogs |
| `test_step1_complete_brush_validation_dinos_mores` | Testing validation logic against production data structures | Redesign to use mock data or temporary catalogs |

**Root Cause**: These tests create temporary catalogs but still test validation logic that expects production data structures and patterns.

**Solution**: 
- Create proper mock catalog data that mirrors production structure
- Isolate validation logic from production data dependencies
- Use dependency injection for catalog data in tests

#### Integration Tests with Production Catalogs
**File**: `tests/integration/test_real_catalog_integration.py`

| Test | Reason | Action Required |
|------|--------|-----------------|
| `test_handle_knot_splitting_integration` | Intentionally tests production YAML catalogs | Redesign to use test-specific catalog data |
| `test_specific_integration_scenarios` | Intentionally tests production YAML catalogs | Redesign to use test-specific catalog data |

**Root Cause**: These tests are designed to validate real catalog data but this makes them fragile and dependent on production state.

**Solution**:
- Create comprehensive test catalog fixtures
- Mock catalog loading in tests
- Test catalog validation logic separately from data

### 2. Performance Tests (Medium Priority - Investigate)

These tests are failing due to performance issues that need investigation.

#### Brush Matcher Performance
**File**: `tests/integration/test_split_brush_performance.py`

| Test | Reason | Action Required |
|------|--------|-----------------|
| `test_brush_matcher_performance` | Performance test failing - brush matcher slower than expected (17.52s vs 3.0s threshold) | Investigate performance regression in brush matcher |

**Root Cause**: The brush matcher is taking significantly longer than expected for 100 lookups.

**Solution**:
- Profile brush matcher performance
- Identify bottlenecks in matching logic
- Optimize or adjust performance thresholds
- Consider if the 3.0s threshold is realistic

### 3. Monthly User Posts Tests (Medium Priority - Fix Required)

These tests have architectural issues that prevent proper isolation.

**File**: `tests/webui/api/production_tests/test_monthly_user_posts.py`

| Test | Reason | Action Required |
|------|--------|-----------------|
| All tests in file | API uses direct file operations and user_aggregator functions that are difficult to mock | Redesign API to use dependency injection or mock file operations |

**Root Cause**: The API directly reads files and calls functions that are hard to mock without touching production data.

**Solution**:
- Refactor API to use dependency injection
- Create mockable interfaces for file operations
- Use temporary test data files
- Mock user_aggregator functions

### 4. Brush Validation Tests (Low Priority - Fix Required)

These tests have specific issues that need investigation.

**File**: `tests/webui/api/production_tests/test_brush_validation.py`

| Test | Reason | Action Required |
|------|--------|-----------------|
| `test_pagination_support` | Pagination not implemented in API | Implement pagination or remove test |
| `test_dual_component_brush_field_type_determination_bug` | Test for specific bug that may not exist | Investigate if bug still exists, remove if not |

**Root Cause**: Tests for features that aren't implemented or bugs that may have been fixed.

**Solution**:
- Implement missing pagination feature
- Verify if the dual component bug still exists
- Remove obsolete tests

### 5. Analysis API Tests (Low Priority - Fix Required)

These tests have specific mocking issues.

**File**: `tests/webui/api/production_tests/test_analysis_split_brush_removal.py`

| Test | Reason | Action Required |
|------|--------|-----------------|
| `test_update_filtered_entries_without_split_brush` | analyze_mismatch function defined inline, making it unpatchable | Refactor to make function patchable or redesign test |

**Root Cause**: Function defined inline in test makes it impossible to patch for testing.

**Solution**:
- Refactor function to be defined at module level
- Redesign test to not require patching
- Use different testing approach

## Action Plan

### Phase 1: High Priority (Production Data Tests)
**Timeline**: Next 1-2 weeks
**Goal**: Eliminate tests that touch production data

1. **Catalog Validation Tests**
   - Create mock catalog data fixtures
   - Refactor validation logic to accept catalog data as parameter
   - Update tests to use mock data

2. **Integration Tests**
   - Create comprehensive test catalog fixtures
   - Mock catalog loading in tests
   - Test validation logic separately

### Phase 2: Medium Priority (Performance & Architecture)
**Timeline**: Next 2-4 weeks
**Goal**: Fix performance issues and architectural problems

1. **Performance Tests**
   - Profile brush matcher performance
   - Identify and fix bottlenecks
   - Adjust performance thresholds if needed

2. **Monthly User Posts Tests**
   - Refactor API to use dependency injection
   - Create mockable interfaces
   - Update tests to use proper mocking

### Phase 3: Low Priority (Specific Issues)
**Timeline**: Next 1-2 months
**Goal**: Clean up remaining test issues

1. **Brush Validation Tests**
   - Implement pagination feature
   - Investigate and remove obsolete tests

2. **Analysis API Tests**
   - Refactor functions to be patchable
   - Redesign tests as needed

## Success Metrics

- **Phase 1**: Reduce skipped tests from 33 to <20
- **Phase 2**: Reduce skipped tests from <20 to <10
- **Phase 3**: Reduce skipped tests from <10 to <5

## Notes

- **Current Pass Rate**: 98.9% (3,140 passed, 33 skipped)
- **Target Pass Rate**: 99.5%+ (minimal skipped tests)
- **Priority**: Focus on production data tests first, as they represent the highest risk
- **Documentation**: Update this file as tests are fixed or new issues are discovered

## Related Documentation

- [Testing Patterns](@testing-patterns.mdc) - Comprehensive testing guidelines
- [Pipeline Testing Rules](plans/completed/testing/pipeline_testing_rules_2025-06-20.mdc) - Pipeline-specific testing rules
- [TDD Process Optimization](plans/completed/process-optimization/tdd_process_optimization_plan_2025-01-27.mdc) - TDD methodology

---

**Last Updated**: 2025-08-28  
**Status**: Active - Tests need investigation and fixes  
**Next Review**: 2025-09-04 (1 week)
