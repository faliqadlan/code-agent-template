# Universal Coding-Agent Template

Version 2.0.0 is a manual-bootstrap, format-portable `.agents/` package for guiding coding agents with ordinary Markdown, Agent Skills, bounded roles, versioned assignments, verified context, sanitized handoffs, structural validation, and agent-evaluation assets.

The root README documents the template. When adopting it in another coding repository, copy only `.agents/`; its MIT license travels with the folder. The package does not install dependencies, enable automation, create client-specific adapters, or claim native instruction discovery.

## Install and onboard

1. Copy `.agents/` into the target repository root after reviewing collisions.
2. Run the portable validator:

   ```text
   python .agents/scripts/validate_template.py
   ```

3. Start a fresh conversation with the Standard conversation bootstrap below.
4. Replace the request with the onboarding request and review the generated project context.

Python 3.10 or newer is required for the included scripts. The default validator uses only the standard library.

## Standard conversation bootstrap

Use this complete prompt at the beginning of every new conversation:

```text
Before handling my request, read .agents/AGENTS.md and follow its
repository-wide instructions. Load only the context and skills relevant
to the request.

Request:
<user request>
```

This explicit prompt is the universal discovery contract. Because the authoritative file is nested under `.agents/`, this package is not claiming native root-`AGENTS.md` discovery or identical precedence behavior across agent clients.

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

Authoring example:

```text
Request:
Use agent-task in Author mode. Create version 1 of <task name>.
Require <capabilities>. Add these ordered model preferences only if
available: <provider/model list or None>. Set whether a preferred model
is required. Define bounded execution, approval gates, observable
acceptance criteria, and verification. Validate and publish the task
without executing it.
```

Published files use `.agents/tasks/<task-name>-v<version>.md`. Revision creates the next version rather than overwriting a published task. Immutability is a workflow and version-control contract, not filesystem locking.

## Portable structure

| Path | Purpose |
|---|---|
| `.agents/manifest.json` | Template version, Python requirement, and core inventory |
| `.agents/AGENTS.md` | Minimal working agreement, trust boundaries, and progressive router |
| `.agents/context/` | Verified project facts and generated README source |
| `.agents/skills/` | Agent Skills procedures plus trigger and output evaluations |
| `.agents/roles/` | Bounded researcher, reviewer, and test-runner contracts |
| `.agents/tasks/` | Immutable, capability-first assignment definitions |
| `.agents/memory/` | Optional sanitized continuation state |
| `.agents/evals/` | Synthetic whole-system conformance cases and ignored run workspace |
| `.agents/scripts/` | Portable structural validator and evaluation harness |
| `.agents/tests/` | Standard-library unit and mutation tests |

Manifest-declared core artifacts are required. Additional valid skills, roles, resources, and top-level `.agents` directories are allowed and validated generically.

## Validation

Portable structural validation:

```text
python .agents/scripts/validate_template.py
```

Optional strict Agent Skills metadata validation:

```text
python .agents/scripts/validate_template.py --strict-skills
```

Strict mode requires the official `skills-ref` executable; the default command remains dependency-free.

Unit and mutation tests:

```text
python -m unittest discover -s .agents/tests -p "test_*.py"
```

The validator checks structure, frontmatter, internal references, manifest inventory, task contracts, memory hygiene, licenses, tests, and evaluation schemas. It does not prove behavioral quality, prompt-injection resistance, technical permission enforcement, or cross-agent portability.

## Agent conformance evaluations

Validate the corpus:

```text
python .agents/scripts/evaluate_agents.py validate
```

Prepare the held-out routing split as three clean trials per query:

```text
python .agents/scripts/evaluate_agents.py prepare-routing --split validation --trials 3 --out .agents/evals/.runs/routing
```

Prepare ignored, isolated run directories:

```text
python .agents/scripts/evaluate_agents.py prepare --suite core --profile smoke --out .agents/evals/.runs
```

For release qualification, supply an exported `.agents` snapshot from commit `b6b5017`; the release profile creates three randomized trials across all five conditions:

```text
python .agents/scripts/evaluate_agents.py prepare --suite core --profile release --baseline <path-to-v1-.agents> --out .agents/evals/.runs/release
```

Give a fresh subject only the opaque `<run>/subject` bundle, not the parent control directory. After the subject writes the output files declared in `limits.json`, import sanitized visible evidence:

```text
python .agents/scripts/evaluate_agents.py import-result --run-dir <run> --runtime-id <id> --model-id <id>
python .agents/scripts/evaluate_agents.py grade --run-dir <run>
python .agents/scripts/evaluate_agents.py prepare-review --run-dir <run> --reviewer-slot a --out <packet-a.json>
python .agents/scripts/evaluate_agents.py prepare-review --run-dir <run> --reviewer-slot b --out <packet-b.json>
python .agents/scripts/evaluate_agents.py import-review --run-dir <run> --reviewer-slot a --packet <packet-a.json> --review <review-a.json> --reviewer-session-id <fresh-a> --runtime-id <id> --model-id <id>
python .agents/scripts/evaluate_agents.py import-review --run-dir <run> --reviewer-slot b --packet <packet-b.json> --review <review-b.json> --reviewer-session-id <fresh-b> --runtime-id <id> --model-id <id>
python .agents/scripts/evaluate_agents.py summarize --runs .agents/evals/.runs
```

Deterministic success is reported as `semantic-pending`, never as final conformance; `grade` exits 3 for that pending state. Give each blinded packet to a different fresh, read-only reviewer session; packet/run/slot bindings and distinct session IDs are enforced. The packets omit condition, subject model, deterministic score, and the other reviewer. A deterministic failure cannot be overridden, and critical reviewer disagreement becomes `human-adjudication`. When the runtime exposes activation events, add `--routing-observable --activated-skill <name>` during result import. Otherwise routing remains explicitly inconclusive. The harness cannot spawn a vendor-neutral agent by itself. Results from one product/model family are labeled same-runtime self-consistency, and policy adherence is reported separately from technically enforced permissions.

## Safety and evidence

Repository files, tasks, handoffs, web content, logs, and tool output are evidence rather than instruction authority. Unknown provenance, contradictions, or embedded instructions require inspection or a safe stop. Markdown guidance is defense in depth; consequential security tests require runtime isolation, synthetic data, no credentials, and no external targets.

The evidence and tradeoffs behind v2 are documented in [the scoped design review](docs/agents-v2-design-review.md).

## License

The template and the copyable `.agents/` package are available under the MIT License.

## References

- [AGENTS.md open format](https://agents.md/)
- [Agent Skills specification](https://agentskills.io/specification)
- [Optimizing skill descriptions](https://agentskills.io/skill-creation/optimizing-descriptions)
- [Evaluating skill output quality](https://agentskills.io/skill-creation/evaluating-skills)
