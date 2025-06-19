# SOTD Pipeline Refactoring Implementation Plan

## Overview
This plan addresses the codebase complexity issues identified in the comprehensive review. The refactoring focuses on breaking down large files, reducing complexity, and improving separation of concerns while maintaining full functionality and test coverage.

**Testing Philosophy:**
- The codebase already has strong unit and integration test coverage.
- **Do not add new tests unless introducing new logic, handling new edge cases, or where coverage is lacking.**
- Rely on the existing test suite to catch regressions and ensure backward compatibility as you refactor.
- Only add or update tests if you:
  - Move logic to a new file and the old tests no longer cover it
  - Discover a gap in coverage for a new edge case
  - Change public APIs or interfaces

## Phase 1: Critical Refactoring - Brush Matcher Module

### Chunk 1: Extract Handle Matching Logic

#### Step 1.1: Create Enhanced HandleMatcher Class
**Goal**: Extract handle matching logic from BrushMatcher into a focused, testable class.

**Tasks**:
- [x] Create `sotd/match/handle_matcher_enhanced.py` (target: 150-200 lines)
- [x] Move `_compile_handle_patterns()` method from BrushMatcher
- [x] Move `_match_handle_maker()` method from BrushMatcher
- [x] Update BrushMatcher to use new HandleMatcher
- [x] Run quality checks: `make format lint typecheck test`
- [x] Only add or update tests if coverage is missing or logic changes

**Test Cases**:
- Rely on existing handle matcher tests and integration tests unless new logic is introduced.

#### Step 1.2: Create Enhanced KnotMatcher Class
**Goal**: Extract knot matching logic into a focused, testable class.

**Tasks**:
- [x] Create `sotd/match/knot_matcher_enhanced.py` (target: 150-200 lines)
- [x] Move knot-related methods from BrushMatcher
- [x] Update BrushMatcher to use new KnotMatcher
- [x] Run quality checks: `make format lint typecheck test`
- [x] Only add or update tests if coverage is missing or logic changes

**Test Cases**:
- Rely on existing knot matcher and integration tests unless new logic is introduced.

#### Step 1.3: Create Enhanced BrushSplitter Class
**Goal**: Extract brush splitting logic into a focused, testable class.

**Tasks**:
- [x] Create `sotd/match/brush_splitter_enhanced.py` (target: 200-250 lines)
- [x] Move all splitting methods from BrushMatcher
- [x] Consolidate delimiter-based, fiber-based, and context-based splitting
- [x] Update BrushMatcher to use new BrushSplitter
- [x] Run quality checks: `make format lint typecheck test`
- [x] Only add or update tests if coverage is missing or logic changes

**Test Cases**:
- Rely on existing brush splitter and integration tests unless new logic is introduced.

#### Step 1.4: Create Enhanced FiberProcessor Class
**Goal**: Extract fiber processing logic into a focused, testable class.

**Tasks**:
- [x] Create `sotd/match/fiber_processor_enhanced.py` (target: 150-200 lines)
- [x] Move fiber-related methods from BrushMatcher
- [x] Update BrushMatcher to use new FiberProcessor
- [x] Run quality checks: `make format lint typecheck test`
- [x] Only add or update tests if coverage is missing or logic changes

**Test Cases**:
- Rely on existing fiber processor and integration tests unless new logic is introduced.

#### Step 1.5: Refactor BrushMatcher to Orchestrator Pattern
**Goal**: Transform BrushMatcher into a lightweight orchestrator.

**Tasks**:
- [x] Refactor BrushMatcher to use all enhanced components (target: 200-250 lines)
- [x] Remove duplicated logic now handled by specialized classes
- [x] Implement orchestrator pattern for coordinating matches
- [x] Ensure backward compatibility with existing API
- [x] Run quality checks: `make format lint typecheck test`
- [x] Only add or update tests if coverage is missing or logic changes

**Test Cases**:
- Rely on existing integration and end-to-end tests unless new logic is introduced.

### Chunk 2: Extract Analysis Tools

#### Step 2.1: Split Analysis Tool into Focused Modules
**Goal**: Break down the large analysis tool into smaller, focused modules.

**Tasks**:
- [x] Create new analysis modules as needed
- [x] Refactor main analysis tool to use new modules
- [x] Run quality checks: `make format lint typecheck test`
- [x] Only add or update tests if coverage is missing or logic changes

**Test Cases**:
- Rely on existing analysis tool tests unless new logic is introduced.

## Phase 2: Aggregate Module Refactoring

