# Design: Community Context Fetch — full community record + query CLI

**Date:** 2026-09-06
**Status:** Approved
**Scope:** New fetch capability (`community`), new raw data store (`data/community/`), and a new `community_query` CLI. The deterministic 6-phase pipeline is untouched. **Consumption (summarizer agent, observations-drafter wiring) is deferred to a later project** — see Out of scope.

---

## Overview

The observations-drafter agent drafts the Observations section of the monthly reports
from two sources today: aggregated numbers (`data/aggregated/`) and report archives
(voice only). Its knowledge of *community events* — contest announcements, drama,
group buys, product releases, moderator news, one-off memes — is limited to a
hardcoded event calendar and what the archives happen to mention. This design adds a
community context layer:

1. **Fetch** everything from r/wetshaving — all posts in the month (SOTD daily
   threads included) with full comment trees — into `data/community/`.
2. **Query**: a fourth report-tools CLI (`community_query`) renders the raw record
   into bounded slices (thread listings, one thread with its tree, windowed search)
   for shell use and for future agent consumers.

How the data gets *consumed* (a summarizer agent feeding the observations-drafter,
or direct drafter CLI access) is a separate design to be done once real data exists
to design against. This project deliberately ships the record + the access surface.

### Decisions settled during brainstorming

- **Scope**: everything — all posts (SOTD daily threads included) + full comment
  trees. A lot of drama and community engagement lives in SOTD-thread replies (e.g.
  Lather Games daily threads), so excluding SOTD threads would cut the most
  contest-relevant conversation at its peak. Fetching everything also removes the
  SOTD-subtraction machinery entirely.
- **Duplication accepted**: top-level SOTD comments exist in both `data/comments/`
  (pipeline dataset) and `data/community/` (context record). Different consumers,
  different purposes.
- **Time range**: forward-only from 2026-09, plus a one-time best-effort backfill of
  the current voice era (2025-07 → 2026-08).
- **Placement**: explicit sidecar command (`python run.py community …`), not a
  seventh pipeline phase — nothing in extract→report consumes community data, and it
  is only needed around report time, so it runs whenever the author wants (sooner is
  better: posts deleted later are lost forever).
- **Consumption deferred**: the summarizer agent and all observations-drafter changes
  were descoped during planning (2026-09-06) — the community_query CLI is the access
  surface this project ships; the consumption design happens in a later project,
  against real data.
- **LLM placement**: this project adds no LLM steps anywhere; fetch + CLI are fully
  deterministic.

---

## Architecture & data flow

```
Reddit API ──> sotd/fetch/community.py ──> data/community/YYYY-MM.json (raw)
                                                    │
                              community_query CLI (meta / threads / thread / search)
                                                    │
                                                    ▼
                              shell use today; agent consumption = later project
```

The deterministic pipeline stays exactly 6 phases. `community` is a new top-level
command in `run.py` following the same CLI conventions (`--month`, `--force`,
`--data-dir`, `--debug`) and the same range support as fetch (`--year`,
`--start/--end`, `--range` — needed for the backfill). It is invoked alongside (not
inside) the normal monthly fetch.

---

## Fetch mechanics (`sotd/fetch/community.py`)

### Discovery — forward months

- Paginate `subreddit.new()` (PRAW) in 100-post batches; stop when a batch contains
  a post older than the target month's 1st.
- Keep posts whose `created_utc` falls inside the target month (UTC day boundaries,
  consistent with the rest of the pipeline).
- A hard pagination cap of 30 batches (3,000 posts — the month needs ~4) prevents
  runaway loops. If the cap trips before the month boundary is reached, record
  `meta.discovery.complete = false` and log a warning — never silently partial.

### `in_pipeline` flag (metadata only, not exclusion)

- Each post gets `in_pipeline: true/false` by checking its ID against
  `data/threads/YYYY-MM.json` (the SOTD threads the pipeline claimed for that month,
  including `thread_overrides.yaml` includes, which fetch already folds into that
  file). This gives the CLI a free SOTD vs non-SOTD filter.
- It is enrichment, not exclusion: nothing is dropped based on it. If the threads
  file is missing, `in_pipeline` is omitted for that month and a warning is logged
  (no hard "run fetch first" error — the community fetch does not depend on the SOTD
  fetch).

### Comments

- Full trees: `submission.comments.replace_more(limit=None)`, then walk every
  comment including nested replies.
- Stored **flat with `parent_id`** (rebuildable threading; consistent with the
  flat-list convention used by `data/comments/`).
- `[removed]` / `[deleted]` bodies and null authors are preserved as-is — they are
  real gaps.

### Backfill — 2025-07 → 2026-08 (one-time)

- `.new()` only reaches a few months back, so older backfill months need
  search/top-listing discovery strategies (Pushshift is dead).
- **Seeding**: backfill months already have known SOTD thread IDs in
  `data/threads/YYYY-MM.json` — the *IDs* are seeded from there, and those threads
  are fetched fresh from Reddit with full comment trees (the pipeline's own
  `data/comments/` store is top-level-only and is never reused by this fetch). This
  guarantees the pipeline-claimed portion of each month regardless of how the
  remaining strategies perform on non-SOTD posts.
