# Aggregate Phase Implementation Plan

## Project Overview
Build the aggregate phase of the SOTD pipeline that processes enriched data to generate statistical summaries for downstream reporting. The phase will calculate metrics for core categories (razors, blades, brushes, soaps, etc.) and output structured JSON data.

## Implementation Checklist

### Phase 1: Foundation & Core Structure

- [x] **Step 1: Basic CLI Structure**
  - [x] Create `sotd/aggregate/run.py` with main CLI entry point
  - [x] Follow same argument pattern as other phases (--month, --year, --range, --start, --end, --out-dir, --debug, --force)
  - [x] Add basic argument parsing and validation
  - [x] Add placeholder for main processing logic
  - [x] Include proper imports and type hints
  - [x] Follow existing code style (Black formatting, 100 char line length)
  - [x] Test basic argument parsing

- [x] **Step 2: Data Loading Module**
  - [x] Create `sotd/aggregate/load.py` module
  - [x] Function to load enriched JSON data from `data/enriched/YYYY-MM.json`
  - [x] Validate JSON structure matches expected enriched data format
  - [x] Extract metadata and data sections
  - [x] Handle missing files gracefully with debug logging
  - [x] Return structured data for processing
  - [x] Include proper error handling and validation
  - [x] Add type hints and docstrings
  - [x] Test with sample enriched data

- [x] **Step 3: Core Aggregation Logic**
  - [x] Create `sotd/aggregate/engine.py` module
  - [x] Implement pandas-based aggregation logic
  - [x] Function to process enriched comment records
  - [x] Filter for successfully matched products only (match_type is "exact" or similar)
  - [x] Group by product name and calculate metrics
  - [x] Calculate: shaves (count), unique_users (nunique), avg_shaves_per_user
  - [x] Handle edge cases (empty data, single records)
  - [x] Include proper error handling and validation
  - [x] Add type hints and docstrings
  - [x] Test with sample enriched data

- [x] **Step 4: Razor Category Implementation**
  - [x] Extend aggregation engine to handle razor-specific logic
  - [x] Extract razor data from enriched records
  - [x] Handle nested structure of razor matches
  - [x] Group by razor name (from matched data)
  - [x] Calculate metrics for razors category
  - [x] Handle edge cases (missing razor data, unmatched razors)
  - [x] Add proper validation for razor data structure
  - [x] Include type hints and docstrings
  - [x] Test with sample enriched data containing razor information

- [x] **Step 5: CLI Integration**
  - [x] Wire up command line interface with aggregation logic
  - [x] Connect data loading, aggregation, and output modules
  - [x] Add proper error handling for CLI operations
  - [x] Test end-to-end CLI functionality
  - [x] Verify output structure matches specification

### Phase 2: Core Categories Implementation

- [x] **Step 6: Additional Hardware Categories**
  - [x] Add aggregation logic for razor formats, manufacturers, blades, brushes
  - [x] Handle different data structures for each category
  - [x] Extract category-specific information from enriched records
  - [x] Implement consistent metric calculation across all categories
  - [x] Handle edge cases for each category
  - [x] Add proper validation for each category
  - [x] Include type hints and docstrings
  - [x] Test with sample enriched data containing all hardware categories

  **Categories to implement:**
  - [x] Razor formats (from razor.matched.format)
  - [x] Razor manufacturers (from razor.matched.brand)
  - [x] Blades (from blade.matched)
  - [x] Brushes (from brush.matched)
  - [x] Brush handle makers (from brush.matched.handle_maker)
  - [x] Brush knot makers (from brush.matched.brand)
  - [x] Brush fibers (from brush.matched.fiber, output as 'brush_fibers')
  - [x] Brush knot sizes (from brush.matched.knot_size_mm, output as 'brush_knot_sizes')

  # Note: The output keys for brush fiber and knot size aggregations are 'brush_fibers' and 'brush_knot_sizes'.
  # These are grouped by fiber type and knot size (mm) respectively, matching the code and output structure.

- [x] **Step 7: Software Categories**
  - [x] Add aggregation logic for soap-related categories
  - [x] Handle soap data extraction from enriched records
  - [x] Implement brand diversity calculation (unique scents per brand)
  - [x] Extract soap maker information from soap.matched.maker
  - [x] Extract soap scent information from soap.matched
  - [x] Handle edge cases for soap data
  - [x] Add proper validation for soap categories
  - [x] Include type hints and docstrings
  - [x] Test with sample enriched data containing soap information

  **Categories to implement:**
  - [x] Soap makers (from soap.matched.maker)
  - [x] Soaps (from soap.matched - combine maker and scent)
  - [x] Brand diversity (count unique scents per soap maker)

