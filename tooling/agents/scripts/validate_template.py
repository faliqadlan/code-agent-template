#!/usr/bin/env python3
"""Validate the operational .agents 2.2 package and optional maintainer tooling."""

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
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any


NAME_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
SEMVER_PATTERN = re.compile(r"^[0-9]+\.[0-9]+\.[0-9]+$")
ABSOLUTE_WINDOWS_PATH = re.compile(r"\b[A-Za-z]:[\\/]")
MARKDOWN_LINK = re.compile(r"\[[^\]]+\]\(([^)]+)\)")
BACKTICK_AGENT_PATH = re.compile(r"`(\.agents/[A-Za-z0-9_./<>*$-]+)`")
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
DEFAULT_ROOT = Path(__file__).resolve().parents[3]
TOOLING_ROOT_REL = Path("tooling/agents")
TASK_VALIDATOR_REL = Path(".agents/skills/agent-task/scripts/validate_task.py")
LEGACY_RUNTIME_PATHS = (
    ".agents/evals",
    ".agents/scripts",
    ".agents/tests",
    ".agents/LICENSE",
)
EXECUTABLE_SUFFIXES = {".bat", ".cmd", ".js", ".ps1", ".py", ".sh"}
SOURCE_FIELDS = {
    "schema_version",
    "catalog_url",
    "source_url",
    "source_revision",
    "source_path",
    "classification",
    "license",
    "validated_with",
    "validated_at",
}
SOURCE_REVISION_PATTERN = re.compile(r"^(?:[0-9a-f]{40}|[0-9a-f]{64})$")
SOURCE_REPOSITORY_PATTERN = re.compile(
    r"^https://github\.com/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+(?:\.git)?/?$"
)
CATALOG_URL_PATTERN = re.compile(
    r"^https://(?:officialskills\.sh(?:/|$)|github\.com/VoltAgent/awesome-agent-skills(?:[/#?]|$))"
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


def load_task_validator(path: Path) -> Any:
    spec = importlib.util.spec_from_file_location("runtime_task_validator", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not load runtime task validator: {path}")
    module = importlib.util.module_from_spec(spec)
    previous = sys.dont_write_bytecode
    sys.dont_write_bytecode = True
    try:
        spec.loader.exec_module(module)
    finally:
        sys.dont_write_bytecode = previous
    return module


class Validator:
    def __init__(
        self,
        root: Path,
        *,
        strict_skills: bool = False,
        runtime_only: bool = False,
    ) -> None:
        self.root = root.resolve()
        self.agents = self.root / ".agents"
        self.tooling = self.root / TOOLING_ROOT_REL
        self.strict_skills = strict_skills
        self.runtime_only = runtime_only
        self.errors: list[str] = []
        self.manifest: dict[str, Any] = {}
        self.tooling_manifest: dict[str, Any] = {}

    def display(self, path: Path) -> str:
        try:
            return path.relative_to(self.root).as_posix()
        except ValueError:
            return str(path)

    def is_generated_or_ignored(self, path: Path) -> bool:
        try:
            parts = path.relative_to(self.root).parts
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
        if data.get("schema_version") != 2:
            self.error(".agents/manifest.json: schema_version must be 2")
        version = data.get("template_version")
        if not isinstance(version, str) or not SEMVER_PATTERN.fullmatch(version):
            self.error(".agents/manifest.json: template_version must use semantic versioning")
        if "python_requires" in data:
            self.error(".agents/manifest.json: operational manifest must not declare python_requires")
        core = data.get("core")
        if not isinstance(core, dict):
            self.error(".agents/manifest.json: core must be an object")
            return
        forbidden = {"evaluations", "fixtures", "scripts", "tests"} & set(core)
        if forbidden:
            self.error(
                ".agents/manifest.json: operational core contains maintainer fields "
                f"{sorted(forbidden)}"
            )
        for field in ("files", "skills", "roles"):
            values = core.get(field)
            if not isinstance(values, list) or not values or not all(
                isinstance(item, str) and item for item in values
            ):
                self.error(f".agents/manifest.json: core.{field} must be a non-empty string list")
            elif len(values) != len(set(values)):
                self.error(f".agents/manifest.json: core.{field} contains duplicates")
        task_validators = core.get("task_validators")
        if not isinstance(task_validators, list) or not all(
            isinstance(item, str) and item for item in task_validators
        ):
            self.error(
                ".agents/manifest.json: core.task_validators must be a string list"
            )
        elif len(task_validators) != len(set(task_validators)):
            self.error(".agents/manifest.json: core.task_validators contains duplicates")
        elif "agent-task" in core.get("skills", []) and task_validators != [
            TASK_VALIDATOR_REL.relative_to(".agents").as_posix()
        ]:
            self.error(
                ".agents/manifest.json: agent-task must declare its single task validator"
            )
        elif "agent-task" not in core.get("skills", []) and task_validators:
            self.error(
                ".agents/manifest.json: task validators require the agent-task skill"
            )
        self.manifest = data

    def load_tooling_manifest(self) -> None:
        path = self.tooling / "manifest.json"
        if not path.is_file():
            self.error("Missing maintainer tooling manifest: tooling/agents/manifest.json")
            return
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            self.error(f"tooling/agents/manifest.json: invalid JSON: {exc}")
            return
        if data.get("schema_version") != 1:
            self.error("tooling/agents/manifest.json: schema_version must be 1")
        version = data.get("tooling_version")
        if not isinstance(version, str) or not SEMVER_PATTERN.fullmatch(version):
            self.error("tooling/agents/manifest.json: tooling_version must use semantic versioning")
        elif version != self.manifest.get("template_version"):
            self.error("Runtime and tooling versions must match")
        if data.get("python_requires") != ">=3.10":
            self.error("tooling/agents/manifest.json: python_requires must be '>=3.10'")
        for field in ("scripts", "tests"):
            values = data.get(field)
            if not isinstance(values, list) or not values or not all(
                isinstance(item, str) and item for item in values
            ):
                self.error(f"tooling/agents/manifest.json: {field} must be a non-empty string list")
            elif len(values) != len(set(values)):
                self.error(f"tooling/agents/manifest.json: {field} contains duplicates")
        evaluations = data.get("evaluations")
        if not isinstance(evaluations, dict):
            self.error("tooling/agents/manifest.json: evaluations must be an object")
        else:
            if evaluations.get("integration_suite") != "evals/cases/core.json":
                self.error("tooling/agents/manifest.json: invalid integration suite path")
            if evaluations.get("skill_eval_root") != "evals/skills":
                self.error("tooling/agents/manifest.json: invalid skill evaluation root")
            for field in (
                "integration_cases",
                "routing_queries_per_skill",
                "output_cases_per_skill",
            ):
                if not isinstance(evaluations.get(field), int) or evaluations[field] < 1:
                    self.error(
                        f"tooling/agents/manifest.json: evaluations.{field} must be positive"
                    )
            fixtures = evaluations.get("fixtures")
            if not isinstance(fixtures, list) or not fixtures or len(fixtures) != len(
                set(fixtures)
            ):
                self.error(
                    "tooling/agents/manifest.json: evaluations.fixtures must be unique and non-empty"
                )
        self.tooling_manifest = data

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
        declared_executables: set[str] = set()
        for relative in self.core("task_validators"):
            candidate = Path(relative)
            if candidate.is_absolute() or ".." in candidate.parts or "\\" in relative:
                self.error(f".agents/manifest.json: unsafe task validator path {relative!r}")
                continue
            if candidate.suffix != ".py" or not relative.startswith(
                "skills/agent-task/scripts/"
            ):
                self.error(
                    ".agents/manifest.json: task validators must be Python resources under "
                    "skills/agent-task/scripts/"
                )
            declared_executables.add(candidate.as_posix())
            if not (self.agents / candidate).is_file():
                self.error(f"Missing manifest-declared task validator: .agents/{relative}")

        for relative in LEGACY_RUNTIME_PATHS:
            if (self.root / relative).exists():
                self.error(f"Operational package contains removed maintainer path: {relative}")
        for eval_dir in sorted((self.agents / "skills").glob("*/evals")):
            if eval_dir.exists():
                self.error(
                    f"Operational skill contains moved evaluation data: {self.display(eval_dir)}"
                )
        observed_executables = {
            path.relative_to(self.agents).as_posix()
            for path in self.agents.rglob("*")
            if path.is_file()
            and path.suffix.lower() in EXECUTABLE_SUFFIXES
            and not self.is_generated_or_ignored(path)
        }
        if observed_executables != declared_executables:
            self.error(
                ".agents executable inventory mismatch: "
                f"declared={sorted(declared_executables)}, observed={sorted(observed_executables)}"
            )

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

    def validate_tooling_structure(self) -> None:
        if not self.tooling.is_dir():
            self.error("Missing maintainer tooling directory: tooling/agents")
            return
        for field in ("scripts", "tests"):
            for relative in self.tooling_manifest.get(field, []):
                candidate = Path(relative)
                if candidate.is_absolute() or ".." in candidate.parts or "\\" in relative:
                    self.error(
                        f"tooling/agents/manifest.json: unsafe {field} path {relative!r}"
                    )
                    continue
                if not (self.tooling / candidate).is_file():
                    self.error(f"Missing manifest-declared tooling file: tooling/agents/{relative}")
        declared_scripts = set(self.tooling_manifest.get("scripts", []))
        observed_scripts = {
            path.relative_to(self.tooling).as_posix()
            for path in (self.tooling / "scripts").rglob("*.py")
            if path.is_file() and not self.is_generated_or_ignored(path)
        }
        if observed_scripts != declared_scripts:
            self.error(
                "Maintainer script inventory mismatch: "
                f"declared={sorted(declared_scripts)}, observed={sorted(observed_scripts)}"
            )
        declared_tests = set(self.tooling_manifest.get("tests", []))
        observed_tests = {
            path.relative_to(self.tooling).as_posix()
            for path in (self.tooling / "tests").glob("test_*.py")
            if path.is_file() and not self.is_generated_or_ignored(path)
        }
        if observed_tests != declared_tests:
            self.error(
                "Maintainer test inventory mismatch: "
                f"declared={sorted(declared_tests)}, observed={sorted(observed_tests)}"
            )
        evaluations = self.tooling_manifest.get("evaluations", {})
        for name in evaluations.get("fixtures", []) if isinstance(evaluations, dict) else []:
            if not NAME_PATTERN.fullmatch(name) or not (
                self.tooling / "evals/fixtures" / name
            ).is_dir():
                self.error(f"Missing or invalid manifest-declared evaluation fixture: {name}")
        for path in self.tooling.rglob("*"):
            if self.is_generated_or_ignored(path) or not path.is_symlink():
                continue
            try:
                resolved = path.resolve(strict=True)
            except OSError as exc:
                self.error(f"{self.display(path)}: broken symbolic link: {exc}")
                continue
            if self.tooling not in resolved.parents and resolved != self.tooling:
                self.error(f"{self.display(path)}: symbolic link escapes tooling/agents")

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
            self.validate_skill_source(directory)
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

    def validate_skill_source(self, directory: Path) -> None:
        path = directory / "SOURCE.json"
        if not path.exists():
            return
        if not path.is_file():
            self.error(f"{self.display(path)}: provenance sidecar must be a regular file")
            return
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            self.error(f"{self.display(path)}: invalid JSON: {exc}")
            return
        if not isinstance(data, dict):
            self.error(f"{self.display(path)}: provenance sidecar must be an object")
            return
        if set(data) != SOURCE_FIELDS:
            self.error(
                f"{self.display(path)}: fields must be exactly {sorted(SOURCE_FIELDS)}"
            )
        if data.get("schema_version") != 1:
            self.error(f"{self.display(path)}: schema_version must be 1")
        catalog_url = data.get("catalog_url")
        if not isinstance(catalog_url, str) or not CATALOG_URL_PATTERN.match(catalog_url):
            self.error(
                f"{self.display(path)}: catalog_url must reference officialskills.sh or "
                "VoltAgent/awesome-agent-skills over HTTPS"
            )
        source_url = data.get("source_url")
        if not isinstance(source_url, str) or not SOURCE_REPOSITORY_PATTERN.fullmatch(source_url):
            self.error(f"{self.display(path)}: source_url must be an HTTPS GitHub repository URL")
        revision = data.get("source_revision")
        if not isinstance(revision, str) or not SOURCE_REVISION_PATTERN.fullmatch(revision):
            self.error(f"{self.display(path)}: source_revision must be a 40- or 64-digit lowercase Git hash")
        source_path = data.get("source_path")
        source_parts = PurePosixPath(source_path).parts if isinstance(source_path, str) else ()
        if (
            not isinstance(source_path, str)
            or not source_path
            or source_path.startswith("/")
            or "\\" in source_path
            or ":" in source_path
            or ".." in source_parts
        ):
            self.error(f"{self.display(path)}: source_path must be a safe relative POSIX path")
        if data.get("classification") not in {"publisher-owned", "community"}:
            self.error(f"{self.display(path)}: classification must be publisher-owned or community")
        license_name = data.get("license")
        if (
            not isinstance(license_name, str)
            or not (1 <= len(license_name) <= 200)
            or not license_name.strip()
            or license_name.strip().casefold() in {"unknown", "unclear", "none", "n/a"}
        ):
            self.error(f"{self.display(path)}: license must identify non-placeholder terms")
        if data.get("validated_with") != "skills-ref":
            self.error(f"{self.display(path)}: validated_with must be skills-ref")
        validated_at = data.get("validated_at")
        try:
            timestamp = datetime.fromisoformat(validated_at.replace("Z", "+00:00"))
        except (AttributeError, ValueError):
            timestamp = None
        if (
            timestamp is None
            or not isinstance(validated_at, str)
            or not validated_at.endswith("Z")
            or timestamp.tzinfo != timezone.utc
        ):
            self.error(f"{self.display(path)}: validated_at must be an ISO-8601 UTC timestamp ending in Z")

    def display_error_paths(self, errors: list[str]) -> list[str]:
        converted: list[str] = []
        root_text = str(self.root)
        for error in errors:
            converted.append(error.replace(root_text + "\\", "").replace(root_text + "/", ""))
        return converted

    def validate_task_file(self, path: Path, *, template: bool = False) -> None:
        try:
            module = load_task_validator(self.root / TASK_VALIDATOR_REL)
            errors = module.validate_task(
                path,
                template=template,
                task_root=self.agents / "tasks",
            )
        except Exception as exc:  # pragma: no cover - defensive integration boundary
            self.error(f"Runtime task validator failed to load or execute: {exc}")
            return
        self.errors.extend(self.display_error_paths([str(error) for error in errors]))

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
        paths.extend(self.agents / name for name in self.core("task_validators"))
        if not self.runtime_only:
            paths.extend(self.tooling / name for name in self.tooling_manifest.get("scripts", []))
            paths.extend(self.tooling / name for name in self.tooling_manifest.get("tests", []))
            paths.append(self.tooling / "README.md")
        for path in paths:
            if not path.is_file():
                continue
            text = path.read_text(encoding="utf-8")
            if "code-agent-template:managed" not in text:
                self.error(f"{self.display(path)}: missing managed provenance marker")

    def validate_links(self) -> None:
        paths = list(self.agents.rglob("*.md"))
        if not self.runtime_only:
            for relative in ("README.md",):
                candidate = self.root / relative
                if candidate.is_file():
                    paths.append(candidate)
            if (self.root / "docs").is_dir():
                paths.extend((self.root / "docs").rglob("*.md"))
            if self.tooling.is_dir():
                paths.extend(self.tooling.rglob("*.md"))
        for path in sorted(set(paths)):
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
        if not self.runtime_only and self.tooling.is_dir():
            scan_paths.extend(
                path
                for path in self.tooling.rglob("*")
                if path.is_file() and not self.is_generated_or_ignored(path)
            )
        if not self.runtime_only and (self.root / "docs").is_dir():
            scan_paths.extend(
                path
                for path in (self.root / "docs").rglob("*")
                if path.is_file() and not self.is_generated_or_ignored(path)
            )
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
        if package_license.exists():
            self.error(".agents/LICENSE must not exist; the repository root LICENSE is authoritative")
        if not root_license.is_file():
            self.error("Missing repository root LICENSE")
        readme = self.root / "README.md"
        if not readme.is_file():
            return
        text = readme.read_text(encoding="utf-8")
        if "# Universal Coding-Agent Template" not in text:
            return
        for required in (
            self.manifest.get("template_version", ""),
            "manual-bootstrap",
            "python tooling/agents/scripts/validate_template.py",
            "--runtime-only",
            "--strict-skills",
            "python -m unittest discover -s tooling/agents/tests",
            "python tooling/agents/scripts/evaluate_agents.py validate",
        ):
            if required not in text:
                self.error(f"README.md: missing v2 contract text {required!r}")
        review = self.root / "docs/agents-v2-design-review.md"
        if not review.is_file():
            self.error("Missing maintainer evidence review: docs/agents-v2-design-review.md")

    def validate_evaluations(self) -> None:
        path = self.tooling / "scripts/evaluate_agents.py"
        if not path.is_file():
            return
        spec = importlib.util.spec_from_file_location("agents_evaluator", path)
        if spec is None or spec.loader is None:
            self.error("tooling/agents/scripts/evaluate_agents.py: could not load evaluator")
            return
        module = importlib.util.module_from_spec(spec)
        try:
            spec.loader.exec_module(module)
            errors = module.collect_validation_errors(self.root)
        except Exception as exc:  # pragma: no cover - defensive integration boundary
            self.error(f"tooling/agents/scripts/evaluate_agents.py: validation crashed: {exc}")
            return
        self.errors.extend(str(error) for error in errors)

    def run(self) -> list[str]:
        self.load_manifest()
        if not self.agents.is_dir():
            return self.errors
        self.validate_structure()
        if not self.runtime_only:
            self.load_tooling_manifest()
            self.validate_tooling_structure()
        self.validate_skills()
        self.validate_tasks()
        self.validate_context_roles_memory()
        self.validate_managed_markers()
        self.validate_links()
        self.validate_hygiene()
        if not self.runtime_only:
            self.validate_licenses_and_readme()
            self.validate_evaluations()
        return self.errors


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root",
        type=Path,
        default=DEFAULT_ROOT,
        help="Repository root containing .agents (default: inferred from this script).",
    )
    parser.add_argument(
        "--runtime-only",
        action="store_true",
        help="Validate only the operational .agents package; maintainer tooling may be absent.",
    )
    parser.add_argument(
        "--strict-skills",
        action="store_true",
        help="Require and run the official skills-ref validator for every skill.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    validator = Validator(
        args.root,
        strict_skills=args.strict_skills,
        runtime_only=args.runtime_only,
    )
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
    scope = "runtime-only" if args.runtime_only else "runtime plus maintainer tooling"
    print(
        f"Portable structural validation passed for .agents {version}: "
        f"{skills} core skills, {roles} roles, tasks, memory; validated scope: {scope}."
    )
    print(
        "This result does not establish behavioral quality, prompt-injection resistance, "
        "runtime permission enforcement, or cross-agent portability."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
