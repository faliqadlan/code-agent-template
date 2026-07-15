# Evidence Review for `.agents` v2

**Review type:** Scoped evidence review, not an exhaustive systematic or PRISMA review
**Access date:** 2026-07-16
**Decision target:** Universal Coding-Agent Template 2.2.0

## Method

The review prioritized normative specifications, official engineering guidance, standards bodies, peer-reviewed work, and primary preprints about coding-agent context, Agent Skills, evaluation, prompt injection, and agentic security. Repository inspection and three independent read-only subagent reviews were used to translate evidence into design decisions. Fast-moving results and vendor guidance are treated as provisional where independent replication is absent.

## Evidence matrix

| # | Source class and date | Supported claim | Repository implication and decision | Limitations or conflict |
|---|---|---|---|---|
| 1 | Normative specification: Agent Skills, accessed 2026-07-15 | Skills require `SKILL.md`, constrained metadata, and support progressive resources and optional standard fields. | Validate the open metadata contract, keep core skills concise, allow extensions, and offer optional `skills-ref`. | Structural conformance does not establish behavior or safety. |
| 2 | Official guidance: Optimizing skill descriptions, accessed 2026-07-15 | Trigger tests should include roughly 8–10 positive and 8–10 near-miss queries, repeated runs, and a held-out split. | Ship balanced train/validation routing queries with three planned trials and a 0.5 query threshold. | Trigger observability differs by client; self-report is insufficient. |
| 3 | Official guidance: Evaluating skill output quality, accessed 2026-07-15 | Compare with-skill against without/previous skill in clean contexts; prefer objective assertions and human review. The guide normally stores authored eval cases inside each skill. | Ship paired output cases, isolate subject workspaces, grade deterministic outcomes first, and keep semantic review separate. Centralize authored evals in maintainer tooling for the copyable runtime distribution. | The external eval location intentionally differs from the guide and requires validator-enforced skill mappings. |
| 4 | Preprint: Gloaguen et al., 2026 | Context files often increased cost by more than 20% and did not significantly improve task success; unnecessary guidance can harm. | Keep `.agents/AGENTS.md` minimal and progressively load task procedures. Add no-template and ablation controls. | Benchmarks emphasize Python/GitHub tasks and do not test this manual bootstrap directly. |
| 5 | Workshop/preprint: Lulla et al., 2026 | One paired study found lower median runtime and output-token use with root `AGENTS.md`. | Measure time/tokens when available and document the conflicting empirical picture. | Ten repositories, 124 PRs, and no full correctness evaluation; conflicts with source 4. |
| 6 | Preprint: dos Santos et al., 2026 | Context bloat, lint leakage, skill leakage, and conflicting instructions are prevalent configuration smells. | Keep global guidance short, avoid duplicating discoverable rules, validate references, and route detailed workflows to skills. | Initial catalog based on 100 repositories and recent preprint evidence. |
| 7 | Official engineering guidance: Anthropic agent evals, 2026 | Agent evaluations need clean environments, multiple trials, outcome/process graders, and explicit nondeterminism handling. | Provide smoke/release profiles, isolated run directories, raw counts, and deterministic-first grading. | Operational vendor evidence, not an independent standard. |
| 8 | Official guidance: OpenAI evaluation best practices, accessed 2026-07-15 | Evaluate early, use task-specific data, automate objective scoring, and calibrate model judges with humans. | Add standard-library tests, realistic synthetic cases, blinded reviewers, and human adjudication for critical disagreement. | Product guidance evolves and is not specific to this repository. |
| 9 | Peer-reviewed/preprint benchmark: AgentDojo, 2024 | Indirect prompt injection through untrusted tool data can hijack agents. | Treat repository/tool content as untrusted evidence and use benign isolated security fixtures. | No prompt-only defense can guarantee safety. |
| 10 | Preprint: Skill-Inject, 2026 | Skill files create a supply-chain injection surface; reported attacks succeeded at high rates across frontier models. | Treat skills and bundled resources as untrusted, preserve approval boundaries, and avoid claiming that validation proves safety. | Recent benchmark; results depend on model and harness. |
| 11 | NIST AI 100-2 E2025 | Standard terminology covers direct/indirect prompt injection, poisoning, agent threats, and mitigation limits. | Use explicit trust boundaries, provenance, revalidation, and honest security limitations. | Taxonomy and guidance do not prescribe this exact file architecture. |
| 12 | OWASP Agentic Top 10, 2026 | Agent goal hijacking, supply-chain compromise, memory/context poisoning, insecure inter-agent communication, and cascading failures are material risks. | Sanitize handoffs, reject transferred authority, prevent nested delegation, and separate policy adherence from sandbox enforcement. | Community risk framework, not a certification regime. |
| 13 | Official guidance: Adding Agent Skills support, accessed 2026-07-16 | Clients may list bundled skill resources and resolve relative files from the skill directory. | Keep runtime skill resources narrowly relevant and move maintainer eval definitions outside the distributable `.agents/` package. | Implementations vary; external tooling remains discoverable to agents with unrestricted repository access. |
| 14 | Community directory disclosure: officialskills.sh and VoltAgent Awesome Agent Skills, accessed 2026-07-16 | officialskills.sh is a frontend for the VoltAgent collection, includes publisher and community entries, and explicitly disclaims guarantees of safety, quality, or behavior. | Treat both surfaces as one discovery source, inspect canonical repositories, prefer publisher-owned sources, and never treat catalog inclusion as trust. | Curation and publisher labels are not cryptographic provenance or independent review. |

