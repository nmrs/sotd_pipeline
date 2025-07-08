# SOTD Match Analysis Tools

This directory contains various analysis and utility tools for the SOTD match phase, organized into logical subdirectories for better maintainability.

## Directory Structure

```
sotd/match/tools/
├── README.md                 # This file
├── analyzers/                # Analysis tools
│   ├── analyze_personna_blade_matches.py
│   ├── blade_analyzer.py
│   ├── brush_analyzer.py
│   ├── razor_analyzer.py
│   ├── soap_analyzer.py
│   ├── mismatch_analyzer.py
│   ├── field_analyzer.py
│   ├── pattern_analyzer.py
│   ├── confidence_analyzer.py
│   └── unmatched_analyzer.py
├── managers/                 # Management tools
│   ├── validate_correct_matches.py
│   ├── correct_matches_manager.py
│   └── pattern_manager.py
├── utils/                    # Utility tools
│   ├── analysis_base.py
│   ├── cli_utils.py
│   ├── data_processor.py
│   ├── report_generator.py
│   ├── mismatch_display.py
│   └── mismatch_detector.py
└── legacy/                   # Legacy tools (for reference)
    ├── analyze_matched.py
    ├── analyze_matched_simple.py
    ├── analyze_matched_enhanced.py
    ├── analyze_unmatched.py
    ├── analyze_soap_matches.py
    ├── suggest_soap_patterns.py
    ├── analyze_mismatches.py
    └── mismatch_analyzer_refactored.py
```

## Quick Start

All tools can be run in two ways:

### Method 1: Using -m flag (from project root)
```bash
# Analyzers
python -m sotd.match.tools.analyzers.analyze_personna_blade_matches --month 2025-05
python -m sotd.match.tools.analyzers.mismatch_analyzer --month 2025-05

# Managers
python -m sotd.match.tools.managers.validate_correct_matches
python -m sotd.match.tools.managers.correct_matches_manager

# Utils (typically imported, not run directly)
python -m sotd.match.tools.utils.data_processor
```

### Method 2: Direct path (from project root) - **Recommended for autocomplete**
```bash
# Analyzers
python sotd/match/tools/analyzers/analyze_personna_blade_matches.py --month 2025-05
python sotd/match/tools/analyzers/mismatch_analyzer.py --month 2025-05

# Managers
python sotd/match/tools/managers/validate_correct_matches.py
python sotd/match/tools/managers/correct_matches_manager.py

# Utils (typically imported, not run directly)
python sotd/match/tools/utils/data_processor.py
```

**Note**: Method 2 provides better autocomplete support in most terminals and IDEs.

## Common CLI Options

Most analyzers support these common options:

### Date Range Options
- `--month YYYY-MM`: Analyze specific month
- `--year YYYY`: Analyze entire year
- `--range YYYY-MM:YYYY-MM`: Analyze date range
- `--start YYYY-MM`: Start month for range
- `--end YYYY-MM`: End month for range

### Analysis Options
- `--field FIELD`: Product field to analyze (razor, blade, brush, soap, handle)
- `--limit N`: Maximum number of entries to show (default varies by tool)
- `--pattern PATTERN`: Regex pattern to match against field values
- `--show-details`: Show detailed match analysis
- `--show-patterns`: Show pattern effectiveness and statistics
- `--show-opportunities`: Show improvement opportunities
- `--show-mismatches`: Show potential mismatches
- `--show-examples`: Show examples for specific pattern
- `--mismatch-limit N`: Limit mismatches shown (default: 20)
- `--example-limit N`: Limit examples shown (default: 15)

### Confidence Analysis Options
- `--confidence-threshold FLOAT`: Confidence threshold for analysis (default: 70.0)
- `--show-confidence-distribution`: Show confidence score distribution
- `--show-low-confidence`: Show only low confidence matches

### Field Analysis Options
- `--show-field-breakdown`: Show breakdown by field components
- `--show-field-patterns`: Show field-specific pattern analysis
- `--field-detail-level LEVEL`: Level of detail (basic, detailed, exhaustive)

### Soap-Specific Options
- `--threshold FLOAT`: Fuzzy similarity threshold (default: 0.9)
- `--mode MODE`: Suggest patterns for 'scent' or 'brand'
- `--reverse`: Reverse the sort order (lowest count first)

