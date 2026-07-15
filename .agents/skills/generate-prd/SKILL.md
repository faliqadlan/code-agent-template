---
name: generate-prd
description: Generate or update an evidence-backed product requirements document from an existing repository. Use when the user wants `docs/PRD.md` to describe verified users, features, flows, data, integrations, constraints, and known gaps.
---

<!-- code-agent-template:managed -->
# Generate PRD

Document observable product behavior without inventing requirements.

## Process

1. Inspect repository instructions, README files, manifests, routes or entry points, data definitions, UI surfaces, tests, environment examples, and existing documentation.
2. Identify product purpose, users, roles, features, primary flows, data contracts, integrations, non-functional behavior, and known limitations.
3. Tie every concrete claim to repository evidence. Mark unresolved behavior as unknown rather than inferring it.
4. If `docs/PRD.md` exists, preserve useful human-authored content and update only evidence-backed sections. Do not replace the file wholesale without approval when the structure or intent materially differs.
5. Write clear acceptance-oriented requirements and distinguish current behavior from proposed behavior.
6. Cross-check the completed document against the evidence inspected.

## Output contract

Create or update `docs/PRD.md` unless the user provides another destination. Include last-updated metadata, product overview, users and roles, features and flows, interfaces and data, integrations, non-functional behavior, limitations, and open questions.

## Safety

List environment-variable names only. Never copy credential values or private operational data into the PRD.
