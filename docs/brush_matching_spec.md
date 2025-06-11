
# Brush Matching Phase Specification

## Goal

Match and normalize shaving brush metadata from the `brush` field extracted during the extraction phase.

## Input

A single `brush` string provided by the extraction phase. This string may be partial or ambiguous, but has already been cleaned and narrowed to one brush mention.

## Matching Fields (in priority order)

1. `brand`
2. `model`
3. `fiber` (e.g., boar, badger, synthetic)
4. `knot_size` (e.g., 26mm)
5. `handle_maker`
6. `knot_maker`

## Matching Rules

- Matching is **regex-based** using YAML pattern files.
- Matching stops at the **first successful match** from the prioritized YAML files.
- Each match must contain:
  - `source_text`: original matched string
  - `source_type`: one of `exact`, `alias`, `brand`, `fiber`, `knot`, `artisan`, `unmatched`

## Output Schema

```yaml
brand: string | null
model: string | null
fiber: string | null
knot_size_mm: float | null
handle_maker: string | null
knot_maker: string | null
source_text: string  # always required
source_type: string  # exact | alias | brand | fiber | knot | artisan | unmatched
```

## Matching Strategy

2. **Matching Order**

Matching proceeds through the following ordered matchers:

   1. Declaration Grooming Brush Matcher *(algorithm)*
   2. Chisel and Hound Brush Matcher *(algorithm)*
   3. Known Brush Matcher *(YAML)*
   4. Omega and Semogue Brush Matcher *(algorithm)*
   5. Zenith Brush Matcher *(algorithm)*
   6. Other Brush Matcher *(YAML)*

## Special Handling

- If no full match occurs, and a partial match can still infer something useful (e.g., fiber or artisan), output a stub record with `"source_type": "unmatched"`.
- Example stub:
  ```yaml
  brand: null
  model: null
  fiber: "boar"
  knot_size: null
  handle_maker: null
  knot_maker: null
  source_text: "custom boar"
  source_type: "unmatched"
  ```
- **TODO**: In a future iteration, implement partial match extraction (e.g., returning only the matched substring from the regex rather than the entire input). This may help isolate handle makers or knot details more accurately, especially when multiple elements are embedded in a single brush string. For now, we only support exact or full-pattern matches.

## Assumptions

- Only one brush will be matched per comment.
- Matching input is restricted to the structured `brush` field from extraction.
- Regex normalization (case-insensitive, whitespace-tolerant) is handled within patterns.

## Notes

- Pattern authors should ensure relevant metadata is embedded in the YAML entry.
- YAML entries should be self-contained and avoid reliance on merging from other tiers.

### Field Resolution Priority

Brush metadata fields are resolved according to the following strict hierarchy:

| Priority | Source                  | Applies to         | Rule                                                      |
|----------|-------------------------|---------------------|-----------------------------------------------------------|
| 1        | Exact field in YAML     | `fiber`, `knot_size_mm` | Always use — authoritative manufacturer data            |
| 2        | Parsed from user input  | `fiber`, `knot_size_mm` | Use if no exact YAML field is present                   |
| 3        | Default field in YAML   | `default fiber`, `default_knot_size_mm` | Use only if nothing else is found        |
| 4        | Fallback                | —                   | Leave unset                                               |

- Each field is evaluated independently.
- A field-specific conflict (e.g., user specifies synthetic, YAML says boar) is resolved in favor of the YAML field and is flagged with a conflict tag (e.g., `fiber_conflict: "user_input: synthetic"`).

### Test Coverage

The following tests should validate the field resolution priority logic:

- **YAML exact fields override all**:
  - Input with user-specified fiber: `"Synthetic"`
  - YAML entry specifies `fiber: "Badger"`
  - Expect output to be `"fiber": "Badger"` with `fiber_conflict: "user_input: Synthetic"`

- **Parsed values used if YAML field missing**:
  - Input: `"Generic 26mm Synthetic"`
  - No YAML match
  - Expect `fiber: "Synthetic"`, `knot_size_mm: 26.0`, `source_type: "unmatched"`

- **YAML default values apply only as fallback**:
  - YAML entry with `default_knot_size_mm: 24.0`
  - Input string lacks any knot size
  - Expect `knot_size_mm: 24.0`

- **Unset if no match or default**:
  - Input: `"Unknown Brush"`
  - No YAML match, no parseable fiber/knot
  - Expect fields like `fiber`, `knot_size_mm` to be null

> These tests should be included in `test_field_resolution.py` or equivalent to ensure brush field resolution logic behaves predictably across matchers and engines.