- [x] **Step 8: User Categories**
  - [x] Add aggregation logic for user-based categories
  - [x] Group by user (author) and calculate shave counts
  - [x] Extract user information from enriched records
  - [x] Calculate metrics for top shavers
  - [x] Handle edge cases for user data
  - [x] Add proper validation for user categories
  - [x] Include type hints and docstrings
  - [x] Test with sample enriched data containing user information

- [x] **Step 9: Output Structure & File I/O**
  - [x] Create `sotd/aggregate/save.py` module
  - [x] Implement JSON output with proper structure
  - [x] Generate metadata section with aggregation info
  - [x] Structure data section with all categories
  - [x] Handle file writing with proper formatting
  - [x] Add force overwrite functionality
  - [x] Include proper error handling
  - [x] Add type hints and docstrings
  - [x] Test with sample aggregated data to ensure proper JSON output

### Phase 3: Multi-Month Processing & Testing

- [x] **Step 10: Multi-Month Processing**
  - [x] Extend main run function to handle multiple months
  - [x] Use tqdm for progress bars during processing
  - [x] Process months sequentially (load, aggregate, save, repeat)
  - [x] Handle date range processing
  - [x] Add proper error handling for multi-month processing
  - [x] Include debug logging for multi-month operations
  - [x] Add type hints and docstrings
  - [x] Test with multiple months of enriched data

- [x] **Step 11: Error Handling & Validation**
  - [x] Validate enriched data structure before processing
  - [x] Check for required fields in enriched records
  - [x] Validate match_type values
  - [x] Handle corrupted JSON files
  - [x] Add data quality checks
  - [x] Implement fail-fast error handling
  - [x] Add comprehensive logging
  - [x] Include type hints and docstrings
  - [x] Test with various error conditions and edge cases

- [x] **Step 12: Testing Suite**
  - [x] Create `tests/aggregate/` directory structure
  - [x] Implement unit tests for each module
  - [x] Create integration tests with sample data
  - [x] Test CLI argument parsing
  - [x] Test data loading and validation
  - [x] Test aggregation logic for each category
  - [x] Test error handling scenarios
  - [x] Test multi-month processing
  - [x] Add test data fixtures
  - [x] Include proper test documentation

  **Test coverage should include:**
  - [x] Unit tests for each function
  - [x] Integration tests for end-to-end processing
  - [x] CLI tests for argument parsing
  - [x] Error handling tests
  - [x] Performance tests for large datasets
  - [x] Edge case tests

- [x] **Step 13: Performance & Integration**
  - [x] Optimize pandas operations for large datasets
  - [x] Add memory usage monitoring in debug mode
  - [x] Integrate with main pipeline runner
  - [x] Add performance benchmarks
  - [skipped] Optimize file I/O operations (skipped: no current performance issues observed)
  - [skipped] Add comprehensive logging (skipped for now)
  - [x] Include type hints and docstrings
  - [x] Test with large datasets and ensure good performance

## Implementation Prompts

### Prompt 1: Basic CLI Structure

```text
Create the basic CLI structure for the aggregate phase following the same pattern as other pipeline phases. 

Requirements:
- Create `sotd/aggregate/run.py` with main CLI entry point
- Follow the same argument pattern as other phases (--month, --year, --range, --start, --end, --out-dir, --debug, --force)
- Create basic argument parsing and validation
- Add placeholder for the main processing logic
- Include proper imports and type hints
- Follow the existing code style (Black formatting, 100 char line length)

The CLI should parse arguments and call a main `run()` function that will be implemented in subsequent steps. Include proper error handling for invalid arguments.

Test this with basic argument parsing to ensure it follows the same pattern as other phases.
```

### Prompt 2: Data Loading Module

```text
Create the data loading functionality for the aggregate phase.

Requirements:
- Create `sotd/aggregate/load.py` module
- Function to load enriched JSON data from `data/enriched/YYYY-MM.json`
- Validate the JSON structure matches expected enriched data format
- Extract metadata and data sections
- Handle missing files gracefully with debug logging
- Return structured data for processing
- Include proper error handling and validation
- Add type hints and docstrings

The function should:
- Load the JSON file
- Validate it has the expected structure (meta, data sections)
- Extract the enriched comment records
- Return both metadata and data for processing
- Fail fast on any data structure issues

Test this with sample enriched data to ensure proper loading and validation.
```

