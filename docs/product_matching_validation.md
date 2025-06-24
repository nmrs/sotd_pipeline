# Product Matching Validation Guide

This guide shows how to use the enhanced analysis tool to validate and improve product matching performance in the SOTD pipeline. The tool works with all product types: brushes, razors, blades, and soaps.

## Matching Priority and match_type Semantics

- **Priority Order:**
    1. **Correct Matches File**: If the original value is found in `data/correct_matches.yaml`, it is matched directly, and `match_type` is set to `exact`.
    2. **Regex Patterns**: If not found in the correct matches file, regex patterns from the YAML catalogs are used. These matches have `match_type` set to `regex`.
    3. **Fallbacks**: Brand/alias/other fallback strategies as before.
- **All catalog specifications are preserved for both correct and regex matches.**

## Confirming Matches
- Use the mismatch analyzer tool to mark matches as correct, which will add them to `data/correct_matches.yaml` for future runs.
- Confirmed matches will always be prioritized and marked as `match_type: exact`.

## Quick Reference Commands

### 1. Basic Health Check
```bash
python -m sotd.match.tools.analyze_matched_enhanced --month 2025-05 --field brush
```
**Purpose**: Get overall matching statistics and confidence score  
**Shows**: Total matches, exact vs brand_default ratio, potential mismatches, average confidence  
**Note**: Replace `--field brush` with `--field razor`, `--field blade`, or `--field soap` as needed

### 2. Find What to Fix First
```bash
python -m sotd.match.tools.analyze_matched_enhanced --month 2025-05 --field brush --show-opportunities
```
**Purpose**: Identify highest-impact improvements  
**Shows**: Specific patterns to add to product YAML files, prioritized by frequency

### 3. Analyze Potential Mismatches
```bash
python -m sotd.match.tools.analyze_matched_enhanced --month 2025-05 --field brush --show-mismatches
```
**Purpose**: Focus on matches with low confidence scores  
**Shows**: Matches that might be incorrect, with reasons why confidence is low

### 4. Examine Specific Problem Cases
```bash
python -m sotd.match.tools.analyze_matched_enhanced --month 2025-05 --field brush --show-examples "Chisel & Hound Badger"
```
**Purpose**: Deep dive into specific problematic patterns  
**Shows**: Actual user input vs matched result for manual review  
**Note**: Use exact pattern name from opportunities or mismatches output

### 5. Check Pattern Performance
```bash
python -m sotd.match.tools.analyze_matched_enhanced --month 2025-05 --field brush --show-patterns
```
**Purpose**: Analyze regex pattern effectiveness  
**Shows**: Which patterns have 100% exact match rates vs poor performance

### 6. Quality Deep Dive
```bash
python -m sotd.match.tools.analyze_matched_enhanced --month 2025-05 --field brush --show-details
```
**Purpose**: Understand match confidence distribution  
**Shows**: Breakdown of high/medium/low confidence matches

### 7. Complete Analysis
```bash
python -m sotd.match.tools.analyze_matched_enhanced --month 2025-05 --field brush --show-details --show-patterns --show-opportunities --show-mismatches
```
**Purpose**: Full comprehensive analysis  
**Shows**: All insights in one command

## Field-Specific Analysis

### Analyze Different Product Types
```bash
# Brushes (default)
python -m sotd.match.tools.analyze_matched_enhanced --month 2025-05 --field brush

# Razors
python -m sotd.match.tools.analyze_matched_enhanced --month 2025-05 --field razor

# Blades
python -m sotd.match.tools.analyze_matched_enhanced --month 2025-05 --field blade

# Soaps
python -m sotd.match.tools.analyze_matched_enhanced --month 2025-05 --field soap
```

### Time Period Options
```bash
# Single month
--month 2025-05

# Full year
--year 2025

# Date range
--range 2024-12:2025-05
```

## Understanding the Output

### Summary Panel
```
╭─────────────────── Product Matching Summary ───────────────────╮
│ Total Matches: 1598                                             │
│ Match Type Distribution:                                         │
│   • exact: 627 (39.2%)                                          │
│   • brand_default: 971 (60.8%)                                  │
│ Potential Mismatches: 971 (60.8%)                               │
│ Average Confidence: 58.5/100                                    │
╰──────────────────────────────────────────────────────────────────╯
```

**Key Metrics**:
- **Total Matches**: How many products were successfully matched
- **Exact Match %**: Products matched with specific patterns (target: >80%)
- **Brand Default %**: Products falling back to generic brand matching (minimize this)
- **Potential Mismatches**: Matches with confidence < 70% that may be incorrect
- **Average Confidence**: Overall match confidence (0-100, target: >70)

### Improvement Opportunities Table
```
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Issue                                          ┃ Count ┃ Suggestion                                     ┃
┡━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ Maggard Synthetic appears 65 times as          │    65 │ Consider adding specific pattern for 'Maggard  │
│ brand_default                                  │       │ Synthetic'                                     │
└────────────────────────────────────────────────┴───────┴────────────────────────────────────────────────┘
```

**How to Use**:
1. **Count**: Higher numbers = higher impact improvements
2. **Issue**: Shows which brand+model combinations need patterns
3. **Suggestion**: Specific action to take

### Pattern Effectiveness Table
```
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━┳━━━━━━━━━━━━━━━┳━━━━━━━━━━━━┳━━━━━━━━━━━━━━━┓
┃ Pattern                                       ┃ Total Uses ┃ Exact Matches ┃ Exact Rate ┃ Effectiveness ┃
┡━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━╇━━━━━━━━━━━━━━━╇━━━━━━━━━━━━╇━━━━━━━━━━━━━━━┩
│ \ba[\s.]*p\b.*g5c                             │         88 │            88 │     100.0% │ high          │
│ synbad                                        │         50 │            50 │     100.0% │ high          │
└───────────────────────────────────────────────┴────────────┴───────────────┴────────────┴───────────────┘
```

