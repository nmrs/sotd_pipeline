### python-test-suite-value-analysis (design smoke vs full sets, safely)

Goal:
Analyze the relative value of all Python tests and propose a safe split into SMOKE (fast, high-signal) and FULL (comprehensive) suites, plus a QUARANTINE list for flaky/low-signal tests. Do not delete or rewrite tests without approval. Persist findings to disk so we can iterate without rerunning everything.

---

Artifacts to produce (persisted)
- Base dir: .reports/test_value/<YYYYMMDD-HHMMSS>/ and symlink .reports/test_value/latest
- durations.log — stdout from a timing run
- results.json — pytest-json-report output (requires pytest-json-report)
- history_fail_rates.json — aggregated failure counts from past .reports/runs/*/results.json
- flaky_rates.json — per-test pass rate from a short re-run probe
- coverage.json — coverage.py JSON with dynamic_context = test_function
- unique_coverage.json — lines/branches uniquely covered by each test
- critical_paths.json — optional list of weighted globs for critical code
- test_scores.json — per-test metrics and value score + class
- smoke_tests.txt / full_tests.txt / quarantine_tests.txt — proposed sets (one nodeid per line)
- test_value_report.md / test_value_report.json — human/machine summaries

Note: Add .reports/ to .gitignore if not already.

---

Data collection (persisted)
1) Durations per test
   - Run:
     - PYTHONPATH=. pytest -q -ra -vv --durations=0 --maxfail=0 2>&1 | tee .reports/test_value/latest/durations.log
   - Optional (recommended): also capture structured results:
     - PYTHONPATH=. pytest -q -ra --json-report --json-report-file .reports/test_value/latest/results.json
     - Requires: pip install pytest-json-report

2) Historical failure rates (local history)
   - Scan .reports/runs/*/results.json; for each nodeid, count runs and failures.
   - Output history_fail_rates.json:
     - { "<nodeid>": { "runs": N, "fails": M, "fail_rate": M/N } }

3) Flakiness probe (quick)
   - Select top 200 slowest tests by duration (or all if small).
   - For each nodeid, run N=5:
     - PYTHONPATH=. pytest -q -k "<nodeid>" --maxfail=1 || true
   - Compute pass_rate; write flaky_rates.json:
     - { "<nodeid>": { "passes": p, "runs": 5, "pass_rate": p/5 } }

4) Coverage contribution (per test)
   - Ensure Coverage.py >= 5 and enable dynamic contexts:
     - Write or merge .coveragerc with:
       [run]
       dynamic_context = test_function
   - Run instrumented suite:
     - coverage erase
     - PYTHONPATH=. coverage run -m pytest -q -ra
     - coverage json -o .reports/test_value/latest/coverage.json
   - Compute unique_coverage.json:
     - For each nodeid, count lines (and optionally branches) covered only by that test.
     - Optionally record overlap ratios with other tests.