- **Stance: best-effort, multi-strategy, measured.** Probe candidates: Reddit search
  with month-scoped queries (flair terms, common keywords), `top` listings with
  time-range windows, and per-author submission histories of the sub's active
  regulars. Each month's `meta.discovery` records which strategies ran, how many
  posts each contributed (union after dedupe), and `complete: true/false`.
- The implementation plan begins with a cheap **coverage probe** on known months
  (e.g. 2025-07, 2026-01, 2026-06) rather than assuming any strategy works.
- Gaps are documented in meta, never hidden.

---

## Storage schema (`data/community/YYYY-MM.json`)

One file per month (posts + comments are one logical unit):

```json
{
  "meta": {
    "month": "2026-09",
    "extracted_at": "2026-09-06T…",
    "post_count": 205,
    "comment_count": 6500,
    "in_pipeline_post_count": 62,
    "discovery": {"strategies": ["new_listing"], "complete": true,
                  "per_strategy": {"new_listing": 205}}
  },
  "data": {
    "posts": [
      {"id", "title", "selftext", "author", "created_utc", "score",
       "num_comments", "flair", "url", "locked", "stickied", "in_pipeline"}
    ],
    "comments": [
      {"id", "thread_id", "parent_id", "author", "created_utc",
       "body", "score", "is_submitter"}
    ]
  }
}
```

Notes:

- `posts` includes SOTD daily threads (identified via `in_pipeline`), so the file is
  the complete community record of the month.
- **Scale (measured, not guessed)**: the comparable artifact that exists today —
  `data/comments/2026-08.json`, top-level SOTD comments only — is 2.0 MB (2,139
  comments, ~583 chars avg). Full-tree files will exceed that, which is why
  consumers go through the CLI rather than Reading files whole.
- Reddit fuzzes scores; they are kept for context ranking only, never quoted as
  facts.
- `flair` = `link_flair_text`; `is_submitter` marks replies by the thread author
  (useful conversational context).

---

## `community_query` CLI (`sotd/report/tools/community_query.py`)

Fourth tool alongside `aggregate_query` / `enriched_query` / `extract_observations`,
same conventions (`--data-dir`, `--json`, exit 0 success / 1 on query errors):

- `meta --month YYYY-MM` — counts, discovery strategies/completeness
- `threads --month YYYY-MM [--min-comments N] [--author X] [--flair X]
  [--top N] [--sort comments|score|date] [--filter sotd|non-sotd|all]` — thread
  listing (`--filter` keys off the `in_pipeline` flag; default `all`)
- `thread --month YYYY-MM --id t3_xxx [--max-comments N] [--json]` — one thread with
  its comment tree (indented render; `--json` for raw)
- `search --months YYYY-MM:YYYY-MM --query "text" [--author X] [--top N]` —
  keyword/author search across an explicitly bounded window; hits show thread title
  + matching snippet

The month/window argument is always explicit, structurally enforcing the "never see
future months" rule (same mechanism as `--end` on history queries).

---

## Error handling

- **Fetch**: rate limits via the existing `safe_call`; missing
  `data/threads/YYYY-MM.json` → warning only (`in_pipeline` omitted for that month);
  pagination boundary not reached within the cap → `complete: false` + warning.
  Deleted/removed content preserved as `[removed]`/`[deleted]` bodies.
- **CLI**: missing month file → exit 1 with a clear message (mirrors
  `aggregate_query`).

---

## Testing

- `tests/fetch/test_community_fetch.py` — month filtering, `in_pipeline` flagging
  (with and without a threads file present), full-tree flattening with `parent_id`
  preserved, meta accounting, pagination-cap behavior, `[removed]`/`[deleted]`
  preservation. PRAW mocked, following the existing `tests/fetch/` patterns.
- `tests/report/tools/test_community_query.py` — fixture month file; listing
  filters, tree rendering, search windowing, exit codes; mirrors the existing
  report-tools tests.
- One fixture-based integration test (raw month file → CLI surface).

---

## Future work (deferred to a later project, 2026-09-06)

- **community-summarizer agent**: distills each month's raw record into a
  reviewable summary for the observations-drafter. The intended pattern is
  **map-then-drill**: the `community_query threads` listing (every post, ~200 rows)
  is the map; `search` finds topics inside comment bodies; `thread` drills into the
  handful of threads worth reading, bounded per thread — the raw file is never Read
  whole. Backfill months would carry a coverage caveat citing
  `meta.discovery.per_strategy`.
- **observations-drafter wiring**: summaries as primary community context, or direct
  `community_query` access. Touch nothing in `.claude/agents/` until that design.

---

## Out of scope (explicitly)

- **Consumption**: the community-summarizer agent and ALL observations-drafter
  changes (deferred — designed in a later project against real data).
- Extract/match/enrich/aggregate/report changes — community data feeds no pipeline
  phase.
- Full-history backfill to 2016-05 (only the voice era 2025-07 → 2026-08).