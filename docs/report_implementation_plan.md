# Report Phase Implementation Plan

## Project Overview
Build the report phase of the SOTD pipeline that generates statistical analysis reports from aggregated data, producing two types of reports that mimic the community's monthly hardware and software reports. The phase will create formatted markdown reports with trend analysis and delta calculations.

## Implementation Checklist

### Phase 1: Foundation & Core Structure

- [x] **Step 1: Basic CLI Structure**
  - [x] Create `sotd/report/run.py` with main CLI entry point
  - [x] Follow same argument pattern as other phases (--month, --type, --out-dir, --debug, --force)
  - [x] Add basic argument parsing and validation
  - [x] Add placeholder for main processing logic
  - [x] Include proper imports and type hints
  - [x] Follow existing code style (Black formatting, 100 char line length)
  - [x] Test basic argument parsing

- [x] **Step 2: Data Loading Module**
  - [x] Create `sotd/report/load.py` module
  - [x] Function to load aggregated JSON data from `data/aggregated/YYYY-MM.json`
  - [x] Function to load historical data for delta calculations
  - [x] Validate JSON structure matches expected aggregated data format
  - [x] Extract metadata and data sections
  - [x] Handle missing files gracefully with clear error messages
  - [x] Return structured data for processing
  - [x] Include proper error handling and validation
  - [x] Add type hints and docstrings
  - [x] Test with sample aggregated data

- [x] **Step 3: Core Report Generation Logic**
  - [x] Create `sotd/report/process.py` module
  - [x] Implement base report generator class
  - [x] Function to generate report header with dynamic content
  - [x] Function to generate observations placeholder
  - [x] Function to generate notes & caveats section
  - [x] Handle report type selection (hardware vs software)
  - [x] Include proper error handling and validation
  - [x] Add type hints and docstrings
  - [x] Test with sample aggregated data

- [x] **Step 4: Basic Table Generator**
  - [x] Create `sotd/report/table_generators/` directory
  - [x] Create `sotd/report/table_generators/base.py` with base table generator
  - [x] Implement generic table generation logic using pandas
  - [x] Function to create markdown tables with proper formatting
  - [x] Handle column alignment and data types
  - [x] Implement configurable row limits with tie-breaking
  - [x] Include proper error handling and validation
  - [x] Add type hints and docstrings
  - [x] Test with sample aggregated data

- [x] **Step 5: CLI Integration**
  - [x] Wire up command line interface with report generation logic
  - [x] Connect data loading, processing, and output modules
  - [x] Add proper error handling for CLI operations
  - [x] Test end-to-end CLI functionality
  - [x] Verify output structure matches specification

  _Step 5 completed. CLI is fully integrated, tested, and all quality checks are passing._

### Phase 2: Hardware Report Implementation

- [x] **Step 6: Hardware Report Structure**
  - [x] Create `sotd/report/hardware_report.py` module
  - [x] Implement hardware report generator class
  - [x] Generate hardware-specific header and notes
  - [x] Implement hardware table order and structure
  - [x] Handle hardware-specific data categories
  - [x] Include proper error handling and validation
  - [x] Add type hints and docstrings
  - [x] Test with sample aggregated data

  _Step 6 completed. hardware_report.py created, logic moved from process.py, and all quality checks are passing._

- [x] **Step 7: Core Hardware Tables**
  - [x] Implement table generators for core hardware categories (RazorFormatsTableGenerator implemented)
  - [x] Create `sotd/report/table_generators/razor_tables.py`
  - [x] Implement razor formats table generator (RazorFormatsTableGenerator implemented)
  - [x] Implement razors table generator (RazorsTableGenerator implemented)
  - [x] Implement razor manufacturers table generator (RazorManufacturersTableGenerator implemented)
  - [x] Handle data extraction and formatting for each table
  - [x] Include proper error handling and validation
  - [x] Add type hints and docstrings
  - [x] Test with sample aggregated data

  _Step 7 completed. All three razor table generators implemented with comprehensive error handling, data validation, and defensive programming. Added extensive test coverage with 16 test cases covering edge cases, invalid data, and proper functionality. Fixed circular import issues by moving BaseReportGenerator to base.py. Updated table generators to work with real aggregated data structure (name, shaves, unique_users fields). Successfully tested with live data from 2025-01.json - generated proper markdown tables with 22 razors showing real usage statistics. All quality checks are passing._