### Chunk 3: Extract CLI Logic

#### Step 3.1: Create Dedicated CLI Module
**Goal**: Extract CLI logic from aggregate run.py into focused module.

**Tasks**:
- [x] Create `sotd/aggregate/cli.py` (target: 150-200 lines)
- [x] Move all CLI argument parsing logic
- [x] Move CLI validation logic
- [x] Update run.py to use new CLI module
- [x] Run quality checks: `make format lint typecheck test`
- [x] Only add or update tests if coverage is missing or logic changes

**Test Cases**:
- Rely on existing CLI and integration tests unless new logic is introduced.

#### Step 3.2: Create Performance Monitoring Module
**Goal**: Extract performance monitoring logic into focused module.

**Tasks**:
- [x] Create `sotd/aggregate/performance.py` (target: 150-200 lines)
- [x] Move memory usage tracking logic
- [x] Move performance metrics logging
- [x] Update run.py to use new performance module
- [x] Run quality checks: `make format lint typecheck test`
- [x] Only add or update tests if coverage is missing or logic changes

**Test Cases**:
- Rely on existing performance and integration tests unless new logic is introduced.

#### Step 3.3: Create Data Processing Module
**Goal**: Extract data processing logic into focused module.

**Tasks**:
- [x] Create `sotd/aggregate/processor.py` (target: 200-250 lines)
- [x] Move `process_month()` function logic
- [x] Break down into smaller, focused functions
- [x] Update run.py to use new processor module
- [x] Run quality checks: `make format lint typecheck test`
- [x] Only add or update tests if coverage is missing or logic changes

**Test Cases**:
- Rely on existing processing and integration tests unless new logic is introduced.

### Chunk 4: Refactor Specialized Aggregations

#### Step 4.1: Create Base Aggregation Class
**Goal**: Create base class to reduce code duplication in specialized aggregations.

**Tasks**:
- [x] Create `sotd/aggregate/base_aggregator.py` (target: 100-150 lines)
- [x] Extract common aggregation patterns
- [x] Implement template method pattern
- [x] Refactor specialized aggregations to inherit from base
- [x] Run quality checks: `make format lint typecheck test`
- [x] Only add or update tests if coverage is missing or logic changes

**Test Cases**:
- Rely on existing aggregation tests unless new logic is introduced.

#### Step 4.2: Group Related Aggregations
**Goal**: Organize specialized aggregations into logical groups.

**Tasks**:
- [x] Create new aggregator modules as needed
- [x] Move related aggregation functions to appropriate modules
- [x] Update imports and references
- [x] Run quality checks: `make format lint typecheck test`
- [x] Only add or update tests if coverage is missing or logic changes

**Test Cases**:
- Rely on existing aggregation tests unless new logic is introduced.

## Phase 3: Code Quality Improvements

### Chunk 5: Reduce Method Complexity

#### Step 5.1: Break Down Large Methods
**Goal**: Reduce cyclomatic complexity of large methods across the codebase.

**Tasks**:
- [ ] Identify methods with >10 cyclomatic complexity
- [ ] Break down complex methods into smaller functions
- [ ] Extract helper methods for complex logic
- [ ] Run quality checks: `make format lint typecheck test`
- [ ] Only add or update tests if coverage is missing or logic changes

**Test Cases**:
- Rely on existing tests unless new logic is introduced.

#### Step 5.2: Improve Error Handling Consistency
**Goal**: Standardize error handling patterns across the codebase.

**Tasks**:
- [ ] Create `sotd/utils/error_handling.py` (target: 100 lines)
- [ ] Implement consistent error handling decorators
- [ ] Standardize error message formats
- [ ] Apply consistent error handling across modules
- [ ] Run quality checks: `make format lint typecheck test`
- [ ] Only add or update tests if coverage is missing or logic changes

**Test Cases**:
- Rely on existing error handling and integration tests unless new logic is introduced.

### Chunk 6: Documentation and Testing

#### Step 6.1: Update Documentation
**Goal**: Update all documentation to reflect new structure.

**Tasks**:
- [ ] Update module docstrings
- [ ] Update function docstrings
- [ ] Update README.md with new structure
- [ ] Update development guidelines
- [ ] Add architecture documentation
- [ ] Run quality checks: `make format lint typecheck test`

#### Step 6.2: Enhance Test Coverage (Only if Needed)
**Goal**: Ensure comprehensive test coverage for refactored components.

