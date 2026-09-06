# Design: Community Context Fetch — full community record + summaries for the observations-drafter

**Date:** 2026-09-06
**Status:** Approved
**Scope:** New fetch capability (`community`), new raw data store (`data/community/`), new summarizer agent, new `community_query` CLI, and updates to the `observations-drafter` agent. The deterministic 6-phase pipeline is untouched.

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
2. **Summarize** each month's raw data via a new author-invoked agent, producing
   `data/community/summaries/YYYY-MM.md`.
3. **Consume**: the observations-drafter treats the summaries as its primary
   community context, with a new `community_query` CLI for verifying or quoting raw
   material. Numeric truth remains `data/aggregated/` exclusively.

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
  is only needed before drafting observations, so it runs whenever the author wants
  (sooner is better: posts deleted later are lost forever).
- **Consumption**: `community_query` CLI + summarizer agent; summaries are the
  drafter's primary community source; the CLI is for drill-down and verification.
- **LLM placement**: both LLM steps (summarize, draft) stay outside the deterministic
  pipeline and are human-reviewed (author edits summaries before the drafter uses
  them).

---

## Architecture & data flow

```
Reddit API ──> sotd/fetch/community.py ──> data/community/YYYY-MM.json (raw)
                                                    │
                                     community-summarizer agent (author-invoked, author-edited)
                                                    ▼
                                     data/community/summaries/YYYY-MM.md
                                                    │ (primary community context)
                                                    ▼
                              observations-drafter ── verify claims via community_query CLI
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
  file). This gives the CLI and summarizer a free SOTD vs non-SOTD filter.
- It is enrichment, not exclusion: nothing is dropped based on it. If the threads
  file is missing, `in_pipeline` is omitted for that month and a warning is logged
  (no hard "run fetch first" error — the community fetch no longer depends on the
  SOTD fetch).

### Comments

- Full trees: `submission.comments.replace_more(limit=None)`, then walk every
  comment including nested replies.
- Stored **flat with `parent_id`** (rebuildable threading; consistent with the
  flat-list convention used by `data/comments/`).
- `[removed]` / `[deleted]` bodies and null authors are preserved as-is — they are
  real gaps. The summarizer is instructed to ignore them.

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
- Gaps are documented in meta, never hidden; summaries for backfill months carry a
  coverage caveat header.

---

## Storage schema (`data/community/YYYY-MM.json`)

One file per month (posts + comments are one logical unit; volumes are modest):

```json
{
  "meta": {
    "month": "2026-09",
    "extracted_at": "2026-09-06T…",
    "post_count": 205,
    "comment_count": 6500,
    "in_pipeline_post_count": 62,
    "discovery": {"strategies": ["new_listing"], "complete": true}
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
  the complete community record of the month. Comment volume roughly doubles versus
  a non-SOTD-only fetch (~5–10k/month) — still modest.
- Reddit fuzzes scores; they are kept for context ranking only, never quoted as
  facts.
- `flair` = `link_flair_text`; `is_submitter` marks replies by the thread author
  (useful conversational context).
- Summaries are generated artifacts, separate from `data/report_archive/` (those are
  published voice; these are context). Path: `data/community/summaries/YYYY-MM.md`.

---

## Summarizer agent (`.claude/agents/community-summarizer.md`)

- **Invocation**: `month 2026-09` (single month) or `range 2025-07:2026-08`
  (backfill — oldest-first, one month at a time, writing each summary before moving
  on). Missing month/range → error note, no guessing.
- **Tools**: Read, Glob, Grep, Bash, Edit.
- **Inputs**: the raw month file `data/community/YYYY-MM.json` — never Read whole
  (it can run to thousands of comments). The agent works **map-then-drill**: a
  compact listing of every post (id/date/flair/author/comment count/title, via the
  `community_query threads` CLI or a jq one-liner) is the map and is small enough
  to see whole; `community_query search` finds specific topics inside comment
  bodies; `community_query thread` drills into the handful of threads worth
  reading, bounded per thread. Prior months' summaries for continuity of running
  jokes.
- **Signal vs noise**: the month file contains every SOTD shave comment ("nice
  shave!" banter included). The agent prioritizes non-SOTD posts and unusually
  high-engagement threads; inside SOTD threads the signal is in the replies, not
  the shave comments themselves (and `in_pipeline` marks which is which). During
  contest months (Lather Games, Austere August), SOTD-thread replies are primary
  material, not noise.
- **Output** (`data/community/summaries/YYYY-MM.md`), fixed sections:
  - *Headline events* — contests launched/ended, moderator news, sub announcements
  - *Product & vendor news* — releases, group buys, brand drama, vendor activity
  - *Notable conversations* — high-engagement threads and what was actually said
  - *Emerging running jokes / memes* — flagged as candidates (the drafter's coinage
    rule: propose fresh material, never present as established)
  - *Notable users* — factual, behavioral not personal
  - *Threads index* — compact table: id, date, title, flair, comment count
- **Discipline**: every claim cites thread ID (plus comment ID when specific);
  quotes verbatim; interpretations of *why* go under open questions; no pipeline
  statistics (numbers are aggregates' job); coverage caveat header on backfill
  months; drafts are for the author to review/edit before the drafter uses them.
- **Writes only its summary file** — never raw data, never archives.

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

The month/window argument is always explicit, structurally enforcing the drafter's
"never see future months" rule (same mechanism as `--end` on history queries).

---

## observations-drafter update (`.claude/agents/observations-drafter.md`)

- New workflow step after voice-track extraction: read
  `data/community/summaries/YYYY-MM.md` plus the prior month's summary (for
  callbacks). Summaries are the **primary community context when present**.
- The allowed-CLIs line gains `community_query`; ad-hoc python/jq over
  `data/community/` joins the permitted read-only analysis.
- Hard rules updated:
  - Summary/CLI-verified material may ground event claims ("LG was announced June
    1st, thread `t3_xxx`") — numeric truth is still aggregates-only.
  - "The author knows things the archives don't" becomes "the author knows things
    the summaries don't"; gaps and open questions still get flagged.
  - Missing summary for the report month → flag as an open question and fall back
    to the hardcoded event calendar; the drafter never fetches.

---

## Error handling

- **Fetch**: rate limits via the existing `safe_call`; missing
  `data/threads/YYYY-MM.json` → warning only (`in_pipeline` omitted for that month);
  pagination boundary not reached within the cap → `complete: false` + warning.
  Deleted/removed content preserved as `[removed]`/`[deleted]` bodies.
- **CLI**: missing month file → exit 1 with a clear message (mirrors
  `aggregate_query`).
- **Summarizer**: missing raw file → report and stop (never fabricate); missing
  prior summary → proceed without continuity and note it in the output.

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
- Agent behavior (summarizer, drafter) is validated by the author running them, as
  today.

---

## Out of scope (explicitly)

- Extract/match/enrich/aggregate/report changes — community data feeds no pipeline
  phase.
- Full-history backfill to 2016-05 (only the voice era 2025-07 → 2026-08).
- Automatic/LLM-in-pipeline summarization (summaries are author-invoked and
  author-reviewed).