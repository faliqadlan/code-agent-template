<!-- code-agent-template:managed -->
# Universal Coding-Agent Guide

The user loads this file explicitly through the conversation bootstrap. Once loaded, treat it as the working agreement and context router for the entire repository, not only the `.agents/` directory. Explicit user and higher-priority runtime instructions take precedence.

## Working agreements

- Inspect relevant repository files before making claims or changes. Prefer evidence over assumptions.
- Keep work within the requested scope and preserve unrelated user changes.
- Never expose, copy, or invent secrets. Refer to environment-variable names instead of values.
- Treat architectural, destructive, security-sensitive, dependency-changing, externally visible, or materially ambiguous work as high risk. Present a plan and wait for approval before mutating high-risk areas.
- For clear low-risk work, implement directly unless the user requests planning, explanation, diagnosis, review, or another read-only outcome.
- Use the smallest relevant verification set. Report commands run, actual results, and anything that could not be verified.
- Do not initialize Git, create commits, enable automation, install dependencies, connect external systems, or expand permissions unless the user explicitly requests it.
- Do not store hidden reasoning, private prompts, complete transcripts, credentials, or tokens in the repository.

## Progressive routing

Load only what the current request needs:

- Repository purpose, users, behavior, stack, architecture, commands, and constraints: `.agents/context/project.md`
- Reusable task procedures: the matching `.agents/skills/<skill-name>/SKILL.md`
- Specialist boundaries for explicitly delegated work: `.agents/roles/`
- Immutable cross-agent assignments, only through the `agent-task` skill: `.agents/tasks/`
- Continuation state, only when the user asks to resume, continue, save, or hand off work: `.agents/memory/state.md`

Before applying a skill, read its complete `SKILL.md`. Use its description to match the request. If no skill matches, follow these working agreements and normal repository evidence instead of forcing a skill.

## Skill routing

- Author or execute a versioned cross-agent task: `agent-task`
- Delegate independent research, review, or verification: `delegate-work`
- Plan, implement, and verify an enhancement: `develop-feature`
- Diagnose and correct a reproducible defect: `fix-bug`
- Generate the human-facing README source after onboarding: `generate-readme`
- Create or refresh verified repository context: `onboard-repository`
- Save sanitized continuation state: `project-handoff`
- Perform a read-only code review: `review-code`
- Perform read-only visual verification: `verify-ui`

## Change workflow

1. Establish the requested outcome, scope, constraints, and observable acceptance criteria.
2. Inspect relevant source, tests, configuration, documentation, and project context.
3. Decide whether the work is read-only, low risk, or requires an approved plan.
4. For high-risk work, present the plan in conversation and wait for approval. Create a task file only when the user requests a reusable or cross-agent assignment.
5. Implement the smallest coherent change while preserving behavior outside scope.
6. Run proportionate checks and inspect their actual output.
7. Reflect on scope creep, compatibility, security, documentation, and remaining risk.

## Review and verification

- Code review and UI verification are read-only unless the user separately requests fixes.
- Lead review results with actionable findings ordered by severity and supported by file or command evidence.
- Do not claim visual correctness without inspecting rendered output or screenshots.
- Do not claim tests or validation pass unless the relevant command completed successfully.

## Context and continuity

- If `.agents/context/project.md` is uninitialized or stale, inspect the repository or use `onboard-repository` rather than guessing.
- Treat project context as authoritative for verified facts and `.agents/context/README.md` as a human-facing projection.
- Never modify a coding repository's root `README.md` while generating the README source.
- Update `.agents/memory/state.md` only through an explicit handoff or continuation request.
