---
name: onboard-repository
description: Analyze an existing repository and create or refresh verified project context. Use when starting work in an unfamiliar codebase, when `.agents/context/project.md` is uninitialized or stale, or when stack, architecture, and verification commands must be documented from evidence.
---

<!-- code-agent-template:managed -->
# Onboard Repository

Create durable orientation without inventing repository facts.

## Inputs

- Repository root and requested onboarding depth
- Existing README, manifests, configuration, CI, and agent instructions
- Any explicit user constraints

## Process

1. Confirm the repository boundary. Do not initialize Git or install dependencies.
2. Inspect the top-level tree, manifests, README files, environment examples, CI definitions, entry points, tests, and deployment configuration.
3. Trace only enough source to describe verified architecture and primary flows.
4. Derive commands from repository files. Run safe read-only checks when useful; never claim an unexecuted command succeeded.
5. Separate verified facts from unknowns. Cite a path or command for every durable claim.
6. Update only `.agents/context/project.md`. Preserve human-authored notes that do not conflict with evidence.
7. Report material contradictions, missing documentation, and commands that still require verification.

## Output contract

Populate purpose, stack, architecture, commands, conventions, external systems, constraints, hazards, and open questions. Set `Last verified` to the actual date. Never include secret values.

## Failure behavior

- If multiple repository roots are plausible, stop before writing and identify them.
- If a command or technology cannot be verified, record `Unknown` with the evidence checked.
- If the context file contains unmanaged content that cannot be merged safely, present the proposed content in chat and request direction.
