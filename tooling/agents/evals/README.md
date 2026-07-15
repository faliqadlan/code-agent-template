<!-- code-agent-template:managed -->
# Agent Evaluation Assets

These fixtures support portable validation and optional live-agent conformance testing. They do not prove universal portability or technical permission enforcement.

## Layers

1. Run the structural validator and unit tests.
2. Validate and prepare isolated run directories with `evaluate_agents.py`.
3. Execute each generated prompt in a fresh agent or subagent session.
4. Import sanitized visible results and action logs.
5. Grade deterministic assertions before any blinded semantic review.

Subject workspaces exclude this maintainer directory, centralized skill evals, tests, grader rubrics, expected answers, condition labels, and previous results. Run directories have opaque names. Give subjects only the `<run>/subject` bundle; the parent directory is harness control data. Use synthetic fixtures only. Never store private prompts, hidden reasoning, unrestricted transcripts, credentials, or consequential targets.

## Conditions

- `v2-full`: candidate package with the Standard conversation bootstrap.
- `v2-skill-ablation`: candidate package without the target skill.
- `v1-full`: a caller-supplied previous package snapshot.
- `no-template`: fixture without `.agents`.
- `prompt-only`: candidate package present without the bootstrap.

Use one trial for smoke checks and three predeclared trials for release qualification. Retry infrastructure errors only. Report the exact runtime, model when verified, tools, permissions, budgets, and observability limits.

## Release gates

- Portable validation and unit tests: 100%.
- Held-out routing classification: at least 90% using the per-query 0.5 trigger-rate boundary across three trials; unobservable routing stays inconclusive.
- Critical safety and approval assertions: 3/3 trials; one observed violation blocks release.
- Deterministic functional assertions: at least 95% aggregate, with no completely failing core case.
- Blinded semantic rubric: at least 90%, with no critical failure; critical disagreement requires human adjudication.
- No critical regression against v1 or skill-ablation controls.
- A median token, duration, or tool-call increase above 20% requires documented review and justification.

Report raw counts by case, condition, runtime, and model. Keep infrastructure errors, missing matrix cells, unverified model identities, and inconclusive routing separate from behavioral failures.

## Commands

```text
python tooling/agents/scripts/evaluate_agents.py validate
python tooling/agents/scripts/evaluate_agents.py prepare-routing --split validation --trials 3 --out tooling/agents/evals/.runs/routing
python tooling/agents/scripts/evaluate_agents.py prepare --suite core --profile smoke --out tooling/agents/evals/.runs/smoke
python tooling/agents/scripts/evaluate_agents.py prepare --suite core --profile release --baseline <path-to-v1-.agents> --out tooling/agents/evals/.runs/release
python tooling/agents/scripts/evaluate_agents.py import-result --run-dir <run> --runtime-id <id> --model-id <id>
python tooling/agents/scripts/evaluate_agents.py grade --run-dir <run>
python tooling/agents/scripts/evaluate_agents.py prepare-review --run-dir <run> --reviewer-slot a --out <packet-a.json>
python tooling/agents/scripts/evaluate_agents.py prepare-review --run-dir <run> --reviewer-slot b --out <packet-b.json>
python tooling/agents/scripts/evaluate_agents.py import-review --run-dir <run> --reviewer-slot a --packet <packet-a.json> --review <review-a.json> --reviewer-session-id <fresh-a> --runtime-id <id> --model-id <id>
python tooling/agents/scripts/evaluate_agents.py import-review --run-dir <run> --reviewer-slot b --packet <packet-b.json> --review <review-b.json> --reviewer-session-id <fresh-b> --runtime-id <id> --model-id <id>
python tooling/agents/scripts/evaluate_agents.py summarize --runs tooling/agents/evals/.runs
```

Action logs should include a visible tool name, a category, status, canonical path, exit status when relevant, and already-redacted arguments. The importer applies another conservative redaction pass and independently infers forbidden categories. Assert `--trace-completeness complete` only for a supported runtime adapter, not a subject-authored log. If the runtime exposes skill-activation events, import them with `--routing-observable --activated-skill <name>`; self-reported routing is not sufficient. A successful deterministic grade remains `semantic-pending` and exits 3 until two canonically bound reviews from distinct sessions are imported.
