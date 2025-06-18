# Enrich Phase Specification

## Overview

The enrich phase analyzes matched product data to extract additional structured metadata that benefits from knowing the identified product first. It operates on `data/matched/YYYY-MM.json` and outputs to `data/enriched/YYYY-MM.json`.

**Key Principle**: Enrichment requires knowledge of the matched product to perform sophisticated analysis, distinguishing it from the matching phase which focuses on product identification.

## Architecture

### Directory Structure
```
sotd/enrich/
├── __init__.py
├── run.py                         # CLI entry point & orchestration
├── save.py                        # File I/O operations
├── enrich.py                      # Main enrichment controller
├── base_enricher.py               # Base enricher interface
├── blade_count_enricher.py        # Extract blade use count (moved from match)
├── straight_razor_enricher.py     # Extract grind, width, point type
├── game_changer_enricher.py       # Extract Game Changer plate information
└── christopher_bradley_enricher.py # Extract Christopher Bradley plate information
```

### Base Enricher Interface

All enrichers implement this interface for consistency:

```python
class BaseEnricher:
    """Base class for all product enrichers."""
    
    target_field: str  # "blade", "razor", "brush", "soap"
    
    def applies_to(self, record: dict) -> bool:
        """Return True if this enricher should process this record."""
        raise NotImplementedError
    
    def enrich(self, field_data: dict) -> dict:
        """Enrich field data, return updated version with enriched section."""
        raise NotImplementedError
```

### Main Controller Pattern

The main enrichment controller follows a simple, extensible pattern:

```python
def enrich_record(record: dict) -> dict:
    """Enrich a single shave record with metadata from applicable enrichers."""
    enrichers = [
        blade_count_enricher,
        straight_razor_enricher, 
        game_changer_enricher,
        christopher_bradley_enricher
    ]
    
    result = record.copy()
    for enricher in enrichers:
        if enricher.applies_to(result):
            target_field = enricher.target_field
            try:
                result[target_field] = enricher.enrich(result[target_field])
            except Exception as e:
                logger.error(f"Enricher {enricher.__class__.__name__} failed: {e}")
                # Continue with other enrichers
    
    return result
```

## Data Structure

### Input Format (from Match Phase)
```python
{
    "blade": {
        "original": "Feather (3)",
        "matched": {
            "brand": "Feather",
            "model": "Hi-Stainless", 
            "format": "DE"
        },
        "match_type": "exact",
        "pattern": "feather.*hi"
    }
}
```

### Output Format (with Enrichment)
```python
{
    "blade": {
        "original": "Feather (3)",
        "matched": {
            "brand": "Feather",
            "model": "Hi-Stainless", 
            "format": "DE"
        },
        "match_type": "exact",
        "pattern": "feather.*hi",
        "enriched": {
            "use_count": 3,
            "_enriched_by": "BladeCountEnricher",
            "_extraction_source": "parenthetical_pattern"
        }
    }
}
```

### Enriched Section Standards

All enrichers must include:
- **Extracted data**: The actual metadata fields
- **`_enriched_by`**: Class name of the enricher that processed this data
- **`_extraction_source`**: Method/pattern used for extraction

## Individual Enrichers

### 1. Blade Count Enricher

**Purpose**: Extract blade use count from user input (moved from match phase)

**Applies To**: Any record with a matched blade

**Extraction Patterns**:
- Parenthetical: `"Feather (3)"` → `use_count: 3`
- Bracketed: `"Astra SP [2]"` → `use_count: 2`  
- Prefixed: `"3x Gillette Silver Blue"` → `use_count: 3`

**Example Output**:
```python
"enriched": {
    "use_count": 3,
    "_enriched_by": "BladeCountEnricher",
    "_extraction_source": "parenthetical_pattern"
}
```

### 2. Straight Razor Enricher

**Purpose**: Extract straight razor specifications when product is identified as a straight razor

**Applies To**: Records where `razor.matched.type == "straight"` or specific straight razor brands

**Extraction Patterns**:
- **Grind**: `"full hollow"`, `"wedge"`, `"half hollow"`
- **Width**: `"6/8"`, `"7/8"` (converted to eighths)
- **Point**: `"round"`, `"square"`, `"barber's notch"`

**Example Output**:
```python
"enriched": {
    "grind": "full hollow",
    "width_eighths": 6,
    "point": "round", 
    "_enriched_by": "StraightRazorEnricher",
    "_extraction_source": "combined_patterns"
}
```

### 3. Game Changer Enricher

**Purpose**: Extract plate information for RazoRock Game Changer razors

**Applies To**: Records where `razor.matched.brand == "RazoRock"` and `"Game Changer"` in model

**Extraction Patterns**:
- Gap specifications: `".68"`, `".84"`, `"1.05"`
- Open comb variants: `"OC"`, `"open comb"`

**Example Output**:
```python
"enriched": {
    "plate_gap": 0.84,
    "variant": "closed_comb",
    "_enriched_by": "GameChangerEnricher", 
    "_extraction_source": "gap_pattern"
}
```

### 4. Christopher Bradley Enricher

**Purpose**: Extract plate information for Karve Christopher Bradley razors