### Mismatch Analyzer Specific Options
- `--threshold N`: Levenshtein distance threshold for similarity (default: 3)
- `--show-all`: Show all matches, not just mismatches
- `--show-unconfirmed`: Show only unconfirmed matches
- `--show-regex-matches`: Show only regex matches that haven't been confirmed
- `--mark-correct`: Mark displayed matches as correct (requires --force)
- `--dry-run`: Preview what would be marked as correct without making changes
- `--no-confirm`: Skip confirmation prompt (use with caution)
- `--clear-correct`: Clear all correct matches
- `--clear-field FIELD`: Clear correct matches for a specific field
- `--show-correct`: Show summary of correct matches by field
- `--force`: Force refresh of pattern cache
- `--pattern-width N`: Maximum width for pattern display (default: 80)
- `--test-correct-matches FILE`: Use test correct_matches file
- `--revalidate-correct-matches`: Re-evaluate all correct matches entries

### General Options
- `--debug`: Enable debug output
- `--help`: Show help message

**Tip**: Run `python <tool>.py --help` for a complete list of options for any specific tool.

## Analyzers Package

### Core Analysis Tools

#### `analyze_personna_blade_matches.py`
**Purpose**: Analyze Personna blade matches for 'accu' patterns and format mismatches.

**What it does**:
- Identifies percentage of Personna blade matches containing 'accu' in original strings
- Detects potential mismatches where 'accu' blades are matched to DE format but used with GEM razors
- Provides specific analysis of Accuforge entries and their razor compatibility

**Usage**:
```bash
# Analyze a specific month
python sotd/match/tools/analyzers/analyze_personna_blade_matches.py --month 2025-05

# Analyze an entire year
python sotd/match/tools/analyzers/analyze_personna_blade_matches.py --year 2024

# Analyze a date range
python sotd/match/tools/analyzers/analyze_personna_blade_matches.py --range 2024-01:2024-12
```

**Output Example**:
```
Results:
Total Personna blade matches: 150
Personna matches with 'accu' in original: 45
Percentage: 30.00%

Accuforge specific analysis:
Total Accuforge blade matches: 25
Accuforge DE blades with DE razors: 15
Accuforge DE blades with GEM razors: 10
Percentage Accuforge with DE razors: 60.00%
Percentage Accuforge with GEM razors: 40.00%

⚠️  Accuforge blades matched to DE format but used with GEM razors

Accuforge examples:
  1. ✅ Original: 'Accuforge Super Stainless'
     Pattern: 'accuforge.*super.*stainless'
     Razor format: DE
     File: 2024-06.json

  2. ❌ Original: 'Accuforge Pro Premium'
     Pattern: 'accuforge.*pro.*premium'
     Razor format: GEM
     File: 2024-07.json
```

#### `mismatch_analyzer.py`
**Purpose**: Comprehensive analysis of match quality and identification of potential mismatches.

**What it does**:
- Analyzes all product categories (razors, blades, brushes, soaps)
- Identifies potential format mismatches (e.g., DE blades with GEM razors)
- Provides confidence scores and pattern analysis
- Generates detailed reports of problematic matches
- Manages correct matches database (mark, clear, validate)

**Usage**:
```bash
# Basic analysis for a specific month
python sotd/match/tools/analyzers/mismatch_analyzer.py --month 2025-05 --field razor

# Show all matches, not just mismatches
python sotd/match/tools/analyzers/mismatch_analyzer.py --month 2025-05 --field razor --show-all

# Show only unconfirmed matches
python sotd/match/tools/analyzers/mismatch_analyzer.py --month 2025-05 --field razor --show-unconfirmed

# Show only regex matches that haven't been confirmed
python sotd/match/tools/analyzers/mismatch_analyzer.py --month 2025-05 --field razor --show-regex-matches

# Mark displayed matches as correct (requires --force)
python sotd/match/tools/analyzers/mismatch_analyzer.py --month 2025-05 --field razor --show-unconfirmed --mark-correct --force

# Preview what would be marked as correct
python sotd/match/tools/analyzers/mismatch_analyzer.py --month 2025-05 --field razor --show-unconfirmed --dry-run

# Show summary of correct matches by field
python sotd/match/tools/analyzers/mismatch_analyzer.py --show-correct

# Clear all correct matches
python sotd/match/tools/analyzers/mismatch_analyzer.py --clear-correct

# Clear correct matches for a specific field
python sotd/match/tools/analyzers/mismatch_analyzer.py --clear-field razor
```

