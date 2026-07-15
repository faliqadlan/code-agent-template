---
name: delegate-work
description: Delegate genuinely independent repository work to constrained researcher, reviewer, or test-runner roles and synthesize their results. Use when the user explicitly requests parallel agents or when a complex task has independent read, review, or verification tracks that benefit from isolated context.
---

<!-- code-agent-template:managed -->
# Delegate Work

Use delegation to isolate independent work, not to avoid primary-agent responsibility.

## Role selection

- Read `.agents/roles/researcher.md` for bounded exploration.
- Read `.agents/roles/reviewer.md` for read-only review.
- Read `.agents/roles/test-runner.md` for verification commands.

## Process

1. Confirm that at least two work items are independent or that the user explicitly requested delegation.
2. Define one bounded outcome per subagent with the minimum paths, context, tools, and permissions needed.
3. On Codex, use the matching project agent from `.codex/agents/` when available.
4. On Antigravity, dynamically define the matching role and disable write, MCP, or further delegation tools unless the role explicitly needs them and the parent is already authorized.
5. Avoid having multiple write-capable agents edit the same files. Prefer isolated worktrees when supported and justified.
6. Wait for results, validate their evidence, resolve contradictions, and perform final synthesis in the primary agent.

## Boundaries

- Subagents inherit the parent task's scope and approval boundaries; never broaden them.
- Architectural decisions, user questions, and final claims remain with the primary agent.
- Do not delegate small sequential tasks where coordination costs exceed the benefit.
