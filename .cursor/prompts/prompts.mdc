---
globs: plans/*.md,plans/*.mdc,plans/**/*.md,plans/**/*.mdc
alwaysApply: false

## 🚀 Development Workflows

### Tracked Implementation Development Process
**Use when**: Working through a multi-session implementation plan systematically.

**Purpose**: These are instructions to proceed carefully through an implementation plan without causing major errors and ensuring that incremental progress is tracked. The plan is designed to be self-contained and will help you track progress across multiple development sessions without losing your place.

**Process**:
1. Start with first unchecked item
2. Follow the workflow: Complete each chunk before moving to the next
3. **Skip quality checks during development** (run only before commits)
4. Check off tasks: Mark each completed task in the implementation plan document with [x] and save the file
5. Update session notes: Add notes after each work session
6. Commit regularly: Commit changes with clear messages after each chunk. Commits should include updates to implementation plan.
7. **Run quality checks before commits**: Use "make format lint typecheck test" before committing, fixing any errors that result
8. Proceed *until context limit is reached*

---
## 📋 Project Planning Prompts



### Non-TDD Project Planning  
**Use when**: Tackling tasks that don’t require test-first development, such as lint cleanup, dependency updates, refactoring, or fixing failing tests.  
**Persona**: You are a Principal Engineer at a software company. You care deeply about clean, maintainable, DRY code that’s easy to read and evolve. You emphasize systematic progress, minimal regressions, and clear, actionable steps.  
**Goal**: Produce an executable project blueprint and a sequence of self-contained prompts—structured for use by a code-generation LLM and ready to save as an `.mdc` plan under `/plans`.  

```
Draft a clear, step-by-step blueprint for completing this task without TDD.

Start with a high-level overview, then iteratively break it down into smaller, incremental steps. Each step should:
- Build logically on the previous one
- Clearly describe the code cleanup, fixes, or improvements
- Avoid large, monolithic changes that are risky or hard to verify
- Be small enough to implement safely, but large enough to show meaningful progress

Once the plan is decomposed into steps:
- For each step, generate a separate code-generation prompt formatted as an MDC section
- Each prompt should be enclosed in fenced code blocks using the `text` tag
- Include just enough context from the previous steps to ensure continuity

Structure the final output as an `.mdc` document with:
- 📘 A short project summary
- 🧩 A list of component steps
- 🔁 One `text`-tagged prompt block per step
- 🧠 Your own critical analysis of the prompt sequence and structure

After drafting, review the plan:
- Check for redundant, ambiguous, or overly large steps
- Ensure each prompt produces coherent, incremental progress
- Refine the plan as needed

Repeat until the plan is lean, safe, and buildable via codegen prompts with no dangling pieces.
```

<!-- 
### Non-TDD Project Planning
**Use when**: Starting a new feature without strict TDD requirements.

```
Draft a detailed, step-by-step blueprint for building this project. Then, once you have a solid plan, break it down into small, iterative chunks that build on each other. Look at these chunks and then go another round to break it into small steps. Review the results and make sure that the steps are small enough to be implemented safely, but big enough to move the project forward. Iterate until you feel that the steps are right sized for this project.

From here you should have the foundation to provide a series of prompts for a code-generation LLM that will implement each step. Prioritize best practices, and incremental progress, ensuring no big jumps in complexity at any stage. Make sure that each prompt builds on the previous prompts, and ends with wiring things together. There should be no hanging or orphaned code that isn't integrated into a previous step.

Make sure and separate each prompt section. Use markdown. Each prompt should be tagged as text using code tags. The goal is to output prompts, but context, etc is important as well.
``` 
-->

---

## 📊 Data Analysis Prompts

### SOTD Monthly Observations Prompt
**Use when**: Generating insights and observations from monthly SOTD hardware reports.

