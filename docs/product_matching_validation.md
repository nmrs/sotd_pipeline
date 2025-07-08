# Product Matching Validation

## Canonical Normalization Function

All correct match lookups in the SOTD Pipeline must use the canonical normalization function:

```python
from sotd.utils.match_filter_utils import normalize_for_matching
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