- [ ] **Step 8: Blade and Brush Tables**
  - [ ] Create `sotd/report/table_generators/blade_tables.py`
  - [ ] Create `sotd/report/table_generators/brush_tables.py`
  - [ ] Implement blades table generator
  - [ ] Implement brush handle makers table generator
  - [ ] Implement brush knot makers table generator
  - [ ] Implement brush fibers table generator
  - [ ] Implement brush knot sizes table generator
  - [ ] Handle data extraction and formatting for each table
  - [ ] Include proper error handling and validation
  - [ ] Add type hints and docstrings
  - [ ] Test with sample aggregated data

- [ ] **Step 9: Specialized Hardware Tables**
  - [ ] Create `sotd/report/table_generators/specialized_tables.py`
  - [ ] Implement Blackbird plates table generator
  - [ ] Implement Christopher Bradley plates table generator
  - [ ] Implement Game Changer plates table generator
  - [ ] Implement straight razor specs tables (widths, grinds, points)
  - [ ] Handle conditional table generation based on data availability
  - [ ] Include proper error handling and validation
  - [ ] Add type hints and docstrings
  - [ ] Test with sample aggregated data

### Phase 3: Software Report Implementation

- [ ] **Step 10: Software Report Structure**
  - [ ] Create `sotd/report/software_report.py` module
  - [ ] Implement software report generator class
  - [ ] Generate software-specific header and notes
  - [ ] Implement software table order and structure
  - [ ] Handle software-specific data categories
  - [ ] Include proper error handling and validation
  - [ ] Add type hints and docstrings
  - [ ] Test with sample aggregated data

- [ ] **Step 11: Software Tables**
  - [ ] Create `sotd/report/table_generators/soap_tables.py`
  - [ ] Implement soap makers table generator
  - [ ] Implement soaps table generator
  - [ ] Implement brand diversity table generator
  - [ ] Handle data extraction and formatting for each table
  - [ ] Include proper error handling and validation
  - [ ] Add type hints and docstrings
  - [ ] Test with sample aggregated data

### Phase 4: Delta Calculations & Trend Analysis

- [ ] **Step 12: Delta Calculation Engine**
  - [ ] Create `sotd/report/delta_calculator.py` module
  - [ ] Implement position-based delta calculation logic
  - [ ] Function to calculate deltas between two datasets
  - [ ] Handle missing data with "n/a" values
  - [ ] Generate Unicode arrow symbols (↑↓) for deltas
  - [ ] Implement comparison period logic (previous month, previous year, 5 years ago)
  - [ ] Include proper error handling and validation
  - [ ] Add type hints and docstrings
  - [ ] Test with sample historical data

- [ ] **Step 13: Historical Data Integration**
  - [ ] Extend data loading to handle historical data files
  - [ ] Implement automatic historical data detection
  - [ ] Function to load comparison period data
  - [ ] Handle missing historical data gracefully
  - [ ] Validate historical data structure consistency
  - [ ] Include proper error handling and validation
  - [ ] Add type hints and docstrings
  - [ ] Test with multiple months of historical data

- [ ] **Step 14: Delta Column Integration**
  - [ ] Integrate delta calculations into table generators
  - [ ] Add delta columns to all relevant tables
  - [ ] Handle delta column formatting and alignment
  - [ ] Implement consistent delta display across all tables
  - [ ] Include proper error handling and validation
  - [ ] Add type hints and docstrings
  - [ ] Test with historical data for delta calculations

### Phase 5: Special Tables & Cross-Product Analysis

