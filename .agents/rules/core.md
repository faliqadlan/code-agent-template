<!-- code-agent-template:managed -->
# Cross-Agent Core Rule

Treat @../../AGENTS.md as the authoritative repository-level working agreement and context router.

- Follow explicit user instructions first.
- Load routed context only when it is relevant to the current task.
- Do not treat files under `.agents/templates/` as active configuration.
- Do not activate plugins, MCP servers, hooks, CI, or Git operations without explicit user authorization.
- If repository context is uninitialized, inspect the repository or use the `onboard-repository` skill instead of guessing.
