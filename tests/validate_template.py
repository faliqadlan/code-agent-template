#!/usr/bin/env python3
"""Validate the cross-agent template using only the Python standard library."""

# code-agent-template:managed

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - Python 3.10 fallback message
    tomllib = None


ROOT = Path(__file__).resolve().parents[1]
EXPECTED_NAMES = {
    "agent-task",
    "configure-extensions",
    "delegate-work",
    "develop-feature",
    "fix-bug",
    "generate-prd",
    "onboard-repository",
    "project-handoff",
    "review-code",
    "verify-prd",
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
BANNED_TEXT = (
    "file://",
    "/var/www/",
    ".ai/",
    "mhcs",
    "laravel",
    "filament",
    "[todo:",
    "todo(",
)


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
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if ":" not in line:
            errors.append(f"{path}: invalid frontmatter line: {line}")
            continue
        key, value = line.split(":", 1)
        metadata[key.strip()] = value.strip().strip('"').strip("'")
    return metadata, errors


def require_files(relative_paths: list[str]) -> list[str]:
    return [f"Missing required file: {path}" for path in relative_paths if not (ROOT / path).is_file()]


def markdown_section(text: str, heading: str) -> str | None:
    match = re.search(
        rf"(?ms)^## {re.escape(heading)}\s*$\n(.*?)(?=^## |\Z)",
        text,
    )
    return match.group(1).strip() if match else None


def validate_task_file(path: Path, *, is_template: bool = False) -> list[str]:
    errors: list[str] = []
    text = path.read_text(encoding="utf-8")
    metadata, metadata_errors = frontmatter(text, path)
    errors.extend(metadata_errors)

    allowed_metadata = {"name", "description"}
    for field in sorted(set(metadata) - allowed_metadata):
        errors.append(f"{path}: unsupported frontmatter field {field!r}")

    task_name = metadata.get("name", "")
    description = metadata.get("description", "")
    if not task_name:
        errors.append(f"{path}: name is required")
    elif not NAME_PATTERN.fullmatch(task_name) or len(task_name) > 64:
        errors.append(f"{path}: invalid task name {task_name!r}")
    if not description:
        errors.append(f"{path}: description is required")
    elif len(description) > 1024:
        errors.append(f"{path}: description must contain at most 1024 characters")

    if not is_template:
        if path.suffix != ".md" or not NAME_PATTERN.fullmatch(path.stem):
            errors.append(f"{path}: filename must use lowercase kebab case")
        elif task_name and task_name != path.stem:
            errors.append(f"{path}: task name must match filename")

    for heading in TASK_REQUIRED_SECTIONS:
        if markdown_section(text, heading) is None:
            errors.append(f"{path}: missing required section {heading!r}")

    declared_inputs: set[str] = set()
    runtime_inputs = markdown_section(text, "Runtime inputs")
    if runtime_inputs is not None:
        declaration_lines = [
            line.strip() for line in runtime_inputs.splitlines() if line.lstrip().startswith("- `")
        ]
        for line in declaration_lines:
            match = TASK_INPUT_LINE_PATTERN.fullmatch(line)
            if not match:
                errors.append(f"{path}: invalid runtime input declaration {line!r}")
                continue
            name = match.group("name")
            mode = match.group("mode")
            default = match.group("default")
            if not TASK_INPUT_NAME_PATTERN.fullmatch(name):
                errors.append(f"{path}: invalid runtime input name {name!r}")
            if name in declared_inputs:
                errors.append(f"{path}: duplicate runtime input {name!r}")
            declared_inputs.add(name)
            if mode == "required" and default is not None:
                errors.append(f"{path}: required input {name!r} must not declare a default")
            if mode == "optional" and not default:
                errors.append(f"{path}: optional input {name!r} must declare a default")

        if not declaration_lines and runtime_inputs.strip() != "None.":
            errors.append(f"{path}: Runtime inputs must contain declarations or exactly 'None.'")

    placeholders = set(TASK_PLACEHOLDER_PATTERN.findall(text))
    for name in sorted(placeholders - declared_inputs):
        errors.append(f"{path}: placeholder references undeclared runtime input {name!r}")
    for name in sorted(declared_inputs - placeholders):
        errors.append(f"{path}: declared runtime input {name!r} is never referenced")

    if not is_template and TASK_UNRESOLVED_PATTERN.search(text):
        errors.append(f"{path}: unresolved placeholder syntax is not allowed")
    if TASK_FORBIDDEN_SETTING_PATTERN.search(text):
        errors.append(f"{path}: runtime model or token setting is not allowed")
    if ".ai/" in text.lower():
        errors.append(f"{path}: legacy prompt path is not allowed")

    return errors


def validate_tasks() -> list[str]:
    errors: list[str] = []
    tasks_root = ROOT / ".agents/tasks"
    for path in sorted(tasks_root.rglob("*.md")):
        if path.parent != tasks_root:
            errors.append(f"{path.relative_to(ROOT)}: task files must be directly under .agents/tasks")
        errors.extend(validate_task_file(path, is_template=path.name == "_template.md"))
    return errors


def validate_skills() -> list[str]:
    errors: list[str] = []
    skills_root = ROOT / ".agents/skills"
    found = {path.parent.name for path in skills_root.glob("*/SKILL.md")}
    if found != EXPECTED_NAMES:
        errors.append(f"Skill set mismatch: expected {sorted(EXPECTED_NAMES)}, found {sorted(found)}")

    for name in sorted(found):
        skill_path = skills_root / name / "SKILL.md"
        text = skill_path.read_text(encoding="utf-8")
        metadata, metadata_errors = frontmatter(text, skill_path.relative_to(ROOT))
        errors.extend(metadata_errors)
        skill_name = metadata.get("name", "")
        description = metadata.get("description", "")
        if skill_name != name:
            errors.append(f"{skill_path.relative_to(ROOT)}: name must match folder")
        if not NAME_PATTERN.fullmatch(skill_name) or len(skill_name) > 64:
            errors.append(f"{skill_path.relative_to(ROOT)}: invalid skill name")
        if not description or len(description) > 1024:
            errors.append(f"{skill_path.relative_to(ROOT)}: description must contain 1-1024 characters")
        if len(text.splitlines()) >= 500:
            errors.append(f"{skill_path.relative_to(ROOT)}: SKILL.md must stay under 500 lines")

        openai_yaml = skills_root / name / "agents/openai.yaml"
        if not openai_yaml.is_file():
            errors.append(f"Missing Codex skill metadata: {openai_yaml.relative_to(ROOT)}")
        else:
            yaml_text = openai_yaml.read_text(encoding="utf-8")
            for field in ("display_name:", "short_description:", "default_prompt:"):
                if field not in yaml_text:
                    errors.append(f"{openai_yaml.relative_to(ROOT)}: missing {field}")
    return errors


def validate_workflows_and_rules() -> list[str]:
    errors: list[str] = []
    workflow_root = ROOT / ".agents/workflows"
    workflows = {path.stem for path in workflow_root.glob("*.md")}
    if workflows != EXPECTED_NAMES:
        errors.append(f"Workflow set mismatch: expected {sorted(EXPECTED_NAMES)}, found {sorted(workflows)}")

    for path in sorted(workflow_root.glob("*.md")):
        text = path.read_text(encoding="utf-8")
        metadata, metadata_errors = frontmatter(text, path.relative_to(ROOT))
        errors.extend(metadata_errors)
        if not metadata.get("description"):
            errors.append(f"{path.relative_to(ROOT)}: workflow description is required")
        if len(text) > 12_000:
            errors.append(f"{path.relative_to(ROOT)}: exceeds Antigravity 12,000-character limit")
        expected_reference = f".agents/skills/{path.stem}/SKILL.md"
        if expected_reference not in text:
            errors.append(f"{path.relative_to(ROOT)}: missing canonical skill reference")

    for path in sorted((ROOT / ".agents/rules").glob("*.md")):
        text = path.read_text(encoding="utf-8")
        if len(text) > 12_000:
            errors.append(f"{path.relative_to(ROOT)}: exceeds Antigravity 12,000-character limit")
        for reference in re.findall(r"@([^\s]+)", text):
            resolved = (path.parent / reference).resolve()
            if not resolved.exists():
                errors.append(f"{path.relative_to(ROOT)}: unresolved @ reference {reference}")
    return errors


def validate_extensions() -> list[str]:
    errors: list[str] = []
    live_mcp = json.loads((ROOT / ".agents/mcp_config.json").read_text(encoding="utf-8"))
    live_hooks = json.loads((ROOT / ".agents/hooks.json").read_text(encoding="utf-8"))
    if live_mcp != {"mcpServers": {}}:
        errors.append(".agents/mcp_config.json must contain no enabled servers")
    if live_hooks != {}:
        errors.append(".agents/hooks.json must contain no enabled hooks")

    plugin_root = ROOT / ".agents/templates/extensions/dual-plugin"
    antigravity = json.loads((plugin_root / "plugin.json").read_text(encoding="utf-8"))
    codex = json.loads((plugin_root / ".codex-plugin/plugin.json").read_text(encoding="utf-8"))
    if antigravity.get("name") != plugin_root.name:
        errors.append("Antigravity plugin name must match the plugin folder")
    if codex.get("name") != plugin_root.name:
        errors.append("Codex plugin name must match the plugin folder")
    for key in ("version", "description", "author", "interface"):
        if not codex.get(key):
            errors.append(f"Codex plugin manifest missing {key}")
    if not re.fullmatch(r"\d+\.\d+\.\d+", str(codex.get("version", ""))):
        errors.append("Codex plugin version must use strict semantic versioning")
    if codex.get("mcpServers") != "./.mcp.json" or not (plugin_root / ".mcp.json").is_file():
        errors.append("Codex plugin MCP companion path is invalid")
    if codex.get("skills") != "./skills/" or not (plugin_root / "skills").is_dir():
        errors.append("Codex plugin skills path is invalid")
    if list((ROOT / ".agents/plugins").glob("marketplace.json")):
        errors.append("No plugin marketplace may be registered by default")
    return errors


def validate_roles_and_agents() -> list[str]:
    errors: list[str] = []
    roles = {path.stem for path in (ROOT / ".agents/roles").glob("*.md")}
    agents = {path.stem for path in (ROOT / ".codex/agents").glob("*.toml")}
    if roles != EXPECTED_ROLES or agents != EXPECTED_ROLES:
        errors.append(f"Role/agent mismatch: roles={sorted(roles)}, agents={sorted(agents)}")
    if tomllib is None:
        errors.append("Python 3.11 or newer is required to validate Codex TOML agents")
        return errors

    for name in sorted(agents):
        path = ROOT / ".codex/agents" / f"{name}.toml"
        with path.open("rb") as handle:
            data = tomllib.load(handle)
        for key in ("name", "description", "developer_instructions"):
            if not data.get(key):
                errors.append(f"{path.relative_to(ROOT)}: missing {key}")
        if data.get("name") != name:
            errors.append(f"{path.relative_to(ROOT)}: name must match filename")
        if name in {"researcher", "reviewer"} and data.get("sandbox_mode") != "read-only":
            errors.append(f"{path.relative_to(ROOT)}: read-only role must narrow its sandbox")
    return errors


def validate_content_hygiene() -> list[str]:
    errors: list[str] = []
    roots = [ROOT / "AGENTS.md", ROOT / "README.md", ROOT / ".agents", ROOT / ".codex"]
    files: list[Path] = []
    for root in roots:
        if root.is_file():
            files.append(root)
        elif root.is_dir():
            files.extend(path for path in root.rglob("*") if path.is_file())

    for path in files:
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        lowered = text.lower()
        for banned in BANNED_TEXT:
            if banned in lowered:
                errors.append(f"{path.relative_to(ROOT)}: contains prohibited legacy or placeholder text {banned!r}")
        if re.search(r"\b[A-Za-z]:[\\/]", text):
            errors.append(f"{path.relative_to(ROOT)}: contains an absolute Windows path")
    return errors


def main() -> int:
    required = [
        "AGENTS.md",
        "README.md",
        ".agents/rules/core.md",
        ".agents/context/project.md",
        ".agents/specs/_template.md",
        ".agents/tasks/_template.md",
        ".agents/mcp_config.json",
        ".agents/hooks.json",
        ".agents/templates/extensions/dual-plugin/plugin.json",
        ".agents/templates/extensions/dual-plugin/.codex-plugin/plugin.json",
        ".agents/templates/ci/github-actions-validate.yml",
    ]
    errors = require_files(required)
    errors.extend(validate_skills())
    errors.extend(validate_workflows_and_rules())
    errors.extend(validate_tasks())
    errors.extend(validate_extensions())
    errors.extend(validate_roles_and_agents())
    errors.extend(validate_content_hygiene())

    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        print(f"Validation failed with {len(errors)} error(s).")
        return 1

    print(
        "Template validation passed: 11 skills/workflows, reusable tasks, 3 roles/adapters, "
        "inactive extensions, and required routing files are valid."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
