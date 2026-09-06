# Design: Community Summarizer — monthly storyline briefs for the observations-drafter

**Date:** 2026-09-06
**Status:** Approved
**Scope:** New agent (`.claude/agents/community-summarizer.md`), a new derived store (`data/community/summaries/`), observations-drafter wiring, runbook + ignore-rule updates. **No pipeline, fetch, or `community_query` changes.** Consumes the record + access surface shipped by `2026-09-06-community-context-fetch-design.md`.

---

## Overview

The observations-drafter drafts the Observations section from aggregated numbers and
report archives; its knowledge of *community events* is a hardcoded calendar plus
what the archives mention. The community fetch project shipped the raw record
(`data/community/YYYY-MM.json`, ~100–120 posts / 2.5–3.5K comments / 0.8–2.3 MB per
month) and the `community_query` CLI, deferring consumption to this design.

This project adds the consumption layer:

1. **Summarize**: a `community-summarizer` agent distills one month's raw record into
   a reviewable storyline brief at `data/community/summaries/YYYY-MM.md` — non-SOTD
   thread inventory, notable SOTD-thread conversation, user happenings — with
   `t3_`/`t1_` provenance on every claim.
2. **Wire**: the drafter reads the report month's brief plus the two prior months'
   (arc context: growing storylines, prefaced events, callbacks) and spawns the
   summarizer inline for any missing month.

The summaries are **context, never a numeric source** — every number in a draft still
comes from `data/aggregated/` or the enriched CLI. Voice drafting stays with the
drafter; the summarizer writes neutral factual notes.

### Decisions settled during brainstorming

- **Artifact**: one markdown brief per month at `data/community/summaries/YYYY-MM.md`,
  gitignored (quotes raw user comments, same posture as the source JSON).
- **Wiring**: drafter reads current + prior two months' summaries; missing ones are
  spawned inline via the summarizer (report month first); a spawn fails cleanly when
  the underlying community file was never fetched — the summarizer never fetches.
- **Regeneration**: explicit-only. The summarizer never overwrites an existing brief
  unless the invoking prompt says to; staleness after a re-fetch is reported, not
  auto-fixed. The drafter never regenerates (it spawns only for missing files).
- **Completeness assumed**: if the month file exists, the record is complete. No
  coverage caveats or under-discovery speculation in summaries; Coverage quotes
  `meta` verbatim and stops. (Months with short records are fixed at the fetch side,
  outside this agent.)
- **Drafter wired now** (same change) — this design resolves the fetch spec's open
  wiring question.
- **Map-then-drill**: the intended pattern from the fetch spec's Future work, kept:
  `threads` listings are the map, `search` finds topics inside comment bodies,
  `thread` drills a bounded handful. Raw JSON files are never Read whole.
- **Single-month summaries**: each run distills exactly one month; cross-month arcs
  are the *drafter's* job (it holds three summaries), not the summarizer's.

---

## Architecture & data flow

```
data/community/YYYY-MM.json (raw, gitignored)
        │
        ▼
sotd.report.tools.community_query CLI (meta / threads / thread / search — bounded slices)
        │
        ▼
community-summarizer agent ──> data/community/summaries/YYYY-MM.md (storyline brief, gitignored)
        │                                        │
        │            spawn-when-missing          │
        └───────────────────────────────────► observations-drafter
                                             (reads current + prior two briefs;
                                              verifies claims via community_query;
                                              drafts into data/report_archive/)
```

---

## Summary file contract

```
# Community context — YYYY-MM

_Source: `data/community/YYYY-MM.json` (extracted_at <ts>) · summarized <date> by community-summarizer_

## Coverage
<post_count / comment_count / in_pipeline_post_count + discovery.strategies, verbatim from meta;
 record completeness is assumed — file exists ⇒ complete>

## Non-SOTD threads
<inventory: id · date · author · title · one-line factual note; mark which were drilled>

## Notable SOTD-thread conversation
<event chatter inside the daily threads; thread + comment ids>

## User happenings
<who did what — contests run/won, milestones, visible drama; u/ handles + ids>

## Open questions / author-only gaps
<[removed]/[deleted] bodies, null authors, unclear references, threads not drilled>

## Threads drilled
<id · title · max-comments used>
```

