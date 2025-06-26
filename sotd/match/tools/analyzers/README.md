# Match Phase Analysis Tools

This directory contains specialized analysis tools for examining matched data and identifying potential issues or patterns.

## Available Tools

### `analyze_blade_razor_conflicts.py`

A comprehensive tool for detecting format mismatches between blades and razors in matched data.

**Purpose**: Identifies potential incompatibilities between blade formats and razor formats, such as:
- DE blades used with cartridge/disposable razors
- AC blades used with DE razors
- GEM blades used with DE razors
- Any other format incompatibilities

**Usage**:
```bash
# Analyze a specific month
python sotd/match/tools/analyzers/analyze_blade_razor_conflicts.py --month 2024-01

# Analyze an entire year
python sotd/match/tools/analyzers/analyze_blade_razor_conflicts.py --year 2024

# Analyze a date range
python sotd/match/tools/analyzers/analyze_blade_razor_conflicts.py --start 2024-01 --end 2024-06

# Show more examples
python sotd/match/tools/analyzers/analyze_blade_razor_conflicts.py --month 2024-01 --examples 50

# Skip detailed examples
python sotd/match/tools/analyzers/analyze_blade_razor_conflicts.py --month 2024-01 --no-examples
```

**Output**: Provides summary statistics, conflict breakdown by type, detailed examples with comment information, and recommendations for addressing issues.

**Detailed Output Format**: Each conflict example includes:
- Comment ID and URL for easy reference
- Author information
- Complete blade details: original string, matched brand/model, format, pattern, match type
- Complete razor details: original string, matched brand/model, format, pattern, match type

### `analyze_personna_blade_matches.py`

A specialized tool for analyzing Personna blade matches, particularly focusing on 'accu' patterns and potential format mismatches.

**Purpose**: Identifies:
- Percentage of Personna blade matches containing 'accu' in original strings
- Potential mismatches where 'accu' blades are matched to DE format but used with GEM razors
- Specific analysis of Accuforge entries and their razor compatibility

**Usage**:
```bash
# Analyze a specific month
python sotd/match/tools/analyzers/analyze_personna_blade_matches.py --month 2024-01

# Analyze an entire year
python sotd/match/tools/analyzers/analyze_personna_blade_matches.py --year 2024
```

## Common Use Cases

### Data Quality Validation
Use these tools to validate the quality of matched data and identify potential issues:
- Format mismatches that could indicate matching errors
- Unusual patterns that might need investigation
- Data consistency across different time periods

### Match Phase Debugging
When investigating issues with the match phase:
- Run conflict analysis to identify problematic patterns
- Use the results to improve matching logic
- Validate fixes by re-running analysis

### Performance Monitoring
Regular analysis can help:
- Track the prevalence of format conflicts over time
- Identify trends in matching accuracy
- Monitor the impact of matching improvements

## Format Compatibility Rules

The blade-razor conflict analysis tool uses the following incompatibility rules:

| Blade Format | Incompatible Razor Formats |
|--------------|---------------------------|
| DE           | CARTRIDGE, DISPOSABLE, AC, GEM, INJECTOR |
| AC           | DE, CARTRIDGE, DISPOSABLE, GEM, INJECTOR |
| GEM          | DE, CARTRIDGE, DISPOSABLE, AC, INJECTOR |
| INJECTOR     | DE, CARTRIDGE, DISPOSABLE, AC, GEM |
| CARTRIDGE    | DE, AC, GEM, INJECTOR |
| DISPOSABLE   | DE, AC, GEM, INJECTOR |

## Contributing

When adding new analysis tools:
1. Follow the existing patterns for CLI argument handling
2. Include comprehensive tests
3. Add documentation to this README
4. Ensure all quality checks pass before committing