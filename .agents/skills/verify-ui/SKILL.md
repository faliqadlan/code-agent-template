---
name: verify-ui
description: Perform read-only visual verification of an existing user interface using available browser tooling, screenshots, and existing end-to-end tests. Use when the user asks to inspect layout, responsive behavior, interactions, visual regressions, or accessibility-visible states without requesting fixes.
---

<!-- code-agent-template:managed -->
# Verify UI

Base visual conclusions on rendered evidence.

## Process

1. Identify the affected pages, roles, routes, states, and acceptance criteria.
2. Discover the documented way to run the application and existing browser tests. Do not install missing dependencies without approval.
3. Use available browser tooling to inspect relevant desktop and narrow viewports, interactive states, loading, empty, error, focus, and disabled states as applicable.
4. Inspect screenshots or rendered output directly. Separate visual defects from functional defects and environment failures.
5. Record exact routes, viewport sizes, interactions, and evidence for each finding.

## Output contract

Return verified states, actionable visual findings ordered by impact, evidence locations, untested states, and environment limitations. Temporary or ignored screenshots are acceptable; do not create or modify tracked tests or application files.

## Read-only boundary

Do not repair defects, update snapshots, or change styles. Use `develop-feature` or `fix-bug` after the user explicitly requests implementation.
