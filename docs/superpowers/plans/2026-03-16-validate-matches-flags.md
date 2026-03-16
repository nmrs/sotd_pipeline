# validate-matches CLI Flags Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add `--field`, `--mode`, and `--model` flags to the `/validate-matches` Claude skill to support field-scoped runs, task mode selection, and model selection.

**Architecture:** This is a pure prompt-engineering task — the entire implementation is edits to `.claude/commands/validate-matches.md`. No Python code is added. Changes are organized by the skill's existing step structure (Steps 1–6), with each task modifying one logical section of the file.

**Tech Stack:** Markdown (Claude Code skill format), Claude Agent tool API (`model` parameter: `sonnet`, `haiku`, `opus`)

**Spec:** `docs/superpowers/specs/2026-03-16-validate-matches-flags-design.md`

---

## Chunk 1: Argument Parsing and Field Filtering

### Task 1: Expand Step 1 — Argument Parsing

**Files:**
- Modify: `.claude/commands/validate-matches.md` (Step 1 section)

**Context:** Step 1 currently parses only `--month`. We need to add parsing for `--field`, `--mode`, and `--model` with validation and defaults.

- [ ] **Step 1.1: Read the current Step 1 section**

  Open `.claude/commands/validate-matches.md` and read lines 1–14 (the "Step 1: Parse Arguments" section). Understand exactly what text will be replaced.

- [ ] **Step 1.2: Replace Step 1 with the expanded version**

  Replace the entire Step 1 section (from `## Step 1: Parse Arguments` through the blank line before `## Step 2`) with:

  ```markdown
  ## Step 1: Parse Arguments and Locate Input File

  Parse the argument string: `$ARGUMENTS`

  - Extract `--month YYYY-MM` if present
  - If no `--month` is provided, find the most recent file in `data/matched/` by listing the directory and sorting by filename
  - Extract `--field VALUE` if present. Split on commas to get a list. Valid values: `razor`, `blade`, `brush`, `soap`. If any value is unrecognised, print an error listing valid values and stop.
  - Extract `--mode VALUE` if present. Valid values: `full`, `verify`, `propose`. Default: `full`. If an unrecognised value is given, print an error listing valid values and stop.
  - Extract `--model VALUE` if present. Valid values: `sonnet`, `haiku`, `opus`. Default: `sonnet`. If an unrecognised value is given, print an error listing valid values and stop.

  Set `MONTH` to the resolved month value.
  Set `ACTIVE_FIELDS` to the resolved field list, or `[razor, blade, brush, soap]` if `--field` was not provided.
  Set `MODE` to the resolved mode.
  Set `MODEL` to the resolved model.

  Print the resolved configuration:
  ```
  Running validate-matches
    Month:  {MONTH}
    Fields: {comma-separated ACTIVE_FIELDS, or "all" if all four are active}
    Mode:   {MODE}
    Model:  {MODEL}
  ```

  Read the file `data/matched/{MONTH}.json`. If it does not exist, report the error and stop.
  ```

- [ ] **Step 1.3: Verify the edit looks right**

  Read back the modified Step 1 section. Confirm:
  - All four flags are described with their valid values and defaults
  - `ACTIVE_FIELDS`, `MODE`, `MODEL` are introduced as named variables for later steps to reference
  - The startup printout block is present
  - Error handling for unknown values is present

- [ ] **Step 1.4: Commit**

  ```bash
  git add .claude/commands/validate-matches.md
  git commit -m "feat(validate-matches): add --field/--mode/--model argument parsing (Step 1)"
  ```

---

### Task 2: Update Step 2 — Field Filtering

**Files:**
- Modify: `.claude/commands/validate-matches.md` (Step 2 section)

**Context:** Step 2 currently collects entries for all four fields unconditionally. We need it to skip fields not in `ACTIVE_FIELDS` and show `—` in the counts printout for skipped fields. We also need to add the zero-entry termination condition specific to field-filtered runs.

- [ ] **Step 2.1: Read the current Step 2 section**

  Read the "Step 2: Filter and Partition Entries" section of the skill. Note the existing "If total is 0" termination clause — we will update it.

- [ ] **Step 2.2: Add field filtering to the collection logic**

  After the sentence "For each field in each entry, collect the field data if `match_type` is **not** one of: ..." add:

  ```markdown
  Only collect entries for fields in `ACTIVE_FIELDS`. Skip all other fields entirely — do not build a list for them.
  ```