### Prompt 3: Core Aggregation Logic

```text
Create the core aggregation engine using pandas for efficient data processing.

Requirements:
- Create `sotd/aggregate/engine.py` module
- Implement pandas-based aggregation logic
- Function to process enriched comment records
- Filter for successfully matched products only (match_type is "exact" or similar)
- Group by product name and calculate metrics
- Calculate: shaves (count), unique_users (nunique), avg_shaves_per_user
- Handle edge cases (empty data, single records)
- Include proper error handling and validation
- Add type hints and docstrings

The aggregation engine should:
- Take enriched comment records as input
- Filter out unmatched records
- Group by product name
- Calculate the three core metrics
- Return structured aggregation results
- Handle pandas operations efficiently

Test this with sample enriched data to ensure proper aggregation calculations.
```

### Prompt 4: Razor Category Implementation

```text
Implement the razors category aggregation as the first working example.

Requirements:
- Extend the aggregation engine to handle razor-specific logic
- Extract razor data from enriched records
- Handle the nested structure of razor matches
- Group by razor name (from matched data)
- Calculate metrics for razors category
- Handle edge cases (missing razor data, unmatched razors)
- Add proper validation for razor data structure
- Include type hints and docstrings

The razor aggregation should:
- Extract razor information from enriched records
- Use the matched razor name as the grouping key
- Calculate shaves, unique_users, and avg_shaves_per_user
- Handle the nested structure of razor.matched data
- Skip records where razor is not successfully matched
- Return properly structured razor aggregation results

Test this with sample enriched data containing razor information.
```

### Prompt 5: Additional Hardware Categories

```text
Extend the aggregation engine to handle all hardware categories.

Requirements:
- Add aggregation logic for razor formats, manufacturers, blades, brushes
- Handle different data structures for each category
- Extract category-specific information from enriched records
- Implement consistent metric calculation across all categories
- Handle edge cases for each category type
- Add proper validation for each category
- Include type hints and docstrings

Categories to implement:
- Razor formats (from razor.matched.format)
- Razor manufacturers (from razor.matched.brand)
- Blades (from blade.matched)
- Brushes (from brush.matched)
- Brush handle makers (from brush.matched.handle_maker)
- Brush knot makers (from brush.matched.brand)
- Brush fibers (from brush.matched.fiber, output as 'brush_fibers')
- Brush knot sizes (from brush.matched.knot_size_mm, output as 'brush_knot_sizes')

Each category should follow the same pattern: extract data, group by name, calculate metrics, return results.

Test this with sample enriched data containing all hardware categories.
```

### Prompt 6: Software Categories

```text
Implement software categories aggregation (soaps, soap makers, brand diversity).

Requirements:
- Add aggregation logic for soap-related categories
- Handle soap data extraction from enriched records
- Implement brand diversity calculation (unique scents per brand)
- Extract soap maker information from soap.matched.maker
- Extract soap scent information from soap.matched
- Handle edge cases for soap data
- Add proper validation for soap categories
- Include type hints and docstrings

Categories to implement:
- Soap makers (from soap.matched.maker)
- Soaps (from soap.matched - combine maker and scent)
- Brand diversity (count unique scents per soap maker)

For brand diversity, calculate:
- Group by soap maker
- Count unique soap scents per maker
- Include total shaves and avg shaves per scent

Test this with sample enriched data containing soap information.
```

### Prompt 7: User Categories

```text
Implement user categories aggregation (top shavers).

Requirements:
- Add aggregation logic for user-based categories
- Group by user (author) and calculate shave counts
- Extract user information from enriched records
- Calculate metrics for top shavers
- Handle edge cases for user data
- Add proper validation for user categories
- Include type hints and docstrings

The top shavers category should:
- Group by author (user)
- Count total shaves per user
- Calculate unique days (if available)
- Return users sorted by shave count
- Handle missing author information
- Include proper user identification

Test this with sample enriched data containing user information.
```

### Prompt 8: Output Structure & File I/O

