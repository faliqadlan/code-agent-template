#!/usr/bin/env python3
"""Validate the portable .agents v2 package using only the standard library."""

# code-agent-template:managed

from __future__ import annotations

import argparse
import ast
import importlib.util
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any


NAME_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
SEMVER_PATTERN = re.compile(r"^[0-9]+\.[0-9]+\.[0-9]+$")
MODEL_PATTERN = re.compile(r"^[^\s`/]+/[^\s`/]+(?:/[^\s`/]+)*$")
INPUT_NAME_PATTERN = re.compile(r"^[A-Z][A-Z0-9_]*$")
INPUT_LINE_PATTERN = re.compile(
    r"^-\s+`(?P<name>[^`]+)`\s+"
    r"\((?P<mode>required|optional)(?:,\s*default:\s*(?P<default>[^)]+))?\):\s+.+$"
)
PLACEHOLDER_PATTERN = re.compile(r"(?<!\$)\$([A-Z][A-Z0-9_]*)")
UNRESOLVED_PATTERN = re.compile(r"\{\{[^{}\n]+\}\}|\b(?:TBD|REPLACE_ME)\b", re.I)
MODEL_PREFERENCE_PATTERN = re.compile(r"^\s+([0-9]+)\.\s+`([^`\r\n]+)`\s*$")
CAPABILITY_PATTERN = re.compile(r"^\s+-\s+`([a-z0-9]+(?:-[a-z0-9]+)*)`\s*$")
MODE_PATTERN = re.compile(r"(?m)^- Mode:\s+`(single-pass|agentic-loop)`\s*$")
ITERATION_PATTERN = re.compile(r"(?m)^- Maximum iterations:\s+`([0-9]+)`\s*$")
APPROVAL_PATTERN = re.compile(r"(?m)^- Approval gates:\s+\S.*$")
ACCEPTANCE_PATTERN = re.compile(r"(?m)^- \[ \]\s+\S.*$")
METHOD_PATTERN = re.compile(r"(?m)^- Method:\s+\S.*$")
EXPECTED_PATTERN = re.compile(r"(?m)^- Expected result:\s+\S.*$")
MUTABLE_HEADING_PATTERN = re.compile(
    r"(?im)^##\s+(?:progress|results|current status|run state|execution log|"
    r"hidden reasoning|transcript)\s*$"
)
ABSOLUTE_WINDOWS_PATH = re.compile(r"\b[A-Za-z]:[\\/]")
MARKDOWN_LINK = re.compile(r"\[[^\]]+\]\(([^)]+)\)")
BACKTICK_AGENT_PATH = re.compile(r"`(\.agents/[A-Za-z0-9_./<>*$-]+)`")

TASK_SECTIONS = (
    "Objective",
    "Runtime requirements",
    "Runtime inputs",
    "Context and evidence",
    "Scope and constraints",
    "Execution policy",
    "Execution procedure",
    "Acceptance criteria",
    "Verification",
    "Output",
)
PROJECT_SECTIONS = (
    "Purpose",
    "Intended users",
    "Current capabilities and flows",
    "Technology stack",
    "Architecture and entry points",
    "Commands",
    "Data and integrations",
    "Repository conventions",
    "Constraints and hazards",
    "Evidence provenance",
    "Proposed behavior",
    "Superseded facts",
    "Known gaps",
    "Open questions",
)
MEMORY_SECTIONS = (
    "Active goal",
    "Active task",
    "Selected runtime",
    "Repository checkpoint",
    "Evidence provenance",
    "Completed work",
    "Current work",
    "Decisions",
    "Verification results",
    "Superseded facts",
    "Unknowns",
    "Blockers",
    "Next action",
    "Safety check",
)
ROLE_SECTIONS = ("Purpose", "Permission boundary", "Inputs", "Output", "Non-goals")
TASK_OUTCOMES = {"succeeded", "failed", "blocked", "awaiting-approval", "exhausted"}
TASK_TEMPLATE_MARKERS = (
    "describe the immutable cross-agent assignment",
    "state the observable result for",
    "identify evidence the executing agent",
    "describe actions requiring approval",
    "define an observable result for",
    "define the smallest relevant command",
    "state the successful outcome",
)
LEGACY_PATHS = (
    ".ai/prompts/",
    ".agents/workflows/",
    ".agents/rules/",
    ".agents/plugins/",
    ".agents/mcp_config.json",
    ".agents/hooks.json",
)
SECRET_PATTERNS = (
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    re.compile(r"\bgh[pousr]_[A-Za-z0-9]{20,}\b"),
    re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b"),
    re.compile(
        r"(?im)^\s*(?:export\s+)?[A-Z0-9_]*(?:API_KEY|ACCESS_TOKEN|PASSWORD|SECRET)"
        r"\s*=\s*(?!\$|<|None\b|Unknown\b|SYNTHETIC_)[^\s#]+"
    ),
    re.compile(r"(?im)^\s*Authorization:\s*Bearer\s+(?!\$|<|SYNTHETIC_)\S+"),
)


