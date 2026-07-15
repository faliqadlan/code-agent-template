---
name: task-name
description: Describe the reusable repository task and when an agent should execute it.
---

<!-- code-agent-template:managed -->
# Task: Task name

## Objective

State the observable result for `$TARGET`.

## Runtime inputs

- `TARGET` (required): Repository path, component, or other bounded execution target.

Use `None.` instead of input declarations when the task needs no runtime values. Reference each declared value with a single dollar sign followed by its input name, as shown by `$TARGET` above; write `$$` when the task needs a literal dollar sign.

## Context

- Identify the repository evidence the executing agent must inspect.
- Record facts that materially affect the requested result.

## Constraints

- List behavior that must remain unchanged.
- Keep runtime configuration outside the task definition.

## Execution requirements

1. Resolve every required runtime input before making changes.
2. Inspect current repository state and applicable instructions.
3. Perform only the work needed to satisfy the acceptance criteria.
4. Respect existing approval boundaries for high-risk actions.

## Acceptance criteria

- [ ] Define an observable result for `$TARGET`.

## Verification

- Command or inspection: Define the smallest relevant check.
- Expected result: State the successful outcome.

## Output

Report the outcome, changed interfaces or files, verification evidence, residual risks, and manual follow-up.