- [ ] **Step 2.3: Update the counts printout**

  Replace the counts printout block:

  ```markdown
  Print the counts per field:
  ```
  Entries to validate:
    razor:  {N}
    blade:  {N}
    brush:  {N}
    soap:   {N}
    total:  {N}
  ```
  ```

  With:

  ```markdown
  Print the counts per field (show `—` for fields not in ACTIVE_FIELDS):
  ```
  Entries to validate:
    razor:  {N or —}
    blade:  {N or —}
    brush:  {N or —}
    soap:   {N or —}
    total:  {N}
  ```
  ```

- [ ] **Step 2.4: Update the zero-entry termination clause**

  Replace:
  ```markdown
  If total is 0, write empty output files and stop with a message.
  ```

  With:
  ```markdown
  If total is 0:
  - If `--field` was not specified (all fields active): write empty output files and stop with a message.
  - If `--field` was specified: print the counts (all `—` or `0`), stop with a message, and do **not** modify any existing output files.
  ```

- [ ] **Step 2.5: Verify the edit**

  Read back the Step 2 section. Confirm:
  - Collection loop only processes `ACTIVE_FIELDS`
  - `—` is shown for skipped fields in the printout
  - The two-branch zero-entry termination is present

- [ ] **Step 2.6: Commit**

  ```bash
  git add .claude/commands/validate-matches.md
  git commit -m "feat(validate-matches): field filtering in entry collection (Step 2)"
  ```

---

## Chunk 2: Mode Behavior, Model Dispatch, Partial Merge, Summary

### Task 3: Update Step 3 — Catalog Loading with `--field`

**Files:**
- Modify: `.claude/commands/validate-matches.md` (Step 3 section)

**Context:** Step 3 already says "Only load catalog/correct_matches for fields that have entries to validate (skip empty fields)." With `--field` filtering this still holds, but we need to make explicit that skipped fields are also skipped for catalog loading even if the existing output files contain entries for those fields.

- [ ] **Step 3.1: Add a clarifying note to Step 3**

  After the existing "Only load catalog/correct_matches for fields that have entries to validate (skip empty fields)." sentence, add:

  ```markdown
  When `--field` is specified, do not load catalogs or correct_matches files for inactive fields, even if existing output files contain entries for those fields.
  ```

- [ ] **Step 3.2: Verify the edit**

  Read back the Step 3 section. Confirm the new sentence is present immediately after the "Only load..." sentence and does not alter any other content in the section.

- [ ] **Step 3.3: Commit**

  ```bash
  git add .claude/commands/validate-matches.md
  git commit -m "feat(validate-matches): explicit catalog loading scope for --field (Step 3)"
  ```

---

### Task 4: Update Step 4 — Mode Instructions and Model Dispatch


**Files:**
- Modify: `.claude/commands/validate-matches.md` (Step 4 section)

**Context:** Step 4 dispatches agents. We need to (a) prepend a mode instruction to each agent's prompt when `MODE` is not `full`, and (b) pass `MODEL` to the Agent tool's `model` parameter.

- [ ] **Step 4.1: Add mode instruction to agent prompt construction**

  In Step 4, find the numbered list that describes how to construct each agent's prompt:
  ```
  Construct each agent's prompt by concatenating:
  1. The **Common Preamble** from Section 6
  ...
  ```

  Replace the entire numbered list with the following 7-item list (the existing items 1–6 become items 2–7; a new item 1 is inserted before them):

  ```markdown
  1. A **mode instruction** (prepended before everything else), if MODE is not `full`:
     - If MODE is `verify`: prepend `"MODE: verify-only\nYour job is ONLY to produce verifications. Do not generate any proposals.\nReturn an empty proposals array: \"proposals\": []\n\n"`
     - If MODE is `propose`: prepend `"MODE: propose-only\nYour job is ONLY to generate proposals for new catalog entries.\nReturn an empty verifications array: \"verifications\": []\nDo not perform match verification.\n\n"`
     - If MODE is `full`: prepend nothing (current behavior)
  2. The **Common Preamble** from Section 6
  3. The **field-specific instructions** from Section 6 (Razor/Blade/Brush/Soap Agent Instructions)
  4. `"\n\n## Entries to Validate\n\n"` followed by the entries as a JSON array
  5. `"\n\n## Catalog (for reference)\n\n"` followed by the raw YAML catalog content for that field
  6. `"\n\n## Correct Matches (for reference)\n\n"` followed by the raw YAML correct_matches content
  7. `"\n\n## Intentionally Unmatched (do not propose these)\n\n"` followed by the relevant section from intentionally_unmatched.yaml
  ```

  Note: The soap-specific reminder sentence ("For the soap agent, include this additional instruction at the end: ...") is NOT part of the numbered list — leave it unchanged after item 7.