**Effectiveness Levels**:
- **High** (green): 80%+ exact match rate - excellent patterns
- **Medium** (yellow): 50-79% exact match rate - needs review
- **Low** (red): <50% exact match rate - fix or remove

### Potential Mismatches Table
```
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Pattern                                        ┃ Count ┃ Average Confidence                             ┃
┡━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ Chisel & Hound Badger                          │    21 │ 0.0/100 (competing_brands_found,              │
│                                                │       │ possible_knot_maker_confusion)                 │
└────────────────────────────────────────────────┴───────┴────────────────────────────────────────────────┘
```

### Confidence Analysis
```
╭─────────────────── Confidence Analysis ───────────────────╮
│ Confidence Distribution:                                   │
│   • High Confidence (70-100): 627 (39.2%)                 │
│   • Medium Confidence (40-69): 585 (36.6%)                │
│   • Low Confidence (0-39): 386 (24.2%)                    │
╰─────────────────────────────────────────────────────────────╯
```

**Confidence Scoring Factors**:
- **Base Score**: Exact match (95%), brand_default (60%)
- **Penalties**: Competing brands (-20), knot maker confusion (-15), generic model (-10)
- **Issues Detected**: competing_brands_found, possible_knot_maker_confusion, generic_model_fallback

## Workflow for Improving Matches

### 1. Assess Current State
```bash
python -m sotd.match.tools.analyze_matched_enhanced --month 2025-05 --field brush --show-opportunities --show-mismatches
```

### 2. Identify Top Priorities
Look for high-count issues in both tables:
- **Opportunities**: Missing patterns (e.g., Maggard Synthetic - 65 occurrences)
- **Mismatches**: Low confidence matches (e.g., Chisel & Hound Badger - 21 cases with 0% confidence)

### 3. Examine Specific Problem Cases
```bash
python -m sotd.match.tools.analyze_matched_enhanced --month 2025-05 --field brush --show-examples "Chisel & Hound Badger"
```
This shows actual user input vs matched results to understand why confidence is low.

### 4. Add Patterns to Product YAML Files
For each high-priority issue, add specific patterns to the appropriate YAML file:

**Product YAML Files:**
- **Brushes**: `data/brushes.yaml`
- **Razors**: `data/razors.yaml` 
- **Blades**: `data/blades.yaml`
- **Soaps**: `data/soaps.yaml`

```yaml
# Example: Adding Maggard Tuxedo pattern to brushes.yaml
Maggard:
  Tuxedo:
    fiber: Synthetic
    patterns:
    - maggard.*tuxedo
    - tuxedo.*maggard

# Example: Adding Gillette pattern to razors.yaml  
Gillette:
  Tech:
    patterns:
    - gillette.*tech
    - tech.*gillette
```

### 5. Test Changes
```bash
# Re-run matching
python -m sotd.match.run --range 2025-05:2025-05 --force

# Check improvements
python -m sotd.match.tools.analyze_matched_enhanced --month 2025-05 --field brush --show-opportunities --show-mismatches
```

### 6. Monitor Progress
Track these metrics over time:
- **Exact match percentage** (target: >80%)
- **Average confidence score** (target: >70)
- **Potential mismatches** (minimize)
- **Number of brand_default fallbacks** (minimize)

## Performance Benchmarks

### Current Performance (May 2025)
- **Brushes**: 39.2% exact matches, 58.5/100 confidence score, 60.8% potential mismatches
- **Razors**: ~90%+ exact matches, high confidence scores
- **Unmatched**: Only 15 unique unmatched brush descriptions

### Target Performance
- **Exact Match Rate**: >80%
- **Confidence Score**: >70/100
- **Potential Mismatches**: <30%
- **Brand Default Rate**: <20%
- **Unmatched Rate**: <1%

## Common Issues and Solutions

### High Brand_Default Rates
**Problem**: Many matches falling back to generic brand matching  
**Solution**: Add specific model patterns for high-frequency combinations

### Low Pattern Effectiveness
**Problem**: Patterns with <80% exact match rate  
**Solution**: Review and refine regex patterns, add more specific alternatives

### Generic Model Matches
**Problem**: Too many "Synthetic", "Badger", "Boar" generic matches  
**Solution**: Add specific model patterns to capture actual product names

### Confidence Score Below 70
**Problem**: Overall match confidence is poor  
**Solution**: Focus on top mismatches and opportunities, examine specific examples, add brand-specific patterns

### High Potential Mismatch Rate
**Problem**: Many matches flagged as potentially incorrect  
**Solution**: Use `--show-examples` to examine specific cases, identify handle vs knot maker confusion

## Advanced Usage

### Compare Time Periods
```bash
# Analyze multiple months to see trends
python -m sotd.match.tools.analyze_matched_enhanced --range 2024-12:2025-05 --show-details
```

### Focus on Specific Brands
```bash
# Use grep to filter opportunities for specific brands
python -m sotd.match.tools.analyze_matched_enhanced --month 2025-05 --field brush --show-opportunities | grep "Maggard"
```

### Export Results
```bash
# Redirect output to file for sharing/archiving
python -m sotd.match.tools.analyze_matched_enhanced --month 2025-05 --field brush --show-details --show-mismatches > brush_analysis_2025-05.txt
```