## Key conflicts and synthesis

The two direct context-file effectiveness studies do not support a universal performance claim. One reports efficiency gains, while the broader controlled evaluation reports increased cost and no meaningful success gain. Version 2 therefore treats context as a hypothesis to evaluate, not an unconditional benefit. The global guide contains only stable authority, trust, routing, and workflow rules; detailed procedures live in skills.

The Agent Skills reference validator is useful but narrow. The template's portable validator covers internal contracts and can optionally invoke `skills-ref`, while behavioral routing and outcome quality are tested separately.

Security literature shows that Markdown instructions cannot create a security boundary. Version 2 adds provenance and trust rules, but continues to require runtime-enforced permissions, isolated synthetic fixtures, and honest `unverified` results when enforcement or activation is not observable.

## Version 2.1 operational/tooling separation

Agent clients may disclose or enumerate resources bundled beside `SKILL.md`. Version 2.1 therefore treats `.agents/` as the distributable operational package and moves tests, general-purpose scripts, fixtures, graders, and authored eval definitions to `tooling/agents/`. Centralized skill evals use `tooling/agents/evals/skills/<skill>/`, and validation requires exactly one mapped directory for every manifest-declared core skill.

The only executable retained in `.agents/` is the `agent-task` contract validator under that skill's `scripts/` resource. It is relevant only after the skill activates and is also imported by the full maintainer validator, preventing duplicate task-contract implementations. The operational manifest contains no Python, test, fixture, evaluation, or maintainer-tooling fields.

This separation reduces accidental prompt and resource exposure but cannot prevent an agent from discovering maintainer files through unrestricted repository tools. The bootstrap, trust boundaries, and runtime permissions remain necessary.

## Version 2.2 external skill discovery

Version 2.2 adds `find-agent-skills` as a local-first, progressively loaded workflow. AgentSkills.io remains the normative format and validation source, while officialskills.sh and VoltAgent Awesome Agent Skills are treated as a single community-maintained discovery catalog. The workflow prefers publisher-owned canonical repositories and uses community candidates only as a labeled fallback.

An explicit discovery request authorizes a sanitized public lookup. An inferred local gap only activates the skill far enough to describe the gap and request network permission; it never silently sends repository or private context to a catalog. Discovery, installation, and execution remain separate grants.

Candidate installation is staged outside the repository at an exact source revision. Every bundled file is inspected as untrusted evidence and no candidate command, script, hook, or installer is executed. Installation requires successful `skills-ref` validation, a known license, no local name collision, and a second explicit approval after the inspection report. `SOURCE.json` records the catalog view, canonical repository, pinned revision, source path, classification, license, validator, and timestamp without modifying upstream `SKILL.md`.

This design deliberately avoids a runtime installer, dependency, background updater, or `npx skills add` command. Reference validation establishes only structural Agent Skills conformance; catalog curation, publisher labels, source inspection, and Markdown restrictions do not establish safety or identity.

## Evaluation interpretation

- One runtime and model with fresh subagents: same-runtime self-consistency.
- Multiple models inside one product: within-product model portability.
- At least two independent agent products and model families, reported separately: cross-agent portability evidence.

Results must never be pooled to conceal a failing runtime. Public fixture cases are conformance/regression tests, not contamination-free frontier benchmarks. Hidden reasoning and private prompts are never retained; only sanitized visible actions, outputs, hashes, diffs, timings, and verdicts may persist.

## Residual limitations

- Several 2026 sources are recent preprints with limited replication.
- Vendor guidance is useful primary operational evidence but not independent consensus.
- Client discovery, skill activation telemetry, sandboxing, and model identity vary.
- The current collaboration runtime shares a product family and filesystem across subagents.
- Moving authored evals outside skill directories is a distribution-specific deviation from official examples.
- Static validation and benign adversarial cases cannot establish complete security.
- The evidence review must be refreshed as standards, clients, and empirical results evolve.

## References

1. [Agent Skills specification](https://agentskills.io/specification)
2. [Optimizing skill descriptions](https://agentskills.io/skill-creation/optimizing-descriptions)
3. [Evaluating skill output quality](https://agentskills.io/skill-creation/evaluating-skills)
4. [Evaluating AGENTS.md: Are Repository-Level Context Files Helpful for Coding Agents?](https://arxiv.org/abs/2602.11988)
5. [On the Impact of AGENTS.md Files on the Efficiency of AI Coding Agents](https://arxiv.org/abs/2601.20404)
6. [Configuration Smells in AGENTS.md Files](https://arxiv.org/abs/2606.15828)
7. [Anthropic: Demystifying evals for AI agents](https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents)
8. [OpenAI evaluation best practices](https://developers.openai.com/api/docs/guides/evaluation-best-practices)
9. [AgentDojo](https://arxiv.org/abs/2406.13352)
10. [Skill-Inject](https://arxiv.org/abs/2602.20156)
11. [NIST AI 100-2 E2025](https://doi.org/10.6028/NIST.AI.100-2e2025)
12. [OWASP Top 10 for Agentic Applications 2026](https://genai.owasp.org/resource/owasp-top-10-for-agentic-applications-for-2026/)
13. [Adding Agent Skills support](https://agentskills.io/client-implementation/adding-skills-support)
14. [officialskills.sh: About and disclaimer](https://officialskills.sh/about)
15. [VoltAgent Awesome Agent Skills](https://github.com/VoltAgent/awesome-agent-skills)