**Key Features**:
- **Mismatch Detection**: Identifies potential format mismatches and low-confidence matches
- **Correct Matches Management**: Mark, clear, and validate entries in `correct_matches.yaml`
- **Pattern Analysis**: Shows which regex patterns are being used for matches
- **Confidence Scoring**: Provides confidence scores for match quality
- **Flexible Display**: Multiple display modes (all, unconfirmed, regex-only, etc.)

### Specialized Analyzers

#### `blade_analyzer.py`
**Purpose**: Deep analysis of blade matching patterns and issues.

#### `brush_analyzer.py`
**Purpose**: Analysis of brush matching, including handle/knot splitting.

#### `razor_analyzer.py`
**Purpose**: Analysis of razor matching patterns and format consistency.

#### `soap_analyzer.py`
**Purpose**: Specialized analysis for soap products with fuzzy matching and scent analysis.

**What it does**:
- Analyzes soap products with fuzzy string matching
- Identifies similar scents and brands
- Suggests pattern improvements for soap matching
- Provides detailed scent and brand analysis
- Helps improve soap catalog coverage

**Usage**:
```bash
# Basic soap analysis
python sotd/match/tools/analyzers/soap_analyzer.py --month 2025-05

# Set fuzzy similarity threshold (default: 0.9)
python sotd/match/tools/analyzers/soap_analyzer.py --month 2025-05 --threshold 0.85

# Suggest patterns for scent matching
python sotd/match/tools/analyzers/soap_analyzer.py --month 2025-05 --mode scent

# Suggest patterns for brand matching
python sotd/match/tools/analyzers/soap_analyzer.py --month 2025-05 --mode brand

# Reverse sort order (lowest count first)
python sotd/match/tools/analyzers/soap_analyzer.py --month 2025-05 --reverse

# Show detailed analysis
python sotd/match/tools/analyzers/soap_analyzer.py --month 2025-05 --show-details

# Limit number of entries shown
python sotd/match/tools/analyzers/soap_analyzer.py --month 2025-05 --limit 100

# Analyze specific pattern
python sotd/match/tools/analyzers/soap_analyzer.py --month 2025-05 --pattern "barrister.*mann" --show-examples
```

**Key Features**:
- **Fuzzy Matching**: Uses fuzzy string matching for soap products
- **Scent Analysis**: Specialized analysis for soap scents
- **Brand Analysis**: Focused analysis of soap brands
- **Pattern Suggestions**: Suggests improvements for soap matching patterns
- **Flexible Thresholds**: Adjustable similarity thresholds for different needs

#### `field_analyzer.py`
**Purpose**: Detailed analysis of specific product fields with pattern effectiveness and improvement suggestions.

**What it does**:
- Analyzes specific product fields (razor, blade, brush, soap, handle)
- Shows pattern effectiveness and statistics
- Identifies improvement opportunities
- Provides detailed breakdown of field components
- Shows examples for specific patterns

**Usage**:
```bash
# Basic field analysis
python sotd/match/tools/analyzers/field_analyzer.py --month 2025-05 --field razor

# Show pattern effectiveness and statistics
python sotd/match/tools/analyzers/field_analyzer.py --month 2025-05 --field razor --show-patterns

# Show improvement opportunities
python sotd/match/tools/analyzers/field_analyzer.py --month 2025-05 --field razor --show-opportunities

# Show detailed breakdown by field components
python sotd/match/tools/analyzers/field_analyzer.py --month 2025-05 --field razor --show-field-breakdown

# Show field-specific pattern analysis
python sotd/match/tools/analyzers/field_analyzer.py --month 2025-05 --field razor --show-field-patterns

# Set detail level (basic, detailed, exhaustive)
python sotd/match/tools/analyzers/field_analyzer.py --month 2025-05 --field razor --field-detail-level detailed

# Show examples for a specific pattern
python sotd/match/tools/analyzers/field_analyzer.py --month 2025-05 --field razor --pattern "gillette.*tech" --show-examples

# Limit number of entries shown
python sotd/match/tools/analyzers/field_analyzer.py --month 2025-05 --field razor --limit 50
```

**Key Features**:
- **Pattern Analysis**: Shows which regex patterns are most/least effective
- **Improvement Suggestions**: Identifies opportunities for better matching
- **Component Breakdown**: Analyzes field components (brand, model, format, etc.)
- **Example Generation**: Shows real examples for specific patterns
- **Flexible Detail Levels**: Adjustable detail level for different analysis needs

