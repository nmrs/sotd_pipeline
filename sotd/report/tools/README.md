# Report-phase operator tools

Point-query CLIs under `python -m sotd.report.tools.*`. They exist so agents and
shell debugging never load whole month files into context: month/window arguments
are explicit (structurally enforcing "never see future months") and output is
bounded. Global flags (`--json`, `--data-dir`) precede the subcommand; each CLI's
`--help` has full usage. Tests: `tests/report/tools/`.

Before hand-coding a python/jq query, check here — the tool may already exist.
When an agent hand-codes something reusable, promote it (see "Adding a tool"
below).

## aggregate_query

Point queries over `data/aggregated/` (monthly + annual): meta block, top tables
per category, rank history for one item.

```bash
.venv/bin/python -m sotd.report.tools.aggregate_query meta --month 2026-08
.venv/bin/python -m sotd.report.tools.aggregate_query top --month 2026-08 --category razors --top 10 --min-shaves 5
.venv/bin/python -m sotd.report.tools.aggregate_query history --category razors --name "Blackland Blackbird" --last 6 --end 2026-08
```

Always pass `--end <report month>` to history — months after the report month are
already aggregated on disk, and a bare `--last N` silently returns them.

## community_query

Queries over `data/community/` month files (all posts + full comment trees):
`meta`, `threads` (filterable/sortable listings), `thread` (one thread + its
reconstructed comment tree), `bodies` (bounded selftext slices for chosen ids —
"body reads"), `search` (keyword/author across a bounded window).

```bash
.venv/bin/python -m sotd.report.tools.community_query meta --month 2026-08
.venv/bin/python -m sotd.report.tools.community_query threads --month 2026-08 --filter non-sotd --sort comments --top 20
.venv/bin/python -m sotd.report.tools.community_query thread --month 2026-08 --id t3_1sbgn5g --max-comments 50
.venv/bin/python -m sotd.report.tools.community_query bodies --month 2026-08 --ids t3_id1,t3_id2 --max-chars 1000
.venv/bin/python -m sotd.report.tools.community_query search --months 2026-03:2026-04 --query "group buy"
```

Post ids in `bodies`/`thread` accept the `t3_` prefix or the bare id; unknown ids
are listed in the output rather than failing the whole call (all-unknown exits 1).

## enriched_query

Per-shave records from `data/enriched/` — aggregates anonymize users, this CLI
doesn't: `user` (one user's shaves with matched products), `usage` (who used a
product, per-shave rows or `--by-user` counts).

```bash
.venv/bin/python -m sotd.report.tools.enriched_query user --month 2026-08 --name scribe__
.venv/bin/python -m sotd.report.tools.enriched_query usage --month 2026-08 --category soap --name "Catie's Bubbles - Tonsorium" --by-user
```

## extract_observations

Extracts Observations sections from `data/report_archive/` reports as the voice
track for drafting. Voice/storyline context only — never a numeric source.

```bash
.venv/bin/python -m sotd.report.tools.extract_observations --last 12 --end 2026-08 --type hardware
```

## Adding a tool

Promotion follows the "Agent tool promotion" section in the root `CLAUDE.md`:
new subcommand or module here, pytest coverage in `tests/report/tools/`,
lint/typecheck clean, and this README plus the relevant agent `.md` updated in
the same change.
