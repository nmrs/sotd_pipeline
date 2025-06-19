# Aggregate Phase Specification

## Overview

The Aggregate phase processes enriched SOTD data to generate statistical summaries for downstream reporting. It takes enriched comment data and produces aggregated metrics organized by product categories.

## Input/Output

### Input
- **Source**: `data/enriched/YYYY-MM.json`
- **Format**: JSON with enriched comment records
- **Structure**: Each record contains matched product data with metadata

### Output  
- **Destination**: `data/aggregated/YYYY-MM.json`
- **Format**: JSON with aggregated statistics
- **Structure**: Organized by product categories with calculated metrics

## Core Categories

### Hardware Categories
- **Razor Formats**: DE, Straight, GEM, AC, Injector, etc.
- **Razors**: Specific razor models (e.g., "RazoRock Game Changer")
- **Razor Manufacturers**: Brand-level aggregation (e.g., "Gillette", "Blackland")
- **Blades**: Specific blade models (e.g., "Astra Superior Platinum (Green)")
- **Brushes**: Specific brush models (e.g., "AP Shave Co G5C")
- **Brush Handle Makers**: Handle manufacturer aggregation
- **Brush Knot Makers**: Knot manufacturer aggregation  
- **Brush Fibers**: Synthetic, Badger, Boar, Mixed Badger/Boar, Horse
- **Brush Knot Sizes**: 20mm, 22mm, 24mm, 26mm, 28mm, etc.

### Software Categories
- **Soap Makers**: Brand-level aggregation (e.g., "Barrister and Mann")
- **Soaps**: Specific soap scents (e.g., "Stirling Soap Co. - Executive Man")
- **Brand Diversity**: Count of unique scents per brand

### User Categories
- **Top Shavers**: Users with highest shave counts

## Metrics Calculated

For each category, the following metrics are calculated:

- **shaves**: Total number of shaves using this item
- **unique_users**: Number of distinct users who used this item
- **avg_shaves_per_user**: shaves / unique_users

## Data Processing Rules

### Filtering
- **Only process successfully matched products**: Records that contain matched product data with appropriate fields (brand, maker, etc.)
- **Skip unmatched records**: Records with no matched data or empty matched fields
- **Presence implies success**: If matched data exists with required fields, it represents a successful match regardless of match strategy
- **Rely on match step**: Business rules like GEM → Personna GEM PTFE mapping are handled in match phase

### Aggregation Logic
- **Group by product name**: Use the matched product name as the grouping key
- **Count occurrences**: Track total usage and unique users
- **Calculate averages**: Pre-calculate avg_shaves_per_user for report efficiency

## Output Structure

```json
{
  "meta": {
    "month": "2025-05",
    "aggregated_at": "2025-05-21T18:40:00Z", 
    "total_shaves": 1609,
    "unique_shavers": 109,
    "categories": ["razor_formats", "razors", "blades", "soaps", ...]
  },
  "data": {
    "razor_formats": [
      {
        "name": "DE",
        "shaves": 1097,
        "unique_users": 99,
        "avg_shaves_per_user": 11.08
      }
    ],
    "razors": [...],
    "blades": [...],
    "soaps": [...],
    "brush_handle_makers": [...],
    "brush_knot_makers": [...],
    "brush_fibers": [...],
    "brush_knot_sizes": [...],
    "soap_makers": [...],
    "brand_diversity": [...],
    "top_shavers": [...]
  }
}
```

## CLI Interface

Follows the same pattern as other pipeline phases:

```bash
python -m sotd.aggregate.run --month 2025-05
python -m sotd.aggregate.run --year 2025
python -m sotd.aggregate.run --range 2025-01:2025-05
```

### Options
- `--month`: Single month (e.g., 2025-05)
- `--year`: All months in year (e.g., 2025)
- `--range`: Date range (e.g., 2025-01:2025-05)
- `--start` / `--end`: Override range boundaries
- `--out-dir`: Base directory (default: "data")
- `--debug`: Enable verbose output
- `--force`: Overwrite existing files

## Implementation Details

### Technology Stack
- **pandas**: For efficient data aggregation and manipulation
- **tqdm**: Progress bars for month processing
- **Sequential processing**: Load one month, aggregate, save, repeat

### Performance Considerations
- Process months sequentially to manage memory usage
- Use pandas for efficient groupby operations
- Pre-calculate metrics to avoid repeated computation in report phase

### Error Handling
- **Fail fast**: Consistent with other pipeline phases
- Validate data structure before processing
- Check for required fields in enriched data
- Handle missing files gracefully with debug logging

## Testing Strategy

Follow the same pattern as other phases:

### Unit Tests
- Aggregation logic for each category
- Metric calculation functions
- Data validation functions

### Integration Tests
- End-to-end processing with sample data
- CLI argument parsing
- File I/O operations

### Test Data
- Sample enriched data files
- Edge cases (empty data, single records)
- Error conditions

## Future Enhancements (TODO)

### Specialized Categories
- **Blackbird Plates**: Only for Blackland Blackbird razors
- **Christopher Bradley Plates**: Only for Karve Christopher Bradley razors
- **Game Changer Plates**: Only for RazoRock Game Changer razors
- **Straight Widths/Grinds/Points**: Only for razors with format: "Straight"

### Cross-Product Analysis
- **Most Used Blades in Most Used Razors**: Top razor+blade combinations
- **Highest Use Count per Blade**: Per-user blade usage tracking

### Performance Optimizations
- Streaming/batching for very large datasets
- Memory usage monitoring in debug mode
- Parallel processing for multiple months (if needed)

## Dependencies

### Added to requirements.txt
- `pandas`: For data aggregation and manipulation

### Existing Dependencies Used
- `tqdm`: Progress bars
- `pathlib`: File path handling
- `json`: JSON I/O operations
- `argparse`: CLI argument parsing

## Integration

### Pipeline Integration
- Integrates with main pipeline runner
- Follows same patterns as fetch, extract, match, and enrich phases
- Output feeds into report generation phase

### Data Flow

## Validation

### Input Validation
- Verify enriched data structure
- Check for required fields in enriched records
- Validate presence of matched data where expected

### Output Validation  
- Verify aggregated data structure
- Check metric calculations
- Ensure all categories are present

### Data Quality Checks
- Verify shaves >= unique_users
- Check for reasonable avg_shaves_per_user values
- Validate category names are consistent

# Note: The output keys for brush fiber and knot size aggregations are 'brush_fibers' and 'brush_knot_sizes'.
# These are grouped by fiber type and knot size (mm) respectively, matching the code and output structure.