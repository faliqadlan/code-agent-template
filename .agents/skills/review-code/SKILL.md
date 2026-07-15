---
name: review-code
description: Perform a read-only code review focused on correctness, security, regressions, maintainability, and missing tests. Use when the user asks to review a diff, branch, commit, pull request, or file set without requesting fixes.
---

<!-- code-agent-template:managed -->
# Review Code

Review as an owner and return actionable evidence, not a narration of the diff.

## Process

1. Establish the review target and intended behavior.
2. Read applicable agent instructions, project context, specifications, tests, and the complete relevant diff.
3. Trace changed behavior through callers, data boundaries, error paths, permissions, and compatibility constraints.
4. Run non-mutating checks when they materially improve confidence.
5. Report findings by severity. Each finding must include evidence, impact, and a concrete remediation direction.
6. Identify missing verification and residual risks separately from confirmed defects.

## Severity order

- Critical: immediate security, data-loss, or system-wide failure risk
- High: likely correctness, authorization, or compatibility failure
- Medium: bounded defect or maintainability issue with concrete impact
- Low: worthwhile issue with limited impact

## Output contract

Lead with findings. If none are actionable, state that clearly and summarize verification limits. Do not edit files unless the user sends a separate implementation request.
