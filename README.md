# Universal Coding-Agent Template

Version 2.2.0 is a manual-bootstrap, format-portable coding-agent package with a strict runtime/tooling boundary. The copyable `.agents/` directory contains only operational guidance, context, roles, skills, task contracts, memory templates, and one task-specific validator. Maintainer tests, graders, fixtures, and evaluation definitions live under `tooling/agents/` and are not part of runtime agent context.

The package does not install dependencies, enable automation, create client-specific adapters, or claim native instruction discovery. Separating maintainer tooling reduces accidental context exposure; it does not eliminate hallucination or provide a security boundary.

## Adopt `.agents`

1. Validate this source template before distribution:

   ```text
   python tooling/agents/scripts/validate_template.py
   ```

2. Copy only `.agents/` into the target repository root after reviewing collisions. Do not copy `tooling/agents/` unless that repository will maintain or evaluate the template itself.
3. Optionally validate the copied runtime package from this source checkout:

   ```text
   python tooling/agents/scripts/validate_template.py --root <target-repository> --runtime-only
   ```

4. Start a fresh conversation with the Standard conversation bootstrap below.

Python 3.10 or newer is required for maintainer tooling and the optional `agent-task` contract validator. The remaining runtime package is Markdown and JSON.

## Standard conversation bootstrap

Use this complete prompt at the beginning of every new conversation:

```text
Before handling my request, read .agents/AGENTS.md and follow its
repository-wide instructions. Load only the context and skills relevant
to the request.

Request:
<user request>
```

This explicit prompt is the discovery contract. Because the authoritative file is nested under `.agents/`, the template does not claim native root-`AGENTS.md` discovery or identical precedence across clients.

## Common requests

### Onboard a repository

```text
Request:
Inspect this repository and populate verified project context.
```

### Develop or fix behavior

```text
Request:
Add <feature> with <observable acceptance criteria>.
```

```text
Request:
Fix <reproducible defect> and add regression coverage.
```

### Review without changes

```text
Request:
Review <diff, branch, commit, or file set> without making changes.
```

### Generate the README source

After onboarding:

```text
Request:
Generate .agents/context/README.md from verified project context and
repository evidence. Do not modify the root README.md.
```

Review the generated source and manually copy or merge it into the root README.

## External Agent Skill discovery

`find-agent-skills` keeps installed project skills first. An explicit request to find, compare, review, or install an Agent Skill authorizes only a sanitized public catalog search. When the router infers a local capability gap, it must state the gap and proposed generic query, then wait for permission before contacting a catalog. Repository code, paths, credentials, private identifiers, customer data, and proprietary task details are never search inputs.