#### `pattern_analyzer.py`
**Purpose**: Analyze regex pattern effectiveness and suggest improvements.

**What it does**:
- Analyzes regex pattern performance across all product categories
- Identifies patterns that are too broad or too narrow
- Suggests pattern improvements and optimizations
- Shows pattern coverage and effectiveness statistics
- Helps optimize catalog matching patterns

**Usage**:
```bash
# Basic pattern analysis
python sotd/match/tools/analyzers/pattern_analyzer.py --month 2025-05

# Analyze specific field patterns
python sotd/match/tools/analyzers/pattern_analyzer.py --month 2025-05 --field razor

# Show pattern effectiveness and statistics
python sotd/match/tools/analyzers/pattern_analyzer.py --month 2025-05 --show-patterns

# Show improvement opportunities
python sotd/match/tools/analyzers/pattern_analyzer.py --month 2025-05 --show-opportunities

# Show potential mismatches
python sotd/match/tools/analyzers/pattern_analyzer.py --month 2025-05 --show-mismatches

# Show examples for specific pattern
python sotd/match/tools/analyzers/pattern_analyzer.py --month 2025-05 --pattern "gillette.*tech" --show-examples

# Limit number of entries shown
python sotd/match/tools/analyzers/pattern_analyzer.py --month 2025-05 --limit 50

# Show detailed analysis
python sotd/match/tools/analyzers/pattern_analyzer.py --month 2025-05 --show-details
```

**Key Features**:
- **Pattern Performance**: Analyzes how well regex patterns are working
- **Coverage Analysis**: Shows which patterns cover the most products
- **Optimization Suggestions**: Identifies patterns that could be improved
- **Effectiveness Metrics**: Provides statistics on pattern success rates
- **Example Generation**: Shows real examples for pattern validation

#### `confidence_analyzer.py`
**Purpose**: Analyze match confidence scores and identify low-confidence matches that need attention.

**What it does**:
- Analyzes confidence scores across all product categories
- Identifies low-confidence matches that may need manual review
- Shows confidence score distribution and statistics
- Provides detailed analysis of confidence patterns
- Helps prioritize which matches to review first

**Usage**:
```bash
# Basic confidence analysis
python sotd/match/tools/analyzers/confidence_analyzer.py --month 2025-05

# Set confidence threshold (default: 70.0)
python sotd/match/tools/analyzers/confidence_analyzer.py --month 2025-05 --confidence-threshold 80.0

# Show confidence score distribution
python sotd/match/tools/analyzers/confidence_analyzer.py --month 2025-05 --show-confidence-distribution

# Show only low confidence matches
python sotd/match/tools/analyzers/confidence_analyzer.py --month 2025-05 --show-low-confidence

# Analyze specific field with confidence threshold
python sotd/match/tools/analyzers/confidence_analyzer.py --month 2025-05 --field razor --confidence-threshold 75.0

# Show detailed confidence analysis
python sotd/match/tools/analyzers/confidence_analyzer.py --month 2025-05 --show-details

# Limit number of low-confidence matches shown
python sotd/match/tools/analyzers/confidence_analyzer.py --month 2025-05 --show-low-confidence --limit 100
```

**Key Features**:
- **Confidence Scoring**: Analyzes match confidence across all product types
- **Threshold Analysis**: Identifies matches below confidence thresholds
- **Distribution Analysis**: Shows confidence score distribution patterns
- **Prioritization**: Helps identify which matches need manual review first
- **Field-Specific Analysis**: Can focus on specific product categories

#### `unmatched_analyzer.py`
**Purpose**: Identify and analyze unmatched products to improve catalog coverage.

**What it does**:
- Identifies products that couldn't be matched to the catalog
- Shows frequency of unmatched products
- Provides suggestions for new catalog entries
- Analyzes patterns in unmatched data
- Helps prioritize which products to add to catalogs

