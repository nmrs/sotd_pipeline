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

**Usage**:
```bash
python sotd/match/tools/analyzers/mismatch_analyzer.py --month 2025-05
```

### Specialized Analyzers

#### `blade_analyzer.py`
**Purpose**: Deep analysis of blade matching patterns and issues.

#### `brush_analyzer.py`
**Purpose**: Analysis of brush matching, including handle/knot splitting.

#### `razor_analyzer.py`
**Purpose**: Analysis of razor matching patterns and format consistency.

#### `soap_analyzer.py`
**Purpose**: Analysis of soap and software matching.

#### `field_analyzer.py`
**Purpose**: Analyze specific fields in matched data.

#### `pattern_analyzer.py`
**Purpose**: Analyze regex pattern performance and effectiveness.

#### `confidence_analyzer.py`
**Purpose**: Analyze match confidence scores and reliability.

#### `unmatched_analyzer.py`
**Purpose**: Analyze unmatched products and suggest improvements.

## Managers Package

### `validate_correct_matches.py`
**Purpose**: Validate and manage the `correct_matches.yaml` file.

**What it does**:
- Validates syntax and structure of correct matches
- Checks for duplicate entries
- Ensures proper formatting
- Provides suggestions for improvements

**Usage**:
```bash
python sotd/match/tools/managers/validate_correct_matches.py
```

### `correct_matches_manager.py`
**Purpose**: Manage and maintain the correct matches database.

### `pattern_manager.py`
**Purpose**: Manage and analyze regex patterns used in matching.

## Utils Package

### `analysis_base.py`
**Purpose**: Base classes and common functionality for analysis tools.

### `cli_utils.py`
**Purpose**: Common CLI utilities and argument parsing.

### `data_processor.py`
**Purpose**: Process and transform match data for analysis.

### `report_generator.py`
**Purpose**: Generate comprehensive match analysis reports.

### `mismatch_display.py`
**Purpose**: Display and format mismatch analysis results.

### `mismatch_detector.py`
**Purpose**: Core logic for detecting mismatches in match data.

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

## Common Options

Most analyzers support these common options:

- `--month YYYY-MM`: Analyze specific month
- `--year YYYY`: Analyze entire year
- `--range YYYY-MM:YYYY-MM`: Analyze date range
- `--start YYYY-MM`: Start month for range
- `--end YYYY-MM`: End month for range

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