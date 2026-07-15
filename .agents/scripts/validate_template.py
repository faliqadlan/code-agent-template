#!/usr/bin/env python3
"""Validate the portable .agents template using only the Python standard library."""

# code-agent-template:managed

from __future__ import annotations

import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
AGENTS_ROOT = ROOT / ".agents"
EXPECTED_TOP_LEVEL = {
    "AGENTS.md",
    "context",
    "memory",
    "roles",
    "scripts",
    "skills",
    "tasks",
}
EXPECTED_SKILLS = {
    "agent-task",
    "delegate-work",
    "develop-feature",
    "fix-bug",
    "generate-readme",
    "onboard-repository",
    "project-handoff",
    "review-code",
    "verify-ui",
}
EXPECTED_ROLES = {"researcher", "reviewer", "test-runner"}
NAME_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
TASK_INPUT_NAME_PATTERN = re.compile(r"^[A-Z][A-Z0-9_]*$")
TASK_INPUT_LINE_PATTERN = re.compile(
    r"^-\s+`(?P<name>[^`]+)`\s+"
    r"\((?P<mode>required|optional)(?:,\s*default:\s*(?P<default>[^)]+))?\):\s+.+$"
)
TASK_PLACEHOLDER_PATTERN = re.compile(r"(?<!\$)\$([A-Z][A-Z0-9_]*)")
TASK_UNRESOLVED_PATTERN = re.compile(r"\{\{[^{}\n]+\}\}|\b(?:TBD|REPLACE_ME)\b", re.IGNORECASE)
TASK_MODEL_IDENTIFIER_PATTERN = re.compile(r"^[^\s`/]+/[^\s`/]+(?:/[^\s`/]+)*$")
TASK_PREFERRED_MODEL_PATTERN = re.compile(
    r"(?m)^- Preferred model:\s+`([^`\r\n]+)`\s*$"
)
TASK_FALLBACK_PATTERN = re.compile(r"^\s+(\d+)\.\s+`([^`\r\n]+)`\s*$")
TASK_CAPABILITY_PATTERN = re.compile(r"^\s+-\s+`([^`\r\n]+)`\s*$")
TASK_MODE_PATTERN = re.compile(r"(?m)^- Mode:\s+`(single-pass|agentic-loop)`\s*$")
TASK_ITERATION_PATTERN = re.compile(r"(?m)^- Maximum iterations:\s+`([0-9]+)`\s*$")
TASK_APPROVAL_PATTERN = re.compile(r"(?m)^- Approval gates:\s+\S.*$")
TASK_ACCEPTANCE_PATTERN = re.compile(r"(?m)^- \[ \]\s+\S.*$")
TASK_VERIFICATION_METHOD_PATTERN = re.compile(r"(?m)^- Method:\s+\S.*$")
TASK_VERIFICATION_RESULT_PATTERN = re.compile(r"(?m)^- Expected result:\s+\S.*$")
TASK_MUTABLE_HEADING_PATTERN = re.compile(
    r"(?im)^##\s+(?:progress|results|current status|run state|execution log|"
    r"hidden reasoning|transcript)\s*$"
)
TASK_SECRET_VALUE_PATTERN = re.compile(
    r"(?im)^\s*(?:[-*]\s*)?(?:[a-z0-9]+[_-])*"
    r"(?:api[_-]?key|secret[_-]?access[_-]?key|password|secret|token)\s*[:=]\s*"
    r"(?!None\.?\s*$)(?!\$[A-Z][A-Z0-9_]*\s*$)\S+"
)
TASK_REQUIRED_SECTIONS = (
    "Objective",
    "Target runtime",
    "Runtime inputs",
    "Context and evidence",
    "Scope and constraints",
    "Execution policy",
    "Execution procedure",
    "Acceptance criteria",
    "Verification",
    "Output",
)
PROJECT_REQUIRED_SECTIONS = (
    "Purpose",
    "Intended users",
    "Current capabilities and flows",
    "Technology stack",
    "Architecture and entry points",
    "Commands",
    "Data and integrations",
    "Repository conventions",
    "Constraints and hazards",
    "Proposed behavior",
    "Known gaps",
    "Open questions",
)
ROLE_REQUIRED_SECTIONS = (
    "Purpose",
    "Permission boundary",
    "Inputs",
    "Output",
    "Non-goals",
)
TASK_ALLOWED_OUTCOMES = {
    "succeeded",
    "failed",
    "blocked",
    "awaiting-approval",
    "exhausted",
}
TASK_TEMPLATE_MARKERS = (
    "describe the immutable cross-agent assignment",
    "state the observable result for",
    "`provider/model-id`",
    "`provider/fallback-model-id`",
    "identify the repository evidence",
    "describe actions that require approval",
    "define an observable result for",
    "define the smallest relevant command or inspection",
    "state the successful outcome",
)
LEGACY_SPEC_PATH = ".agents/" + "specs"
STALE_CONTRACT_PROHIBITIONS = (
    LEGACY_SPEC_PATH,
    "active " + "specification",
    "approved task " + "specification",
)
PORTABILITY_PROHIBITIONS = (
    "antigravity",
    "codex",
    ".codex/",
    ".agents/workflows",
    ".agents/rules",
    ".agents/plugins",
    "mcp_config.json",
    "hooks.json",
    "agents/openai.yaml",
    "docs/prd.md",
    "generate-prd",
    "verify-prd",
    "tests/validate_template.py",
)
HYGIENE_PROHIBITIONS = (
    "file://",
    "/var/www/",
    ".ai/",
    "mhcs",
    "laravel",
    "filament",
    "[todo:",
    "todo(",
)


