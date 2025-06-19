# Report Phase Specification

## Overview

The Report phase generates statistical analysis reports from aggregated SOTD data, producing two types of reports that mimic the community's monthly hardware and software reports. It takes aggregated data and produces formatted markdown reports with trend analysis.

## Input/Output

### Input
- **Source**: `data/aggregated/YYYY-MM.json`
- **Format**: JSON with aggregated statistics by product categories
- **Structure**: Organized by product categories with calculated metrics and metadata

### Output  
- **Destination**: `data/reports/YYYY-MM-{Type}.md`
- **Format**: Markdown with formatted tables and analysis
- **Structure**: Community-style reports with observations, notes, and statistical tables

## Report Types

### Hardware Report
Covers razors, blades, brushes, and related equipment with the following sections:

1. **Header**: "Welcome to your SOTD Hardware Report for [Month] [Year]"
2. **Observations**: Auto-generated or manual analysis of trends
3. **Notes & Caveats**: Static content explaining methodology and data interpretation
4. **Razor Formats**: DE, Straight, GEM, AC, Injector, etc.
5. **Razors**: Specific razor models with rankings
6. **Razor Manufacturers**: Brand-level aggregation
7. **Blades**: Specific blade models with rankings
8. **Brushes**: Specific brush models with rankings
9. **Brush Handle Makers**: Handle manufacturer aggregation
10. **Brush Knot Makers**: Knot manufacturer aggregation
11. **Knot Fibers**: Synthetic, Badger, Boar, Mixed Badger/Boar, Horse
12. **Knot Sizes**: 20mm, 22mm, 24mm, 26mm, 28mm, etc.
13. **Blackbird Plates**: Only for Blackland Blackbird razors
14. **Christopher Bradley Plates**: Only for Karve Christopher Bradley razors
15. **Game Changer Plates**: Only for RazoRock Game Changer razors
16. **Straight Widths**: Only for straight razors
17. **Straight Grinds**: Only for straight razors
18. **Straight Points**: Only for straight razors
19. **Most Used Blades in Most Used Razors**: Cross-product analysis
20. **Highest Use Count per Blade**: Per-user blade usage tracking
21. **Top Shavers**: Users with highest shave counts

### Software Report
Covers soaps, aftershaves, and related products with the following sections:

1. **Header**: "Welcome to your SOTD Lather Log for [Month] [Year]"
2. **Observations**: Auto-generated or manual analysis of trends
3. **Notes & Caveats**: Static content explaining methodology and data interpretation
4. **Soap Makers**: Brand-level aggregation
5. **Soaps**: Specific soap scents with rankings
6. **Brand Diversity**: Count of unique scents per brand
7. **Top Shavers**: Users with highest shave counts

## Data Processing Rules

### Trend Analysis
- **Delta Calculations**: Position-based comparisons using Unicode arrows (↑↓)
- **Comparison Periods**: 
  - Previous month (e.g., "Δ vs Apr 2025")
  - Previous year, same month (e.g., "Δ vs May 2024") 
  - 5 years ago, same month (e.g., "Δ vs May 2020")
- **Missing Data**: Display "n/a" for items not present in comparison period
- **No Change**: Display "=" for items with same position

### Table Formatting
- **Column Order**: name, shaves, unique_users, avg_shaves_per_user, delta columns
- **Data Types**: Integers for counts, 2 decimal places for averages
- **Alignment**: Right-aligned numeric columns, left-aligned text
- **Missing Values**: "n/a" for missing data
- **Row Limits**: Configurable limits with tie-breaking (include all rows with same primary/secondary sort data)

### Special Tables
- **Most Used Blades in Most Used Razors**: Combinations of top razors with their most used blades
- **Highest Use Count per Blade**: Per-user blade usage with format and use count
- **Top Shavers**: Include all users tied for the 20th position

## Output Structure

### Report Header
```markdown
Welcome to your SOTD Hardware Report for May 2025

## Observations

* [Auto-generated or manual observations about trends]

## Notes & Caveats

* [Static content explaining methodology]
```

### Data Tables
```markdown
## Razors

| name                                     |   shaves |   unique users |   avg shaves per user | Δ vs Apr 2025   | Δ vs May 2024   | Δ vs May 2020   |
|:-----------------------------------------|---------:|---------------:|----------------------:|:----------------|:----------------|:----------------|
| RazoRock Game Changer                    |      125 |             15 |                  8.33 | =               | =               | ↑8              |
| Gillette Super Speed                     |      123 |             21 |                  5.86 | ↑1              | ↑3              | ↑3              |
```

