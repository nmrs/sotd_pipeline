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
- **Brush Handle Makers**: Handle maker aggregation from `brush.matched.handle.brand`
- **Brush Knot Makers**: Knot maker aggregation from `brush.matched.knot.brand`
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

### Cross-Product Categories
- **Razor Blade Combinations**: Most used blades in most used razors
- **Highest Use Count per Blade**: Per-user blade usage tracking

## Position Field and Sorting Requirements

### Position Field
Each aggregation output list must include a `"position"` field for each item, indicating its 1-based rank within the list. This enables robust, explicit delta calculations in the report phase.

### Sort Orders
All aggregations must be sorted according to the following rules:

#### Default Sort Order (Most Aggregations)
- **Primary:** `shaves` (descending)
- **Secondary:** `unique_users` (descending, if present)

#### Special Sort Orders
- **Users**: `shaves` (descending), `missed_days` (descending)
- **Highest Use Count per Blade**: `uses` (descending)

### Complete Sort Order Reference

| Aggregation | Primary | Secondary |
|-------------|---------|-----------|
| razor_formats | shaves desc | unique_users desc |
| razors | shaves desc | unique_users desc |
| razor_manufacturers | shaves desc | unique_users desc |
| blades | shaves desc | unique_users desc |
| blade_manufacturers | shaves desc | unique_users desc |
| brushes | shaves desc | unique_users desc |
| brush_handle_makers | shaves desc | unique_users desc |
| brush_knot_makers | shaves desc | unique_users desc |
| brush_fibers | shaves desc | unique_users desc |
| brush_knot_sizes | shaves desc | unique_users desc |
| soaps | shaves desc | unique_users desc |
| soap_makers | shaves desc | unique_users desc |
| blackbird_plates | shaves desc | unique_users desc |
| christopher_bradley_plates | shaves desc | unique_users desc |
| game_changer_plates | shaves desc | unique_users desc |
| super_speed_tips | shaves desc | unique_users desc |
| straight_widths | shaves desc | unique_users desc |
| straight_grinds | shaves desc | unique_users desc |
| straight_points | shaves desc | unique_users desc |
| users | shaves desc | missed_days desc |
| razor_blade_combinations | shaves desc | unique_users desc |
| highest_use_count_per_blade | uses desc | - |

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
      "handle": {
        "brand": "Semogue",
        "model": "610",
        "source_text": "Semogue 610 21mm Boar",
        "_matched_by": "OmegaSemogueBrushMatchingStrategy",
        "_pattern": "\\bsemogue\\b.*\\b610\\b"
      },
      "knot": {
        "brand": "Semogue",
        "model": "610",
        "fiber": "Boar",
        "knot_size_mm": 21,
        "source_text": "Semogue 610 21mm Boar",
        "_matched_by": "OmegaSemogueBrushMatchingStrategy",
        "_pattern": "\\bsemogue\\b.*\\b610\\b"
      }
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
      {"position": 1, "format": "DE", "shaves": 1200, "unique_users": 100},
      {"position": 2, "format": "Straight", "shaves": 150, "unique_users": 20}
    ],
    "razors": [
      {"position": 1, "name": "Fatip Grande", "shaves": 50, "unique_users": 15},
      {"position": 2, "name": "Gillette Tech", "shaves": 45, "unique_users": 12}
    ],
    "razor_manufacturers": [
      {"position": 1, "brand": "Gillette", "shaves": 300, "unique_users": 50},
      {"position": 2, "brand": "Fatip", "shaves": 100, "unique_users": 25}
    ],
    "blades": [
      {"position": 1, "name": "Gillette Minora", "shaves": 80, "unique_users": 30},
      {"position": 2, "name": "Personna Lab Blue", "shaves": 60, "unique_users": 25}
    ],
    "blade_manufacturers": [
      {"position": 1, "brand": "Gillette", "shaves": 400, "unique_users": 40},
      {"position": 2, "brand": "Personna", "shaves": 200, "unique_users": 30}
    ],
    "brushes": [
      {"position": 1, "name": "Semogue 610", "shaves": 30, "unique_users": 10},
      {"position": 2, "name": "AP Shave Co MiG", "shaves": 25, "unique_users": 8}
    ],
    "brush_handle_makers": [
      {"position": 1, "brand": "Semogue", "shaves": 150, "unique_users": 30},
      {"position": 2, "brand": "AP Shave Co", "shaves": 100, "unique_users": 20}
    ],
    "brush_knot_makers": [
      {"position": 1, "brand": "Declaration Grooming", "shaves": 80, "unique_users": 15},
      {"position": 2, "brand": "Semogue", "shaves": 150, "unique_users": 30}
    ],
    "brush_fibers": [
      {"position": 1, "fiber": "Synthetic", "shaves": 400, "unique_users": 60},
      {"position": 2, "fiber": "Boar", "shaves": 300, "unique_users": 45}
    ],
    "brush_knot_sizes": [
      {"position": 1, "knot_size_mm": 24, "shaves": 200, "unique_users": 35},
      {"position": 2, "knot_size_mm": 26, "shaves": 180, "unique_users": 30}
    ],
    "blackbird_plates": [
      {"position": 1, "plate": "Ti", "shaves": 40, "unique_users": 8},
      {"position": 2, "plate": "Lite", "shaves": 25, "unique_users": 5}
    ],
    "christopher_bradley_plates": [
      {"position": 1, "plate_type": "SB", "plate_level": "C", "shaves": 30, "unique_users": 6},
      {"position": 2, "plate_type": "SB", "plate_level": "D", "shaves": 20, "unique_users": 4}
    ],
    "game_changer_plates": [
      {"position": 1, "gap": "1.05", "shaves": 35, "unique_users": 7},
      {"position": 2, "gap": ".84", "shaves": 25, "unique_users": 5}
    ],
    "super_speed_tips": [
      {"position": 1, "super_speed_tip": "Flare", "shaves": 45, "unique_users": 12},
      {"position": 2, "super_speed_tip": "Black", "shaves": 30, "unique_users": 8}
    ],
    "straight_widths": [
      {"position": 1, "width": "6/8", "shaves": 80, "unique_users": 15},
      {"position": 2, "width": "5/8", "shaves": 40, "unique_users": 8}
    ],
    "straight_grinds": [
      {"position": 1, "grind": "Full Hollow", "shaves": 60, "unique_users": 12},
      {"position": 2, "grind": "Hollow", "shaves": 30, "unique_users": 6}
    ],
    "straight_points": [
      {"position": 1, "point": "Round", "shaves": 50, "unique_users": 10},
      {"position": 2, "point": "Barber's Notch", "shaves": 20, "unique_users": 4}
    ],
    "soaps": [
      {"position": 1, "name": "Grooming Dept - Laundry II", "shaves": 40, "unique_users": 12},
      {"position": 2, "name": "Declaration Grooming - Persephone", "shaves": 35, "unique_users": 10}
    ],
    "soap_makers": [
      {"position": 1, "maker": "Grooming Dept", "shaves": 200, "unique_users": 30},
      {"position": 2, "maker": "Declaration Grooming", "shaves": 180, "unique_users": 25}
    ],
    "users": [
      {"position": 1, "user": "user1", "shaves": 31, "missed_days": 0, "missed_dates": []},
      {"position": 2, "user": "user2", "shaves": 31, "missed_days": 2, "missed_dates": []}
    ],
    "razor_blade_combinations": [
      {"position": 1, "name": "Fatip Grande + Gillette Minora", "shaves": 25, "unique_users": 8},
      {"position": 2, "name": "Gillette Tech + Personna Lab Blue", "shaves": 20, "unique_users": 6}
    ],
    "highest_use_count_per_blade": [
      {"position": 1, "user": "user1", "blade": "Gillette Minora", "format": "DE", "uses": 15},
      {"position": 2, "user": "user2", "blade": "Personna Lab Blue", "format": "DE", "uses": 12}
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

### Cross-Product Fields
- **Razor Blade Combinations**: `razor.matched.brand` + `razor.matched.model` + `blade.matched.brand` + `blade.matched.model`
- **Highest Use Count per Blade**: `author` + `blade.matched.brand` + `blade.matched.model` + `blade.enriched.use_count`

## Aggregation Logic

### Basic Aggregation
- Count occurrences of each unique value in the specified field
- Sort by the defined sort order for the aggregation
- Include position field (1-based rank) for delta calculations
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

### Core Product Aggregations
- **Razors**: `{"position": N, "name": "Brand Model", "shaves": N, "unique_users": N}`
- **Blades**: `{"position": N, "name": "Brand Model", "shaves": N, "unique_users": N}`
- **Brushes**: `{"position": N, "name": "Brand Model", "shaves": N, "unique_users": N}`
- **Soaps**: `{"position": N, "name": "Maker - Scent", "shaves": N, "unique_users": N}`

### Manufacturer Aggregations
- **Razor Manufacturers**: `{"position": N, "brand": "Brand", "shaves": N, "unique_users": N}`
- **Blade Manufacturers**: `{"position": N, "brand": "Brand", "shaves": N, "unique_users": N}`
- **Soap Makers**: `{"position": N, "maker": "Maker", "shaves": N, "unique_users": N}`

### Format Aggregations
- **Razor Formats**: `{"position": N, "format": "Format", "shaves": N, "unique_users": N}`

### Brush Component Aggregations
- **Handle Makers**: `{"position": N, "handle_maker": "Maker", "shaves": N, "unique_users": N}`
- **Knot Makers**: `{"position": N, "brand": "Brand", "shaves": N, "unique_users": N}`
- **Fibers**: `{"position": N, "fiber": "Fiber", "shaves": N, "unique_users": N}`
- **Knot Sizes**: `{"position": N, "knot_size_mm": N, "shaves": N, "unique_users": N}`

### Specialized Razor Aggregations
- **Blackbird Plates**: `{"position": N, "plate": "Plate", "shaves": N, "unique_users": N}`
- **Christopher Bradley Plates**: `{"position": N, "plate_type": "Type", "plate_level": "Level", "shaves": N, "unique_users": N}`
- **Game Changer Plates**: `{"position": N, "gap": "Gap", "shaves": N, "unique_users": N}`
- **Super Speed Tips**: `{"position": N, "super_speed_tip": "Tip", "shaves": N, "unique_users": N}`
- **Straight Widths**: `{"position": N, "width": "Width", "shaves": N, "unique_users": N}`
- **Straight Grinds**: `{"position": N, "grind": "Grind", "shaves": N, "unique_users": N}`
- **Straight Points**: `{"position": N, "point": "Point", "shaves": N, "unique_users": N}`

### User Aggregations
- **Users**: `{"position": N, "user": "Username", "shaves": N, "missed_days": N, "missed_dates": [YYYY-MM-DD, ...]}`
  - **missed_days**: The count of days in the month where the user did not post a shave (regardless of late/early posting).
  - **missed_dates**: List of those missed days in YYYY-MM-DD format.
  - **Sorting**: By shaves (descending), then missed_days (ascending).

### Cross-Product Aggregations
- **Razor Blade Combinations**: `{"position": N, "name": "Razor + Blade", "shaves": N, "unique_users": N}`
- **Highest Use Count per Blade**: `{"position": N, "user": "Username", "blade": "Blade Name", "format": "Format", "uses": N}`

## CLI Interface

Follows the same pattern as other pipeline phases:

```bash
python -m sotd.aggregate run --month 2025-01
python -m sotd.aggregate run --year 2025
python -m sotd.aggregate run --range 2025-01:2025-05
```

### Options
- `--month`: Single month (YYYY-MM format)
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
- Validate position field is present and sequential

### Data Quality Checks
- Verify shaves >= unique_users
- Check for reasonable avg_shaves_per_user values
- Validate category names are consistent
- Ensure position fields are 1-based and sequential

# Note: The output keys for brush fiber and knot size aggregations are 'brush_fibers' and 'brush_knot_sizes'.
# These are grouped by fiber type and knot size (mm) respectively, matching the code and output structure.

## Brush Aggregation Data Model Clarification (2024-06)

- For brush knot maker aggregation, use `brush.matched.brand` (not `knot_maker`).
- For brush handle maker aggregation, use `brush.matched.handle_maker`.
- The `knot_maker` field is a legacy/unused field and is always null in current data; it should not be used for aggregation.
- The aggregator code and documentation should be updated to reflect this reality.
- This matches the current data model and enrich phase output.