- [ ] **Step 15: Cross-Product Tables**
  - [ ] Create `sotd/report/table_generators/cross_product_tables.py`
  - [ ] Implement "Most Used Blades in Most Used Razors" table
  - [ ] Implement "Highest Use Count per Blade" table
  - [ ] Handle complex data relationships and aggregations
  - [ ] Implement proper sorting and ranking logic
  - [ ] Include proper error handling and validation
  - [ ] Add type hints and docstrings
  - [ ] Test with sample aggregated data

- [ ] **Step 16: Top Shavers Table**
  - [ ] Create `sotd/report/table_generators/user_tables.py`
  - [ ] Implement top shavers table generator
  - [ ] Handle tie-breaking logic (include all users tied for 20th position)
  - [ ] Calculate missed days from aggregated data
  - [ ] Implement proper sorting and ranking logic
  - [ ] Include proper error handling and validation
  - [ ] Add type hints and docstrings
  - [ ] Test with sample aggregated data

### Phase 6: Output & File Management

- [ ] **Step 17: Markdown Output Module**
  - [ ] Create `sotd/report/save.py` module
  - [ ] Implement markdown file generation
  - [ ] Function to write formatted markdown content
  - [ ] Handle file naming convention (YYYY-MM-{Type}.md)
  - [ ] Implement force overwrite functionality
  - [ ] Add proper error handling for file operations
  - [ ] Include type hints and docstrings
  - [ ] Test with sample report content

- [ ] **Step 18: Report Assembly**
  - [ ] Integrate all components into complete report generation
  - [ ] Assemble header, observations, notes, and all tables
  - [ ] Handle proper markdown formatting and structure
  - [ ] Implement consistent styling across all sections
  - [ ] Include proper error handling and validation
  - [ ] Add type hints and docstrings
  - [ ] Test end-to-end report generation

### Phase 7: Testing & Validation

- [ ] **Step 19: Testing Suite**
  - [ ] Create `tests/report/` directory structure
  - [ ] Implement unit tests for each module
  - [ ] Create integration tests with sample data
  - [ ] Test CLI argument parsing
  - [ ] Test data loading and validation
  - [ ] Test table generation logic for each category
  - [ ] Test delta calculation logic
  - [ ] Test error handling scenarios
  - [ ] Add test data fixtures
  - [ ] Include proper test documentation

  **Test coverage should include:**
  - [ ] Unit tests for each function
  - [ ] Integration tests for end-to-end report generation
  - [ ] CLI tests for argument parsing
  - [ ] Error handling tests
  - [ ] Delta calculation tests
  - [ ] Table formatting tests
  - [ ] Edge case tests

- [ ] **Step 20: Error Handling & Validation**
  - [ ] Validate aggregated data structure before processing
  - [ ] Check for required fields in aggregated data
  - [ ] Validate historical data availability
  - [ ] Handle corrupted JSON files
  - [ ] Add data quality checks
  - [ ] Implement fail-fast error handling
  - [ ] Add comprehensive logging
  - [ ] Include type hints and docstrings
  - [ ] Test with various error conditions and edge cases

### Phase 8: Performance & Integration

- [ ] **Step 21: Performance Optimization**
  - [ ] Optimize pandas operations for large datasets
  - [ ] Add memory usage monitoring in debug mode
  - [ ] Optimize historical data loading
  - [ ] Implement efficient delta calculations
  - [ ] Add performance benchmarks
  - [ ] Include type hints and docstrings
  - [ ] Test with large datasets and ensure good performance

- [ ] **Step 22: Pipeline Integration**
  - [ ] Integrate with main pipeline runner
  - [ ] Add report phase to pipeline workflow
  - [ ] Test integration with aggregate phase output
  - [ ] Verify data flow from aggregate to report
  - [ ] Include proper error handling and validation
  - [ ] Add type hints and docstrings
  - [ ] Test end-to-end pipeline integration

## Implementation Prompts

### Prompt 1: Basic CLI Structure

