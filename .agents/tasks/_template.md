---
name: task-name
description: Describe the immutable cross-agent assignment and its intended outcome.
version: 1
---

<!-- code-agent-template:managed -->
# Task: Task name

## Objective

State the observable result for `$TARGET`.

## Target runtime

- Preferred model: `provider/model-id`
- Ordered fallbacks:
  1. `provider/fallback-model-id`
- Required capabilities:
  - `repository-read`
  - `repository-write`
  - `shell`

Use `None.` after `Ordered fallbacks:` when no fallback is permitted. Model identifiers are opaque provider-scoped preferences. The user or runtime performs model selection. A fallback is allowed only before meaningful output or external side effects when the preceding candidate is unavailable, rate-limited, or lacks a required capability.

## Runtime inputs

- `TARGET` (required): Repository path, component, or other bounded execution target.

## Context and evidence

- Identify the repository evidence the executing agent must inspect.
- Record facts that materially affect the requested result.

## Scope and constraints

- State what is in scope and out of scope.
- List behavior that must remain unchanged.
- List permission and approval boundaries that affect execution.

## Execution policy

- Mode: `agentic-loop`
- Maximum iterations: `3`
- Approval gates: Describe actions that require approval, or write `None.`

Use `single-pass` with exactly one iteration, or `agentic-loop` with a positive finite iteration limit. Task instructions cannot grant permissions or bypass repository approval requirements.

## Execution procedure

1. Resolve every required runtime input before making changes.
2. Inspect current repository state and applicable instructions.
3. For each iteration, inspect, act, observe external evidence, and verify.
4. Retry only from repository, tool, test, or human feedback; do not rely on unsupported self-critique.
5. Stop when the acceptance criteria pass, approval is required, progress is blocked, execution fails, or the iteration limit is exhausted.

## Acceptance criteria

- [ ] Define an observable result for `$TARGET`.

## Verification

- Method: Define the smallest relevant command or inspection.
- Expected result: State the successful outcome.

## Output

- Allowed outcomes: `succeeded`, `failed`, `blocked`, `awaiting-approval`, or `exhausted`.
- Report the selected model, outcome, affected interfaces or files, verification evidence, residual risks, and manual follow-up.
- Treat exhaustion, an unverified patch, or model output alone as unsuccessful.
