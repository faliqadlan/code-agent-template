# Universal Coding-Agent Template

This repository provides a portable `.agents/` folder for guiding coding agents through ordinary Markdown instructions. It does not depend on a platform-specific workflow, rule, plugin, hook, or custom-agent format.

The root `README.md` documents the template itself. When adopting the template in another coding repository, copy only `.agents/`.

## Install in a coding repository

1. Copy this repository's `.agents/` directory into the coding repository root.
2. Review collisions before replacing an existing `.agents/` directory or any files inside it.
3. Start each new agent conversation with the bootstrap below.
4. Ask the agent to onboard the repository before relying on uninitialized project context.
5. Run `python .agents/scripts/validate_template.py` to check the copied structure.

Copying `.agents/` does not initialize Git, install dependencies, enable automation, connect external tools, or modify the coding repository's root `README.md`.

## Conversation bootstrap

Use this prompt at the beginning of a new conversation:

```text
Before handling my request, read .agents/AGENTS.md and follow its
repository-wide instructions. Load only the context and skills relevant
to the request.

Request:
<user request>
```

The explicit bootstrap is the universal discovery contract. It does not assume that the selected agent automatically loads instructions or skills from a particular directory.

## Example requests

### Onboard a repository

```text
Before handling my request, read .agents/AGENTS.md and follow its
repository-wide instructions. Load only the context and skills relevant
to the request.

Request:
Inspect this repository and populate the verified project context.
```

### Develop a feature

```text
Before handling my request, read .agents/AGENTS.md and follow its
repository-wide instructions. Load only the context and skills relevant
to the request.

Request:
Add <feature> with <acceptance criteria>.
```

### Review code

```text
Before handling my request, read .agents/AGENTS.md and follow its
repository-wide instructions. Load only the context and skills relevant
to the request.

Request:
Review <diff, branch, commit, or file set> without making changes.
```

### Author a task for another model

Use a task when one agent should prepare an immutable assignment for another model or conversation:

```text
Before handling my request, read .agents/AGENTS.md and follow its
repository-wide instructions. Load only the context and skills relevant
to the request.

Request:
Use the agent-task skill in Author mode. Create version 1 of <task name>
for preferred model <provider/model>. Use these ordered fallbacks: <models
or None>. Require these capabilities: <capabilities>. Define a bounded
execution policy, observable acceptance criteria, and verification.
Validate and publish the task, but do not execute it.
```

Successful validation publishes `.agents/tasks/<task-name>-v1.md` as immutable under the agent workflow. This is a procedural and version-control guarantee, not filesystem locking: the validator checks current structure but cannot detect a historical rewrite. To revise a task, create the next version instead of overwriting the published file.

### Transfer and execute a task

The task records model preferences but cannot switch providers or models by itself. Select the preferred model in the product or runtime, open a conversation with repository access, and send:

```text
Before handling my request, read .agents/AGENTS.md and follow its
repository-wide instructions. Load only the context and skills relevant
to the request.

Request:
Use the agent-task skill in Execute mode to execute
.agents/tasks/<task-name>-v1.md with <NAME="value" inputs>. Keep the task
file unchanged. If this runtime cannot select or verify a compatible
declared model, stop and give me a prompt for manual transfer.
```

Fallback is availability-only. The runtime may use the first compatible declared fallback before meaningful output or external side effects when the preferred candidate is unavailable, rate-limited, or capability-incompatible. Verification failure does not authorize a model switch, and an undeclared model must never be substituted.

### Start a new conversation safely

Memory is optional and intended only for unfinished work that must continue in another conversation. Before closing the current conversation, ask the agent to prepare a concise handoff:

```text
Before I start a new conversation, read .agents/AGENTS.md and use the
project-handoff skill to create or update .agents/memory/state.md.

Record only verified progress, decisions, verification results, blockers,
and the next action. Do not continue implementation.
```

Then start the new conversation with:

```text
Before handling my request, inspect .agents/, starting with
.agents/AGENTS.md, and follow its repository-wide instructions. Then read
.agents/memory/state.md and verify the handoff against the current files,
working-tree or Git state, and active task before continuing.

Request:
Continue the previous work from the recorded next action.
```

Do not create memory for completed work. Never store credentials, tokens, private prompts, hidden reasoning, or full transcripts in `state.md`. The file is ignored by Git, so it remains local to the current working directory unless the user transfers it manually to another machine, clone, or worktree.

### Generate a project README source

First onboard the repository, then use a separate request:

```text
Before handling my request, read .agents/AGENTS.md and follow its
repository-wide instructions. Load only the context and skills relevant
to the request.

Request:
Generate .agents/context/README.md from verified project context and
repository evidence. Do not modify the root README.md.
```

Review `.agents/context/README.md` after generation. Copy or merge it into the coding repository's root `README.md` manually. Future updates remain manual; the agent must never overwrite or synchronize the root file automatically.

## Portable structure

| Path | Purpose |
|---|---|
| `.agents/AGENTS.md` | Repository-wide working agreements and routing instructions |
| `.agents/context/project.md` | Verified project and product facts |
| `.agents/context/README.md` | Generated human-facing README source |
| `.agents/skills/` | Portable task procedures using the Agent Skills format |
| `.agents/roles/` | Read-only researcher, reviewer, and test-runner contracts |
| `.agents/tasks/` | Template for immutable, versioned cross-agent assignments |
| `.agents/memory/` | Optional sanitized continuation state |
| `.agents/scripts/validate_template.py` | Standard-library structural validator |

## Context and README responsibilities

`.agents/context/project.md` is authoritative for verified project facts. It separates current behavior from proposals and unknowns.

`.agents/context/README.md` is a human-facing projection created only when explicitly requested. If the two conflict, refresh project context first and regenerate the README source. The root README in a coding repository remains user-controlled.

## Validation

Run:

```text
python .agents/scripts/validate_template.py
```

The validator checks the portable package structure, skill metadata, role contracts, versioned task contracts, model preferences, bounded execution policies, internal hygiene, and absence of removed platform-specific adapters. It uses only the Python standard library.

## Safety defaults

- Inspect repository evidence before making claims or changes.
- Preserve unrelated work and never expose credential values.
- Request approval before architectural, destructive, security-sensitive, dependency-changing, or externally visible work.
- Do not install dependencies, initialize Git, activate automation, or contact external systems without explicit authorization.
- Report the checks actually run and anything that could not be verified.

## References

- [AGENTS.md open format](https://github.com/openai/agents.md)
- [Agent Skills specification](https://agentskills.io/specification)
