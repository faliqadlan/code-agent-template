<!-- code-agent-template:managed:start -->
# Coding Agent Guide

This file is the compact, durable router for coding agents working in this repository. Explicit user instructions override this file. A closer nested `AGENTS.md` overrides it for files in that subtree.

## Working agreements

- Inspect the relevant repository files before making claims or changes. Prefer repository evidence over assumptions.
- Keep changes within the requested scope and preserve unrelated user work.
- Never expose, copy, or invent secrets. Refer to environment-variable names instead of values.
- Treat architectural, destructive, security-sensitive, dependency-changing, externally visible, or materially ambiguous work as high risk. Present a plan and wait for approval before mutating high-risk areas.
- For clear low-risk work, implement directly unless the user requests plan-only behavior.
- Use the smallest relevant verification set. Report commands run, results, and anything that could not be verified.
- Do not initialize Git, create commits, enable CI, install plugins, connect MCP servers, or activate hooks unless the user explicitly requests that action.
- Do not store hidden reasoning or complete transcripts in the repository.

## Context routing

Load only the context needed for the current task:

- Repository purpose, stack, commands, and architecture: `.agents/context/project.md`
- Approved complex-task contracts: `.agents/specs/`
- Reusable cross-agent task definitions, invoked only through the `agent-task` skill or workflow: `.agents/tasks/`
- Continuation state when the user asks to resume or continue: `.agents/memory/state.md`
- Specialist role boundaries before delegation: `.agents/roles/`
- Reusable task workflows: `.agents/skills/`
- Antigravity slash-command adapters: `.agents/workflows/`

If a routed file is missing or still marked uninitialized, inspect the repository instead of guessing. Use `onboard-repository` when durable project context should be created or refreshed.

## Change workflow

1. Establish the requested outcome, scope, constraints, and acceptance criteria.
2. Inspect relevant source, tests, configuration, and documentation.
3. Decide whether the task is low risk or requires an approved plan.
4. For approved complex work, create or update `.agents/specs/<task-slug>.md` from the provided template.
5. Implement the smallest coherent change while preserving existing behavior outside scope.
6. Run proportionate checks and inspect their output.
7. Summarize the outcome, verification evidence, remaining risks, and manual follow-up.

## Review and verification

- Code review, PRD verification, and UI verification are read-only unless the user separately asks for fixes.
- Lead review responses with actionable findings ordered by severity and supported by file or command evidence.
- Do not claim visual correctness without inspecting rendered output or screenshots.
- Do not claim tests pass unless the relevant command completed successfully.

## Continuity and logging

- Update `.agents/memory/state.md` only through an explicit handoff request.
- Activity logging is opt-in. Store only concise, sanitized summaries in `.agents/logs/`; never store prompts, hidden reasoning, credentials, tokens, or full transcripts.
- Prefer linking an active specification from handoff state instead of duplicating its contents.
<!-- code-agent-template:managed:end -->
