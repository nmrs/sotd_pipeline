### python-test-todo-generator

**Instruction:**  
Run the full Python test suite via `make test`, analyze failures enough to produce a clean, actionable **to-do list**, save it, and stop. Do **not** fix anything, stage files, or run follow-up tests.

1. **Run Tests & Collect Failures**
   - Capture the full output of the test run, including stack traces and error summaries.

2. **Categorize Each Failure**
   For each failing test, assign one category:
   - **Test Drift** – Implementation intentionally evolved; test likely outdated.
   - **Regression** – Previously passed; now failing due to a defect.
   - **Incomplete Implementation** – Feature never fully implemented.
   - **Environment/Dependency Issue** – Env config, dependency, or tooling breakage.

3. **Lightweight History Check (Confirm Category)**
   - Skim relevant source and test file history to confirm whether changes were intentional vs. accidental.
   - Note the most relevant commit(s) or PR(s) if obvious; do not over-investigate.

4. **Group Failures**
   - Cluster into logical workgroups (by module/feature/root cause).
   - Name each group descriptively.

5. **Create the To-Do List**
   - Produce a single Markdown file with checkboxes, one section per group.
   - Each task should include:
     - **[ ] Task title** (succinct action)
     - **Category:** (one of the above)
     - **Failing tests:** (list test nodeids)
     - **Files involved:** (key src/test paths)
     - **Observed error:** (1–2 lines)
     - **Quick next steps:** (bullet list; concrete)
     - **Notes/links:** (optional commit/PR refs)
     - **Owner** and **ETA** fields (leave blank if unknown)

6. **Save and Stop**
   - Write the to-do to `TEST_SUITE_TODO.md` at the repo root **only if it does not already exist**.
   - Do **not** modify code or tests.   - Do **not** modify code or tests.
   - Do **not** push, commit, or trigger additional runs.

**Constraints:**
- Do not delete or alter tests/code.
- Keep investigation **lightweight**—just enough to yield a reliable category and next steps.

**Output Format (File Content):**
- **Header summary:** total tests, failures by category, number of groups.
- **Sections per group:** checklist items as specified above.
- End with a **“Next Runner Guidance”** note: suggested order to tackle groups (highest leverage/lowest effort first), and any env setup hints.

**Final Output:**
- Save only: `TEST_SUITE_TODO.md`.
- Print the absolute path to the saved file and a one-line summary: “To-do generated; X groups, Y tasks.”