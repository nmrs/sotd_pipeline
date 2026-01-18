# Product Matching Validation

## Canonical Normalization Function

All correct match lookups in the SOTD Pipeline must use the canonical normalization function:

```python
from sotd.utils.extract_normalization import normalize_for_matching
```

This function is the **single source of truth** for normalizing strings for correct match lookups in matchers, analyzers, and any other consumers. All components must use this function to ensure consistent normalization.

### Field-Specific Normalization
- **Blades**: Strips blade count/usage patterns (including 'new' as usage)
- **Razors**: Strips handle swap/modification indicators
- **Soaps**: Strips soap-related patterns (sample, puck, croap, cream, etc.)
- **All fields**: Strips competition tags and normalizes whitespace
- **Case is preserved** to maintain consistency with stored `correct_matches.yaml` entries

#### Example Usage
```python
normalized = normalize_for_matching("treet platinum (3x) #sotd", field="blade")
# normalized == "treet platinum #sotd"

normalized = normalize_for_matching("Razor / [brand] handle $CNC", field="razor")
# normalized == "Razor"

normalized = normalize_for_matching("B&M Seville soap sample", field="soap")
# normalized == "B&M Seville"
```

## Deprecation Notice: `normalize_for_storage`

The old `normalize_for_storage` function is **deprecated** and should not be used. All code and tests must use `normalize_for_matching` instead. The deprecated function is retained only for backward compatibility and will be removed in a future release.

## Test Coverage
- All entries in `correct_matches.yaml` are now guaranteed to be found as exact matches by the matchers.
- There are zero "confirmed but not exact" mismatches in the test suite.

## Lessons Learned
- Consistent, field-aware normalization is critical for robust product matching.
- All normalization logic must be unified in a single function to avoid subtle bugs and mismatches.

## Blade Format-Aware Duplicate Validation

### Rules for Blade Duplicates
- The same blade string (e.g., "Accuforge") **may appear under multiple brand/model combinations** in `correct_matches.yaml` **if and only if** those combinations represent different blade formats (e.g., DE, GEM, AC).
- **Duplicate blade strings under the SAME format** (e.g., both under DE) are **FORBIDDEN** and will be flagged as errors by the validator.
- The same model name **can legitimately appear across different product types** (e.g., "Muhle Neo" can be both a razor and a brush). This is not considered a duplicate since they represent different products.
- The validator uses the format from `blades.yaml` to determine if a duplicate is legitimate.

### Rationale
This rule allows for legitimate cases where the same blade string is used for different physical blade formats (e.g., "Accuforge" for both GEM and DE Personna blades). It prevents ambiguity within a single format, ensuring that each string maps to only one canonical product per format.

### Examples

#### Legitimate (Allowed)
```yaml
blade:
  Personna:
    GEM PTFE:
      - "Accuforge"   # GEM format
    Lab Blue:
      - "Accuforge"   # DE format
# This is allowed because GEM PTFE and Lab Blue are different formats.
```

#### Forbidden (Will Fail Validation)
```yaml
blade:
  Personna:
    Lab Blue:
      - "Accuforge"   # DE format
    Med Prep:
      - "Accuforge"   # DE format
# This is NOT allowed because both are DE format.
```

### See Also
- [Blade Format-Aware Validation Plan](../plans/features/blade_format_aware_validation_plan_2025-07-09.mdc)
- Schema and examples at the top of `data/correct_matches.yaml`