def markdown_section(text: str, heading: str) -> str | None:
    match = re.search(rf"(?ms)^## {re.escape(heading)}\s*$\n(.*?)(?=^## |\Z)", text)
    return match.group(1).strip() if match else None


def clean_scalar(value: str, path: Path, line_number: int, errors: list[str]) -> str:
    value = value.strip()
    if not value:
        return ""
    if value[0:1] in {"'", '"'}:
        try:
            parsed = ast.literal_eval(value)
        except (SyntaxError, ValueError):
            errors.append(f"{path}:{line_number}: invalid quoted YAML scalar")
            return value
        if not isinstance(parsed, str):
            errors.append(f"{path}:{line_number}: frontmatter scalars must be strings")
            return str(parsed)
        return parsed
    if re.search(r":\s", value):
        errors.append(f"{path}:{line_number}: quote YAML scalars containing ': '")
    if value.startswith(("[", "{", "&", "*", "!")):
        errors.append(f"{path}:{line_number}: unsupported complex YAML scalar")
    return value


def parse_frontmatter(path: Path) -> tuple[dict[str, Any], str, list[str]]:
    errors: list[str] = []
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return {}, "", [f"{path}: file is not valid UTF-8"]
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}, text, [f"{path}: missing opening YAML frontmatter delimiter"]
    try:
        closing = next(i for i, line in enumerate(lines[1:], 1) if line.strip() == "---")
    except StopIteration:
        return {}, text, [f"{path}: missing closing YAML frontmatter delimiter"]

    metadata: dict[str, Any] = {}
    active_block: str | None = None
    block_fold = False
    block_lines: list[str] = []
    active_mapping: str | None = None

    def flush_block() -> None:
        nonlocal active_block, block_lines
        if active_block is not None:
            metadata[active_block] = (
                " ".join(item.strip() for item in block_lines).strip()
                if block_fold
                else "\n".join(item.rstrip() for item in block_lines).strip()
            )
        active_block = None
        block_lines = []

    for index, line in enumerate(lines[1:closing], 2):
        if not line.strip() or line.lstrip().startswith("#"):
            if active_block is not None:
                block_lines.append("")
            continue
        if line.startswith((" ", "\t")):
            if active_block is not None:
                block_lines.append(line.lstrip())
                continue
            if active_mapping == "metadata":
                nested = line.strip()
                if ":" not in nested:
                    errors.append(f"{path}:{index}: invalid metadata mapping entry")
                    continue
                key, value = nested.split(":", 1)
                key = key.strip()
                mapping = metadata.setdefault("metadata", {})
                if key in mapping:
                    errors.append(f"{path}:{index}: duplicate metadata key {key!r}")
                else:
                    mapping[key] = clean_scalar(value, path, index, errors)
                continue
            errors.append(f"{path}:{index}: unexpected indented frontmatter content")
            continue

        flush_block()
        active_mapping = None
        if ":" not in line:
            errors.append(f"{path}:{index}: invalid frontmatter line")
            continue
        key, raw_value = line.split(":", 1)
        key = key.strip()
        raw_value = raw_value.strip()
        if not key:
            errors.append(f"{path}:{index}: empty frontmatter key")
            continue
        if key in metadata:
            errors.append(f"{path}:{index}: duplicate frontmatter field {key!r}")
            continue
        if raw_value in {"|", ">"}:
            active_block = key
            block_fold = raw_value == ">"
            block_lines = []
        elif key == "metadata" and not raw_value:
            metadata[key] = {}
            active_mapping = key
        else:
            metadata[key] = clean_scalar(raw_value, path, index, errors)
    flush_block()
    body = "\n".join(lines[closing + 1 :]).strip()
    return metadata, body, errors


