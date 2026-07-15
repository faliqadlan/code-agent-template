<!-- code-agent-template:managed -->
# Task Specification: Reusable Cross-Agent Tasks

**Status:** Complete  
**Last updated:** 2026-07-15

## Goal

Provide a repository-scoped task library that lets Codex author reusable task definitions and lets Antigravity execute them with runtime inputs through one shared skill contract.

## Non-goals

- Do not restore or alias the legacy dot-ai prompt directory.
- Do not store execution state, model selection, context-window settings, token budgets, secrets, private prompts, hidden reasoning, or transcripts in task files.
- Do not make task files a substitute for user approval on high-risk work.

## Inputs and evidence

- User request: implement the approved Reusable Cross-Agent Tasks plan.
- Relevant files: `AGENTS.md`, `README.md`, `.agents/skills/`, `.agents/workflows/`, and `tests/validate_template.py`.
- Existing behavior: the template validates ten mirrored skills and Antigravity workflows, but has no repository task-definition contract.

## Constraints

- Compatibility: preserve Codex skill discovery and Antigravity workflow discovery under `.agents/`.
- Security and permissions: task execution must retain all repository instruction and approval boundaries.
- Performance or operational limits: use only the Python standard library for validation and tests.

## Acceptance criteria

- [x] `.agents/tasks/_template.md` defines the approved reusable task format and runtime-input syntax.
- [x] The `agent-task` skill supports explicit Author and Execute modes without modifying task files during execution.
- [x] Antigravity exposes the matching `/agent-task` workflow.
- [x] Repository routing and usage documentation distinguish reusable tasks from approved implementation specifications.
- [x] Validation covers task filenames, metadata, sections, inputs, placeholders, legacy paths, and runtime model settings.
- [x] Positive and negative standard-library tests pass with the full template validator.

## Implementation approach

Add a flat Markdown task library with a strict, machine-checkable contract. Route both authoring and execution through one focused skill, mirror it with an Antigravity workflow, and extend the existing validator with a pure task-file validation function that can be tested independently.

## Affected interfaces

- New repository interface: `.agents/tasks/<task-name>.md`.
- New skill invocation: `$agent-task` in Codex.
- New workflow invocation: `/agent-task` in Antigravity.
- Updated validation output: eleven mirrored skills and workflows.

## Verification plan

- Command or inspection: `python tests/validate_template.py`.
- Expected result: the complete template passes with eleven skills and workflows.
- Command or inspection: `python -m unittest discover -s tests -p "test_*.py"`.
- Expected result: all task-contract positive and negative cases pass.

## Decisions

- 2026-07-15: Store reusable task definitions under `.agents/tasks` and access them only through the shared skill/workflow contract.
- 2026-07-15: Supply per-run values as `NAME="value"`; keep model and context selection in the executing runtime.
- 2026-07-15: Keep task definitions unchanged during execution and require explicit approval independently of task content.

## Progress

- Completed: task contract, shared skill/workflow, documentation, validation, regression tests, and final verification.
- Remaining: None.
