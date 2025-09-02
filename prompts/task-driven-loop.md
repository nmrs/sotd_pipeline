---
description:
globs:
alwaysApply: false
---
### task-driven-loop
**Use when**: Implementing features with a task-driven development approach.

**Instructions (tracking required)**
- At the start of each new **plan task**, print the loop summary and the checklist template below with all boxes empty (☐).
- As each item completes, replace ☐ with ☑, reprint the checklist, and show which step is currently in progress.
- Continue until all steps are ☑.
- At the end of the loop, print the **Structured Progress Report** (see Step 6).
- Do not skip or reorder steps.
- Reset to empty boxes at the beginning of each new **plan task**.
- If you ever get lost, **reset to the Checklist Template** and restart from Step 1.
- **Do not silently handle failures, gaps, or new work items.** Always communicate them to the user and record them in the implementation plan.
- The implementation plan is the single source of truth for feature tasks.
- **Do not modify yaml files without explicity permission from the user.**

**Loop Summary:**  
Pick task → Update/Review plan → Run quality checks → Capture/record new work → Reconcile plan → Commit → Report progress → Move to next task

**Workflow Checklist (with progress tracking):**  
1. ☐ Pick the next **plan task** from the implementation plan.  
2. ☐ Update and review the implementation plan.  
2a. ☐ Re-read the plan top to bottom.  
2b. ☐ If not internally consistent or complete, update it and restart 2a–2b (do not proceed until consistent and complete).  
3. ☐ If new work items are discovered — such as failing tests, architectural direction changes, gaps in requirements, or other tasks we had not considered — communicate them to the user and **immediately record** them as new tasks in the implementation plan. **Do not skip upating the plan with the new tasks.**
4. ☐ Reconcile the implementation plan after recording new tasks.  
4a. ☐ Re-read the plan top to bottom.  
4b. ☐ If not internally consistent or complete, update it and restart 4a–4b (do not proceed until consistent and complete).  
5. ☐ If new work items are discovered — such as failing tests, architectural direction changes, gaps in requirements, or other tasks we had not considered — communicate them to the user and **immediately record** them as new tasks in the implementation plan. **Do not skip upating the plan with the new tasks.**
6. ☐ Commit changes with a clear message summarizing the task (per `.cursor/rules/git-and-cleanup.mdc`).  
7. ☐ Report progress to the user using the structured format below.  
   - **Task Completed:** …  
   - **Plan Updates:** …  
   - **New Tasks Discovered:** …  
   *(If none, print “None” explicitly)*  
8. ☐ Move to the next **plan task**.  

**Checklist Template (reset to this at the start of each new plan task, or if you ever get lost):**  
1. ☐ Pick the next **plan task** from the implementation plan.  
2. ☐ Update and review the implementation plan.  
2a. ☐ Re-read the plan top to bottom.  
2b. ☐ If not internally consistent or complete, update it and restart 2a–2b (do not proceed until consistent and complete).  
3. ☐ If new work items are discovered — such as failing tests, architectural direction changes, gaps in requirements, or other tasks we had not considered — communicate them to the user and **immediately record** them as new tasks in the implementation plan. **Do not skip upating the plan with the new tasks.**
4. ☐ Reconcile the implementation plan after recording new tasks.  
4a. ☐ Re-read the plan top to bottom.  
4b. ☐ If not internally consistent or complete, update it and restart 4a–4b (do not proceed until consistent and complete).  
5. ☐ If new work items are discovered — such as failing tests, architectural direction changes, gaps in requirements, or other tasks we had not considered — communicate them to the user and **immediately record** them as new tasks in the implementation plan. **Do not skip upating the plan with the new tasks.**
6. ☐ Commit changes with a clear message summarizing the task (per `.cursor/rules/git-and-cleanup.mdc`).  
7. ☐ Report progress to the user using the structured format below.  
   - **Task Completed:** …  
   - **Plan Updates:** …  
   - **New Tasks Discovered:** …  
   *(If none, print “None” explicitly)*  
8. ☐ Move to the next **plan task**.  
