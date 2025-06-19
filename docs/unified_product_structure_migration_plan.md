# Unified Product Field Structure Migration Plan

## Overview

This plan outlines the migration from the current dual-location enrichment structure to a unified product field structure where all product-related data (original, matched, enriched, etc.) is nested under the product field itself.

**Key Decision**: Since all files can be regenerated easily, we will implement the new structure directly without backward compatibility, simplifying the migration.

## Current vs Target Structure

### Current Structure
```json
{
  "razor": {
    "original": "Koraat Moarteen",
    "matched": {
      "brand": "Koraat",
      "model": "Moarteen",
      "format": "Straight"
    }
  },
  "enriched": {
    "razor": {
      "grind": "Full Hollow",
      "width": "15/16",
      "_enriched_by": "StraightRazorEnricher"
    }
  }
}
```

### Target Structure
```json
{
  "razor": {
    "original": "Koraat Moarteen",
    "matched": {
      "brand": "Koraat",
      "model": "Moarteen",
      "format": "Straight"
    },
    "enriched": {
      "grind": "Full Hollow",
      "width": "15/16",
      "_enriched_by": "StraightRazorEnricher"
    }
  }
}
```

## Migration Strategy: Direct Implementation

### Phase 1: Enrich Phase Migration
**Goal**: Update enrich phase to write enriched data directly to product fields.

#### 1.1 Update Enricher Registry
**File**: `sotd/enrich/registry.py`

**Changes**:
- Modify `enrich_record()` to write enriched data directly to product fields
- Remove record-level `enriched` field creation

**Implementation**:
```python
def enrich_record(self, record: Dict[str, Any], original_comment: str) -> Dict[str, Any]:
    """Enrich a single record with all applicable enrichers."""
    enriched_record = record.copy()
    
    # Process each field that has enrichers
    for field, enrichers in self._enrichers_by_field.items():
        field_data = enriched_record.get(field)
        if not field_data:
            continue
            
        # Get extracted value for enrichment
        extracted_field_name = f"{field}_extracted"
        extracted_value = record.get(extracted_field_name, "")
        if not extracted_value and isinstance(field_data, dict):
            extracted_value = field_data.get("original", "")
            
        field_enriched_data = {}
        
        for enricher in enrichers:
            try:
                if enricher.applies_to(record):
                    enrichment_result = enricher.enrich(field_data, extracted_value)
                    if enrichment_result:
                        field_enriched_data.update(enrichment_result)
                        logger.debug(f"Applied {enricher.get_enricher_name()} to {field}")
            except Exception as e:
                logger.error(f"Error applying enricher {enricher.get_enricher_name()} to {field}: {e}")
                
        # Write enriched data directly to product field
        if field_enriched_data:
            if not isinstance(field_data, dict):
                field_data = {"original": field_data}
            field_data["enriched"] = field_enriched_data
            enriched_record[field] = field_data
    
    return enriched_record
```

#### 1.2 Update Aggregate Phase
**File**: `sotd/aggregate/base_aggregator.py`

**Changes**:
- Add helper method to extract enriched data from unified structure
- Update all aggregators to use new structure
- Remove old record-level enriched field access

**Implementation**:
```python
def _extract_enriched_data(self, record: Dict[str, Any], product_field: str) -> Optional[Dict[str, Any]]:
    """Extract enriched data from unified product structure."""
    product_data = record.get(product_field, {})
    if isinstance(product_data, dict) and "enriched" in product_data:
        return product_data["enriched"]
    return None
```

#### 1.3 Update Tests
**Files**: `tests/enrich/test_*.py`, `tests/aggregate/test_*.py`

**Changes**:
- Update test data to use new structure
- Update assertions to expect new field locations
- Remove tests for old structure

#### 1.4 Update Documentation
**Files**: `docs/enrich_phase_spec.md`, `docs/aggregate_phase_spec.md`

**Changes**:
- Update data structure examples
- Update CLI examples
- Document new unified structure

### Phase 2: Match Phase Migration
**Goal**: Ensure match phase output is compatible with unified structure.

#### 2.1 Verify Match Phase Output
**File**: `sotd/match/run.py`

**Changes**:
- Ensure matched data is written to `{product}.matched`
- Ensure original data is written to `{product}.original`
- Verify structure is compatible with enrich phase expectations

### Phase 3: Extract Phase Migration
**Goal**: Update extract phase to prepare for unified structure.

#### 3.1 Update Extract Phase Output
**File**: `sotd/extract/comment.py`

**Changes**:
- Write extracted data to `{product}.original`
- Prepare structure for match phase

## Implementation Timeline

### Week 1: Phase 1 Implementation
- [ ] Update enricher registry
- [ ] Update aggregate phase
- [ ] Update tests
- [ ] Test with sample data

### Week 2: Validation & Testing
- [ ] Run full pipeline with new structure
- [ ] Validate output correctness
- [ ] Performance testing
- [ ] Documentation updates

### Week 3: Phase 2 & 3
- [ ] Verify match phase compatibility
- [ ] Update extract phase
- [ ] Full pipeline testing
- [ ] Complete documentation update

## Implementation Steps

### Step 1: Update Enrich Phase
1. Update `sotd/enrich/registry.py` to write to product fields
2. Test with sample data
3. Update tests

### Step 2: Update Aggregate Phase
1. Add helper method to `sotd/aggregate/base_aggregator.py`
2. Update all aggregator implementations
3. Test aggregation with new structure

### Step 3: Regenerate Data
1. Run full pipeline to regenerate all files
2. Validate new structure
3. Update documentation

### Step 4: Clean Up
1. Remove any remaining old structure code
2. Update all documentation
3. Final testing

## Benefits of Direct Migration

1. **Simpler Implementation** - No backward compatibility code needed
2. **Cleaner Codebase** - Single structure throughout
3. **Faster Development** - No need to maintain dual code paths
4. **Better Performance** - No fallback logic overhead
5. **Easier Testing** - Single structure to test against

## Success Criteria

- [ ] Enrich phase writes to unified structure
- [ ] Aggregate phase reads from unified structure
- [ ] All tests pass
- [ ] Full pipeline runs successfully
- [ ] All documentation updated
- [ ] Performance maintained or improved
- [ ] Debugging significantly easier

## Next Steps

1. **Start with Phase 1** - Implement enrich phase migration
2. **Test thoroughly** - Validate with real data
3. **Regenerate files** - Run full pipeline
4. **Update documentation** - Complete all docs
5. **Validate improvements** - Confirm debugging is easier

## Questions for Discussion

1. Should we maintain backward compatibility indefinitely or set a deprecation timeline?
2. Do we want to migrate historical data files or leave them in old format?
3. Should we add a migration CLI tool for converting old files?
4. What performance impact is acceptable for the improved structure? 