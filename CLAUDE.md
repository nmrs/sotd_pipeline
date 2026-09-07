# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Essential Commands
- `make all` - Complete development workflow (preprocess + lint + format + typecheck + test)
- `make test` - Run Python tests with pytest (`PYTHONPATH=. pytest tests/`)
- `make lint` - Lint code with Ruff
- `make typecheck` - Type check with Pyright
- `make test-coverage` - Run tests with coverage reporting

**Note**: Makefile targets call bare `python`/`pytest`, so activate the venv first (`source .venv/bin/activate`).

### WebUI Commands
The React/TypeScript WebUI is optional; see `webui/README.md`. Test targets wrap `webui/scripts/manage-servers.sh` (servers start/stop automatically):
- `make test-react` - React/TypeScript unit tests
- `make test-e2e` - Playwright end-to-end tests
- `make start-servers` / `make stop-servers` / `make server-status` - Manage test servers

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
python run.py report --month 2025-05 --force --no-slug  # Reports without WSDB links in soap names
python run.py community --month 2025-05 --force  # Fetch all posts + full comment trees (community context)
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

#### Community context operations

The `community` sidecar is run when needed (sooner after month end = fewer
lost-to-deletion posts); the author explores the record via the CLI:

```bash
# 1. Fetch the month's full community record
python run.py community --month 2026-09 --force

# 2. (Author) explore — the CLI renders bounded slices
python -m sotd.report.tools.community_query threads --month 2026-09 --top 20
python -m sotd.report.tools.community_query search --months 2026-08:2026-09 --query "group buy"
```

Consumption: the `community-summarizer` agent (`.claude/agents/community-summarizer.md`)
distills one fetched month into `data/community/summaries/YYYY-MM.md` — storyline
context with thread/comment provenance, gitignored, never a numeric source. Invoke it
explicitly with a month ("summarize community context for 2026-09"); the
`observations-drafter` reads that summary (plus the two prior months', as arc context)
when drafting and spawns the summarizer itself when a summary is missing. Design:
`docs/superpowers/specs/2026-09-06-community-summarizer-design.md`.

Backfill notes: months `.new()` cannot reach fall back to best-effort discovery
(SOTD-thread seeding from `data/threads/` + timestamp search + active-author
histories); each month's `meta.discovery` records what ran and how complete it is.
Reddit serves only ~1000 items per `/new` listing (~8 months of r/wetshaving), so
older months always need backfill — the fetch cross-checks the listing's completeness
claim against the pipeline's known SOTD thread IDs and flips `meta.discovery.complete`
to `false` when the listing ended mid-history (never silently partial).
Run the voice-era backfill with `python run.py community --range 2025-07:2026-08 --force`.

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
5. **Aggregate** (`sotd/aggregate/`) - Generate usage statistics (monthly + annual)
6. **Report** (`sotd/report/`) - Render markdown reports (hardware/software × monthly/annual); `--no-slug` omits WSDB links in soap names

Each phase reads from the previous phase's output. Artifact layout under `--data-dir` (default `data/`, or `SOTD_DATA_DIR` env var):

- **Fetch**: `data/threads/YYYY-MM.json` + `data/comments/YYYY-MM.json`
- **Extract / Match / Enrich**: `data/{extracted,matched,enriched}/YYYY-MM.json`
- **Aggregate**: `data/aggregated/YYYY-MM.json` (+ `data/aggregated/annual/YYYY.json`)
- **Report**: `data/report/YYYY-MM-{hardware|software}.md` (+ `data/report/annual/`)
- **Community fetch (sidecar)**: `data/community/YYYY-MM.json` (all posts + full comment trees, `in_pipeline` flags); consumed via the `community_query` CLI

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
- Match resolution order: pre-validated matches in `data/correct_matches/*.yaml` are checked first, then catalogs; `data/intentionally_unmatched.yaml` marks strings that should stay unmatched

### Data Flow
```
Reddit API → Raw Comments → Extracted Products → Matched Products → Enriched Data → Reports
```

Data persists at each stage, enabling individual phase re-runs and debugging.

## Testing Approach

- **Framework**: pytest with coverage via pytest-cov
- **Mocking**: Extensive mocking of external APIs (PRAW) and filesystem operations
- **Structure**: Tests mirror source structure (`tests/{module}/test_*.py`)
- **Integration**: `tests/integration/` (e.g. `test_real_catalog_integration.py`, `test_correct_matches_integration.py`); production-catalog tests run via `make test-production`
- **Skipped tests**: Documented with reasons and action items in `docs/skipped_tests.md`
- **Run single test**: `PYTHONPATH=. pytest tests/path/to/test_file.py::test_function`

## Configuration

- **Python 3.14** (enforced by pyrightconfig.json)
- **Black formatting** with 100-char line length
- **Ruff linting** (E, F, I rules)
- **Reddit API**: Requires `praw.ini` in the project root (gitignored); only needed for `fetch`
- **Type checking**: Pyright with recommended settings
- **Cursor rules**: `.cursor/rules/` contains phase-specific dev rules (aggregate phase, brush matching, data processing, API handling)

### Operator override files (under `data/`)
- `thread_overrides.yaml` - Thread inclusion/exclusion for fetch (`include` / `exclude` date→URL maps)
- `extract_overrides.yaml` - Extraction fixes (default path for extract's `--override-file`)
- `enrichment_overrides.yaml` - Enrichment fixes
- `intentionally_unmatched.yaml` - Strings that should intentionally remain unmatched
- `correct_matches/*.yaml` - Confirmed matches (checked first in the match phase)

## Data Processing Context

- **Date Range**: 2016-05 onward, extended month-by-month (data for the current month is present)
- **Source**: r/wetshaving SOTD threads
- **Catalogs** (`data/*.yaml`): ~800 soaps, ~745 razors, ~165 blades, ~300 brushes, plus separate handle (~208) and knot (~166) catalogs
- **Pre-validated matches** (`data/correct_matches/*.yaml`): ~1800 soaps, ~600 razors, ~650 brushes, ~145 blades
- **Volume**: ~150k comments across 10+ years

## Important Implementation Notes

- **Brush Matching**: Most complex due to varied naming (handle + knot combinations); see `.cursor/rules/brush-matching.mdc`
- **Hybrid Fetching**: Combines Reddit API with Pushshift for completeness
- **Error Handling**: Graceful degradation when APIs fail
- **Analysis Tools**: Utilities in `sotd/match/tools/` for debugging matches
- **WebUI – WSDB Alignment Analyzer**: Two modes—**Alignment** (bidirectional pipeline vs WSDB, catalog or match files, two tabs) and **Slug finder** (pipeline scents from soaps.yaml → suggested WSDB slugs from software.json, catalog-only, single “Slug suggestions” view)

## Agent memory

This repo is tracked in the **AgentMemory** vault (`github.com/nmrs/agent-memory`; local clone `../agent-memory`). Before substantive work, read the vault's `INDEX.md` and follow its protocol: `git pull --rebase` first, attribute changes (agent-id + date), record durable knowledge only.

This project's vault entry: `projects/sotd-pipeline/status.md` (repo dir is `sotd-pipeline`, renamed from `sotd_pipeline` on 2026-09-05; the vault entry is kebab-case).