class Validator:
    def __init__(self, root: Path, *, strict_skills: bool = False) -> None:
        self.root = root.resolve()
        self.agents = self.root / ".agents"
        self.strict_skills = strict_skills
        self.errors: list[str] = []
        self.manifest: dict[str, Any] = {}

    def display(self, path: Path) -> str:
        try:
            return path.relative_to(self.root).as_posix()
        except ValueError:
            return str(path)

    def is_generated_or_ignored(self, path: Path) -> bool:
        try:
            parts = path.relative_to(self.agents).parts
        except ValueError:
            return False
        return ".runs" in parts or "__pycache__" in parts or path.suffix.lower() == ".pyc"

    def error(self, message: str) -> None:
        self.errors.append(message)

    def load_manifest(self) -> None:
        path = self.agents / "manifest.json"
        if not path.is_file():
            self.error("Missing required file: .agents/manifest.json")
            return
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            self.error(f".agents/manifest.json: invalid JSON: {exc}")
            return
        if data.get("schema_version") != 1:
            self.error(".agents/manifest.json: schema_version must be 1")
        version = data.get("template_version")
        if not isinstance(version, str) or not SEMVER_PATTERN.fullmatch(version):
            self.error(".agents/manifest.json: template_version must use semantic versioning")
        if data.get("python_requires") != ">=3.10":
            self.error(".agents/manifest.json: python_requires must be '>=3.10'")
        core = data.get("core")
        if not isinstance(core, dict):
            self.error(".agents/manifest.json: core must be an object")
            return
        for field in ("files", "skills", "roles", "tests"):
            values = core.get(field)
            if not isinstance(values, list) or not values or not all(
                isinstance(item, str) and item for item in values
            ):
                self.error(f".agents/manifest.json: core.{field} must be a non-empty string list")
            elif len(values) != len(set(values)):
                self.error(f".agents/manifest.json: core.{field} contains duplicates")
        evaluations = core.get("evaluations")
        if not isinstance(evaluations, dict):
            self.error(".agents/manifest.json: core.evaluations must be an object")
        else:
            if evaluations.get("integration_suite") != "evals/cases/core.json":
                self.error(".agents/manifest.json: invalid integration suite path")
            for field in (
                "integration_cases",
                "routing_queries_per_skill",
                "output_cases_per_skill",
            ):
                if not isinstance(evaluations.get(field), int) or evaluations[field] < 1:
                    self.error(f".agents/manifest.json: core.evaluations.{field} must be positive")
            fixtures = evaluations.get("fixtures")
            if not isinstance(fixtures, list) or not fixtures or len(fixtures) != len(set(fixtures)):
                self.error(".agents/manifest.json: core.evaluations.fixtures must be unique and non-empty")
        self.manifest = data

    def core(self, field: str) -> list[str]:
        values = self.manifest.get("core", {}).get(field, [])
        return values if isinstance(values, list) else []

    def validate_structure(self) -> None:
        if not self.agents.is_dir():
            self.error("Missing required directory: .agents")
            return
        for relative in self.core("files"):
            candidate = Path(relative)
            if candidate.is_absolute() or ".." in candidate.parts or "\\" in relative:
                self.error(f".agents/manifest.json: unsafe core file path {relative!r}")
                continue
            if not (self.agents / candidate).is_file():
                self.error(f"Missing manifest-declared core file: .agents/{relative}")
        for name in self.core("skills"):
            if not NAME_PATTERN.fullmatch(name):
                self.error(f".agents/manifest.json: invalid core skill name {name!r}")
            if not (self.agents / "skills" / name / "SKILL.md").is_file():
                self.error(f"Missing manifest-declared core skill: {name}")
        for name in self.core("roles"):
            if not NAME_PATTERN.fullmatch(name):
                self.error(f".agents/manifest.json: invalid core role name {name!r}")
            if not (self.agents / "roles" / f"{name}.md").is_file():
                self.error(f"Missing manifest-declared core role: {name}")
        for name in self.core("tests"):
            if not (self.agents / "tests" / name).is_file():
                self.error(f"Missing manifest-declared test: .agents/tests/{name}")
        evaluations = self.manifest.get("core", {}).get("evaluations", {})
        for name in evaluations.get("fixtures", []) if isinstance(evaluations, dict) else []:
            if not NAME_PATTERN.fullmatch(name) or not (self.agents / "evals/fixtures" / name).is_dir():
                self.error(f"Missing or invalid manifest-declared evaluation fixture: {name}")

        for path in self.agents.rglob("*"):
            if self.is_generated_or_ignored(path):
                continue
            if not path.is_symlink():
                continue
            try:
                resolved = path.resolve(strict=True)
            except OSError as exc:
                self.error(f"{self.display(path)}: broken symbolic link: {exc}")
                continue
            if self.agents not in resolved.parents and resolved != self.agents:
                self.error(f"{self.display(path)}: symbolic link escapes .agents")

    def validate_skills(self) -> None:
        root = self.agents / "skills"
        if not root.is_dir():
            self.error("Missing required directory: .agents/skills")
            return
        core_skills = set(self.core("skills"))
        skill_paths: list[Path] = []
        for directory in sorted(path for path in root.iterdir() if path.is_dir()):
            skill = directory / "SKILL.md"
            if not skill.is_file():
                self.error(f"{self.display(directory)}: skill directory is missing SKILL.md")
                continue
            skill_paths.append(skill)
            metadata, body, errors = parse_frontmatter(skill)
            self.errors.extend(self.display_error_paths(errors))
            name = metadata.get("name", "")
            description = metadata.get("description", "")
            if name != directory.name:
                self.error(f"{self.display(skill)}: name must match parent directory")
            if not isinstance(name, str) or not NAME_PATTERN.fullmatch(name) or len(name) > 64:
                self.error(f"{self.display(skill)}: invalid skill name")
            if not isinstance(description, str) or not description or len(description) > 1024:
                self.error(f"{self.display(skill)}: description must contain 1-1024 characters")
            compatibility = metadata.get("compatibility")
            if compatibility is not None and (
                not isinstance(compatibility, str) or not (1 <= len(compatibility) <= 500)
            ):
                self.error(f"{self.display(skill)}: compatibility must contain 1-500 characters")
            if not body:
                self.error(f"{self.display(skill)}: Markdown body must not be empty")
            if len(skill.read_text(encoding="utf-8").splitlines()) >= 500:
                self.error(f"{self.display(skill)}: SKILL.md must stay under 500 lines")
            if directory.name in core_skills and metadata.get("license") != "MIT":
                self.error(f"{self.display(skill)}: core skills must declare license: MIT")
            if directory.name in core_skills:
                for required in ("evals/trigger_queries.json", "evals/evals.json"):
                    if not (directory / required).is_file():
                        self.error(f"{self.display(directory / required)}: missing core skill evaluation")

        if self.strict_skills:
            executable = shutil.which("skills-ref")
            if not executable:
                self.error(
                    "Strict skill validation requested, but 'skills-ref' is not installed. "
                    "Install the official reference validator documented at "
                    "https://agentskills.io/specification, confirm `skills-ref validate` is on "
                    "PATH, and retry."
                )
            else:
                for skill in skill_paths:
                    result = subprocess.run(
                        [executable, "validate", str(skill.parent)],
                        cwd=self.root,
                        text=True,
                        capture_output=True,
                        shell=False,
                    )
                    if result.returncode:
                        detail = (result.stdout + result.stderr).strip()
                        self.error(f"{self.display(skill.parent)}: skills-ref failed: {detail}")

    def display_error_paths(self, errors: list[str]) -> list[str]:
        converted: list[str] = []
        root_text = str(self.root)
        for error in errors:
            converted.append(error.replace(root_text + "\\", "").replace(root_text + "/", ""))
        return converted

    def validate_task_file(self, path: Path, *, template: bool = False) -> None:
        text = path.read_text(encoding="utf-8")
        metadata, body, errors = parse_frontmatter(path)
        self.errors.extend(self.display_error_paths(errors))
        allowed = {"name", "description", "version"}
        for field in sorted(set(metadata) - allowed):
            self.error(f"{self.display(path)}: unsupported task frontmatter field {field!r}")
        name = metadata.get("name", "")
        description = metadata.get("description", "")
        version_text = str(metadata.get("version", ""))
        if not isinstance(name, str) or not NAME_PATTERN.fullmatch(name) or len(name) > 64:
            self.error(f"{self.display(path)}: invalid task name")
        if not isinstance(description, str) or not description or len(description) > 1024:
            self.error(f"{self.display(path)}: description must contain 1-1024 characters")
        version = int(version_text) if re.fullmatch(r"[1-9][0-9]*", version_text) else 0
        if not version:
            self.error(f"{self.display(path)}: version must be a positive integer")
        if not template and name and version and path.name != f"{name}-v{version}.md":
            self.error(f"{self.display(path)}: filename must be {name}-v{version}.md")
        if not body:
            self.error(f"{self.display(path)}: task body must not be empty")
        for heading in TASK_SECTIONS:
            section = markdown_section(text, heading)
            if section is None:
                self.error(f"{self.display(path)}: missing required section {heading!r}")
            elif not section:
                self.error(f"{self.display(path)}: section {heading!r} must not be empty")

        runtime = markdown_section(text, "Runtime requirements") or ""
        lines = runtime.splitlines()
        cap_indexes = [i for i, line in enumerate(lines) if line == "- Required capabilities:"]
        capabilities: list[str] = []
        if len(cap_indexes) != 1:
            self.error(f"{self.display(path)}: Runtime requirements must declare Required capabilities once")
        else:
            for line in lines[cap_indexes[0] + 1 :]:
                match = CAPABILITY_PATTERN.fullmatch(line)
                if not match:
                    break
                capabilities.append(match.group(1))
            if not capabilities:
                self.error(f"{self.display(path)}: at least one required capability is required")
            elif len(capabilities) != len(set(capabilities)):
                self.error(f"{self.display(path)}: required capabilities must be unique")

        preference_indexes = [
            i for i, line in enumerate(lines) if line.startswith("- Ordered model preferences:")
        ]
        preferences: list[str] = []
        if len(preference_indexes) != 1:
            self.error(f"{self.display(path)}: Ordered model preferences must be declared once")
        else:
            index = preference_indexes[0]
            value = lines[index].split(":", 1)[1].strip()
            if value == "None.":
                pass
            elif value:
                self.error(f"{self.display(path)}: model preferences must be a numbered list or None.")
            else:
                expected = 1
                for line in lines[index + 1 :]:
                    if line.startswith("- Require preferred model:"):
                        break
                    if not line.strip():
                        continue
                    match = MODEL_PREFERENCE_PATTERN.fullmatch(line)
                    if not match:
                        self.error(f"{self.display(path)}: invalid model preference line {line!r}")
                        continue
                    if int(match.group(1)) != expected:
                        self.error(f"{self.display(path)}: model preference numbering must be contiguous")
                    expected += 1
                    model = match.group(2)
                    if not MODEL_PATTERN.fullmatch(model):
                        self.error(f"{self.display(path)}: invalid provider/model preference {model!r}")
                    preferences.append(model)
                if not preferences:
                    self.error(f"{self.display(path)}: model preferences list must not be empty")
        require_matches = re.findall(r"(?m)^- Require preferred model:\s+`(true|false)`\s*$", runtime)
        if len(require_matches) != 1:
            self.error(f"{self.display(path)}: Require preferred model must be true or false exactly once")
        elif require_matches[0] == "true" and not preferences:
            self.error(f"{self.display(path)}: required preferred model needs at least one preference")
        if len(preferences) != len(set(preferences)):
            self.error(f"{self.display(path)}: model preferences must be unique")

        declared: set[str] = set()
        inputs = markdown_section(text, "Runtime inputs")
        if inputs is not None:
            input_lines = [line.strip() for line in inputs.splitlines() if line.strip()]
            if input_lines != ["None."]:
                if "None." in input_lines:
                    self.error(f"{self.display(path)}: Runtime inputs cannot mix None. and declarations")
                for line in input_lines:
                    match = INPUT_LINE_PATTERN.fullmatch(line)
                    if not match:
                        self.error(f"{self.display(path)}: invalid runtime input declaration {line!r}")
                        continue
                    input_name = match.group("name")
                    mode = match.group("mode")
                    default = match.group("default")
                    if not INPUT_NAME_PATTERN.fullmatch(input_name):
                        self.error(f"{self.display(path)}: invalid runtime input name {input_name!r}")
                    if input_name in declared:
                        self.error(f"{self.display(path)}: duplicate runtime input {input_name!r}")
                    declared.add(input_name)
                    if mode == "required" and default is not None:
                        self.error(f"{self.display(path)}: required input cannot declare a default")
                    if mode == "optional" and not default:
                        self.error(f"{self.display(path)}: optional input must declare a default")
        placeholders = set(PLACEHOLDER_PATTERN.findall(text))
        for name_ in sorted(placeholders - declared):
            self.error(f"{self.display(path)}: placeholder references undeclared input {name_!r}")
        for name_ in sorted(declared - placeholders):
            self.error(f"{self.display(path)}: declared input {name_!r} is never referenced")

        if not template and UNRESOLVED_PATTERN.search(text):
            self.error(f"{self.display(path)}: unresolved placeholder syntax is not allowed")
        if not template:
            lowered = text.lower()
            for marker in TASK_TEMPLATE_MARKERS:
                if marker in lowered:
                    self.error(f"{self.display(path)}: unresolved template text {marker!r}")
        policy = markdown_section(text, "Execution policy") or ""
        modes = MODE_PATTERN.findall(policy)
        iterations = ITERATION_PATTERN.findall(policy)
        if len(modes) != 1 or len(iterations) != 1:
            self.error(f"{self.display(path)}: Execution policy needs one mode and iteration count")
        elif int(iterations[0]) < 1 or (modes[0] == "single-pass" and int(iterations[0]) != 1):
            self.error(f"{self.display(path)}: invalid execution iteration policy")
        if len(APPROVAL_PATTERN.findall(policy)) != 1:
            self.error(f"{self.display(path)}: Execution policy must declare approval gates once")
        acceptance = markdown_section(text, "Acceptance criteria") or ""
        if not ACCEPTANCE_PATTERN.search(acceptance):
            self.error(f"{self.display(path)}: at least one unchecked acceptance criterion is required")
        verification = markdown_section(text, "Verification") or ""
        if len(METHOD_PATTERN.findall(verification)) != 1 or len(EXPECTED_PATTERN.findall(verification)) != 1:
            self.error(f"{self.display(path)}: Verification needs one Method and Expected result")
        output = markdown_section(text, "Output") or ""
        missing = sorted(outcome for outcome in TASK_OUTCOMES if f"`{outcome}`" not in output)
        if missing:
            self.error(f"{self.display(path)}: Output is missing outcomes {missing}")
        if MUTABLE_HEADING_PATTERN.search(text):
            self.error(f"{self.display(path)}: mutable run-state or transcript heading is not allowed")

    def validate_tasks(self) -> None:
        root = self.agents / "tasks"
        if not root.is_dir():
            self.error("Missing required directory: .agents/tasks")
            return
        for path in sorted(item for item in root.rglob("*") if item.is_file()):
            if path.suffix.lower() != ".md":
                self.error(f"{self.display(path)}: task library accepts Markdown files only")
                continue
            if path.parent != root:
                self.error(f"{self.display(path)}: task files must be directly under .agents/tasks")
            self.validate_task_file(path, template=path.name == "_template.md")

    def require_sections(self, path: Path, headings: tuple[str, ...]) -> None:
        if not path.is_file():
            return
        text = path.read_text(encoding="utf-8")
        for heading in headings:
            if markdown_section(text, heading) is None:
                self.error(f"{self.display(path)}: missing required section {heading!r}")

    def validate_context_roles_memory(self) -> None:
        self.require_sections(self.agents / "context/project.md", PROJECT_SECTIONS)
        self.require_sections(self.agents / "memory/state.template.md", MEMORY_SECTIONS)
        role_root = self.agents / "roles"
        for path in sorted(role_root.glob("*.md")):
            self.require_sections(path, ROLE_SECTIONS)
        ignored = self.agents / "memory/.gitignore"
        if ignored.is_file():
            entries = {
                line.strip()
                for line in ignored.read_text(encoding="utf-8").splitlines()
                if line.strip() and not line.lstrip().startswith("#")
            }
            if entries != {"state.md", "!.gitignore", "!state.template.md"}:
                self.error(".agents/memory/.gitignore: must ignore only state.md and retain templates")

    def validate_managed_markers(self) -> None:
        paths: list[Path] = []
        for relative in self.core("files"):
            path = self.agents / relative
            if path.suffix in {".md", ".py"}:
                paths.append(path)
        paths.extend(self.agents / "skills" / name / "SKILL.md" for name in self.core("skills"))
        paths.extend(self.agents / "roles" / f"{name}.md" for name in self.core("roles"))
        paths.extend(self.agents / "tests" / name for name in self.core("tests"))
        for path in paths:
            if not path.is_file():
                continue
            text = path.read_text(encoding="utf-8")
            if "code-agent-template:managed" not in text:
                self.error(f"{self.display(path)}: missing managed provenance marker")

    def validate_links(self) -> None:
        for path in sorted(self.agents.rglob("*.md")):
            if self.is_generated_or_ignored(path):
                continue
            text = path.read_text(encoding="utf-8")
            for target in MARKDOWN_LINK.findall(text):
                target = target.strip().split("#", 1)[0]
                if not target or target.startswith(("http://", "https://", "mailto:", "#")):
                    continue
                if "<" in target or ">" in target:
                    continue
                resolved = (path.parent / target).resolve()
                if not resolved.exists():
                    self.error(f"{self.display(path)}: broken relative link {target!r}")
            for target in BACKTICK_AGENT_PATH.findall(text):
                if any(marker in target for marker in ("<", ">", "*", "$")):
                    continue
                if target == ".agents/memory/state.md":
                    continue
                resolved = self.root / target
                if not resolved.exists():
                    self.error(f"{self.display(path)}: broken referenced path {target!r}")

    def validate_hygiene(self) -> None:
        scan_paths = [
            path
            for path in self.agents.rglob("*")
            if path.is_file() and not self.is_generated_or_ignored(path)
        ]
        root_readme = self.root / "README.md"
        if root_readme.is_file():
            scan_paths.append(root_readme)
        for path in scan_paths:
            if path.suffix.lower() not in {".md", ".py", ".json", ".txt", ""}:
                continue
            try:
                text = path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                continue
            if path.name not in {"validate_template.py", "test_validate_template.py"}:
                for pattern in SECRET_PATTERNS:
                    if pattern.search(text):
                        self.error(f"{self.display(path)}: contains a high-confidence secret-like value")
                        break
            if path.name not in {"validate_template.py", "test_validate_template.py"}:
                if ABSOLUTE_WINDOWS_PATH.search(text):
                    self.error(f"{self.display(path)}: contains an absolute Windows path")
                lowered = text.lower()
                for legacy in LEGACY_PATHS:
                    if legacy in lowered:
                        self.error(f"{self.display(path)}: contains removed legacy path {legacy!r}")

    def validate_licenses_and_readme(self) -> None:
        package_license = self.agents / "LICENSE"
        root_license = self.root / "LICENSE"
        if package_license.is_file() and root_license.is_file():
            if package_license.read_bytes() != root_license.read_bytes():
                self.error("LICENSE and .agents/LICENSE must be identical")
        readme = self.root / "README.md"
        if not readme.is_file():
            return
        text = readme.read_text(encoding="utf-8")
        if "# Universal Coding-Agent Template" not in text:
            return
        for required in (
            "2.0.0",
            "manual-bootstrap",
            "python .agents/scripts/validate_template.py",
            "--strict-skills",
            "python -m unittest discover -s .agents/tests",
            "python .agents/scripts/evaluate_agents.py validate",
        ):
            if required not in text:
                self.error(f"README.md: missing v2 contract text {required!r}")
        review = self.root / "docs/agents-v2-design-review.md"
        if not review.is_file():
            self.error("Missing maintainer evidence review: docs/agents-v2-design-review.md")

    def validate_evaluations(self) -> None:
        path = self.agents / "scripts/evaluate_agents.py"
        if not path.is_file():
            return
        spec = importlib.util.spec_from_file_location("agents_evaluator", path)
        if spec is None or spec.loader is None:
            self.error(".agents/scripts/evaluate_agents.py: could not load evaluation validator")
            return
        module = importlib.util.module_from_spec(spec)
        try:
            spec.loader.exec_module(module)
            errors = module.collect_validation_errors(self.root)
        except Exception as exc:  # pragma: no cover - defensive integration boundary
            self.error(f".agents/scripts/evaluate_agents.py: validation crashed: {exc}")
            return
        self.errors.extend(str(error) for error in errors)

    def run(self) -> list[str]:
        self.load_manifest()
        if not self.agents.is_dir():
            return self.errors
        self.validate_structure()
        self.validate_skills()
        self.validate_tasks()
        self.validate_context_roles_memory()
        self.validate_managed_markers()
        self.validate_links()
        self.validate_hygiene()
        self.validate_licenses_and_readme()
        self.validate_evaluations()
        return self.errors


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parents[2],
        help="Repository root containing .agents (default: inferred from this script).",
    )
    parser.add_argument(
        "--strict-skills",
        action="store_true",
        help="Require and run the official skills-ref validator for every skill.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    validator = Validator(args.root, strict_skills=args.strict_skills)
    errors = validator.run()
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        print(f"Validation failed with {len(errors)} error(s).")
        if args.strict_skills and any("skills-ref" in error and "not installed" in error for error in errors):
            return 2
        return 1
    skills = len(validator.core("skills"))
    roles = len(validator.core("roles"))
    version = validator.manifest.get("template_version", "unknown")
    print(
        f"Portable structural validation passed for .agents {version}: "
        f"{skills} core skills, {roles} roles, tasks, memory, tests, and eval contracts."
    )
    print(
        "This result does not establish behavioral quality, prompt-injection resistance, "
        "runtime permission enforcement, or cross-agent portability."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