- [ ] **Step 4.2: Add model parameter to agent dispatch**

  Find the sentence describing how to dispatch agents (e.g., "dispatch an agent using the **Agent tool**"). After it, add:

  ```markdown
  Pass `MODEL` as the `model` parameter to the Agent tool for every field agent dispatched.
  ```

- [ ] **Step 4.3: Verify the edit**

  Read back Step 4. Confirm:
  - Mode instruction is item 1 in the prompt construction list, with all three branches
  - The remaining items (Common Preamble, field-specific instructions, entries, catalog, correct_matches, intentionally_unmatched) are renumbered correctly
  - The model parameter instruction is present in the dispatch description

- [ ] **Step 4.4: Commit**

  ```bash
  git add .claude/commands/validate-matches.md
  git commit -m "feat(validate-matches): mode instructions and model dispatch (Step 4)"
  ```

---

### Task 5: Update Step 5 — Partial Output Merging

**Files:**
- Modify: `.claude/commands/validate-matches.md` (Step 5 section)

**Context:** Step 5 currently writes both output files unconditionally. We need to replace this with a merge algorithm that (a) only writes files appropriate to `MODE`, and (b) merges with existing file contents when `--field` restricts the run to a subset of fields.

- [ ] **Step 5.1: Read the current Step 5 section**

  Read the "Step 5: Merge Agent Results" section carefully. Note the two output file specs and the "Write both files using Python (via bash)" instruction.

- [ ] **Step 5.2: Replace Step 5 with the new merge-aware version**

  Replace the entire Step 5 section with:

  ````markdown
  ## Step 5: Merge Agent Results

  Collect all agent responses. Parse the JSON from each.

  Merge all `verifications` arrays from this run into a single list.
  Merge all `proposals` arrays from this run into a single list.

  ### Determine which output files to write

  Based on MODE:
  - `full`: write both `data/verified/{MONTH}.json` and `data/proposed/{MONTH}.json`
  - `verify`: write only `data/verified/{MONTH}.json`; do not touch `data/proposed/{MONTH}.json`
  - `propose`: write only `data/proposed/{MONTH}.json`; do not touch `data/verified/{MONTH}.json`

  ### Partial merge algorithm (for each file being written)

  1. If the output file exists on disk, load it and extract its current entries array (`verifications` or `proposals`).
  2. Remove all entries from the loaded array where `entry.field` is in `ACTIVE_FIELDS`.
  3. Append the new agent results from this run.
  4. Re-sort: verifications by `field` then `comment_id`; proposals by `field` then `type`.
  5. Recalculate stats (for the verified file):
     - `verified_correct`: count verifications with `verdict == "verified"`
     - `needs_review`: count verifications with `verdict == "needs_review"`
     - `incorrect`: count verifications with `verdict == "incorrect"`
     - `total_non_exact`: sum of the above three
     - `proposals_generated`: if `data/proposed/{MONTH}.json` exists on disk, count its `proposals` array length; otherwise keep the existing value as-is
  6. Update `metadata.processed_at` to the current ISO timestamp.
  7. Write back.

  If the output file does not exist, write from scratch (no merge needed).

  ### Output file schemas

  #### `data/verified/{MONTH}.json`
  ```json
  {
    "metadata": {
      "month": "YYYY-MM",
      "processed_at": "ISO timestamp",
      "source_file": "data/matched/YYYY-MM.json",
      "stats": {
        "total_non_exact": 0,
        "verified_correct": 0,
        "needs_review": 0,
        "incorrect": 0,
        "proposals_generated": 0
      }
    },
    "verifications": [...]
  }
  ```

  #### `data/proposed/{MONTH}.json`
  ```json
  {
    "metadata": {
      "month": "YYYY-MM",
      "processed_at": "ISO timestamp",
      "proposal_count": 0
    },
    "proposals": [...]
  }
  ```

  Write output files using Python (via bash) to ensure valid JSON with proper formatting.
  ````

- [ ] **Step 5.3: Verify the edit**

  Read back Step 5. Confirm:
  - MODE determines which files are written (with explicit "do not touch" for the excluded file)
  - The 7-step merge algorithm is present with all steps including `proposals_generated` cross-file logic
  - Output file schemas are preserved
  - The Python/bash write instruction is retained

- [ ] **Step 5.4: Commit**

  ```bash
  git add .claude/commands/validate-matches.md
  git commit -m "feat(validate-matches): partial output merge algorithm (Step 5)"
  ```

---

### Task 6: Update Step 6 — Summary Output

**Files:**
- Modify: `.claude/commands/validate-matches.md` (Step 6 section)

**Context:** The summary header should show active fields, mode, and model.

