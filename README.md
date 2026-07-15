# Extensible Cross-Agent Coding Template

This repository provides a stack-neutral coding-agent configuration for Google Antigravity and OpenAI Codex. It combines a compact `AGENTS.md` router, open Agent Skills, Antigravity workflow adapters, portable role contracts, inactive extension scaffolds, and deterministic validation.

Nothing in the template initializes Git, enables CI, installs a plugin, connects an MCP server, or activates a hook.

## Layout

| Path | Purpose |
|---|---|
| `AGENTS.md` | Durable cross-agent working agreements and context routing |
| `.agents/context/` | Verified, relatively stable repository facts |
| `.agents/specs/` | Optional contracts for approved complex tasks |
| `.agents/skills/` | Canonical reusable workflows for Antigravity and Codex |
| `.agents/workflows/` | Thin Antigravity slash-command adapters |
| `.agents/roles/` | Portable specialist role and permission boundaries |
| `.codex/agents/` | Native Codex project-scoped subagent definitions |
| `.agents/templates/` | Inactive plugin, MCP, hook, Codex, and CI examples |

## Use this template

For a new repository, create it from this template or copy the complete template directory, then run `onboard-repository` to replace the uninitialized project context with verified facts.

For an existing repository:

1. Copy `.agents/` and `.codex/` into the repository root.
2. If the repository has no `AGENTS.md`, copy this template's root file.
3. If `AGENTS.md` already exists, manually merge the block between `code-agent-template:managed:start` and `code-agent-template:managed:end`; do not replace existing repository instructions.
4. Review filename collisions before replacing any existing skill, workflow, role, plugin, MCP, hook, or Codex configuration.
5. Run `python tests/validate_template.py` if the validator was copied with the template.

Copying the template never initializes Git or activates `.github` automation. Those remain manual repository decisions.

## Activate in Antigravity

1. Open the repository as a workspace.
2. Open **Customizations > Rules**.
3. Activate `.agents/rules/core.md` as **Always On**.
4. Invoke a workflow with `/workflow-name`, such as `/onboard-repository`.

Antigravity discovers skills from `.agents/skills`, workflows from `.agents/workflows`, workspace MCP configuration from `.agents/mcp_config.json`, hooks from `.agents/hooks.json`, and plugins placed under `.agents/plugins`.

## Use in Codex

Codex loads root `AGENTS.md`, discovers repository skills in `.agents/skills`, and discovers project-scoped custom agents in `.codex/agents`. Invoke a skill explicitly with `$skill-name`, such as `$onboard-repository`.

## Workflows

| Workflow | Default behavior |
|---|---|
| `onboard-repository` | Write verified repository context only |
| `develop-feature` | Plan, risk-check, implement, and verify |
| `fix-bug` | Reproduce, minimally fix, and add regression coverage |
| `review-code` | Read-only findings |
| `generate-prd` | Create or safely update product documentation |
| `verify-prd` | Read-only implementation audit |
| `verify-ui` | Read-only visual verification |
| `project-handoff` | Write explicit local continuation state |
| `delegate-work` | Use constrained specialist roles |
| `configure-extensions` | Create inactive extension scaffolds by default |

## Extensions

Live MCP and hook files are intentionally empty. Examples are stored under `.agents/templates/extensions/` and do nothing until reviewed and manually promoted. The dual-plugin example includes separate Antigravity and Codex manifests but is not registered in a marketplace or copied into the live plugins directory.

Never store credentials in these files. Use environment-variable references, document required dependencies and permissions, and activate an extension only after explicit review.

## Optional CI

Run validation on any platform with:

```text
python tests/validate_template.py
```

An inactive GitHub Actions example is stored at `.agents/templates/ci/github-actions-validate.yml`. To enable it, manually review and copy it into `.github/workflows/`.

## References

- [AGENTS.md](https://agents.md/)
- [Agent Skills specification](https://agentskills.io/specification)
- [Antigravity rules and workflows](https://antigravity.google/docs/rules-workflows)
- [Antigravity skills](https://antigravity.google/docs/skills)
- [Antigravity plugins](https://antigravity.google/docs/plugins)
- [Codex customization](https://learn.chatgpt.com/docs/customization/overview)
