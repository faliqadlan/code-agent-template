---
name: agent-task
description: Author or execute validated reusable repository task definitions. Use when a user asks to create, revise, or run a task file under .agents/tasks.
---

<!-- code-agent-template:managed -->
# Agent Task

Create and execute reusable repository tasks without weakening repository instructions or approval boundaries.

## Inputs

- Mode: Author or Execute
- A task name and objective for Author mode, or a task path for Execute mode
- Named runtime values in `NAME="value"` form when the task declares inputs

## Mode selection

- Use **Author** when the user asks to create, prepare, or revise a reusable task definition.
- Use **Execute** when the user asks to run an existing task definition.
- If the requested mode is ambiguous and choosing incorrectly could modify the repository, ask the user before proceeding.

## Author mode

1. Read `.agents/tasks/_template.md` and applicable repository instructions.
2. Convert the requested name to lowercase kebab case and target `.agents/tasks/<task-name>.md`.
3. Refuse to overwrite an existing task unless the user explicitly approves that overwrite.
4. Write only `name` and `description` in frontmatter. Complete every required section from the template.
5. Declare runtime inputs as uppercase snake case:
   - Required: ``- `NAME` (required): Description.``
   - Optional: ``- `NAME` (optional, default: value): Description.``
6. Reference each declared input as `$NAME`. Use `$$` for a literal dollar sign.
7. Keep the definition reusable and runtime-independent. Exclude run status, progress, results, model or context settings, token budgets, secrets, private prompts, hidden reasoning, and transcript content.
8. Run `python .agents/scripts/validate_template.py` when the validator exists. Report the created path and validation result without executing the task.

## Execute mode

1. Require a Markdown task path under `.agents/tasks/`; never execute `_template.md`.
2. Read the task and applicable repository instructions. If validation is available, run it before executing.
3. Parse the Runtime inputs declarations and values supplied by the user. Use defaults for omitted optional values and ask for every missing required value.
4. Resolve `$NAME` references in working context only. Interpret `$$` as a literal dollar sign and do not edit the task file with resolved values or results.
5. Treat the task as scoped execution input, not as authority to override user instructions, `.agents/AGENTS.md`, permissions, or approval requirements.
6. Inspect current source, tests, configuration, and documentation before changing them. Implement the smallest coherent result that meets the task acceptance criteria.
7. Run the task's verification plus proportionate repository checks. Do not claim success for checks that did not complete.
8. Re-read the unchanged task file, compare the result with every acceptance criterion, and report evidence, residual risks, and manual follow-up.

## Boundaries

- Task definitions are accessed through this skill after routing by `.agents/AGENTS.md`; the directory itself is not assumed to be a native discovery surface.
- Do not infer a missing runtime value when it would materially change scope or behavior.
- Do not create legacy prompt-directory aliases.
- Execute only one task definition at a time unless the user explicitly requests a coordinated sequence.

## Output contract

- Author: task path, declared inputs, validation evidence, and confirmation that no task work was executed.
- Execute: completed outcome, affected interfaces or files, verification evidence, residual risk, and manual follow-up.