## CLI Interface

Follows the same pattern as other pipeline phases:

```bash
python -m sotd.report run --month 2025-05 --type hardware
python -m sotd.report run --month 2025-05 --type software --force
```

### Options
- `--month`: Required month (YYYY-MM format)
- `--type`: Report type (hardware|software)
- `--out-dir`: Base directory (default: "data")
- `--debug`: Enable verbose output
- `--force`: Overwrite existing files (default: error if file exists)

## Implementation Details

### Technology Stack
- **pandas**: For data manipulation and table formatting
- **pathlib**: File path handling
- **Modular design**: Base table generator with specialized implementations

### Architecture Pattern
Follows existing phase structure:
- `run.py`: CLI entry point and main orchestration
- `cli.py`: Argument parsing and validation
- `load.py`: Data loading from aggregated files
- `process.py`: Report generation logic
- `save.py`: Markdown file output
- `table_generators/`: Modular table generation components

### Performance Considerations
- Load historical data only for delta calculations
- Use pandas for efficient data manipulation
- Generate tables sequentially to manage memory usage

### Error Handling
- **Fail fast**: Consistent with other pipeline phases
- Validate aggregated data structure before processing
- Check for required historical data files
- Clear error messages for missing data or invalid formats

## Data Requirements

### Current Month Data
- Must exist in `data/aggregated/YYYY-MM.json`
- Must contain all required categories for report type
- Must have valid metadata (total_shaves, unique_shavers)

### Historical Data
- Previous month data for delta calculations
- Previous year same month data for delta calculations  
- 5 years ago same month data for delta calculations
- All historical data must follow same structure as current data

### Data Validation
- Verify all required categories are present
- Check for required fields in each category
- Validate metric calculations (shaves, unique_users, avg_shaves_per_user)
- Ensure data types are correct (integers, floats)

## Testing Strategy

Follow the same pattern as other phases:

### Unit Tests
- Table generation logic for each category
- Delta calculation functions
- Data validation functions
- Markdown formatting functions

### Integration Tests
- End-to-end report generation with sample data
- CLI argument parsing and validation
- File I/O operations
- Historical data loading and processing

### Test Data
- Sample aggregated data files for multiple months
- Edge cases (empty data, single records, missing categories)
- Error conditions (missing files, invalid data structure)

## Future Enhancements (TODO)

### LLM Integration
- **Observations Generation**: Generate prompt for LLM to create observations section
- **Trend Analysis**: AI-powered trend detection and commentary
- **Custom Reports**: User-defined report types and sections

### Advanced Analytics
- **Seasonal Trends**: Year-over-year seasonal analysis
- **User Behavior**: Advanced user pattern analysis
- **Product Lifecycle**: Track product adoption and decline

### Output Formats
- **HTML Reports**: Web-friendly report format
- **PDF Generation**: Printable report format
- **Interactive Dashboards**: Web-based interactive reports

### Performance Optimizations
- **Caching**: Cache historical data for repeated calculations
- **Parallel Processing**: Generate multiple tables concurrently
- **Streaming**: Handle very large datasets efficiently

## Dependencies

### Added to requirements.txt
- `pandas`: For data manipulation and table formatting

### Existing Dependencies Used
- `pathlib`: File path handling
- `json`: JSON I/O operations
- `argparse`: CLI argument parsing

## Integration

### Pipeline Integration
- Integrates with main pipeline runner
- Follows same patterns as fetch, extract, match, enrich, and aggregate phases
- Consumes output from aggregate phase

### Data Flow
```
Aggregate Phase → Report Phase → Markdown Reports
     ↓                ↓              ↓
data/aggregated/ → sotd.report → data/reports/
```

## Validation

### Input Validation
- Verify aggregated data structure and required fields
- Check for required historical data files
- Validate month format and date ranges

### Output Validation  
- Verify markdown syntax and formatting
- Check table structure and column alignment
- Ensure all required sections are present
- Validate delta calculations and symbols

### Data Quality Checks
- Verify metric calculations match source data
- Check for consistency in naming conventions
- Ensure proper handling of missing data
- Validate trend analysis accuracy

## Notes & Caveats Content

### Hardware Report Notes
Static content explaining:
- Data source and methodology
- Product categorization rules
- Blade format differentiation
- Brush maker attribution rules
- Delta calculation methodology
- User statistics interpretation

### Software Report Notes  
Static content explaining:
- Data source and methodology
- Soap maker attribution rules
- Brand diversity calculations
- Delta calculation methodology
- User statistics interpretation 