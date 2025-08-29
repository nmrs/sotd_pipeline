---
description:
globs:
alwaysApply: false
---
### react-test-analysis-and-remediation

**Instruction:**  
Use the Makefile targets to run and remediate React test failures. Do **not** assume failures are test bugs or code bugs. Use Git history to decide whether behavior changes were intentional (tests should evolve) or unintentional (regressions/incomplete work). Work in logical buckets, keep a running checklist, commit after each bucket, and report progress frequently.

---

## 0) Commands & Environment (from Makefile)
- Primary React suite: `make test-react` (manages servers via `restart-servers` and stops after)
- Variants:
  - Watch: `make test-react-watch`
  - Coverage: `make test-react-coverage`
  - Unit-only: `make test-react-unit`
  - Integration focus: `make test-react-integration`
  - API focus: `make test-react-api`
- E2E (only when needed/after unit passes or to verify end-to-end): `make test-e2e` (and variants like `make test-e2e-quick`, `make test-e2e-all`)
- Server helpers: `make start-servers`, `make stop-servers`, `make restart-servers`, `make server-status`

> Always rely on these Makefile targets for consistent server lifecycle.

---

## 1) Run Tests & Capture Output
1. Execute:
   - `make restart-servers`
   - `make test-react`
2. Save raw logs to `artifacts/react-test-output-<timestamp>.log` (create the `artifacts/` folder if missing).
3. Extract failing test names, file paths, and error snippets.

> Do **not** assume the failure source; simply collect data.

---

## 2) Categorize Each Failure
Assign a **primary** category (add a secondary tag if helpful):

- **Test Drift** — Implementation intentionally evolved; tests weren’t updated.
- **Regression** — Previously working behavior unintentionally broke.
- **Incomplete Implementation** — Feature/contract partially implemented; tests ahead of code.
- **Environment/Dependency** — Node/JS-DOM, polyfills, tsconfig/babel/jest config, peer deps.
- **Flaky/Timing** — RTL async (`findBy*`, `waitFor`, `userEvent`), `act()` warnings, timers, races.
- **Selector/Fixture (E2E or Integration)** — Brittle test selectors, changed data/setup.

Produce a **Categorization Table** (Markdown) with:
- test file
- test name / `describe/it`
- error snippet (short)
- category (primary)
- suspected root cause
- notes

Write this table to `TEST_REMEDIATION_TODO.md` under a “Categorization” section.

---

## 3) Confirm with Git History (No Guessing)
For each failing spec, inspect related files:

- `git log --decorate --oneline -- <files>`
- `git blame <file>`
- `git show <commit>`
- `git log -p -- <files>`

Answer:
- Was the implementation **intentionally** changed? → **Test Drift** (tests should be updated or retired).
- Was behavior **accidentally** changed? → **Regression** (fix code to restore intended behavior).
- Was the feature **never finished**? → **Incomplete Implementation** (complete or re-scope).

Record the rationale and relevant commit hashes/PRs in the table.

---

## 4) Group Work into Logical Buckets
Group by feature/module or by root cause. Example buckets:
- `Auth`, `Search`, `Cart`, etc.
- Cross-cutting: RTL async cleanup, i18n keys, date/time mocks, API clients.
- Config/env: JSDOM polyfills, tsconfig/jest/vite/babel.
- E2E selectors/fixtures.

For each bucket, list affected tests/files and a short plan:
- **Plan**: code fix vs test update vs config/env changes
- **Validation command**: targeted `make` targets (unit/integration), or `npm test -- --testPathPattern=<pattern>` from `webui` if needed
- **Risk/rollback**: note any risky changes

Append buckets to `TEST_REMEDIATION_TODO.md` with checkboxes.

---

## 5) Execute Iteratively (One Bucket at a Time)
For the active bucket:

1) **Propose minimal changes** (avoid broad refactors).  
2) **Implement**:
   - For RTL/Jest: fix async (`await findBy*`, `waitFor`), ensure `userEvent` usage, clean timers, stable queries (`getByRole` with `name`), test ids only if necessary.
   - For Test Drift: update expectations/messages/selectors; if a test no longer reflects product behavior, deprecate/retire with justification.
   - For Regression: fix code with minimal diff that restores intended contract.
   - For Incomplete: finish feature slice or reduce scope; update tests accordingly.
   - For Env/Config: adjust `jest`/`vitest` setup, polyfills, `setupTests.ts`, module mocks, tsconfig/babel/vite as indicated.
3) **Validate quickly**:
   - `make restart-servers`
   - Run the narrowest test set (e.g., `make test-react-unit` or `cd webui && npm test -- --testPathPattern="<module|file>"`)
4) **Update checklist**: mark the bucket tasks done in `TEST_REMEDIATION_TODO.md`.
5) **Commit**:
   - One atomic commit per bucket.
   - Message format:
     ```
     test: remediate <BucketName> — <primary category>

     Summary:
     - Files:
     - Category:
     - Rationale (git history):
     - Notes:
     ```
6) **Report progress** to the user:
   - Bucket status, impacted tests, what changed, validation result, commit hash.

---

## 6) Handle E2E Only If Needed
If failures implicate end-to-end flows or selectors:
- Use `make test-e2e-quick` first; then `make test-e2e` or `make test-e2e-all` if necessary.
- Stabilize selectors (prefer `getByRole`/accessible names or explicit `data-testid` for non-semantic nodes).
- Ensure consistent test data/fixtures and server state.

---

## 7) Final Verification
- `make test-react-coverage` (or `make test-react`) to ensure green React tests.
- If E2E used, run `make test-e2e-quick` (or full as needed).
- Update `TEST_REMEDIATION_TODO.md` with a **Final Summary**:
  - Buckets completed
  - Categories counts (Drift/Regression/Incomplete/Env/Flaky/Selector)
  - Links to commits
- Commit the updated TODO if changed.

---

## Constraints
- Do not delete or drastically alter tests without explicit justification captured in the TODO (and preferably user confirmation).
- Keep diffs small and readable; avoid sweeping refactors.
- Prefer test stability and accessibility-aligned queries over brittle DOM details.
- Use repository Makefile targets for consistent server lifecycle.

**Outputs**
- `artifacts/react-test-output-<timestamp>.log`
- `TEST_REMEDIATION_TODO.md` (checklists + categorization + buckets + progress)
- Frequent progress reports (after each bucket)
- Atomic commits per bucket