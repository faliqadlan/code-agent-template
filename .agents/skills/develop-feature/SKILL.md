---
name: develop-feature
description: Plan, implement, and verify a new repository feature. Use when the user requests new behavior or an enhancement and expects code changes, including complex work that requires conversational plan approval.
---

<!-- code-agent-template:managed -->
# Develop Feature

Deliver the smallest coherent feature that meets verified acceptance criteria.

## Inputs

- Requested outcome and target users
- In-scope and out-of-scope behavior
- Repository context, relevant code, and existing tests

## Process

1. Inspect the implementation path and state observable acceptance criteria.
2. Classify risk. Architectural, destructive, security-sensitive, dependency-changing, externally visible, or materially ambiguous work requires an approved plan.
3. Present high-risk plans in conversation and wait for approval. Create a task through `agent-task` only when the user requests a reusable or cross-agent assignment.
4. Implement the narrowest design consistent with repository conventions. Preserve unrelated user changes.
5. Add or update tests at the closest useful level.
6. Run proportionate formatting, static checks, tests, builds, and visual inspection when the user-visible interface changes.
7. Reflect on the diff for scope creep, security implications, compatibility, and documentation impact.

## Output contract

Return the implemented outcome, affected interfaces, verification evidence, residual risk, and any manual follow-up. Keep execution results outside immutable task files.

## Boundaries

- Respect explicit plan-only requests and do not mutate.
- Do not add production dependencies or alter public contracts without surfacing the decision.
- Do not claim complete verification when required checks could not run.
