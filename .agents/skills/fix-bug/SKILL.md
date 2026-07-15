---
name: fix-bug
description: Diagnose and fix a reproducible software defect with minimal scope and regression coverage. Use when the user reports incorrect behavior, an error, a failed test, or a regression and expects the underlying cause to be corrected.
---

<!-- code-agent-template:managed -->
# Fix Bug

Correct the root cause while preserving unrelated behavior.

## Process

1. Capture the expected behavior, actual behavior, environment, and reproduction evidence.
2. Reproduce the problem with the smallest reliable command or test. If reproduction is impossible, gather evidence and label the diagnosis accordingly.
3. Trace the failure to its root cause instead of patching the visible symptom.
4. Add a failing regression test first when practical. Explain when a deterministic regression test is not feasible.
5. Apply the smallest safe fix and avoid opportunistic refactoring.
6. Run the regression test, relevant neighboring tests, and proportionate broader checks.
7. Inspect the final diff for compatibility, error handling, and unintended changes.

## Output contract

Report the root cause, fix, regression coverage, exact verification results, and any remaining uncertainty.

## Risk gate

Pause for approval before a fix that changes architecture, public interfaces, data migration behavior, security boundaries, dependencies, or destructive operations.
