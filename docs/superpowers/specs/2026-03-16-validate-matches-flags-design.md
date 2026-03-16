# Design: validate-matches CLI Flags — `--field`, `--mode`, `--model`

**Date:** 2026-03-16
**Status:** Approved
**Scope:** Update the `/validate-matches` Claude skill only. Ollama/WebUI path is a separate future project.

---

## Overview

Add three optional flags to the `/validate-matches` slash command to support field-scoped runs, task mode selection, and model selection. These enable faster targeted re-runs and A/B model testing without changing any output file formats or agent logic.

---

## New Flags

### `--field FIELD`
Comma-separated list of fields to process. Valid values: `razor`, `blade`, `brush`, `soap`.

```
/validate-matches --month 2026-02 --field soap
/validate-matches --month 2026-02 --field soap,razor
```

If omitted, all four fields are processed (current behavior).

### `--mode MODE`
Controls what agents produce. Valid values: `full`, `verify`, `propose`. Defaults to `full`.

```
/validate-matches --month 2026-02 --mode propose
/validate-matches --month 2026-02 --field soap --mode propose
```

| Mode | Agent output | verified file | proposed file |
|------|-------------|---------------|---------------|
| `full` | verifications + proposals | write/merge | write/merge |
| `verify` | verifications only | write/merge | untouched |
| `propose` | proposals only | untouched | write/merge |

### `--model MODEL`
Claude model to use for agent dispatch. Valid values: `sonnet`, `haiku`, `opus`. Defaults to `sonnet`.

```
/validate-matches --month 2026-02 --field soap --model haiku
```

Passed directly to the Agent tool's `model` parameter.

---

## Argument Parsing (Step 1 changes)

Parse all four flags from `$ARGUMENTS`:

- `--month YYYY-MM` — existing behavior (auto-detect if omitted)
- `--field` — split on comma, validate each value against `{razor, blade, brush, soap}`, error on unknown
- `--mode` — validate against `{full, verify, propose}`, error on unknown, default `full`
- `--model` — validate against `{sonnet, haiku, opus}`, error on unknown, default `sonnet`

Print resolved values at the start:
```
Running validate-matches
  Month:  2026-02
  Fields: soap          (or "all" if not specified)
  Mode:   propose
  Model:  haiku
```

---

## Field Filtering (Step 2 changes)

Only collect entries for active fields. In the counts printout, show `—` for skipped fields:

```
Entries to validate:
  razor:  —
  blade:  —
  brush:  —
  soap:   147
  total:  147
```

---

## Mode Behavior (Step 4 changes)

Prepend a mode instruction to each agent's prompt, before the common preamble:

**`--mode verify`:**
```
MODE: verify-only
Your job is ONLY to produce verifications. Do not generate any proposals.
Return an empty proposals array: "proposals": []
```

**`--mode propose`:**
```
MODE: propose-only
Your job is ONLY to generate proposals for new catalog entries.
Return an empty verifications array: "verifications": []
Do not perform match verification.
```

**`--mode full`:** No prepended instruction (current behavior).

---

## Partial Output Merging (Step 5 changes)

When `--field` restricts the run to a subset of fields, the orchestrator must merge results with any existing output file rather than overwriting it.

**Algorithm:**

1. If the output file exists, load it.
2. Remove all entries from the loaded file where `entry.field` is in the active fields set.
3. Append the new agent results.
4. Re-sort: verifications by `field` then `comment_id`; proposals by `field` then `type`.
5. Recalculate `verified_correct`, `needs_review`, `incorrect`, and `total_non_exact` from the full merged verifications set. For `proposals_generated` in the verified file: if the proposed file exists on disk, count its proposals and use that value; otherwise leave the existing count as-is.
6. Update `metadata.processed_at` to the current ISO timestamp.
7. Write back.

If the output file does not exist, write from scratch (same as current behavior).

**Applies to:** Both `data/verified/{MONTH}.json` and `data/proposed/{MONTH}.json`, subject to mode:
- In `verify` mode, only merge into verified file; leave proposed file untouched.
- In `propose` mode, only merge into proposed file; leave verified file untouched.

**Catalog loading with `--field`:** Only load catalogs and correct_matches files for the active fields (same as the existing rule "only load for fields that have entries to validate"). When `--field soap` is specified, do not load razor/blade/brush catalogs even if those fields have entries in the existing output file.

---

## Agent Dispatch — Model Selection (Step 4 changes, continued)

Pass the resolved `--model` value to the Agent tool's `model` parameter when dispatching each field agent:

```
Agent(model=resolved_model, prompt=...)
```

No changes to prompt construction based on model.

---

## Summary Output (Step 6 changes)

Add active fields and mode to the summary header:

```
Match Validation Complete — 2026-02
  Fields: soap | Mode: propose | Model: haiku
=====================================
...
```

---

## Error Handling

- Unknown `--field` value: print error listing valid values, stop.
- Unknown `--mode` value: print error listing valid values, stop.
- Unknown `--model` value: print error listing valid values, stop.
- `--field` with no matching entries in the matched file: print counts (all `—` or `0`), stop with message. Do **not** modify existing output files.

---

## Out of Scope

- Ollama / local model support (future project)
- WebUI trigger for validation runs (future project)
- Changes to agent prompt content or output JSON schema
- New proposal types or verification logic
