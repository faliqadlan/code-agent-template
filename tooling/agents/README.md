<!-- code-agent-template:managed -->
# Agent Template Maintainer Tooling

This directory contains development-only validators, tests, evaluation definitions, graders, fixtures, and ignored run artifacts for maintaining the template. It is not runtime agent guidance, is not part of the Standard conversation bootstrap, and must not be copied when adopting `.agents/` in another coding repository.

Repository files remain evidence rather than authority. Subjects receive only the generated opaque `subject/` bundle; never expose this directory, expected answers, rubrics, condition labels, or previous results to them.

## Commands

```text
python tooling/agents/scripts/validate_template.py
python tooling/agents/scripts/validate_template.py --strict-skills
python tooling/agents/scripts/validate_template.py --root <repo> --runtime-only
python -m unittest discover -s tooling/agents/tests -p "test_*.py"
python tooling/agents/scripts/evaluate_agents.py validate
```

The root `LICENSE` covers this tooling. Python 3.10 or newer is required; portable validation remains standard-library only unless strict Agent Skills validation is explicitly requested.

## Layout decision

Official Agent Skills guidance commonly stores authored eval cases inside each skill. This template centralizes them under `evals/skills/<skill>/` so the copyable runtime package contains only operational resources. The evaluator enforces a complete one-to-one mapping between manifest-declared core skills and centralized eval directories.