def relative(path: Path) -> Path:
    return path.relative_to(ROOT)


def markdown_section(text: str, heading: str) -> str | None:
    match = re.search(
        rf"(?ms)^## {re.escape(heading)}\s*$\n(.*?)(?=^## |\Z)",
        text,
    )
    return match.group(1).strip() if match else None


def frontmatter(
    text: str, path: Path, *, allow_indented: bool = False
) -> tuple[dict[str, str], list[str]]:
    errors: list[str] = []
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}, [f"{path}: missing opening YAML frontmatter delimiter"]
    try:
        closing = next(index for index, line in enumerate(lines[1:], 1) if line.strip() == "---")
    except StopIteration:
        return {}, [f"{path}: missing closing YAML frontmatter delimiter"]

    metadata: dict[str, str] = {}
    for line in lines[1:closing]:
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if line.startswith((" ", "\t")):
            if not allow_indented:
                errors.append(f"{path}: nested or indented frontmatter is not supported: {line}")
            continue
        if ":" not in line:
            errors.append(f"{path}: invalid frontmatter line: {line}")
            continue
        key, value = line.split(":", 1)
        key = key.strip()
        if key in metadata:
            errors.append(f"{path}: duplicate frontmatter field {key!r}")
            continue
        metadata[key] = value.strip().strip('"').strip("'")
    return metadata, errors


def require_files(relative_paths: tuple[str, ...]) -> list[str]:
    return [
        f"Missing required file: {path}"
        for path in relative_paths
        if not (ROOT / path).is_file()
    ]


def validate_structure() -> list[str]:
    errors: list[str] = []
    if not AGENTS_ROOT.is_dir():
        return ["Missing required directory: .agents"]

    found = {path.name for path in AGENTS_ROOT.iterdir()}
    if found != EXPECTED_TOP_LEVEL:
        errors.append(
            f".agents top-level mismatch: expected {sorted(EXPECTED_TOP_LEVEL)}, found {sorted(found)}"
        )

    errors.extend(
        require_files(
            (
                ".agents/AGENTS.md",
                ".agents/context/project.md",
                ".agents/context/README.md",
                ".agents/memory/.gitignore",
                ".agents/memory/state.template.md",
                ".agents/tasks/_template.md",
                ".agents/scripts/validate_template.py",
            )
        )
    )

    return errors


def validate_skills() -> list[str]:
    errors: list[str] = []
    skills_root = AGENTS_ROOT / "skills"
    if not skills_root.is_dir():
        return ["Missing required directory: .agents/skills"]
    found = {path.name for path in skills_root.iterdir() if path.is_dir()}
    if found != EXPECTED_SKILLS:
        errors.append(
            f"Skill set mismatch: expected {sorted(EXPECTED_SKILLS)}, found {sorted(found)}"
        )

    for name in sorted(found):
        skill_path = skills_root / name / "SKILL.md"
        if not skill_path.is_file():
            errors.append(f"{relative(skill_path)}: missing required skill definition")
            continue
        text = skill_path.read_text(encoding="utf-8")
        metadata, metadata_errors = frontmatter(
            text, relative(skill_path), allow_indented=True
        )
        errors.extend(metadata_errors)
        skill_name = metadata.get("name", "")
        description = metadata.get("description", "")
        if skill_name != name:
            errors.append(f"{relative(skill_path)}: name must match folder")
        if not NAME_PATTERN.fullmatch(skill_name) or len(skill_name) > 64:
            errors.append(f"{relative(skill_path)}: invalid skill name")
        if not description or len(description) > 1024:
            errors.append(
                f"{relative(skill_path)}: description must contain 1-1024 characters"
            )
        if len(text.splitlines()) >= 500:
            errors.append(f"{relative(skill_path)}: SKILL.md must stay under 500 lines")
        if (skill_path.parent / "agents").exists():
            errors.append(f"{relative(skill_path.parent)}: platform metadata directory is not allowed")
    return errors