Rules: every claim carries `t3_`/`t1_` ids inline (the drafter spot-checks them);
neutral factual notes with significance flags allowed ("the challenge kicked off
here — likely bullet-worthy"); no drafted voice. The `extracted_at` in the header is
the staleness key: if the source is re-fetched, a fresh `meta` comparison reports the
existing brief as "exists and stale" and regeneration happens only on explicit ask.

---

## Agent: community-summarizer

`.claude/agents/community-summarizer.md` — frontmatter `tools: Read, Glob, Grep,
Bash, Write` (Write creates the brief; no Edit — it never modifies, it stops
instead); no `model` field; trigger-focused description like the drafter's.

Workflow (mirrors the drafter's numbered-step skeleton):

1. **Validate prerequisites** — Glob `data/community/{month}.json`; missing → stop
   with "fetch it first: `python run.py community {month} --force`". Never fetch.
2. **Check for an existing summary** — if present, compare its header `extracted_at`
   against fresh `meta`; report current/stale and stop. Never overwrite unless told.
3. **Read the meta** — `community_query meta --month`; the only numeric source.
4. **Map the month** (four listings): `threads --filter non-sotd --sort comments
   --top 25`; `--filter non-sotd --sort score --top 15`; `--filter sotd --sort
   comments --top 10`; `--sort date --top 30`. AutoModerator fixtures (SOTD dailies,
   Daily Questions, Deals, Free Talk Friday) are recurring low-signal rows —
   inventory, don't drill unless a title signals an event. If the flag column shows
   `n/a` (threads file missing at fetch time), `--filter` is unreliable — separate
   dailies by author/title instead.
5. **Search comment bodies** — 6–10 targeted queries, each bounded
   `--months {month}:{month}`, `--top 20`; seeds from the map (contest/challenge
   names, product names in titles, event words, the event-calendar term for the
   month, notable authors). Every hit's ids are provenance.
6. **Drill** — ≤ 8 threads, `thread --month --id X --max-comments 50`; escalate
   exactly one central thread to 100; abandon duds after the first screen.
7. **Author follow-ups** (optional, ≤ 4) — `threads --author X`, `search --author X
   --query …` for contest organizers or users the map makes notable.
8. **Write the brief** — re-Glob immediately before writing; stop if the file
   appeared meanwhile.
9. **Report back** — structured return (summary path + digests, coverage basis,
   gaps/open questions).

Hard rules: exactly one write (the brief); Bash read-only via `community_query` plus
bounded ad-hoc python/jq printing small slices — never Read/cat a community JSON
whole; every month/window explicit and ≤ the summary month; never invent
storylines/motives/identities (deleted/removed content is a gap to record, not fill);
Reddit-fuzzed scores are ranking context only, never stated as fact; completeness
assumed (no under-discovery speculation); stop-never-fetch on missing months; no
voice drafting; stay inside budgets and record the rest as gaps.

---

## observations-drafter wiring

`.claude/agents/observations-drafter.md` changes:

- Frontmatter `tools` gains `Task` (inline spawning; the workflow degrades gracefully
  if spawning is unavailable). Description text unchanged.
- New workflow step 4 "Gather community context" after step 3; old steps 4–9 renumber
  5–10 (both `step 8` hard-rule references become `step 9`). The step reads the
  current + prior two months' summaries, spawns the summarizer for any missing month
  (report month first; a spawn fails cleanly when the month's community file was
  never fetched), and marks all summaries context-never-numeric-source.
- Story-candidates step gains: weigh the summaries alongside the numbers — a
  community event can be the story behind a number, a two-month arc the story behind
  a trend.
- Hard rules: "the three `sotd.report.tools` CLIs" → four (community_query included);
  never Read raw community JSON — use `community_query` or the summaries; new rule
  making summaries storyline/arc context with provenance ids that get verified via
  `community_query` before drafting (prior-month events are background framing, never
  new numeric claims; never cite a later month via a mis-named summary).
- Return format: Fact basis cites the summary's thread/comment ids (per month) for
  community-grounded bullets; Open questions includes community-summary gaps.

---

## Runbook & repo edits

- **CLAUDE.md** "Community context operations": the "Consumption … later project"
  sentence becomes the real flow — summarizer agent distills one fetched month into
  `data/community/summaries/YYYY-MM.md` (gitignored, never a numeric source), invoked
  explicitly with a month; the observations-drafter reads it (plus the two prior
  months') and spawns the summarizer when missing. Pointer to this spec.
- **.gitignore**: `data/community/summaries/` (the `*.json` rule doesn't cover .md).
- **Fetch spec** (`2026-09-06-community-context-fetch-design.md`): Future-work section
  gains a pointer noting both items were designed here; the Out-of-scope consumption
  bullet notes the design landed.

---

## Edge cases

- **Missing community month (e.g. 2026-08 pre-fetch)**: summarizer stops, names the
  fetch command; the drafter notes the gap and proceeds — aggregated data is
  independent, the drafter still works.
- **Summary-exists race**: single user, serialized sessions; belt-and-braces re-Glob
  before Write; stop-rule makes a lost race harmless.
- **Stale brief after a backfill re-fetch**: reported via the `extracted_at`
  comparison; regeneration is explicit-only.
- **Null/[deleted] authors and [removed] bodies**: recorded as gaps with ids; never
  guessed. `is_submitter` can attribute an OP reply without a name.
- **AutoModerator dominance**: neutralized by the four-sort map + fixture-title rule;
  no `--exclude-author` flag exists (positive `--author` filters only).
- **Fuzzed scores leaking**: hard rule + spot-check in verification.
- **Nested spawning**: the drafter's `Task` tool must support spawning the summarizer
  as a sub-subagent; if unavailable, the documented two-step flow (summarize first,
  then draft) is the fallback and the gap is noted.

---

## Testing & verification

No pytest/ruff/pyright impact (markdown + .gitignore only; agent files aren't
pytest-covered, per repo precedent). End-to-end verification:

1. `git check-ignore -v data/community/summaries/2026-07.md` → matches the dir rule.
2. Live summarizer run for 2026-07 → brief with all six sections; spot-check 2–3
   provenance ids via `community_query thread`/`search`; Coverage matches `meta`.
3. Idempotency: second invoke reports "exists and current"; file unchanged (shasum).
4. Missing-month path: invoke for 2026-08 → error note names the fetch command;
   nothing written.
5. Drafter run for `month 2026-07, type hardware` (the vault-noted pending re-draft):
   exercises all three spawn branches on the window — 2026-07 succeeds, 2026-06
   succeeds, 2026-05 fails cleanly (no community file) and is noted.
6. Consistency greps: no "three `sotd"/"step 8" left in the drafter; no "later
   project" in CLAUDE.md; `community-summarizer` referenced in both agent files +
   CLAUDE.md + specs.
7. `make lint` + `make typecheck` once to prove no drift.

---

## Out of scope (explicitly)

- Pipeline, fetch, or `community_query` changes — the CLI ships as-is.
- Numeric-source use of summaries; voice drafting inside summaries.
- Completeness caveats / under-discovery speculation (record completeness assumed;
  short-record months are fixed at the fetch side).
- Summary backfill for months nobody drafts; fetching missing community months.
- A slash command or orchestration around the two agents — explicit invocation only.