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
per category, rank history for one item — and a `schema` subcommand so nobody
has to probe the JSON for valid categories or field names.

```bash
.venv/bin/python -m sotd.report.tools.aggregate_query meta --month 2026-08
.venv/bin/python -m sotd.report.tools.aggregate_query schema --month 2026-08
.venv/bin/python -m sotd.report.tools.aggregate_query top --month 2026-08 --category razors --top 10 --min-shaves 5
.venv/bin/python -m sotd.report.tools.aggregate_query history --category razors --name "Blackland Blackbird" --last 6 --end 2026-08
.venv/bin/python -m sotd.report.tools.aggregate_query history --category razors --name "Schick Injector" --name "Merkur 37C" --last 3 --end 2026-08
```

Always pass `--end <report month>` to history — months after the report month are
already aggregated on disk, and a bare `--last N` silently returns them. Repeat
`--name` for a side-by-side rank matrix (one row per month, one column per item).

## community_query

Queries over `data/community/` month files (all posts + full comment trees):
`meta`, `threads` (filterable/sortable listings), `thread` (one thread + its
reconstructed comment tree), `bodies` (bounded body slices for chosen post or
comment ids — "body reads"), `search` (keyword/author across a bounded window),
and `schema` (meta keys, counts, post/comment record keys).

```bash
.venv/bin/python -m sotd.report.tools.community_query meta --month 2026-08
.venv/bin/python -m sotd.report.tools.community_query schema --month 2026-08
.venv/bin/python -m sotd.report.tools.community_query threads --month 2026-08 --filter non-sotd --sort comments --top 20
.venv/bin/python -m sotd.report.tools.community_query thread --month 2026-08 --id t3_1sbgn5g --max-comments 50
.venv/bin/python -m sotd.report.tools.community_query bodies --month 2026-08 --ids t3_id1,t3_id2 --max-chars 1000
.venv/bin/python -m sotd.report.tools.community_query bodies --month 2026-08 --id t1_ovchl1k,t1_ovhanvs --max-chars 1200
.venv/bin/python -m sotd.report.tools.community_query search --months 2026-03:2026-04 --query "group buy"
```

Ids in `bodies`/`thread` accept the `t3_`/`t1_` prefix or the bare id (`--id` is
an alias for `--ids`); unknown ids are listed in the output rather than failing
the whole call (all-unknown exits 1). Comment bodies carry thread context
(`in t3_<thread>: <title>`).

Record shape (also shown by `schema`): `{"meta": {...}, "data": {"posts": [...],
"comments": [...]}}` — posts carry `id/title/selftext/author/created_utc/...`
plus the `in_pipeline` flag; comments are a flattened list with
`id/thread_id/thread_title/parent_id/author/created_utc/body/...`.

**Recipe — daily contest target calendar** (Join Us July-style daily threads):
search for the recurring marker, then read the matched comment bodies; each day's
`Today's target` / `Tomorrow's target` sections carry the `Soap:`/`Brush:`/
`Razor:` lines with difficulty tags.

```bash
.venv/bin/python -m sotd.report.tools.community_query search --months 2026-07:2026-07 --query "Join Us July - July"
.venv/bin/python -m sotd.report.tools.community_query bodies --month 2026-07 --id t1_ovchl1k,t1_ovhanvs --max-chars 1500
```

## enriched_query

Per-shave records from `data/enriched/` — aggregates anonymize users, this CLI
doesn't: `user` (one user's shaves with matched products), `usage` (who used a
product, per-shave rows or `--by-user` counts), `timeline` (adoption timing
across a month window), and `schema` (record + category subobject shapes).

```bash
.venv/bin/python -m sotd.report.tools.enriched_query user --month 2026-08 --name scribe__
.venv/bin/python -m sotd.report.tools.enriched_query usage --month 2026-08 --category soap --name "Catie's Bubbles - Tonsorium" --by-user
.venv/bin/python -m sotd.report.tools.enriched_query timeline --months 2026-06:2026-07 --category razor --name "Schick Injector" --by-day --by-user
.venv/bin/python -m sotd.report.tools.enriched_query schema --month 2026-08
```

`timeline` scans the lookback months (all on disk before the window start,
bounded by `--since`) to classify each user as `new` (first-ever visible use in
the window) or `returning` — the contest-surge attribution question ("who
adopted, and when"). `--by-day` adds per-day counts (spike detection); `--by-user`
adds per-user rows spanning lookback + window (shaves, first/last dates, status).

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
