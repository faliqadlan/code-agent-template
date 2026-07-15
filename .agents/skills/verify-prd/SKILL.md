---
name: verify-prd
description: Compare an existing product requirements document with repository implementation and tests. Use when the user requests a read-only PRD compliance audit, feature matrix, evidence mapping, gap analysis, or remediation backlog.
---

<!-- code-agent-template:managed -->
# Verify PRD

Audit implementation evidence without changing application code.

## Process

1. Locate the authoritative PRD and establish the repository boundary.
2. Extract testable requirements, roles, flows, interfaces, data rules, integrations, and non-functional expectations.
3. Map each requirement to source, configuration, migrations or schemas, UI behavior, and tests.
4. Classify implementation as met, partial, unmet, or unverifiable. Classify verification separately.
5. Identify contradictions between documentation, implementation, and tests.
6. Prioritize a remediation backlog by user impact, risk, and dependency order.

## Output contract

Return an executive summary, requirement matrix, evidence links, confirmed gaps, verification gaps, and prioritized remediation. Deliver in chat unless the user explicitly requests a report file.

## Read-only boundary

Do not fix code, rewrite the PRD, generate migrations, or update tests. A follow-up implementation request is required for mutations.