def validate_task_file(path: Path, *, is_template: bool = False) -> list[str]:
    errors: list[str] = []
    text = path.read_text(encoding="utf-8")
    metadata, metadata_errors = frontmatter(text, relative(path))
    errors.extend(metadata_errors)

    allowed_metadata = {"name", "description", "version"}
    for field in sorted(set(metadata) - allowed_metadata):
        errors.append(f"{relative(path)}: unsupported frontmatter field {field!r}")

    task_name = metadata.get("name", "")
    description = metadata.get("description", "")
    version_text = metadata.get("version", "")
    if not task_name:
        errors.append(f"{relative(path)}: name is required")
    elif not NAME_PATTERN.fullmatch(task_name) or len(task_name) > 64:
        errors.append(f"{relative(path)}: invalid task name {task_name!r}")
    if not description:
        errors.append(f"{relative(path)}: description is required")
    elif len(description) > 1024:
        errors.append(f"{relative(path)}: description must contain at most 1024 characters")

    version = int(version_text) if re.fullmatch(r"[1-9][0-9]*", version_text) else 0
    if version < 1:
        errors.append(f"{relative(path)}: version must be a positive integer")

    if not is_template:
        expected_filename = f"{task_name}-v{version}.md" if task_name and version else ""
        if path.suffix != ".md" or not NAME_PATTERN.fullmatch(path.stem):
            errors.append(f"{relative(path)}: filename must use lowercase kebab case")
        elif expected_filename and path.name != expected_filename:
            errors.append(
                f"{relative(path)}: filename must be {expected_filename!r} for its name and version"
            )

    for heading in TASK_REQUIRED_SECTIONS:
        section = markdown_section(text, heading)
        if section is None:
            errors.append(f"{relative(path)}: missing required section {heading!r}")
        elif not section:
            errors.append(f"{relative(path)}: required section {heading!r} must not be empty")

    target_runtime = markdown_section(text, "Target runtime")
    if target_runtime:
        preferred_matches = TASK_PREFERRED_MODEL_PATTERN.findall(target_runtime)
        preferred = preferred_matches[0] if len(preferred_matches) == 1 else ""
        if len(preferred_matches) != 1:
            errors.append(f"{relative(path)}: Target runtime must declare exactly one preferred model")
        elif not TASK_MODEL_IDENTIFIER_PATTERN.fullmatch(preferred):
            errors.append(
                f"{relative(path)}: preferred model must use an opaque provider/model identifier"
            )

        runtime_lines = target_runtime.splitlines()
        fallback_indexes = [
            index
            for index, line in enumerate(runtime_lines)
            if line.startswith("- Ordered fallbacks:")
        ]
        fallbacks: list[str] = []
        if len(fallback_indexes) != 1:
            errors.append(f"{relative(path)}: Target runtime must declare Ordered fallbacks once")
        else:
            fallback_index = fallback_indexes[0]
            fallback_line = runtime_lines[fallback_index]
            fallback_value = fallback_line.split(":", 1)[1].strip()
            if fallback_value not in {"", "None."}:
                errors.append(
                    f"{relative(path)}: Ordered fallbacks must be a numbered list or exactly 'None.'"
                )
            elif not fallback_value:
                expected_number = 1
                for line in runtime_lines[fallback_index + 1 :]:
                    if line.startswith("- Required capabilities:"):
                        break
                    if not line.strip():
                        continue
                    match = TASK_FALLBACK_PATTERN.fullmatch(line)
                    if not match:
                        errors.append(f"{relative(path)}: invalid ordered fallback line {line!r}")
                        continue
                    number = int(match.group(1))
                    model = match.group(2)
                    if number != expected_number:
                        errors.append(
                            f"{relative(path)}: ordered fallback numbering must start at 1 without gaps"
                        )
                    expected_number += 1
                    if not TASK_MODEL_IDENTIFIER_PATTERN.fullmatch(model):
                        errors.append(
                            f"{relative(path)}: fallback model must use an opaque provider/model identifier"
                        )
                    fallbacks.append(model)
                if not fallbacks:
                    errors.append(
                        f"{relative(path)}: Ordered fallbacks must contain a model or exactly 'None.'"
                    )

        if len(fallbacks) != len(set(fallbacks)):
            errors.append(f"{relative(path)}: ordered fallback models must be unique")
        if preferred and preferred in fallbacks:
            errors.append(f"{relative(path)}: preferred model must not also be a fallback")

        capability_indexes = [
            index
            for index, line in enumerate(runtime_lines)
            if line == "- Required capabilities:"
        ]
        capabilities: list[str] = []
        if len(capability_indexes) != 1:
            errors.append(f"{relative(path)}: Target runtime must declare Required capabilities once")
        else:
            for line in runtime_lines[capability_indexes[0] + 1 :]:
                if not line.strip():
                    break
                match = TASK_CAPABILITY_PATTERN.fullmatch(line)
                if not match:
                    break
                capabilities.append(match.group(1))
            if not capabilities:
                errors.append(f"{relative(path)}: at least one required capability is required")
            elif len(capabilities) != len(set(capabilities)):
                errors.append(f"{relative(path)}: required capabilities must be unique")

    declared_inputs: set[str] = set()
    runtime_inputs = markdown_section(text, "Runtime inputs")
    if runtime_inputs is not None:
        runtime_lines = [line.strip() for line in runtime_inputs.splitlines() if line.strip()]
        if runtime_lines == ["None."]:
            pass
        else:
            if "None." in runtime_lines:
                errors.append(
                    f"{relative(path)}: Runtime inputs must not mix 'None.' with declarations"
                )
            for line in runtime_lines:
                match = TASK_INPUT_LINE_PATTERN.fullmatch(line)
                if not match:
                    errors.append(f"{relative(path)}: invalid runtime input declaration {line!r}")
                    continue
                name = match.group("name")
                mode = match.group("mode")
                default = match.group("default")
                if not TASK_INPUT_NAME_PATTERN.fullmatch(name):
                    errors.append(f"{relative(path)}: invalid runtime input name {name!r}")
                if name in declared_inputs:
                    errors.append(f"{relative(path)}: duplicate runtime input {name!r}")
                declared_inputs.add(name)
                if mode == "required" and default is not None:
                    errors.append(f"{relative(path)}: required input {name!r} must not declare a default")
                if mode == "optional" and not default:
                    errors.append(f"{relative(path)}: optional input {name!r} must declare a default")

    placeholders = set(TASK_PLACEHOLDER_PATTERN.findall(text))
    for name in sorted(placeholders - declared_inputs):
        errors.append(f"{relative(path)}: placeholder references undeclared runtime input {name!r}")
    for name in sorted(declared_inputs - placeholders):
        errors.append(f"{relative(path)}: declared runtime input {name!r} is never referenced")

    if not is_template and TASK_UNRESOLVED_PATTERN.search(text):
        errors.append(f"{relative(path)}: unresolved placeholder syntax is not allowed")
    if not is_template:
        lowered = text.lower()
        for marker in TASK_TEMPLATE_MARKERS:
            if marker in lowered:
                errors.append(f"{relative(path)}: unresolved template text {marker!r} is not allowed")

    execution_policy = markdown_section(text, "Execution policy")
    if execution_policy:
        mode_matches = TASK_MODE_PATTERN.findall(execution_policy)
        iteration_matches = TASK_ITERATION_PATTERN.findall(execution_policy)
        if len(mode_matches) != 1:
            errors.append(f"{relative(path)}: Execution policy must declare exactly one valid mode")
        if len(iteration_matches) != 1:
            errors.append(
                f"{relative(path)}: Execution policy must declare exactly one maximum iteration count"
            )
        if len(mode_matches) == 1 and len(iteration_matches) == 1:
            mode = mode_matches[0]
            iterations = int(iteration_matches[0])
            if iterations < 1:
                errors.append(f"{relative(path)}: maximum iterations must be positive")
            if mode == "single-pass" and iterations != 1:
                errors.append(f"{relative(path)}: single-pass tasks must use exactly one iteration")
        if len(TASK_APPROVAL_PATTERN.findall(execution_policy)) != 1:
            errors.append(f"{relative(path)}: Execution policy must declare approval gates once")

    acceptance = markdown_section(text, "Acceptance criteria")
    if acceptance is not None and not TASK_ACCEPTANCE_PATTERN.search(acceptance):
        errors.append(f"{relative(path)}: at least one unchecked acceptance criterion is required")

    verification = markdown_section(text, "Verification")
    if verification:
        if len(TASK_VERIFICATION_METHOD_PATTERN.findall(verification)) != 1:
            errors.append(f"{relative(path)}: Verification must declare exactly one method")
        if len(TASK_VERIFICATION_RESULT_PATTERN.findall(verification)) != 1:
            errors.append(f"{relative(path)}: Verification must declare exactly one expected result")

    output = markdown_section(text, "Output")
    if output:
        missing_outcomes = sorted(
            outcome for outcome in TASK_ALLOWED_OUTCOMES if f"`{outcome}`" not in output
        )
        if missing_outcomes:
            errors.append(
                f"{relative(path)}: Output is missing allowed outcomes {missing_outcomes}"
            )

    if TASK_MUTABLE_HEADING_PATTERN.search(text):
        errors.append(f"{relative(path)}: mutable run-state or transcript headings are not allowed")
    if TASK_SECRET_VALUE_PATTERN.search(text):
        errors.append(f"{relative(path)}: embedded secret-like values are not allowed")
    if ".ai/" in text.lower():
        errors.append(f"{relative(path)}: legacy prompt path is not allowed")
    return errors