- [ ] **Step 6.1: Update the summary printout template**

  In Step 6, replace:
  ```markdown
  ```
  Match Validation Complete — {MONTH}
  =====================================
  ```
  ```

  With:
  ```markdown
  ```
  Match Validation Complete — {MONTH}
    Fields: {comma-separated ACTIVE_FIELDS, or "all"} | Mode: {MODE} | Model: {MODEL}
  =====================================
  ```
  ```

- [ ] **Step 6.2: Verify the edit**

  Read back Step 6. Confirm the header line with fields/mode/model is present and correctly placed before the `===` separator.

- [ ] **Step 6.3: Commit**

  ```bash
  git add .claude/commands/validate-matches.md
  git commit -m "feat(validate-matches): add fields/mode/model to summary header (Step 6)"
  ```

---

## Chunk 3: Smoke Testing

### Task 7: Verify the Updated Skill

**Files:**
- Read: `.claude/commands/validate-matches.md` (final state)

**Context:** Since this is a prompt file, not executable code, testing means (a) reading the final file to check coherence, and (b) running the skill with different flag combinations to confirm the argument parsing and routing logic works.

- [ ] **Step 7.1: Read the full updated skill file**

  Read `.claude/commands/validate-matches.md` from top to bottom. Confirm:
  - Step 1 references `ACTIVE_FIELDS`, `MODE`, `MODEL` consistently throughout later steps
  - No step still says "all four fields" unconditionally without gating on `ACTIVE_FIELDS`
  - No step still says "write both output files" without the MODE gate
  - Step numbering (1–6) is intact

- [ ] **Step 7.2: Check that existing 2026-02 matched file is available**

  ```bash
  ls data/matched/2026-02.json
  ```
  Expected: file exists (if not, use whatever month is available).

- [ ] **Step 7.3: Run propose-only soap smoke test**

  Run:
  ```
  /validate-matches --month 2026-02 --field soap --mode propose --model haiku
  ```

  Confirm in the output:
  - Startup block shows `Fields: soap | Mode: propose | Model: haiku`
  - Counts show `—` for razor, blade, brush
  - No "writing verified file" output
  - `data/proposed/2026-02.json` is updated; `data/verified/2026-02.json` is untouched (check `processed_at` timestamp)

- [ ] **Step 7.4: Run verify-only all-fields smoke test**

  Run:
  ```
  /validate-matches --month 2026-02 --mode verify
  ```

  Confirm:
  - Startup block shows `Fields: all | Mode: verify | Model: sonnet`
  - All four field counts are shown
  - `data/verified/2026-02.json` is updated
  - `data/proposed/2026-02.json` is untouched

- [ ] **Step 7.5: Test partial merge preserves non-active fields**

  This is the most important correctness test. The scenario: a full run already produced `data/verified/2026-02.json` with entries for all four fields. A field-scoped re-run must preserve the other fields' entries.

  First, note how many verifications currently exist per field:
  ```bash
  python3 -c "
  import json
  data = json.load(open('data/verified/2026-02.json'))
  from collections import Counter
  c = Counter(v['field'] for v in data['verifications'])
  print(dict(c))
  "
  ```

  Then run a soap-only verify:
  ```
  /validate-matches --month 2026-02 --field soap --mode verify
  ```

  Then re-check per-field counts:
  ```bash
  python3 -c "
  import json
  data = json.load(open('data/verified/2026-02.json'))
  from collections import Counter
  c = Counter(v['field'] for v in data['verifications'])
  print(dict(c))
  "
  ```

  Confirm: razor, blade, brush counts are identical to before the re-run. Soap count may differ (it was re-verified).

- [ ] **Step 7.6: Run multi-field comma-separated smoke test**

  Run:
  ```
  /validate-matches --month 2026-02 --field soap,razor --mode verify
  ```

  Confirm in output:
  - Startup block shows `Fields: soap, razor`
  - Counts show actual numbers for soap and razor; `—` for blade and brush

- [ ] **Step 7.7: Run with `--model opus`**

  Run:
  ```
  /validate-matches --month 2026-02 --field razor --mode verify --model opus
  ```

  Confirm startup block shows `Model: opus` and the run completes without error.

- [ ] **Step 7.8: Run invalid flag smoke test**

  Run:
  ```
  /validate-matches --month 2026-02 --field badvalue
  ```

  Confirm: error message is printed listing valid field values, skill stops.

- [ ] **Step 7.9: Final commit if any fixes were needed**

  If Steps 7.1–7.8 revealed issues, fix them and commit:
  ```bash
  git add .claude/commands/validate-matches.md
  git commit -m "fix(validate-matches): smoke test corrections"
  ```