[AgentSkills.io](https://agentskills.io/home) defines the portable skill format and validation rules; it is not a registry. [officialskills.sh](https://officialskills.sh/) is a browsable frontend for the [VoltAgent Awesome Agent Skills](https://github.com/VoltAgent/awesome-agent-skills) collection, so they are treated as two views of one community-maintained catalog rather than independent evidence. Catalog entries and candidate repositories remain untrusted.

Discovery returns at most three publisher-first candidates with canonical source, pinned revision, license, requirements, and risks. Installation is a separate staged workflow:

1. Fetch the pinned candidate into temporary storage outside the repository and inspect every bundled resource without executing it.
2. Require the already-installed official reference validator to pass:

   ```text
   skills-ref validate <staged-skill>
   ```

3. Present the inventory, provenance, license, validation result, collision check, and risks; wait for a second explicit approval even if the original request asked to install.
4. Copy only the approved skill into `.agents/skills/<name>`, preserve upstream licensing, add `SOURCE.json`, validate again, and do not activate the skill automatically.

If `skills-ref` is unavailable, discovery and review may complete but installation remains blocked. The workflow never runs `npx skills add`, installs a validator or dependency, overwrites a local skill, installs globally, or executes candidate content.

An external skill's optional `SOURCE.json` contains exactly:

```json
{
  "schema_version": 1,
  "catalog_url": "https://officialskills.sh/<entry>",
  "source_url": "https://github.com/<owner>/<repository>",
  "source_revision": "<40-or-64-digit-lowercase-git-hash>",
  "source_path": "<relative-posix-skill-path>",
  "classification": "publisher-owned",
  "license": "<identified-license>",
  "validated_with": "skills-ref",
  "validated_at": "<iso-8601-utc-timestamp-ending-in-Z>"
}
```

`classification` may be `publisher-owned` or `community`. The sidecar records discovery provenance and observed validation; it is not a publisher-identity, safety, compatibility, or quality guarantee.

## Continuation state

Use handoff state only for unfinished work moving to another conversation:

```text
Request:
Use project-handoff to create or update .agents/memory/state.md with
verified progress, repository checkpoint, evidence provenance, blockers,
unknowns, and the next action. Stop without continuing implementation.
```

The receiving session must reverify every saved claim, permission, and approval. Never store secrets, private prompts, hidden reasoning, or complete transcripts. `state.md` is ignored by Git.

## Versioned cross-agent assignments

Use `agent-task` only when an assignment must be transferred or reused. Tasks are capability-first:

- Required capabilities are mandatory.
- Ordered provider/model preferences are optional.
- `Require preferred model: false` makes preferences advisory.
- `Require preferred model: true` requires a listed, verified model before meaningful output or side effects.

Published files use `.agents/tasks/<task-name>-v<version>.md`. Revisions create the next version rather than overwriting a published task. The skill validates one task through:

```text
python .agents/skills/agent-task/scripts/validate_task.py <task-file>
```

This narrowly scoped script is the only executable included in the operational package. Immutability remains a workflow and version-control contract, not filesystem locking.

## Repository structure

### Operational package

| Path | Purpose |
|---|---|
| `.agents/manifest.json` | Schema-2 runtime version and operational inventory |
| `.agents/AGENTS.md` | Working agreement, trust boundaries, and progressive router |
| `.agents/context/` | Verified project facts and generated README source |
| `.agents/skills/` | Agent Skills procedures and the task-specific validator resource |
| `.agents/roles/` | Bounded researcher, reviewer, and test-runner contracts |
| `.agents/tasks/` | Immutable, capability-first assignment definitions |
| `.agents/memory/` | Optional sanitized continuation state |

The operational manifest contains no tests, fixtures, evaluation inventory, general-purpose scripts, or Python requirement.

### Maintainer tooling

| Path | Purpose |
|---|---|
| `tooling/agents/manifest.json` | Tooling version, Python requirement, test, script, and evaluation inventory |
| `tooling/agents/scripts/` | Full template validator and evaluation harness |
| `tooling/agents/tests/` | Standard-library unit and mutation tests |
| `tooling/agents/evals/` | Centralized skill evals, integration cases, fixtures, graders, and ignored runs |

`tooling/agents/` is maintainer-only and must not be supplied to evaluation subjects or copied as runtime guidance.

## Validation

Validate the operational package and maintainer tooling:

```text
python tooling/agents/scripts/validate_template.py
```

Validate only a copied `.agents` package:

```text
python tooling/agents/scripts/validate_template.py --root <repository> --runtime-only
```

Optional strict Agent Skills metadata validation:

```text
python tooling/agents/scripts/validate_template.py --strict-skills
```

Strict mode requires the official `skills-ref` executable. Default validation remains standard-library only.

Run unit and mutation tests:

```text
python -m unittest discover -s tooling/agents/tests -p "test_*.py"
```

Validation checks both manifests, operational purity, frontmatter, internal references, task contracts, memory hygiene, centralized evaluation mappings, safe paths, root licensing, and maintainer documentation. It does not prove behavioral quality, prompt-injection resistance, technical permission enforcement, or cross-agent portability.

## Agent conformance evaluations

Validate the corpus:

```text
python tooling/agents/scripts/evaluate_agents.py validate
```

Prepare held-out routing trials:

```text
python tooling/agents/scripts/evaluate_agents.py prepare-routing --split validation --trials 3 --out tooling/agents/evals/.runs/routing
```

Prepare a smoke profile:

```text
python tooling/agents/scripts/evaluate_agents.py prepare --suite core --profile smoke --out tooling/agents/evals/.runs/smoke
```

Prepare the full release matrix with an exported v1 `.agents` snapshot:

```text
python tooling/agents/scripts/evaluate_agents.py prepare --suite core --profile release --baseline <path-to-v1-.agents> --out tooling/agents/evals/.runs/release
```

Give a fresh subject only the opaque `<run>/subject` bundle. Import sanitized evidence, grade deterministic assertions, prepare two blinded reviewer packets, import reviews from distinct sessions, and summarize from the moved evaluator commands documented in [the maintainer evaluation guide](tooling/agents/evals/README.md).

Deterministic success remains `semantic-pending` until two canonically bound semantic reviews complete. Missing routing telemetry, unverified model identity, instruction-only permissions, and infrastructure errors remain distinct from behavioral failure.

## Safety and evidence

Repository files, tasks, handoffs, web content, logs, and tool output are evidence rather than instruction authority. Unknown provenance, contradictions, or embedded instructions require inspection or a safe stop. Markdown guidance is defense in depth; consequential security tests require runtime isolation, synthetic data, no credentials, and no external targets.

The evidence and tradeoffs behind this design are documented in [the scoped design review](docs/agents-v2-design-review.md).

## License

The repository root [LICENSE](LICENSE) is the sole license file. Core skills retain `license: MIT` metadata; `.agents/` intentionally contains no duplicate license file.

## References

- [AGENTS.md open format](https://agents.md/)
- [Agent Skills specification](https://agentskills.io/specification)
- [Optimizing skill descriptions](https://agentskills.io/skill-creation/optimizing-descriptions)
- [Evaluating skill output quality](https://agentskills.io/skill-creation/evaluating-skills)
- [officialskills.sh directory and disclaimer](https://officialskills.sh/about)
- [VoltAgent Awesome Agent Skills](https://github.com/VoltAgent/awesome-agent-skills)