**Usage**:
```bash
# Basic unmatched analysis
python sotd/match/tools/analyzers/unmatched_analyzer.py --month 2025-05

# Analyze specific field
python sotd/match/tools/analyzers/unmatched_analyzer.py --month 2025-05 --field razor

# Show detailed analysis
python sotd/match/tools/analyzers/unmatched_analyzer.py --month 2025-05 --show-details

# Show potential mismatches
python sotd/match/tools/analyzers/unmatched_analyzer.py --month 2025-05 --show-mismatches

# Limit number of unmatched entries shown
python sotd/match/tools/analyzers/unmatched_analyzer.py --month 2025-05 --limit 50

# Show examples for specific unmatched pattern
python sotd/match/tools/analyzers/unmatched_analyzer.py --month 2025-05 --pattern "unknown.*brand" --show-examples

# Analyze multiple months
python sotd/match/tools/analyzers/unmatched_analyzer.py --range 2025-01:2025-06
```

**Key Features**:
- **Unmatched Detection**: Identifies products not in current catalogs
- **Frequency Analysis**: Shows how often unmatched products appear
- **Pattern Recognition**: Identifies patterns in unmatched data
- **Catalog Improvement**: Suggests new entries for catalogs
- **Multi-Month Analysis**: Can analyze trends across time periods

## Managers Package

The `managers/` directory contains tools for managing catalog data and patterns.

#### `correct_matches_manager.py`
**Purpose**: Manage the correct matches database for manual overrides.

**What it does**:
- Add, remove, and list correct matches entries
- Validate correct matches against current patterns
- Export and import correct matches data
- Manage correct matches by field and category

**Usage**:
```bash
# List all correct matches
python sotd/match/tools/managers/correct_matches_manager.py --list

# List correct matches for specific field
python sotd/match/tools/managers/correct_matches_manager.py --list --field razor

# Add a correct match
python sotd/match/tools/managers/correct_matches_manager.py --add --field razor --original "Gillette Tech" --matched '{"brand": "Gillette", "model": "Tech"}'

# Remove a correct match
python sotd/match/tools/managers/correct_matches_manager.py --remove --field razor --original "Gillette Tech"

# Validate all correct matches
python sotd/match/tools/managers/correct_matches_manager.py --validate

# Export correct matches to file
python sotd/match/tools/managers/correct_matches_manager.py --export --output correct_matches_backup.yaml

# Import correct matches from file
python sotd/match/tools/managers/correct_matches_manager.py --import --input correct_matches_backup.yaml
```

**Key Features**:
- **CRUD Operations**: Create, read, update, delete correct matches
- **Validation**: Ensures correct matches are still valid
- **Import/Export**: Backup and restore correct matches data
- **Field Management**: Organize correct matches by product field
- **Batch Operations**: Process multiple entries at once

#### `pattern_manager.py`
**Purpose**: Manage and optimize regex patterns in product catalogs.

**What it does**:
- Analyze pattern effectiveness across catalogs
- Suggest pattern improvements and optimizations
- Validate patterns against test data
- Manage pattern conflicts and overlaps
- Export pattern statistics and reports

**Usage**:
```bash
# Analyze all patterns
python sotd/match/tools/managers/pattern_manager.py --analyze

# Analyze patterns for specific field
python sotd/match/tools/managers/pattern_manager.py --analyze --field razor

# Suggest pattern improvements
python sotd/match/tools/managers/pattern_manager.py --suggest --field razor

# Validate patterns against test data
python sotd/match/tools/managers/pattern_manager.py --validate --field razor

# Show pattern conflicts
python sotd/match/tools/managers/pattern_manager.py --conflicts --field razor

# Export pattern statistics
python sotd/match/tools/managers/pattern_manager.py --export --output pattern_stats.json

# Test specific pattern
python sotd/match/tools/managers/pattern_manager.py --test --field razor --pattern "gillette.*tech"
```

**Key Features**:
- **Pattern Analysis**: Comprehensive analysis of regex pattern performance
- **Optimization Suggestions**: Identifies patterns that could be improved
- **Conflict Detection**: Finds overlapping or conflicting patterns
- **Validation**: Tests patterns against real data
- **Statistics Export**: Generates detailed pattern performance reports

## Utils Package

The `utils/` directory contains shared utilities and helper functions.

#### `analysis_base.py`
**Purpose**: Base classes and utilities for analysis tools.

**What it does**:
- Provides base classes for all analysis tools
- Common CLI argument parsing and validation
- Shared data loading and processing utilities
- Standard output formatting and reporting
- Common error handling and logging

**Usage**: This is a library module used by other analysis tools, not run directly.