```
Act as a **snark-drenched yet insightful data analyst** who's been elbow-deep in shave logs and spreadsheet stubble. You've inhaled an entire timeline of Shave-of-the-Day reports and now clutch **the freshest month's tables**—complete with **Δ columns, Top Shavers, and maximum-blade-use brag sheets**.

## Mission

Unleash **10 + observations** that spotlight the latest month in the context of the full date range.

## Observation Fuel — Pick What Sparks Joy

1. **Biggest movers** – products or brands posting the largest ↑ or ↓ vs. last month.  
2. **Long-haul loyalty** – absurd cumulative counts or unbroken streaks (e.g., one Feather blade for 30 straight shaves).  
3. **Underdog comebacks** – gear that languished for months, then rocketed into the Top lists.  
4. **Brand defections** – makers that vanished—or rookies elbowing legacy names aside.  
5. **Cross-category chemistry** – razor × blade or brush × soap pairings that climbed together.  
6. **Persistent weirdness** – statistical outliers that refuse to behave.  
7. **Top Shavers shout-outs** – name-drop or gently roast the heroes atop the leaderboard.  
8. **Blade iron-men** – highest single-blade use counts (edge-of-sanity milestones).  
9. **Leaderboard jockeying** – who muscled into the Top 10, who fell out of the Top 3, or which #1 and #3 swapped places like they're drafting at Eau Rouge.

*Each observation should riff on at least one of these. Or maybe not. Maybe you're feeling crazy and want to highlight something totally unexpected.*

*Prioritize 

## Tone Guide

- **Half of the observations**: *"Jerry Seinfeld writing for BuzzFeed."*  
  - Keep it smart, punchy, and data-anchored.  
  - Shamelessly name-check the community where possible.  
  - Sprinkle metaphors involving boldness and questionable life choices—**but only where they sharpen the gag**.  
  - End each observation with a wink, sigh, or raised eyebrow.  
  - Humblebrag numbers sparingly, story-arc numbers generously.

- **Half of the observations**: *Play the straight-man.*  
  - Just the numbers here.  
  - "This happened. It was remarkable, so I'm remarking on it."

  > **Remember:** If forced to choose, pick the angle that delivers the most **noteworthy, surprising, or decision-driving finding**—then season with humor.
```

---

## 🛠️ Utility Prompts

### TODO Checklist Generation
**Use when**: Need a comprehensive checklist for a task or feature.

```
Can you make a `todo.md` that I can use as a checklist? Be thorough.
```

### Error Resolution
**Use when**: Need to fix a specific error in the codebase.

```
You are the ChatGPT code editor. Review the error below. Read the file open in Work with Code and determine the best plan to resolve the issue. Generate a diff and apply it directly to the file open in Work with Code.

[error]
```

### Session Continuation
**Use when**: Continuing work in a new chat session.

```
Use the Tracked Implementation Development Process in @prompts.mdc to implement the @aggregate_implementation_plan.mdc using @aggregate_phase_spec.md and @sotd-pipeline-core.mdc for reference. Perform multiple tasks before asking for user feedback or permission to continue.
```

---

## 📝 Usage Examples

### Starting a New Feature
```
Follow the TDD Project Planning prompt in @prompts.mdc to plan the new feature.
```

### Working Through Implementation
```
Follow the Tracked Implementation Development Process in @prompts.mdc to implement the current phase.
```

### Continuing in New Session
```
Use the Session Continuation prompt in @prompts.mdc to continue the current work.
```

### Fixing Errors
```
Use the Error Resolution prompt in @prompts.mdc to fix the current error.
```

### Generating Observations
```
Use the SOTD Monthly Observations Prompt in @prompts.mdc to analyze the latest monthly report.
```

---

## 🔄 Quick Reference

| Scenario | Use This Prompt |
|----------|----------------|
| New feature with TDD | TDD Project Planning |
| New feature without TDD | Non-TDD Project Planning |
| Multi-session implementation | Tracked Implementation Development Process |
| Error fixing | Error Resolution |
| Session continuation | Session Continuation |
| Monthly report analysis | SOTD Monthly Observations Prompt |
| Checklist generation | TODO Checklist Generation |
| Idea development | Idea Honing |
| Focused discussion | Focused Discussion Rule |

---


<!-- '''
use ### Tracked Implementation Development Process to proceed with @plan_webui_lint_issues_fix_2025-07-25.mdc 

run all react tests and lint and build to validate that there are no remaining issues. Update plan status and add additional steps (or modify additional steps) if issues are found. Then use the process to continue the implementation if necessary
''' -->

### python-test-triage-analysis-only

**Instruction:**  
Run the full Python test suite and identify all failing tests. For each failure:  

1. **Locate and review** all relevant source and test files involved in the failure.  
2. **Inspect the Git history** of these files to understand the context and recent changes.  
3. **Classify the failure** as one of the following:  
   - **Test drift** – the test is outdated compared to current intended behavior.  
   - **Code regression** – functionality broke after previously working.  
   - **Incomplete implementation** – the feature was never fully implemented.  
4. **Document your reasoning** for the classification.  
5. **Propose a clear, actionable resolution plan** for each issue, including recommended code or test changes.  

**Important:**  
Do **not** modify any files before presenting your analysis and plan to the user.


---

### python-test-triage-analysis-only (JSON artifact)

**Goal:**  
Run the full Python test suite, save results in a structured JSON file, and analyze all failures.  
The JSON artifact allows re-analysis without re-running tests, keeping results outside chat context.

---

## Artifact location & naming
- Run dir: `.reports/runs/<YYYYMMDD-HHMMSS>/`
- Symlink/text pointer to latest: `.reports/latest`
- Main file: `.reports/latest/results.json`
- Additional files:
  - `pytest.log` — full stdout/stderr from the run
  - `failure_inventory.jsonl` — normalized list of failing tests
  - `failure_groups.json` — grouped root causes with classification, confidence, and evidence
  - `triage.md` / `triage.json` — human and machine-readable summaries
  - `pip-freeze.txt` — dependency snapshot
  - `run_meta.json` — run metadata (start/end, python version, branch, commit)