def validate_tasks() -> list[str]:
    errors: list[str] = []
    tasks_root = AGENTS_ROOT / "tasks"
    if not tasks_root.is_dir():
        return ["Missing required directory: .agents/tasks"]
    for path in sorted(tasks_root.rglob("*.md")):
        if path.parent != tasks_root:
            errors.append(f"{relative(path)}: task files must be directly under .agents/tasks")
        errors.extend(validate_task_file(path, is_template=path.name == "_template.md"))
    return errors


def validate_context_and_roles() -> list[str]:
    errors: list[str] = []
    project_path = AGENTS_ROOT / "context/project.md"
    if project_path.is_file():
        project_text = project_path.read_text(encoding="utf-8")
        for heading in PROJECT_REQUIRED_SECTIONS:
            if markdown_section(project_text, heading) is None:
                errors.append(f"{relative(project_path)}: missing required section {heading!r}")

    roles_root = AGENTS_ROOT / "roles"
    roles = {path.stem for path in roles_root.glob("*.md")}
    if roles != EXPECTED_ROLES:
        errors.append(f"Role set mismatch: expected {sorted(EXPECTED_ROLES)}, found {sorted(roles)}")
    for path in sorted(roles_root.glob("*.md")):
        text = path.read_text(encoding="utf-8")
        for heading in ROLE_REQUIRED_SECTIONS:
            if markdown_section(text, heading) is None:
                errors.append(f"{relative(path)}: missing required section {heading!r}")
    return errors


