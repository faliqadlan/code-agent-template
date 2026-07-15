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
        ".agents/mcp_config.json",
        ".agents/hooks.json",
        ".agents/templates/extensions/dual-plugin/plugin.json",
        ".agents/templates/extensions/dual-plugin/.codex-plugin/plugin.json",
        ".agents/templates/ci/github-actions-validate.yml",
    ]
    errors = require_files(required)
    errors.extend(validate_skills())
    errors.extend(validate_workflows_and_rules())
    errors.extend(validate_extensions())
    errors.extend(validate_roles_and_agents())
    errors.extend(validate_content_hygiene())

    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        print(f"Validation failed with {len(errors)} error(s).")
        return 1

    print(
        "Template validation passed: 10 skills/workflows, 3 roles/adapters, "
        "inactive extensions, and required routing files are valid."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