```text
Create the output structure and file I/O functionality.

Requirements:
- Create `sotd/aggregate/save.py` module
- Implement JSON output with proper structure
- Generate metadata section with aggregation info
- Structure data section with all categories
- Handle file writing with proper formatting
- Add force overwrite functionality
- Include proper error handling
- Add type hints and docstrings

The output should follow this structure:
```json
{
  "meta": {
    "month": "2025-05",
    "aggregated_at": "2025-05-21T18:40:00Z",
    "total_shaves": 1609,
    "unique_shavers": 109,
    "categories": ["razor_formats", "razors", "blades", ...]
  },
  "data": {
    "razors": [...],
    "blades": [...],
    "soaps": [...],
    ...
  }
}
```

Test this with sample aggregated data to ensure proper JSON output.
```

### Prompt 9: Multi-Month Processing

```text
Implement multi-month processing with progress bars.

Requirements:
- Extend the main run function to handle multiple months
- Use tqdm for progress bars during processing
- Process months sequentially (load, aggregate, save, repeat)
- Handle date range processing
- Add proper error handling for multi-month processing
- Include debug logging for multi-month operations
- Add type hints and docstrings

The multi-month processing should:
- Parse date ranges (year, month, range)
- Process each month sequentially
- Show progress with tqdm
- Handle errors gracefully (skip failed months)
- Provide summary statistics
- Support all CLI date options

Test this with multiple months of enriched data.
```

### Prompt 10: Error Handling & Validation

```text
Add comprehensive error handling and data validation.

Requirements:
- Validate enriched data structure before processing
- Check for required fields in enriched records
- Validate match_type values
- Handle corrupted JSON files
- Add data quality checks
- Implement fail-fast error handling
- Add comprehensive logging
- Include type hints and docstrings

Error handling should:
- Validate input data structure
- Check for required fields
- Handle missing or corrupted files
- Validate metric calculations
- Provide clear error messages
- Log errors appropriately
- Fail fast on any data issues

Test this with various error conditions and edge cases.
```

### Prompt 11: Testing Suite

```text
Create comprehensive unit and integration tests.

Requirements:
- Create `tests/aggregate/` directory structure
- Implement unit tests for each module
- Create integration tests with sample data
- Test CLI argument parsing
- Test data loading and validation
- Test aggregation logic for each category
- Test error handling scenarios
- Test multi-month processing
- Add test data fixtures
- Include proper test documentation

Test coverage should include:
- Unit tests for each function
- Integration tests for end-to-end processing
- CLI tests for argument parsing
- Error handling tests
- Performance tests for large datasets
- Edge case tests

Test this with various scenarios and ensure good coverage.
```

### Prompt 12: Performance & Integration

```text
Add performance optimizations and integrate with main pipeline.

Requirements:
- Optimize pandas operations for large datasets
- Add memory usage monitoring in debug mode
- Integrate with main pipeline runner
- Add performance benchmarks
- Optimize file I/O operations
- Add comprehensive logging
- Include type hints and docstrings

Performance optimizations should:
- Use efficient pandas operations
- Minimize memory usage
- Optimize file I/O
- Add progress monitoring
- Handle large datasets efficiently
- Provide performance metrics

Integration should:
- Work with main pipeline runner
- Follow existing patterns
- Provide proper error reporting
- Support all CLI options
- Integrate with existing tooling

Test this with large datasets and ensure good performance.
```

## Progress Tracking

### Current Status
- [x] Phase 1: Foundation & Core Structure (5/5 steps completed)
- [x] Phase 2: Core Categories Implementation (4/4 steps completed)
- [x] Phase 3: Multi-Month Processing & Testing (3/4 steps completed)

### Next Steps
1. Start with **Step 13: Performance & Integration** (2/8 tasks completed)
2. Continue with remaining tasks in Step 13
3. Follow the prompts in order
4. Test each step before moving to the next
5. Check off completed items as you go

### Notes
- Each step builds on the previous
- Test thoroughly before moving to next step
- Follow existing code patterns and style
- Maintain proper error handling throughout
- Document any deviations from the plan

## Future Enhancements (TODO)

### Specialized Categories
- [ ] Blackbird Plates: Only for Blackland Blackbird razors
- [ ] Christopher Bradley Plates: Only for Karve Christopher Bradley razors
- [ ] Game Changer Plates: Only for RazoRock Game Changer razors
- [ ] Straight Widths/Grinds/Points: Only for razors with format: "Straight"

### Cross-Product Analysis
- [ ] Most Used Blades in Most Used Razors: Top razor+blade combinations
- [ ] Highest Use Count per Blade: Per-user blade usage tracking

### Performance Optimizations
- [ ] Streaming/batching for very large datasets
- [ ] Memory usage monitoring in debug mode
- [ ] Parallel processing for multiple months (if needed) 