**Key Features**:
- **Base Classes**: Common functionality for all analyzers
- **CLI Utilities**: Standardized command-line interface components
- **Data Processing**: Shared data loading and validation logic
- **Output Formatting**: Consistent reporting and display utilities
- **Error Handling**: Standardized error handling across tools

#### `cli_utils.py`
**Purpose**: Command-line interface utilities for analysis tools.

**What it does**:
- Common CLI argument definitions
- Argument validation and parsing
- Help text generation
- Error message formatting
- Interactive prompts and confirmations

**Usage**: This is a library module used by other analysis tools, not run directly.

**Key Features**:
- **Argument Parsing**: Standardized CLI argument handling
- **Validation**: Input validation and error checking
- **Help Generation**: Automatic help text generation
- **Interactive Features**: User prompts and confirmations
- **Error Reporting**: Consistent error message formatting

#### `data_utils.py`
**Purpose**: Data loading and processing utilities.

**What it does**:
- Load and validate matched data files
- Process date ranges and filtering
- Handle different data formats
- Provide data transformation utilities
- Manage data caching and performance

**Usage**: This is a library module used by other analysis tools, not run directly.

**Key Features**:
- **Data Loading**: Efficient loading of matched data files
- **Date Processing**: Flexible date range handling
- **Format Support**: Multiple data format support
- **Caching**: Performance optimization through caching
- **Validation**: Data integrity checking and validation

#### `report_utils.py`
**Purpose**: Report generation and formatting utilities.

**What it does**:
- Generate formatted reports and tables
- Export data to various formats (CSV, JSON, etc.)
- Create visualizations and charts
- Format output for different display methods
- Manage report templates and styling

**Usage**: This is a library module used by other analysis tools, not run directly.

**Key Features**:
- **Report Generation**: Automated report creation
- **Format Export**: Multiple output format support
- **Visualization**: Chart and graph generation
- **Templating**: Flexible report templates
- **Styling**: Consistent output formatting

#### `validation_utils.py`
**Purpose**: Data validation and quality checking utilities.

**What it does**:
- Validate data structure and format
- Check for data quality issues
- Verify catalog consistency
- Validate regex patterns
- Provide data integrity reports

**Usage**: This is a library module used by other analysis tools, not run directly.

**Key Features**:
- **Data Validation**: Comprehensive data quality checking
- **Structure Verification**: Ensures proper data format
- **Catalog Validation**: Checks catalog consistency
- **Pattern Validation**: Validates regex patterns
- **Quality Reporting**: Detailed quality assessment reports

## Legacy Package

The `legacy/` directory contains older versions of analysis tools that have been superseded by newer, more comprehensive tools. These are kept for reference but should not be used for new analysis.

**Legacy tools and their replacements**:
- `analyze_matched.py` → `mismatch_analyzer.py`
- `analyze_matched_simple.py` → `field_analyzer.py`
- `analyze_matched_enhanced.py` → `confidence_analyzer.py`
- `analyze_unmatched.py` → `unmatched_analyzer.py`
- `analyze_soap_matches.py` → `soap_analyzer.py`
- `suggest_soap_patterns.py` → `pattern_manager.py`
- `analyze_mismatches.py` → `mismatch_analyzer.py`
- `mismatch_analyzer_refactored.py` → `mismatch_analyzer.py`

### `analyze_mismatches.py` (Legacy Tool)

**Purpose**: Legacy mismatch analysis tool with correct matches revalidation capability.

**What it does**:
- Re-evaluates all entries in `correct_matches.yaml` against current regex patterns
- Reports entries that no longer match any regex patterns
- Reports entries that now match different products than originally expected
- Helps maintain data quality as regex patterns evolve over time

**Usage**:
```bash
# Revalidate all correct matches entries
python sotd/match/tools/legacy/analyze_mismatches.py --revalidate-correct-matches

# Revalidate only razor entries
python sotd/match/tools/legacy/analyze_mismatches.py --revalidate-correct-matches --field razor

# Revalidate only blade entries
python sotd/match/tools/legacy/analyze_mismatches.py --revalidate-correct-matches --field blade

# Revalidate only brush entries
python sotd/match/tools/legacy/analyze_mismatches.py --revalidate-correct-matches --field brush

# Revalidate only soap entries
python sotd/match/tools/legacy/analyze_mismatches.py --revalidate-correct-matches --field soap
```