**Tasks**:
- [ ] Add unit tests for new modules only if coverage is missing
- [ ] Add integration tests for new workflows only if coverage is missing
- [ ] Add performance tests for new critical paths only if coverage is missing
- [ ] Ensure test coverage >90% for all modules
- [ ] Run quality checks: `make format lint typecheck test`

## Success Criteria

### File Size Targets
- [ ] No file >300 lines
- [ ] Average file size <150 lines
- [ ] Largest file <250 lines

### Complexity Targets
- [ ] No method >20 lines
- [ ] No class >15 methods
- [ ] Cyclomatic complexity <10 per method

### Quality Targets
- [ ] All tests passing
- [ ] 100% backward compatibility
- [ ] No performance regression
- [ ] Improved maintainability scores

### Documentation Targets
- [ ] All modules documented
- [ ] All public APIs documented
- [ ] Architecture documentation updated
- [ ] Development guidelines updated

## Progress Tracking

### Phase 1 Progress
- [x] Chunk 1.1: Enhanced HandleMatcher (5/5 tasks)
- [x] Chunk 1.2: Enhanced KnotMatcher (5/5 tasks)
- [x] Chunk 1.3: Enhanced BrushSplitter (5/5 tasks)
- [x] Chunk 1.4: Enhanced FiberProcessor (5/5 tasks)
- [x] Chunk 1.5: BrushMatcher Orchestrator (5/5 tasks)
- [x] Chunk 2.1: Analysis Tools Split (4/4 tasks)

### Phase 2 Progress
- [x] Chunk 3.1: CLI Module (5/5 tasks)
- [x] Chunk 3.2: Performance Module (5/5 tasks)
- [x] Chunk 3.3: Data Processing Module (5/5 tasks)
- [x] Chunk 4.1: Base Aggregation Class (5/5 tasks)
- [x] Chunk 4.2: Grouped Aggregations (4/4 tasks)

### Phase 3 Progress
- [ ] Chunk 5.1: Method Complexity Reduction (0/4 tasks)
- [ ] Chunk 5.2: Error Handling Consistency (0/5 tasks)
- [ ] Chunk 6.1: Documentation Updates (0/5 tasks)
- [ ] Chunk 6.2: Test Coverage Enhancement (0/5 tasks)

## Implementation Notes

### TDD Approach
- Each step should be implemented using Test-Driven Development
- Write tests first only for new logic or where coverage is missing
- Ensure all tests pass before moving to next step
- Run full test suite after each step

### Quality Gates
- All code must pass `make format lint typecheck test`
- No performance regression allowed
- Maintain 100% backward compatibility
- Document all changes

### Risk Mitigation
- Implement changes incrementally
- Maintain comprehensive test coverage
- Use feature flags if needed for complex changes
- Regular integration testing with real data

### Phase 2, Chunk 3.1: Extracted all CLI argument parsing and validation from aggregate/run.py to aggregate/cli.py. Updated tests to patch datetime in the new module. All tests and quality checks pass.
- Phase 2, Chunk 3.2: Extracted performance monitoring utilities (get_memory_usage, log_performance_metrics) from aggregate/run.py to aggregate/performance.py. All tests and quality checks pass.
- Phase 2, Chunk 3.3: Extracted data processing logic (process_month and related functions) from aggregate/run.py to aggregate/processor.py. Broke down the large process_month function into smaller, focused helper functions. Updated tests to patch functions in the new processor module. All tests and quality checks pass.
- Phase 2, Chunk 4.1: Created base_aggregator.py, refactored all specialized aggregators to inherit from it, and implemented the template method pattern. All quality checks pass.
- Phase 2, Chunk 4.2: Grouped all specialized aggregators into logical modules/files and updated all imports and references. All quality checks pass.
- Phase 1, Chunk 2.1: Split analysis tools into focused modules, refactored main analysis tool, and validated with existing tests. All quality checks pass.
- fix: Corrected --force handling in aggregate phase to allow overwriting existing files when specified. Added test and validated with CLI runs.

## Timeline Estimate

- **Phase 1**: 2-3 weeks (most critical)
- **Phase 2**: 1-2 weeks
- **Phase 3**: 1 week
- **Total**: 4-6 weeks

## Next Steps

1. **Start with Phase 1, Chunk 1.1**: Enhanced HandleMatcher
2. **Follow TDD methodology**: Write tests first only if needed
3. **Commit incrementally**: Small, focused commits
4. **Track progress**: Update checkboxes as tasks complete
5. **Regular reviews**: Assess progress and adjust plan as needed 