# Aggregate Phase Specification

## Overview

The Aggregate phase processes enriched SOTD data to generate statistical summaries for downstream reporting. It takes enriched comment data and produces aggregated metrics organized by product categories.

## Input/Output

### Input
- **Source**: `data/enriched/YYYY-MM.json`
- **Format**: JSON with enriched comment records
- **Structure**: Each record contains matched product data with metadata and enriched fields

### Output  
- **Destination**: `data/aggregated/YYYY-MM.json`
- **Format**: JSON with aggregated statistics
- **Structure**: Organized by product categories with calculated metrics

## Core Categories

### Hardware Categories
- **Razor Formats**: DE, Straight, GEM, AC, Injector, etc.
- **Razors**: Individual razor models with brand/model/format
- **Razor Manufacturers**: Brand-level aggregation from `razor.matched.brand`
- **Blades**: Individual blade models with brand/model/format  
- **Blade Manufacturers**: Brand-level aggregation from `blade.matched.brand`
- **Brushes**: Individual brush models with brand/model/fiber
- **Brush Handle Makers**: Handle maker aggregation from `brush.matched.handle_maker`
- **Brush Knot Makers**: Knot maker aggregation from `brush.matched.knot_maker`
- **Brush Fibers**: Fiber type aggregation from `brush.matched.fiber` or `brush.enriched.fiber`
- **Brush Knot Sizes**: Knot size aggregation from `brush.matched.knot_size_mm` or `brush.enriched.knot_size_mm`

### Software Categories
- **Soaps**: Individual soap scents with maker/scent
- **Soap Makers**: Maker-level aggregation from `soap.matched.maker`

### Specialized Categories
- **Blackbird Plates**: Plate type aggregation from `razor.enriched.plate`
- **Christopher Bradley Plates**: Plate type/level aggregation from `razor.enriched.plate_type` and `razor.enriched.plate_level`
- **Game Changer Plates**: Gap aggregation from `razor.enriched.gap`
- **Super Speed Tips**: Tip type aggregation from `razor.enriched.super_speed_tip`
- **Straight Razor Widths**: Width aggregation from `razor.enriched.width`
- **Straight Razor Grinds**: Grind type aggregation from `razor.enriched.grind`
- **Straight Razor Points**: Point type aggregation from `razor.enriched.point`

### User Categories
- **Users**: Individual user aggregation from `author`

## Data Structure

### Input Record Structure
```json
{
  "author": "username",
  "razor": {
    "original": "Blackland Blackbird Ti",
    "matched": {
      "brand": "Blackland",
      "model": "Blackbird", 
      "format": "DE"
    },
    "enriched": {
      "plate": "Lite",
      "_enriched_by": "BlackbirdPlateEnricher"
    }
  },
  "blade": {
    "original": "Gillette Minora Platinum",
    "matched": {
      "brand": "Gillette",
      "model": "Minora",
      "format": "DE"
    }
  },
  "brush": {
    "original": "Semogue 610 21mm Boar",
    "matched": {
      "brand": "Semogue",
      "model": "610",
      "fiber": "Boar",
      "knot_size_mm": 21,
      "handle_maker": "Semogue",
      "knot_maker": null
    },
    "enriched": {
      "knot_size_mm": 21.0,
      "fiber": "Boar"
    }
  },
  "soap": {
    "original": "Grooming Dept - Laundry II",
    "matched": {
      "maker": "Grooming Dept",
      "scent": "Laundry II"
    }
  }
}
```

