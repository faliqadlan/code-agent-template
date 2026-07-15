---
name: project-handoff
description: Create concise sanitized continuation state for a later conversation. Use when the user asks to save progress, prepare a handoff, pause complex work, or make a future agent conversation resume from repository evidence.
---

<!-- code-agent-template:managed -->
# Project Handoff

Persist only the minimum state another conversation needs.

## Process

1. Inspect the actual working tree or available file state, active specification, completed changes, verification output, blockers, and next action.
2. Copy `.agents/memory/state.template.md` to `.agents/memory/state.md` when the state file does not exist.
3. Replace stale state with a concise current handoff. Link the active specification instead of duplicating it.
4. Include only verified file, command, and status information.
5. Re-read the result and remove secrets, tokens, credentials, personal data, private prompts, hidden reasoning, and transcript-like detail.

## Output contract

Write `.agents/memory/state.md` and report its path.

## Boundaries

- Do not create commits, branches, or Git metadata.
- Do not mark work complete when required implementation or verification remains.
- Do not use the handoff as a substitute for durable project context or an approved task specification.