**Applies To**: Records where `razor.matched.brand == "Karve"` and `"Christopher Bradley"` in model

**Extraction Patterns**:
- Plate designations: `"A"`, `"B"`, `"C"`, `"D"`, `"E"`, `"F"`
- Material variants: `"brass"`, `"copper"`, `"stainless"`

**Example Output**:
```python
"enriched": {
    "plate": "C",
    "material": "brass",
    "_enriched_by": "ChristopherBradleyEnricher",
    "_extraction_source": "plate_letter_pattern"
}
```

## Error Handling Strategy

### Partial Extraction Success
Include successfully extracted fields, use `null` for missing data:

```python
"enriched": {
    "grind": "full hollow",    # Successfully extracted
    "width_eighths": null,     # Not found in text
    "point": "round",          # Successfully extracted
    "_enriched_by": "StraightRazorEnricher",
    "_extraction_source": "partial_pattern_match"
}
```

### Enricher Failures
- Log errors with context but continue processing other enrichers
- Never crash the entire enrichment process due to one enricher failure
- Include error information in processing metadata

### Ambiguous Data
For unclear extractions, prefer partial data over no data:

```python
"enriched": {
    "plate_gap": null,
    "variant": "open_comb",    # Clear from "OC" mention
    "_enriched_by": "GameChangerEnricher",
    "_extraction_source": "variant_only_pattern"
}
```

## File I/O Pattern

### CLI Interface
Following existing phase conventions:
```bash
python -m sotd.enrich.run --month 2025-05 [--debug] [--force]
python -m sotd.enrich.run --range 2024-12:2025-05 [--debug] [--force]
```

### Input/Output Files
- **Input**: `data/matched/YYYY-MM.json`
- **Output**: `data/enriched/YYYY-MM.json`

### Output File Structure
```json
{
    "meta": {
        "month": "2025-05",
        "processed_at": "2025-05-21T18:40:00Z",
        "records_input": 1247,
        "records_enriched": 1198,
        "enrichers_applied": {
            "BladeCountEnricher": 891,
            "StraightRazorEnricher": 23,
            "GameChangerEnricher": 45,
            "ChristopherBradleyEnricher": 31
        },
        "processing_errors": []
    },
    "data": [
        // ... enriched shave records
    ]
}
```

## Extensibility Guidelines

### Adding New Enrichers

1. **Create enricher class** implementing `BaseEnricher`
2. **Set target field** (`"blade"`, `"razor"`, `"brush"`, `"soap"`)
3. **Implement `applies_to()`** with specific product detection logic
4. **Implement `enrich()`** with extraction patterns
5. **Add to enricher list** in main controller
6. **Add comprehensive tests** following existing patterns

### Design Principles

- **One enricher per feature**: Decide case-by-case whether to combine related extractions
- **Self-contained logic**: Each enricher determines its own applicability
- **Consistent metadata**: Always include `_enriched_by` and `_extraction_source`
- **Graceful failures**: Handle errors without crashing the pipeline
- **Partial extraction**: Prefer partial data over no data

### Future Extension Examples

**Potential future enrichers**:
- **Adjustable Razor Enricher**: Extract settings for Progress, Slim, etc.
- **Soap Scent Enricher**: Extract scent families, seasonal themes
- **Vintage Dating Enricher**: Extract manufacturing dates for vintage products
- **Brush Condition Enricher**: Extract break-in status, wear indicators

**Adding combined enrichers**:
```python
# If multiple razor plates have similar logic
class DEPlateEnricher(BaseEnricher):
    def __init__(self):
        self.sub_enrichers = [
            game_changer_enricher,
            christopher_bradley_enricher,
            rockwell_enricher  # Future addition
        ]
    
    def applies_to(self, record: dict) -> bool:
        return any(enricher.applies_to(record) for enricher in self.sub_enrichers)
```

## Integration with Pipeline

### Phase Dependencies
- **Requires**: Completed match phase output in `data/matched/`
- **Provides**: Enriched metadata for aggregation phase
- **Independent**: Can be re-run without affecting other phases

### Makefile Integration
```makefile
enrich:
	python -m sotd.enrich.run --month $(MONTH) --debug

enrich-range:
	python -m sotd.enrich.run --range $(START):$(END) --debug
```

### Development Workflow
1. **Test individual enrichers** with unit tests
2. **Validate on small datasets** before processing full months
3. **Monitor enrichment success rates** in processing metadata
4. **Add patterns iteratively** based on unmatched data analysis

## Testing Strategy

### Unit Tests
- **Each enricher** should have comprehensive test coverage
- **Edge cases**: Test malformed input, ambiguous data, extraction failures
- **Pattern validation**: Verify regex patterns work correctly
- **Metadata consistency**: Ensure all enrichers follow metadata standards

### Integration Tests
- **Full pipeline**: Test complete enrichment process
- **Cross-enricher**: Verify enrichers don't interfere with each other
- **Performance**: Ensure enrichment doesn't significantly slow processing

### Validation Tools
- **Enrichment coverage reports**: Track what percentage of products get enriched
- **Extraction accuracy**: Manual validation of extracted metadata
- **Error analysis**: Monitor and improve error handling patterns 