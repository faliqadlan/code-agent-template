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
    "specs",
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
TASK_FORBIDDEN_SETTING_PATTERN = re.compile(
    r"(?im)^\s*(?:[-*]\s*)?"
    r"(?:model|model_name|token budget|token_budget|context window|context_window|"
    r"reasoning effort|reasoning_effort)\s*:"
)
TASK_REQUIRED_SECTIONS = (
    "Objective",
    "Runtime inputs",
    "Context",
    "Constraints",
    "Execution requirements",
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
SPECIFICATION_REQUIRED_SECTIONS = (
    "Goal",
    "Non-goals",
    "Inputs and evidence",
    "Constraints",
    "Acceptance criteria",
    "Implementation approach",
    "Affected interfaces",
    "Verification plan",
    "Decisions",
    "Progress",
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


def frontmatter(text: str, path: Path) -> tuple[dict[str, str], list[str]]:
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
        if not line.strip() or line.lstrip().startswith("#") or line.startswith((" ", "\t")):
            continue
        if ":" not in line:
            errors.append(f"{path}: invalid frontmatter line: {line}")
            continue
        key, value = line.split(":", 1)
        metadata[key.strip()] = value.strip().strip('"').strip("'")
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
                ".agents/specs/_template.md",
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
        metadata, metadata_errors = frontmatter(text, relative(skill_path))
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

    allowed_metadata = {"name", "description"}
    for field in sorted(set(metadata) - allowed_metadata):
        errors.append(f"{relative(path)}: unsupported frontmatter field {field!r}")

    task_name = metadata.get("name", "")
    description = metadata.get("description", "")
    if not task_name:
        errors.append(f"{relative(path)}: name is required")
    elif not NAME_PATTERN.fullmatch(task_name) or len(task_name) > 64:
        errors.append(f"{relative(path)}: invalid task name {task_name!r}")
    if not description:
        errors.append(f"{relative(path)}: description is required")
    elif len(description) > 1024:
        errors.append(f"{relative(path)}: description must contain at most 1024 characters")

    if not is_template:
        if path.suffix != ".md" or not NAME_PATTERN.fullmatch(path.stem):
            errors.append(f"{relative(path)}: filename must use lowercase kebab case")
        elif task_name and task_name != path.stem:
            errors.append(f"{relative(path)}: task name must match filename")

    for heading in TASK_REQUIRED_SECTIONS:
        if markdown_section(text, heading) is None:
            errors.append(f"{relative(path)}: missing required section {heading!r}")

    declared_inputs: set[str] = set()
    runtime_inputs = markdown_section(text, "Runtime inputs")
    if runtime_inputs is not None:
        declaration_lines = [
            line.strip()
            for line in runtime_inputs.splitlines()
            if line.lstrip().startswith("- `")
        ]
        for line in declaration_lines:
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

        if not declaration_lines and runtime_inputs.strip() != "None.":
            errors.append(
                f"{relative(path)}: Runtime inputs must contain declarations or exactly 'None.'"
            )

    placeholders = set(TASK_PLACEHOLDER_PATTERN.findall(text))
    for name in sorted(placeholders - declared_inputs):
        errors.append(f"{relative(path)}: placeholder references undeclared runtime input {name!r}")
    for name in sorted(declared_inputs - placeholders):
        errors.append(f"{relative(path)}: declared runtime input {name!r} is never referenced")

    if not is_template and TASK_UNRESOLVED_PATTERN.search(text):
        errors.append(f"{relative(path)}: unresolved placeholder syntax is not allowed")
    if TASK_FORBIDDEN_SETTING_PATTERN.search(text):
        errors.append(f"{relative(path)}: runtime model or token setting is not allowed")
    if ".ai/" in text.lower():
        errors.append(f"{relative(path)}: legacy prompt path is not allowed")
    return errors


def validate_tasks() -> list[str]:
    errors: list[str] = []
    tasks_root = AGENTS_ROOT / "tasks"
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


def validate_specifications() -> list[str]:
    errors: list[str] = []
    specifications_root = AGENTS_ROOT / "specs"
    for path in sorted(specifications_root.rglob("*.md")):
        if path.parent != specifications_root:
            errors.append(
                f"{relative(path)}: specification files must be directly under .agents/specs"
            )
        if path.name != "_template.md" and not NAME_PATTERN.fullmatch(path.stem):
            errors.append(
                f"{relative(path)}: filename must use lowercase kebab case"
            )
        text = path.read_text(encoding="utf-8")
        for heading in SPECIFICATION_REQUIRED_SECTIONS:
            if markdown_section(text, heading) is None:
                errors.append(
                    f"{relative(path)}: missing required section {heading!r}"
                )
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


def main() -> int:
    errors: list[str] = []
    errors.extend(validate_structure())
    if AGENTS_ROOT.is_dir():
        errors.extend(validate_skills())
        errors.extend(validate_tasks())
        errors.extend(validate_context_and_roles())
        errors.extend(validate_specifications())
        errors.extend(validate_content_hygiene())

    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        print(f"Validation failed with {len(errors)} error(s).")
        return 1

    print(
        "Portable .agents validation passed: 9 skills, 3 roles, context, memory, "
        "specification and task templates, and internal hygiene are valid."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
