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

### Save continuation state

```text
Before handling my request, read .agents/AGENTS.md and follow its
repository-wide instructions. Load only the context and skills relevant
to the request.

Request:
Prepare a sanitized project handoff for the next conversation.
```

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
| `.agents/specs/` | Template for approved complex implementation contracts |
| `.agents/tasks/` | Template for reusable repository tasks |
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

The validator checks the portable package structure, skill metadata, role contracts, templates, task syntax, internal hygiene, and absence of removed platform-specific adapters. It uses only the Python standard library.

## Safety defaults

- Inspect repository evidence before making claims or changes.
- Preserve unrelated work and never expose credential values.
- Request approval before architectural, destructive, security-sensitive, dependency-changing, or externally visible work.
- Do not install dependencies, initialize Git, activate automation, or contact external systems without explicit authorization.
- Report the checks actually run and anything that could not be verified.

## References

- [AGENTS.md open format](https://github.com/openai/agents.md)
- [Agent Skills specification](https://agentskills.io/specification)
