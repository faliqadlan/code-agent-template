---
name: configure-extensions
description: Safely scaffold or validate repository-scoped plugins, MCP server definitions, and hooks for Antigravity or Codex. Use when the user asks to add an extension, prepare inactive integration configuration, validate manifests, or explicitly activate a reviewed extension.
---

<!-- code-agent-template:managed -->
# Configure Extensions

Create inactive, reviewable extension configuration by default.

## Required inputs

- Extension type: plugin, MCP server, or hook
- Target product: Antigravity, Codex, or both
- Intended capability and trust boundary
- Dependencies, command or server URL, authentication model, and required permissions
- Whether the user requests staging only or explicit activation

## Process

1. Inspect live configuration and `.agents/templates/extensions/` before writing.
2. Refuse to invent package names, URLs, credentials, headers, commands, or permission grants.
3. Stage new configuration under `.agents/templates/extensions/` unless the user explicitly requests activation.
4. For plugins, start from `dual-plugin`, normalize the name, keep Antigravity `plugin.json` and Codex `.codex-plugin/plugin.json` consistent, and do not register a marketplace entry automatically.
5. For MCP, use environment-variable references for secrets and document transport, dependencies, and permissions. Never add wildcard permissions.
6. For hooks, keep examples disabled, use repository-relative commands, set finite timeouts, and document trigger and failure behavior.
7. Validate syntax and manifests. Show the exact staged or live diff and activation steps.

## Activation gate

Moving a plugin into `.agents/plugins`, adding a server to live `mcp_config.json`, enabling a hook, installing dependencies, or changing permissions requires explicit user authorization.

## Output contract

Report created files, validation evidence, inactive or active state, required environment variables, permissions, and manual activation or rollback steps.
