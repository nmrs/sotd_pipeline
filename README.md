# 🧸 SOTD Pipeline

A Python data processing pipeline that extracts, processes, and analyzes "Shave of the Day" posts from Reddit's r/wetshaving community.

## 🚀 Quick Start

### Setup
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt
```

### Development Workflow
```bash
# Fast development testing (recommended during development)
make test-fast

# Complete validation (run before commits)
make format lint typecheck test

# Run pipeline phases
python run.py fetch --month 2025-05 --force
python run.py extract --month 2025-05 --force
python run.py match --month 2025-05 --force
python run.py enrich --month 2025-05 --force
python run.py aggregate --month 2025-05 --force
python run.py report --month 2025-05 --force

# Or run complete pipeline
python run.py pipeline --month 2025-05 --force
```

## 📊 Pipeline Overview

The pipeline consists of 6 sequential phases:

1. **Fetch** - Extract Reddit threads and comments
2. **Extract** - Parse product mentions from comments
3. **Match** - Normalize product names against catalogs
4. **Enrich** - Extract additional metadata
5. **Aggregate** - Generate statistical summaries
6. **Report** - Create human-readable reports

## 🛠️ Development Features

### Optimized Testing Strategy
- **Fast Tests**: `make test-fast` (~4.6s, 57% faster than sequential)
- **Complete Validation**: `make test` (~10.8s, full coverage)
- **Performance Analysis**: `make test-slow` (identify bottlenecks)
- **Test Count**: 1,255 optimized tests (5.8% reduction from baseline)

### Quality Assurance
- **Code Formatting**: Black + Ruff
- **Linting**: Ruff (E, F, I rules)
- **Type Checking**: Pyright
- **Test Coverage**: pytest-cov

## 📚 Documentation

- **[Pipeline Specification](docs/SOTD_Pipeline_Spec.md)** - Complete pipeline documentation
- **[Development Workflow](docs/SOTD_Pipeline_Spec.md#-development-workflow)** - Optimized testing and development process
- **[Phase Specifications](docs/)** - Detailed specifications for each pipeline phase

## 🔧 Configuration

- **Python**: 3.11
- **Environment**: Virtual environment with `.venv`
- **Dependencies**: See `requirements.txt` and `requirements-dev.txt`
- **Configuration**: `pyproject.toml`, `pyrightconfig.json`

## 📁 Project Structure

```
sotd_pipeline/
├── sotd/                    # Main pipeline modules
│   ├── fetch/              # Reddit data extraction
│   ├── extract/            # Product mention parsing
│   ├── match/              # Product name normalization
│   ├── enrich/             # Metadata enrichment
│   ├── aggregate/          # Statistical aggregation
│   └── report/             # Report generation
├── tests/                  # Comprehensive test suite
├── data/                   # Pipeline data storage
├── docs/                   # Detailed documentation
├── run.py                  # Pipeline orchestration
└── Makefile               # Development commands
```

## 🤝 Contributing

1. Follow the **Pipeline --force Rule**: Always use `--force` flag during development
2. Use **Test-First Development**: Write tests before implementing features
3. Run **Fast Tests** during development: `make test-fast`
4. Run **Complete Validation** before commits: `make format lint typecheck test`
5. Update documentation with code changes

## 📈 Performance

- **Test Execution**: 57% improvement with parallel execution
- **Test Coverage**: 71% with comprehensive edge case coverage
- **Development Speed**: Fast feedback loop with optimized testing strategy

## Product Matching Normalization (2024-07)

All correct match lookups in the pipeline now use a single, canonical normalization function:

```
from sotd.utils.match_filter_utils import normalize_for_matching
```

- This function is the only allowed normalization for correct match lookups.
- The old `normalize_for_storage` function is deprecated and should not be used.
- See [docs/product_matching_validation.md](docs/product_matching_validation.md) for details and examples.

This change ensures that all entries in `correct_matches.yaml` are always found as exact matches, eliminating normalization inconsistencies and "confirmed but not exact" mismatches.

---

For detailed information, see the [Pipeline Specification](docs/SOTD_Pipeline_Spec.md). 

## Brush Correct Matches Enhancement (2025-07)

The brush matcher now supports advanced correct matching for combo brushes using separate `handle:` and `knot:` sections in `data/correct_matches.yaml`. For brushes like `DG B15 w/ C&H Zebra`, the matcher extracts and stores handle and knot details separately, and defers the decision of top-level brand/model to the reporting phase. Simple brushes continue to use the `brush:` section as before.

### Example YAML
```yaml
handle:
  Chisel & Hound:
    Zebra:
      - "DG B15 w/ C&H Zebra"
knot:
  Declaration Grooming:
    B15:
      strings:
        - "DG B15 w/ C&H Zebra"
      fiber: "Badger"
      knot_size_mm: 26.0
```

### Example Match Output
```python
{
    "matched": {
        "brand": None,  # Deferred to reporting
        "model": None,  # Deferred to reporting
        "handle_maker": "Chisel & Hound",
        "handle": {"brand": "Chisel & Hound", "model": "Zebra", "source_text": "DG B15 w/ C&H Zebra"},
        "knot": {"brand": "Declaration Grooming", "model": "B15", "fiber": "Badger", "knot_size_mm": 26.0, "source_text": "DG B15 w/ C&H Zebra"}
    },
    "match_type": "exact"
}
```

- For combo brushes, reporting/aggregation code should use the `knot` and `handle` fields for display.
- For simple brushes, `brand` and `model` are set as before.
- Backward compatibility is maintained for all existing data and workflows.

## User Intent Preservation Fix (2025-08)

**Critical Bug Fix**: The system now preserves user intent information when processing correct matches, preventing data loss.

### Problem
Previously, when brushes were added to `correct_matches.yaml`, the system would lose user intent information (whether the user considered the brush "handle-primary" or "knot-primary") that was previously captured through automated matching.

### Solution
All correct match processing methods now include user intent detection:
- `_process_handle_knot_correct_match()`
- `_process_split_brush_correct_match()`
- `_process_regular_correct_match()`
- `_process_split_result()`

### User Intent Detection
The system detects user intent based on component order in the input string:
- **"knot_primary"**: When knot component appears before handle component (e.g., "G5C Rad Dinosaur")
- **"handle_primary"**: When handle component appears before knot component (e.g., "Rad Dinosaur G5C")

### Data Quality Enhancement
Correct matches now enhance rather than degrade data quality by preserving all available information, including user intent. This ensures that adding brushes to `correct_matches.yaml` improves data quality without any information loss.

### Example
```python
# Input: "G5C Rad Dinosaur Creation"
# User intent: "knot_primary" (G5C appears first)
{
    "matched": {
        "user_intent": "knot_primary",  # Preserved in correct matches
        "handle": {"brand": "Rad Dinosaur", "model": "Creation"},
        "knot": {"brand": "AP Shave Co", "model": "G5C"}
    }
}
``` 