### Output Structure
```json
{
  "meta": {
    "month": "2025-01",
    "total_shaves": 1499,
    "unique_shavers": 114,
    "avg_shaves_per_user": 13.15
  },
  "data": {
    "razor_formats": [
      {"format": "DE", "shaves": 1200},
      {"format": "Straight", "shaves": 150}
    ],
    "razors": [
      {"name": "Fatip Grande", "shaves": 50},
      {"name": "Gillette Tech", "shaves": 45}
    ],
    "razor_manufacturers": [
      {"brand": "Gillette", "shaves": 300},
      {"brand": "Fatip", "shaves": 100}
    ],
    "blades": [
      {"name": "Gillette Minora", "shaves": 80},
      {"name": "Personna Lab Blue", "shaves": 60}
    ],
    "blade_manufacturers": [
      {"brand": "Gillette", "shaves": 400},
      {"brand": "Personna", "shaves": 200}
    ],
    "brushes": [
      {"name": "Semogue 610", "shaves": 30},
      {"name": "AP Shave Co MiG", "shaves": 25}
    ],
    "brush_handle_makers": [
      {"handle_maker": "Semogue", "shaves": 150},
      {"handle_maker": "AP Shave Co", "shaves": 100}
    ],
    "brush_knot_makers": [
      {"brand": "Declaration Grooming", "shaves": 80},
      {"brand": "Semogue", "shaves": 150}
    ],
    "brush_fibers": [
      {"fiber": "Synthetic", "shaves": 400},
      {"fiber": "Boar", "shaves": 300}
    ],
    "brush_knot_sizes": [
      {"knot_size_mm": 24, "shaves": 200},
      {"knot_size_mm": 26, "shaves": 180}
    ],
    "blackbird_plates": [
      {"plate": "Ti", "shaves": 40},
      {"plate": "Lite", "shaves": 25}
    ],
    "christopher_bradley_plates": [
      {"plate_type": "SB", "plate_level": "C", "shaves": 30},
      {"plate_type": "SB", "plate_level": "D", "shaves": 20}
    ],
    "game_changer_plates": [
      {"gap": "1.05", "shaves": 35},
      {"gap": ".84", "shaves": 25}
    ],
    "super_speed_tips": [
      {"super_speed_tip": "Flare", "shaves": 45},
      {"super_speed_tip": "Black", "shaves": 30}
    ],
    "straight_widths": [
      {"width": "6/8", "shaves": 80},
      {"width": "5/8", "shaves": 40}
    ],
    "straight_grinds": [
      {"grind": "Full Hollow", "shaves": 60},
      {"grind": "Hollow", "shaves": 30}
    ],
    "straight_points": [
      {"point": "Round", "shaves": 50},
      {"point": "Barber's Notch", "shaves": 20}
    ],
    "soaps": [
      {"name": "Grooming Dept - Laundry II", "shaves": 40},
      {"name": "Declaration Grooming - Persephone", "shaves": 35}
    ],
    "soap_makers": [
      {"maker": "Grooming Dept", "shaves": 200},
      {"maker": "Declaration Grooming", "shaves": 180}
    ],
    "users": [
      {"name": "user1", "shaves": 25},
      {"name": "user2", "shaves": 20}
    ]
  }
}
```

## Field Mapping

### Core Product Fields
- **Razors**: `razor.matched.brand`, `razor.matched.model`, `razor.matched.format`
- **Blades**: `blade.matched.brand`, `blade.matched.model`, `blade.matched.format`
- **Brushes**: `brush.matched.brand`, `brush.matched.model`, `brush.matched.fiber`
- **Soaps**: `soap.matched.maker`, `soap.matched.scent`

### Specialized Fields
- **Blackbird Plates**: `razor.enriched.plate`
- **Christopher Bradley Plates**: `razor.enriched.plate_type`, `razor.enriched.plate_level`
- **Game Changer Plates**: `razor.enriched.gap`
- **Super Speed Tips**: `razor.enriched.super_speed_tip`
- **Straight Razor Specs**: `razor.enriched.width`, `razor.enriched.grind`, `razor.enriched.point`

### Brush Specialized Fields
- **Handle Makers**: `brush.matched.handle_maker`
- **Knot Makers**: `brush.matched.knot_maker`
- **Fibers**: `brush.matched.fiber` (fallback to `brush.enriched.fiber`)
- **Knot Sizes**: `brush.matched.knot_size_mm` (fallback to `brush.enriched.knot_size_mm`)

### User Fields
- **Users**: `author`

## Aggregation Logic

### Basic Aggregation
- Count occurrences of each unique value in the specified field
- Sort by count descending
- Include total count as "shaves" field

### Specialized Aggregation
- For composite fields (e.g., Christopher Bradley plates), combine multiple fields
- For numeric fields (e.g., knot sizes), group by value ranges if needed
- Handle null/missing values appropriately

### Data Quality
- Filter out records with missing required fields
- Normalize field values (case, whitespace, etc.)
- Handle edge cases (empty strings, null values)

## Required Field Names by Category

| Category | Primary Field | Required Fields |
|----------|---------------|-----------------|
| razor_formats | `format` | format, shaves, unique_users |
| razors | `name` | name, shaves, unique_users |
| razor_manufacturers | `brand` | brand, shaves, unique_users |
| blades | `name` | name, shaves, unique_users |
| blade_manufacturers | `brand` | brand, shaves, unique_users |
| brushes | `name` | name, shaves, unique_users |
| brush_handle_makers | `handle_maker` | handle_maker, shaves, unique_users |
| brush_knot_makers | `brand` | brand, shaves, unique_users |
| brush_fibers | `fiber` | fiber, shaves, unique_users |
| brush_knot_sizes | `knot_size_mm` | knot_size_mm, shaves, unique_users |
| blackbird_plates | `plate` | plate, uses, users |
| christopher_bradley_plates | `plate` | plate, uses, users |
| game_changer_plates | `plate` | plate, uses, users |
| super_speed_tips | `tip` | tip, uses, users |
| straight_razor_specs | `specs` | specs, uses, users |
| straight_widths | `width` | width, shaves, unique_users |
| straight_grinds | `grind` | grind, shaves, unique_users |
| straight_points | `point` | point, shaves, unique_users |
| soaps | `name` | name, shaves, unique_users |
| soap_makers | `maker` | maker, shaves, unique_users |
| brand_diversity | `maker` | maker, unique_scents, total_shaves |
| users | `username` | username, shaves, unique_users |

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