```text
Create the basic CLI structure for the report phase following the same pattern as other pipeline phases. 

Requirements:
- Create `sotd/report/run.py` with main CLI entry point
- Follow the same argument pattern as other phases (--month, --type, --out-dir, --debug, --force)
- Create basic argument parsing and validation
- Add placeholder for the main processing logic
- Include proper imports and type hints
- Follow the existing code style (Black formatting, 100 char line length)

The CLI should parse arguments and call a main `run()` function that will be implemented in subsequent steps. Include proper error handling for invalid arguments.

Test this with basic argument parsing to ensure it follows the same pattern as other phases.
```

### Prompt 2: Data Loading Module

```text
Create the data loading functionality for the report phase.

Requirements:
- Create `sotd/report/load.py` module
- Function to load aggregated JSON data from `data/aggregated/YYYY-MM.json`
- Function to load historical data for delta calculations
- Validate JSON structure matches expected aggregated data format
- Extract metadata and data sections
- Handle missing files gracefully with clear error messages
- Return structured data for processing
- Include proper error handling and validation
- Add type hints and docstrings

The module should handle loading both current month data and historical data for trend analysis. Include validation to ensure the data structure is correct before processing.

Test with sample aggregated data to ensure proper loading and validation.
```

### Prompt 3: Basic Table Generator

```text
Create the basic table generation functionality for the report phase.

Requirements:
- Create `sotd/report/table_generators/base.py` with base table generator
- Implement generic table generation logic using pandas
- Function to create markdown tables with proper formatting
- Handle column alignment and data types
- Implement configurable row limits with tie-breaking
- Include proper error handling and validation
- Add type hints and docstrings

The base table generator should handle the common table formatting requirements and provide a foundation for specialized table generators. Focus on creating properly formatted markdown tables with the correct column structure.

Test with sample aggregated data to ensure proper table formatting and output.
```

### Prompt 4: Hardware Report Structure

```text
Create the hardware report structure and basic implementation.

Requirements:
- Create `sotd/report/hardware_report.py` module
- Implement hardware report generator class
- Generate hardware-specific header and notes
- Implement hardware table order and structure
- Handle hardware-specific data categories
- Include proper error handling and validation
- Add type hints and docstrings

The hardware report should follow the exact structure specified in the requirements, including the proper header format, notes & caveats section, and table ordering. Focus on creating the basic structure that can be extended with individual table generators.

Test with sample aggregated data to ensure proper report structure and formatting.
```

### Prompt 5: Delta Calculation Engine

```text
Create the delta calculation functionality for trend analysis.

Requirements:
- Create `sotd/report/delta_calculator.py` module
- Implement position-based delta calculation logic
- Function to calculate deltas between two datasets
- Handle missing data with "n/a" values
- Generate Unicode arrow symbols (↑↓) for deltas
- Implement comparison period logic (previous month, previous year, 5 years ago)
- Include proper error handling and validation
- Add type hints and docstrings

The delta calculator should handle position-based comparisons and generate the appropriate Unicode arrows for trend analysis. Focus on accurate delta calculations and proper handling of missing data.

Test with sample historical data to ensure proper delta calculations and symbol generation.
```

## Success Criteria

### Functional Requirements
- [ ] Generate hardware reports with all required tables and sections
- [ ] Generate software reports with all required tables and sections
- [ ] Calculate accurate delta values for trend analysis
- [ ] Handle missing historical data gracefully
- [ ] Produce properly formatted markdown output
- [ ] Support force overwrite functionality
- [ ] Include comprehensive error handling

### Quality Requirements
- [ ] Follow existing code style and patterns
- [ ] Include comprehensive test coverage
- [ ] Provide clear error messages
- [ ] Handle edge cases and error conditions
- [ ] Maintain good performance with large datasets
- [ ] Include proper documentation and type hints

### Integration Requirements
- [ ] Integrate with main pipeline workflow
- [ ] Consume aggregated data correctly
- [ ] Follow existing phase patterns and structure
- [ ] Provide consistent CLI interface
- [ ] Handle data flow properly

## Notes

- The implementation should follow the existing pipeline patterns and code style
- Focus on modular design with clear separation of concerns
- Prioritize comprehensive testing from the start
- Ensure proper error handling and validation throughout
- Maintain consistency with other pipeline phases 