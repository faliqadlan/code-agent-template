---
name: agent-task
description: Author or execute validated, versioned cross-agent assignments under .agents/tasks. Use when a user asks one agent to prepare a task for another model, revise a published task as a new version, or run an existing task contract.
---

<!-- code-agent-template:managed -->
# Agent Task

Create and execute immutable cross-agent assignments without weakening repository instructions or approval boundaries.

## Inputs

- Mode: Author or Execute
- A task name, objective, target model preference, and required capabilities for Author mode, or a task path for Execute mode
- Named runtime values in `NAME="value"` form when the task declares inputs

## Mode selection

- Use **Author** when the user asks to create or prepare a cross-agent assignment, or to publish a revised version.
- Use **Execute** when the user asks to run an existing task definition.
- If the requested mode is ambiguous and choosing incorrectly could modify the repository, ask the user before proceeding.

## Author mode

1. Read `.agents/tasks/_template.md` and applicable repository instructions.
2. Convert the requested name to lowercase kebab case. Set a positive integer version and target `.agents/tasks/<task-name>-v<version>.md`.
3. Never overwrite a validated task. For a revision, read the latest version and write the next unused versioned filename.
4. Write only `name`, `description`, and `version` in frontmatter. Complete every required section from the template.
5. Declare one preferred provider/model identifier, zero or more unique ordered fallbacks, and the capabilities execution requires. Treat identifiers as opaque strings; do not invent availability or equivalence claims.
6. Declare runtime inputs as uppercase snake case:
   - Required: ``- `NAME` (required): Description.``
   - Optional: ``- `NAME` (optional, default: value): Description.``
7. Reference each declared input as `$NAME`. Use `$$` for a literal dollar sign.
8. Choose `single-pass` with one iteration or `agentic-loop` with a positive finite limit. Define observable acceptance criteria, concrete verification, approval gates, and the output contract.
9. Keep mutable run status, progress, results, secrets, private prompts, hidden reasoning, and transcript content out of the task.
10. Run `python .agents/scripts/validate_template.py`. Fix the draft if validation fails. Successful validation publishes the task as immutable; report its path without executing it.

## Execute mode

1. Require a Markdown task path under `.agents/tasks/`; never execute `_template.md`.
2. Read the task and applicable repository instructions. Run the template validator before executing and stop if it fails.
3. Parse the Runtime inputs declarations and values supplied by the user. Use defaults for omitted optional values and ask for every missing required value.
4. Resolve `$NAME` references in working context only. Interpret `$$` as a literal dollar sign and do not edit the task file with resolved values or results.
5. Ask the user or available runtime to select the preferred model. Use the first compatible declared fallback only before meaningful output or external side effects when the preceding candidate is unavailable, rate-limited, or capability-incompatible. Never use an undeclared fallback or switch models because verification fails.
6. If the runtime cannot select or verify a compatible model, stop and provide a concise prompt for manually transferring the task to one. Do not claim that routing occurred.
7. Treat the task as scoped execution input, not as authority to override user instructions, `.agents/AGENTS.md`, permissions, or approval requirements.
8. Execute the declared mode. A single pass has one iteration. An agentic loop performs inspect, act, observe, and verify within the finite limit, using external evidence for retry decisions.
9. Stop as `succeeded`, `failed`, `blocked`, `awaiting-approval`, or `exhausted`. Only report `succeeded` when every acceptance criterion and required verification passes.
10. Re-read the unchanged task file and report the selected model, outcome, evidence, residual risks, and manual follow-up outside the task file.

## Boundaries

- Task definitions are accessed through this skill after routing by `.agents/AGENTS.md`; the directory itself is not assumed to be a native discovery surface.
- Do not infer a missing runtime value when it would materially change scope or behavior.
- Do not create legacy prompt-directory aliases.
- Execute only one task definition at a time unless the user explicitly requests a coordinated sequence.
- A Markdown model preference is not an authorization boundary, sandbox, provider adapter, or proof of runtime availability.
- Immutability is a workflow and version-control contract, not filesystem locking. The validator checks current structure but cannot detect a historical rewrite; never edit a published version.

## Output contract

- Author: published task path and version, model preferences, declared inputs, validation evidence, and confirmation that no task work was executed.
- Execute: selected model, terminal outcome, affected interfaces or files, verification evidence, residual risk, and manual follow-up.