---

## Steps (analysis-only)
1) **Preflight**
   - Ensure `.reports/` exists.
   - Capture `python --version`, `pip freeze > .reports/runs/<ts>/pip-freeze.txt`.
   - Record `git rev-parse --abbrev-ref HEAD` and `git rev-parse --short HEAD` into run_meta.json.

2) **Run tests (or reuse)**
   - If `.reports/latest/results.json` exists and is < 30 min old, reuse it.
   - Else run:
     ```bash
     mkdir -p .reports/runs/<ts>
     ln -fnsv runs/<ts> .reports/latest
     PYTHONPATH=. pytest tests/ -q -ra \
       --json-report \
       --json-report-file=.reports/latest/results.json \
       2>&1 | tee .reports/latest/pytest.log
     ```
     *(Requires `pip install pytest-json-report`.)*

3) **Inventory failures**
   - Parse `.reports/latest/results.json` to create `failure_inventory.jsonl`.
   - Each JSON line: nodeid, error_type, top_project_frame, message_first_line, duration.

4) **Group & classify**
   - Build `failure_groups.json` with grouped failures and:
     - category: `test_drift`, `regression`, `incomplete`, `flaky`, `env`, or `fixture`
     - confidence: 0–1
     - tests[], files[], evidence (blame, commits, stack snippet)
   - Classification heuristics:
     - **Test drift**: API renamed or semantics changed intentionally; test not updated.
     - **Regression**: unintended change broke intended behavior.
     - **Incomplete**: feature never fully implemented.
     - **Flaky**: intermittent failures, time/state-dependent.
     - **Env**: dependency or platform mismatch.
     - **Fixture**: faulty test setup/teardown.

5) **Plans (no edits)**
   - For each group, propose a minimal resolution plan:
     - If drift: update expectations/renames/fixtures.
     - If regression: smallest code fix + regression test.
     - If incomplete: define acceptance criteria and tasks.
     - If flaky: seed RNG/freeze time/fix teardown.
     - If env: pin/bump dependency or add skip guard.
     - If fixture: stabilize setup/teardown.

6) **Human & machine summaries**
   - `triage.md`: run meta, counts per category, table of groups, checklist.
   - `triage.json`: structured equivalent.

7) **Console output**
   - Print path to `.reports/latest/results.json`, counts per category, and brief summary.

---

## Important constraints
- **No file modifications** — analysis only.
- Always write new artifacts to `.reports/runs/<ts>/`, update `.reports/latest`.
- Prefer absolute file paths in JSON for reproducibility.
- If parsing fails, still write partial results and note limitations in triage.md.

---


### python-test-triage-confirm-before-fixing

**Instruction:**  
Run the full Python test suite and identify all failing tests. Then:  

1. **Group failures** by root cause (shared code paths, dependencies, or similar error messages).  
2. For each group:  
   - **Review sources & tests** involved.  
   - **Inspect Git history** to decide if the cause is test drift, regression, or incomplete implementation.  
   - **Document a concise diagnosis** and **proposed fix plan** (code changes, test updates, refactors, docs).  
3. **Validate with the user before making any edits:**  
   - If any part of the diagnosis or plan is uncertain, explicitly call that out.  
   - Present a brief, numbered checklist of changes you intend to make.  
   - **Wait for user approval** before touching the repo.  
4. After approval, **apply fixes incrementally**, re-running tests after each change to confirm resolution.  
5. **Summarize outcomes** and any follow-ups (tech debt, flaky tests, missing coverage).  

**Important:**  
- No file modifications until the user confirms the plan.  
- Keep changes minimal and scoped to resolving the failures.


---

### python-test-triage-autonomous

**Instruction:**  
Run the full Python test suite and identify all failing tests. Then:  

1. **Group failures** by root cause (shared code paths, shared dependencies, or similar error messages).  
2. For each group:  
   - **Review all relevant source and test files**.  
   - **Inspect the Git history** to determine if the cause is test drift, code regression, or incomplete implementation.  
   - **Document the classification** and reasoning.  
   - **If classification is uncertain or evidence is inconclusive, pause and validate your reasoning with the user before proceeding.**  
3. **Prioritize issues** by:  
   - Number of dependent tests or modules affected.  
   - Criticality of functionality impacted.  
4. **Draft a resolution plan** that includes:  
   - Recommended code changes.  
   - Recommended test updates or additions.  
   - Potential refactoring or documentation updates if relevant.  
5. **Apply the proposed fixes** in a safe, minimal-impact way, running the test suite after each change to confirm resolution.  
6. **Summarize the changes** made and remaining recommendations for the user.  

**Important:**  
- Always present your reasoning before applying changes.  
- Validate uncertain findings with the user before making modifications.  
- Limit changes to directly resolving test failures; do not make unrelated modifications.