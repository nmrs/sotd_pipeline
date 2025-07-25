# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Essential Commands
- `make all` - Complete development workflow (lint + format + typecheck + test)
- `make test` - Run tests with pytest (`PYTHONPATH=. pytest tests/`)
- `make lint` - Lint code with Ruff
- `make typecheck` - Type check with Pyright
- `make coverage` - Run tests with coverage reporting

### Pipeline Execution
The pipeline can be run using the unified `run.py` orchestration script:

#### Individual Phases
```bash
python run.py fetch --month 2025-05 --force      # Fetch Reddit data
python run.py extract --month 2025-05 --force    # Extract product mentions
python run.py match --month 2025-05 --force      # Match to product catalogs
python run.py enrich --month 2025-05 --force     # Add metadata
python run.py aggregate --month 2025-05 --force  # Generate statistics
python run.py report --month 2025-05 --force     # Generate reports
```

#### Complete Pipeline
```bash
python run.py pipeline --month 2025-05 --force   # Run all phases
python run.py pipeline --month 2025-05 --force --debug  # With debug logging
```

#### Phase Ranges
```bash
python run.py pipeline --month 2025-05 --force extract:enrich  # Run extract through enrich
python run.py pipeline --month 2025-05 --force match:          # Run from match to end
python run.py pipeline --month 2025-05 --force :enrich         # Run from start to enrich
```

#### Date Ranges
```bash
python run.py pipeline --year 2024 --force                    # Process entire year
python run.py pipeline --start-month 2024-01 --end-month 2024-06 --force  # Date range
python run.py pipeline --range 2024-01:2024-06 --force        # Alternative range syntax
```

**Note**: The `--force` flag is MANDATORY for all pipeline operations unless explicitly specified otherwise. This ensures fresh data processing and avoids cached results.

### Legacy Direct Phase Execution
Individual phases can still be run directly (though the unified interface is preferred):
```bash
python sotd/fetch/run.py --month 2025-05 --force     # Fetch Reddit data
python sotd/extract/run.py --month 2025-05 --force   # Extract product mentions
python sotd/match/run.py --month 2025-05 --force     # Match to product catalogs
python sotd/enrich/run.py --month 2025-05 --force    # Add metadata
```

## Architecture Overview

The SOTD Pipeline processes Reddit "Shave of the Day" posts through **6 sequential phases**:

1. **Fetch** (`sotd/fetch/`) - Extract Reddit threads/comments via PRAW + Pushshift
2. **Extract** (`sotd/extract/`) - Parse comments to identify razor/blade/brush/soap mentions
3. **Match** (`sotd/match/`) - Normalize product names against YAML catalogs (`data/*.yaml`)
4. **Enrich** (`sotd/enrich/`) - Extract metadata (blade counts, brush fibers, knot sizes)
5. **Aggregate** (`sotd/aggregate/`) - Generate usage statistics (placeholder)
6. **Report** (`sotd/report/`) - Create human-readable summaries (placeholder)

Each phase reads from the previous phase's output and writes to `data/{phase}/YYYY-MM.json`.

## Key Design Patterns

### Phase Structure
Each phase follows a consistent pattern:
- `run.py` - CLI entry point with date range support
- Core processing logic in dedicated modules
- `save.py` - File I/O operations
- Comprehensive test coverage in `tests/{phase}/`

### Matching System
The matching phase uses a **strategy pattern** with specialized matchers:
- `base_matcher.py` - Abstract base class
- Product-specific matchers (`blade_matcher.py`, `soap_matcher.py`, etc.)
- `brush_matching_strategies/` - Complex brush matching with brand-specific strategies
- YAML-based product catalogs for normalization

### Data Flow
```
Reddit API → Raw Comments → Extracted Products → Matched Products → Enriched Data → Reports
```

Data persists at each stage, enabling individual phase re-runs and debugging.

## Testing Approach

- **Framework**: pytest with coverage via pytest-cov
- **Mocking**: Extensive mocking of external APIs (PRAW) and filesystem operations
- **Structure**: Tests mirror source structure (`tests/{module}/test_*.py`)
- **Integration**: End-to-end tests like `test_e2e_enrich.py`
- **Run single test**: `PYTHONPATH=. pytest tests/path/to/test_file.py::test_function`

## Configuration

- **Python 3.11** (enforced by pyrightconfig.json)
- **Black formatting** with 100-char line length
- **Ruff linting** (E, F, I rules)
- **Reddit API**: Requires `praw.ini` with credentials (gitignored)
- **Type checking**: Pyright with recommended settings

## Data Processing Context

- **Date Range**: 2016-06 to 2025-05
- **Source**: r/wetshaving SOTD threads
- **Products**: ~4000 soaps, ~800 razors, ~400 blades, complex brush taxonomy
- **Volume**: ~150k comments processed across 9 years

## Important Implementation Notes

- **Brush Matching**: Most complex due to varied naming (handle + knot combinations)
- **Manual Overrides**: `overrides/sotd_thread_overrides.json` for thread inclusion/exclusion
- **Hybrid Fetching**: Combines Reddit API with Pushshift for completeness
- **Error Handling**: Graceful degradation when APIs fail
- **Analysis Tools**: Utilities in `sotd/match/tools/` for debugging matches