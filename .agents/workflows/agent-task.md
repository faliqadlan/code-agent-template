---
description: Author or execute a validated reusable cross-agent repository task
---

<!-- code-agent-template:managed -->
# Agent Task

Load and follow the `agent-task` skill from `.agents/skills/agent-task/SKILL.md`.

Use Author mode to create a reusable definition under `.agents/tasks/`. Use Execute mode when the user provides an existing task path and any runtime values as `NAME="value"`.

The task is scoped input, not approval to bypass repository instructions, permissions, or high-risk review. Keep the task file unchanged during execution.
