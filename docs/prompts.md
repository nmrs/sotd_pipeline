Idea Honing
Ask me one question at a time so we can develop a thorough, step-by-step spec for this idea. Each question should build on my previous answers, and our end goal is to have a detailed specification I can hand off to a developer. Let’s do this iteratively and dig into every relevant detail. Remember, only one question at a time.

Here’s the idea:

<IDEA>


TDD Prompt
Draft a detailed, step-by-step blueprint for building this project. Then, once you have a solid plan, break it down into small, iterative chunks that build on each other. Look at these chunks and then go another round to break it into small steps. Review the results and make sure that the steps are small enough to be implemented safely with strong testing, but big enough to move the project forward. Iterate until you feel that the steps are right sized for this project.

From here you should have the foundation to provide a series of prompts for a code-generation LLM that will implement each step in a test-driven manner. Prioritize best practices, incremental progress, and early testing, ensuring no big jumps in complexity at any stage. Make sure that each prompt builds on the previous prompts, and ends with wiring things together. There should be no hanging or orphaned code that isn't integrated into a previous step.

Make sure and separate each prompt section. Use markdown. Each prompt should be tagged as text using code tags. The goal is to output prompts, but context, etc is important as well.

<SPEC>


Non-TDD Prompt
Draft a detailed, step-by-step blueprint for building this project. Then, once you have a solid plan, break it down into small, iterative chunks that build on each other. Look at these chunks and then go another round to break it into small steps. review the results and make sure that the steps are small enough to be implemented safely, but big enough to move the project forward. Iterate until you feel that the steps are right sized for this project.

From here you should have the foundation to provide a series of prompts for a code-generation LLM that will implement each step. Prioritize best practices, and incremental progress, ensuring no big jumps in complexity at any stage. Make sure that each prompt builds on the previous prompts, and ends with wiring things together. There should be no hanging or orphaned code that isn't integrated into a previous step.

Make sure and separate each prompt section. Use markdown. Each prompt should be tagged as text using code tags. The goal is to output prompts, but context, etc is important as well.

<SPEC>

TODO
Can you make a `todo.md` that I can use as a checklist? Be thorough.

You are the ChatGPT code editor. Review the error below. Read the file open in Work with Code and determine the best plan to resolve the issue. Generate a diff and apply it directly to the file open in Work with Code.

[error]

Task Driven TDD Loop
Proceed through the remaining tasks in the current step one at a time. After completing each task:
	1.	Update the implementation plan to reflect the completed work.
	2.	Run make format lint typecheck test.
	3.	If any errors or failures occur, fix them immediately.
	4.	Commit the changes with a clear message summarizing the task completed.


Tracked Implementation Development Process
Start with first unchecked item
1. Check off tasks: Mark each completed task with [x]
2. Update session notes: Add notes after each work session
3. Follow the workflow: Complete each chunk before moving to the next
4. Run quality checks: Use make format lint typecheck test after each chunk
5. Commit regularly: Commit changes with clear messages after each chunk. Commits should include updates to implementation plan.
The plan is designed to be self-contained and will help you track progress across multiple development sessions without losing your place. You can start with the first chunk and work through the plan systematically, checking off tasks as you complete them.