5) Critical paths (optional weighting)
   - If critical_paths.txt exists (one glob per line, e.g., sotd/match/**):
     - Read and expand to critical_paths.json.
   - Otherwise infer defaults like:
     - sotd/**
     - */match/**, */extract/**, */enrich/**, */aggregate/**
     - run.py

---

Scoring & classification
- Normalize metrics to [0,1] across the suite:
  - U = unique_coverage_lines (or branches)
  - F = historical_failure_rate (0 if no history)
  - C = critical_path_coverage share (lines in critical files / lines covered)
  - T = duration_penalty (normalized runtime; higher is worse)
  - K = flake_penalty (1 − pass_rate; higher is worse)

- Value score (tunable weights; start here):
  - value = 0.35*U + 0.25*F + 0.20*C - 0.15*T - 0.05*K
  - Clamp to [0,1]

- Classification:
  - SMOKE: value ≥ 0.55 AND duration ≤ P50 AND K ≤ 0.1
  - QUARANTINE: K > 0.3 OR (value < 0.25 AND duration ≥ P75 AND U == 0)
  - FULL: everything else

- Persist test_scores.json:
  - {
      "<nodeid>": {
        "value": 0.73,
        "U": 0.62, "F": 0.10, "C": 0.55, "T": 0.20, "K": 0.00,
        "duration_s": 0.84,
        "class": "SMOKE",
        "reasons": ["high unique coverage", "covers critical paths", "fast"]
      }
    }

- Write selection files:
  - smoke_tests.txt / full_tests.txt / quarantine_tests.txt (one nodeid per line)

---

Reports (human & machine)
- test_value_report.md includes:
  - Summary: total tests; SMOKE/FULL/QUARANTINE counts; estimated runtime for SMOKE vs FULL
  - Top 50 highest-value tests: nodeid | value | duration | unique lines | critical share
  - Top 50 slow but low-value (candidates for quarantine/refactor) with rationale bullets
  - Flakiest 25 tests with pass_rate and stabilization suggestions (seed RNG, freeze time, mock IO, cleanup)
  - Proposed Makefile/CI snippets to run SMOKE vs FULL

- test_value_report.json is the structured mirror.

---

Safety & change policy
- Do not delete, xfail, or tag tests automatically.
- Recommend only; ask for approval before:
  - Adding @pytest.mark.smoke to selected tests
  - Moving slow tests to a heavy/slow marker
  - Adjusting fixtures to stabilize flakiness
- Provide validation commands to ensure SMOKE still catches representative regressions.

---

Suggested Makefile/CI (proposed, not applied automatically)
- Makefile additions (non-destructive, read selection files):
  - test-smoke:
      PYTHONPATH=. pytest -q -ra -k "$$(tr '\n' '|' < .reports/test_value/latest/smoke_tests.txt)"
  - test-full:
      PYTHONPATH=. pytest -q -ra
  - test-quarantine:
      PYTHONPATH=. pytest -q -ra -k "$$(tr '\n' '|' < .reports/test_value/latest/quarantine_tests.txt)"

- GitHub Actions (example):
  - PRs: run test-smoke on push; optionally a 25% shard of FULL
  - Nightly/main: run FULL (optionally with quarantine on separate job)
  - Merge gate: SMOKE must pass; FULL shard + periodic FULL-all

---

Implementation steps (now)
1) Create artifact dir and update .reports/test_value/latest symlink.
2) Collect durations, history, flake probe, and coverage with dynamic_context.
3) Compute metrics and the value score per nodeid; classify into SMOKE/FULL/QUARANTINE.
4) Write artifacts: *json, *txt, test_value_report.md/json.
5) Print a concise summary: e.g., “Proposed SMOKE 320/2480 tests (12.9%); est runtime 6m vs 41m. Artifacts in .reports/test_value/latest/test_value_report.md”.
6) Offer optional diffs to tag smoke tests or add Makefile/CI entries; await approval.

---

Heuristics (consistent usage)
- Unique coverage: prefer lines; if available, incorporate branch coverage for higher fidelity.
- History: if no prior runs, set F = 0.
- Durations: compute suite-wide P50 and P75 thresholds for classification.
- Critical paths: weight coverage in critical files higher; defaults can be inferred if no list is provided.
- Flakiness: if probe shows intermittent failures or timeouts, set K accordingly (e.g., K ≥ 0.5 if pass_rate < 0.5).
- Redundancy flags: if two tests have ≥90% line overlap and similar assertions/messages, list as “likely redundant pair” in the report (do not auto-remove).

---

Constraints
- No file modifications without explicit approval.
- Prefer absolute paths in JSON artifacts.
- If any step fails (e.g., coverage not configured), continue with available signals and record limitations in the report.

Begin now:
1) Build the artifact directory and symlink.
2) Collect durations/history/flake/coverage.
3) Score and classify tests; write selections and reports.
4) Print a one-paragraph summary with artifact paths and suggested next steps.