def validate_content_hygiene() -> list[str]:
    errors: list[str] = []
    validator_path = Path(__file__).resolve()
    operational_roots = (
        AGENTS_ROOT / "AGENTS.md",
        AGENTS_ROOT / "roles",
        AGENTS_ROOT / "skills",
    )
    files: list[Path] = []
    for root in operational_roots:
        if root.is_file():
            files.append(root)
        elif root.is_dir():
            files.extend(path for path in root.rglob("*") if path.is_file())

    for path in files:
        if path.resolve() == validator_path:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        lowered = text.lower()
        for prohibited in PORTABILITY_PROHIBITIONS + HYGIENE_PROHIBITIONS:
            if prohibited in lowered:
                errors.append(f"{relative(path)}: contains prohibited text {prohibited!r}")
        if re.search(r"\b[A-Za-z]:[\\/]", text):
            errors.append(f"{relative(path)}: contains an absolute Windows path")
    return errors


def validate_stale_contract_references() -> list[str]:
    errors: list[str] = []
    validator_path = Path(__file__).resolve()
    files = [ROOT / "README.md"]
    files.extend(path for path in AGENTS_ROOT.rglob("*") if path.is_file())

    for path in files:
        if path.resolve() == validator_path:
            continue
        try:
            lowered = path.read_text(encoding="utf-8").lower()
        except UnicodeDecodeError:
            continue
        for prohibited in STALE_CONTRACT_PROHIBITIONS:
            if prohibited in lowered:
                errors.append(f"{relative(path)}: contains stale contract text {prohibited!r}")
    return errors


def main() -> int:
    errors: list[str] = []
    errors.extend(validate_structure())
    if AGENTS_ROOT.is_dir():
        errors.extend(validate_skills())
        errors.extend(validate_tasks())
        errors.extend(validate_context_and_roles())
        errors.extend(validate_content_hygiene())
        errors.extend(validate_stale_contract_references())

    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        print(f"Validation failed with {len(errors)} error(s).")
        return 1

    print(
        "Portable .agents validation passed: 9 skills, 3 roles, context, memory, "
        "versioned task contracts, and internal hygiene are valid."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