**What the revalidation does**:
- Loads all entries from `correct_matches.yaml`
- For each entry, runs the current regex-based matcher (bypassing the correct matches shortcut)
- Reports:
  - Entries that no longer match any regex patterns
  - Entries that now match a different product/model than originally expected
- Summarizes results and shows tables of problematic entries (first 10 of each type)

**When to use revalidation**:
- After updating regex patterns in catalog files
- When adding new products to catalogs that might affect existing patterns
- Periodically to ensure data quality
- Before running large-scale analysis to ensure accurate results

**If issues are found**:
- Review the problematic entries
- Update regex patterns if needed
- Use `--clear-correct` to reset all correct matches if necessary
- Use `--clear-field <field>` to reset specific field's correct matches

## Common Options

Most tools support these common options:

- `--help`: Show help message
- `--debug`: Enable debug output
- `--month YYYY-MM`: Analyze specific month
- `--year YYYY`: Analyze entire year
- `--range YYYY-MM:YYYY-MM`: Analyze date range

## Best Practices and Workflow

### Recommended Analysis Workflow

1. **Start with Revalidation** (if you've made catalog changes):
   ```bash
   python sotd/match/tools/legacy/analyze_mismatches.py --revalidate-correct-matches
   ```

2. **Run Comprehensive Mismatch Analysis**:
   ```bash
   python sotd/match/tools/analyzers/mismatch_analyzer.py --month 2025-05 --field razor
   ```

3. **Analyze Confidence Scores**:
   ```bash
   python sotd/match/tools/analyzers/confidence_analyzer.py --month 2025-05 --show-low-confidence
   ```

4. **Check for Unmatched Products**:
   ```bash
   python sotd/match/tools/analyzers/unmatched_analyzer.py --month 2025-05 --field razor
   ```

5. **Analyze Pattern Effectiveness**:
   ```bash
   python sotd/match/tools/analyzers/pattern_analyzer.py --month 2025-05 --field razor --show-patterns
   ```

### When to Use Each Tool

- **`mismatch_analyzer.py`**: Primary tool for identifying problematic matches
- **`confidence_analyzer.py`**: When you want to focus on low-confidence matches
- **`unmatched_analyzer.py`**: When you want to improve catalog coverage
- **`pattern_analyzer.py`**: When you want to optimize regex patterns
- **`field_analyzer.py`**: When you want detailed analysis of specific fields
- **`soap_analyzer.py`**: When working specifically with soap products

### Data Quality Maintenance

- Run revalidation after any catalog changes
- Review low-confidence matches regularly
- Update correct matches when you find good matches
- Monitor unmatched products for catalog improvements
- Test pattern changes before applying them

### Performance Tips

- Use `--limit` to control output size for large datasets
- Use `--field` to focus analysis on specific product types
- Use `--range` for multi-month analysis when needed
- Use `--force` to refresh cached data when needed

## Output Formats

Tools typically provide:
- **Console output**: Summary statistics and key findings
- **Detailed examples**: Specific cases of interest
- **Warnings**: Potential issues or mismatches
- **Recommendations**: Suggestions for improvements

## Best Practices

1. **Always use `--force`** when testing to ensure fresh data processing
2. **Start with specific months** before running year-long analysis
3. **Review warnings carefully** as they often indicate real issues
4. **Use multiple analyzers** for comprehensive analysis
5. **Check file existence** before running analysis on date ranges
6. **Use the appropriate analyzer** for your specific analysis needs

## Troubleshooting

### Common Issues

**"No files found for the specified date range"**
- Check that matched data files exist for the requested dates
- Verify the date format (YYYY-MM)

**"Error loading file"**
- Check file permissions
- Verify JSON file integrity
- Ensure file is not corrupted

**"No matches found"**
- Verify the data contains the expected product types
- Check that the date range contains data
- Ensure the tool is looking for the right patterns

### Getting Help

For issues with specific tools:
1. Check the tool's help: `python sotd/match/tools/analyzers/<tool>.py --help`
2. Review the tool's source code for detailed logic
3. Check the main pipeline documentation for context

## Contributing

When adding new analysis tools:
1. **Choose the right package**: Put analyzers in `analyzers/`, managers in `managers/`, utilities in `utils/`
2. Follow the existing naming conventions
3. Include comprehensive docstrings
4. Support common CLI options (month, year, range)
5. Add appropriate error handling
6. Update this README with tool documentation
7. Add the tool to the appropriate `__init__.py` file