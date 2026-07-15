from __future__ import annotations

# code-agent-template:managed

import importlib.util
import json
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest import mock


SOURCE_ROOT = Path(__file__).resolve().parents[3]
VALIDATOR_PATH = SOURCE_ROOT / "tooling/agents/scripts/validate_template.py"
SPEC = importlib.util.spec_from_file_location("template_validator", VALIDATOR_PATH)
assert SPEC and SPEC.loader
validator_module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(validator_module)


class TemplateValidatorTests(unittest.TestCase):
    def make_root(self) -> tuple[tempfile.TemporaryDirectory[str], Path]:
        temporary = tempfile.TemporaryDirectory()
        root = Path(temporary.name)
        shutil.copytree(SOURCE_ROOT / ".agents", root / ".agents")
        for name in ("README.md", "LICENSE"):
            shutil.copy2(SOURCE_ROOT / name, root / name)
        shutil.copytree(SOURCE_ROOT / "docs", root / "docs")
        shutil.copytree(
            SOURCE_ROOT / "tooling",
            root / "tooling",
            ignore=shutil.ignore_patterns(".runs", "__pycache__", "*.pyc"),
        )
        return temporary, root

    def validate(
        self,
        root: Path,
        *,
        strict: bool = False,
        runtime_only: bool = False,
    ) -> list[str]:
        return validator_module.Validator(
            root,
            strict_skills=strict,
            runtime_only=runtime_only,
        ).run()

    def add_extension_skill(
        self,
        root: Path,
        *,
        directory_name: str = "external-audit",
        skill_name: str | None = None,
    ) -> Path:
        skill = root / ".agents/skills" / directory_name
        skill.mkdir()
        name = skill_name or directory_name
        (skill / "SKILL.md").write_text(
            f"---\nname: {name}\n"
            "description: Use this skill when the user requests an external audit.\n"
            "license: MIT\n---\n\n# External Audit\n\nInspect evidence.\n",
            encoding="utf-8",
        )
        return skill

    def valid_source(self) -> dict[str, object]:
        return {
            "schema_version": 1,
            "catalog_url": "https://officialskills.sh/example/external-audit",
            "source_url": "https://github.com/example/agent-skills",
            "source_revision": "a" * 40,
            "source_path": "skills/external-audit",
            "classification": "publisher-owned",
            "license": "MIT",
            "validated_with": "skills-ref",
            "validated_at": "2026-07-16T00:00:00Z",
        }

    def test_shipped_template_passes(self) -> None:
        self.assertEqual([], self.validate(SOURCE_ROOT))

    def test_operational_package_excludes_maintainer_artifacts(self) -> None:
        agents = SOURCE_ROOT / ".agents"
        for relative in ("evals", "scripts", "tests", "LICENSE"):
            self.assertFalse((agents / relative).exists(), relative)
        self.assertFalse(any((agents / "skills").glob("*/evals")))
        self.assertFalse(
            any(
                path.name == "__pycache__" or path.suffix == ".pyc"
                for path in agents.rglob("*")
            )
        )
        executables = {
            path.relative_to(agents).as_posix()
            for path in agents.rglob("*")
            if path.is_file() and path.suffix == ".py"
        }
        self.assertEqual(
            {"skills/agent-task/scripts/validate_task.py"},
            executables,
        )

    def test_operational_manifest_has_no_maintainer_fields(self) -> None:
        manifest = validator_module.json.loads(
            (SOURCE_ROOT / ".agents/manifest.json").read_text(encoding="utf-8")
        )
        self.assertEqual(2, manifest["schema_version"])
        self.assertEqual("2.2.0", manifest["template_version"])
        self.assertNotIn("python_requires", manifest)
        self.assertFalse(
            {"evaluations", "fixtures", "scripts", "tests"}
            & set(manifest["core"])
        )

    def test_valid_extensions_are_allowed(self) -> None:
        temporary, root = self.make_root()
        self.addCleanup(temporary.cleanup)
        skill = root / ".agents/skills/custom-audit"
        skill.mkdir()
        (skill / "SKILL.md").write_text(
            "---\nname: custom-audit\n"
            "description: Use this skill when the user requests a custom audit.\n"
            "compatibility: Works with Codex or another skills-compatible client.\n"
            "---\n\n# Custom Audit\n\nInspect evidence.\n",
            encoding="utf-8",
        )
        role = root / ".agents/roles/security.md"
        role.write_text(
            "# Security\n\n## Purpose\nAudit.\n\n## Permission boundary\nRead only.\n\n"
            "## Inputs\nTarget.\n\n## Output\nFindings.\n\n## Non-goals\nNo fixes.\n",
            encoding="utf-8",
        )
        (root / ".agents/custom").mkdir()
        self.assertEqual([], self.validate(root))

    def test_valid_external_skill_source_is_allowed(self) -> None:
        temporary, root = self.make_root()
        self.addCleanup(temporary.cleanup)
        skill = self.add_extension_skill(root)
        (skill / "SOURCE.json").write_text(
            json.dumps(self.valid_source()),
            encoding="utf-8",
        )
        self.assertEqual([], self.validate(root))

    def test_malformed_external_skill_source_is_rejected(self) -> None:
        temporary, root = self.make_root()
        self.addCleanup(temporary.cleanup)
        skill = self.add_extension_skill(root)
        (skill / "SOURCE.json").write_text("{broken", encoding="utf-8")
        self.assertTrue(any("invalid JSON" in error for error in self.validate(root)))

    def test_unsafe_external_skill_source_path_is_rejected(self) -> None:
        temporary, root = self.make_root()
        self.addCleanup(temporary.cleanup)
        skill = self.add_extension_skill(root)
        source = self.valid_source()
        source["source_path"] = "../outside"
        (skill / "SOURCE.json").write_text(json.dumps(source), encoding="utf-8")
        self.assertTrue(
            any("safe relative POSIX path" in error for error in self.validate(root))
        )

    def test_external_skill_source_requires_strict_validation_record(self) -> None:
        temporary, root = self.make_root()
        self.addCleanup(temporary.cleanup)
        skill = self.add_extension_skill(root)
        source = self.valid_source()
        source["validated_with"] = "manual-review"
        (skill / "SOURCE.json").write_text(json.dumps(source), encoding="utf-8")
        self.assertTrue(
            any("validated_with must be skills-ref" in error for error in self.validate(root))
        )

    def test_skill_name_collision_is_rejected(self) -> None:
        temporary, root = self.make_root()
        self.addCleanup(temporary.cleanup)
        self.add_extension_skill(
            root,
            directory_name="review-code-copy",
            skill_name="review-code",
        )
        self.assertTrue(
            any("name must match parent directory" in error for error in self.validate(root))
        )

    def test_malformed_yaml_is_rejected(self) -> None:
        temporary, root = self.make_root()
        self.addCleanup(temporary.cleanup)
        path = root / ".agents/skills/review-code/SKILL.md"
        path.write_text(
            path.read_text(encoding="utf-8").replace(
                "description: Use this skill", "description: Use when: this skill"
            ),
            encoding="utf-8",
        )
        self.assertTrue(any("quote YAML scalars" in error for error in self.validate(root)))

    def test_overlong_compatibility_is_rejected(self) -> None:
        temporary, root = self.make_root()
        self.addCleanup(temporary.cleanup)
        path = root / ".agents/skills/review-code/SKILL.md"
        text = path.read_text(encoding="utf-8").replace(
            "license: MIT\n", "license: MIT\ncompatibility: " + ("x" * 501) + "\n"
        )
        path.write_text(text, encoding="utf-8")
        self.assertTrue(any("compatibility must contain" in error for error in self.validate(root)))

    def test_empty_skill_body_is_rejected(self) -> None:
        temporary, root = self.make_root()
        self.addCleanup(temporary.cleanup)
        path = root / ".agents/skills/review-code/SKILL.md"
        text = path.read_text(encoding="utf-8")
        closing = text.find("---", 4)
        path.write_text(text[: closing + 3] + "\n", encoding="utf-8")
        self.assertTrue(any("body must not be empty" in error for error in self.validate(root)))

    def test_broken_router_reference_is_rejected(self) -> None:
        temporary, root = self.make_root()
        self.addCleanup(temporary.cleanup)
        path = root / ".agents/AGENTS.md"
        path.write_text(
            path.read_text(encoding="utf-8").replace(
                ".agents/context/project.md", ".agents/context/missing.md"
            ),
            encoding="utf-8",
        )
        self.assertTrue(any("broken referenced path" in error for error in self.validate(root)))

    def test_memory_ignore_contract_is_enforced(self) -> None:
        temporary, root = self.make_root()
        self.addCleanup(temporary.cleanup)
        (root / ".agents/memory/.gitignore").write_text("# empty\n", encoding="utf-8")
        self.assertTrue(any("must ignore only state.md" in error for error in self.validate(root)))

    def test_duplicate_runtime_license_is_rejected(self) -> None:
        temporary, root = self.make_root()
        self.addCleanup(temporary.cleanup)
        (root / ".agents/LICENSE").write_text("duplicate\n", encoding="utf-8")
        self.assertTrue(any("must not exist" in error for error in self.validate(root)))

    def test_runtime_only_accepts_operational_package_without_tooling(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            shutil.copytree(SOURCE_ROOT / ".agents", root / ".agents")
            self.assertEqual([], self.validate(root, runtime_only=True))

    def test_runtime_validation_does_not_write_bytecode_into_agents(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            shutil.copytree(SOURCE_ROOT / ".agents", root / ".agents")
            self.assertEqual([], self.validate(root, runtime_only=True))
            self.assertFalse(
                any(
                    path.name == "__pycache__" or path.suffix == ".pyc"
                    for path in (root / ".agents").rglob("*")
                )
            )

    def test_legacy_maintainer_directory_is_rejected(self) -> None:
        temporary, root = self.make_root()
        self.addCleanup(temporary.cleanup)
        (root / ".agents/tests").mkdir()
        self.assertTrue(
            any("removed maintainer path" in error for error in self.validate(root))
        )

    def test_unmanaged_maintainer_script_is_rejected(self) -> None:
        temporary, root = self.make_root()
        self.addCleanup(temporary.cleanup)
        (root / "tooling/agents/scripts/unmanaged.py").write_text(
            "# unmanaged\n",
            encoding="utf-8",
        )
        self.assertTrue(
            any("script inventory mismatch" in error for error in self.validate(root))
        )

    def test_orphan_centralized_skill_evals_are_rejected(self) -> None:
        temporary, root = self.make_root()
        self.addCleanup(temporary.cleanup)
        orphan = root / "tooling/agents/evals/skills/missing-skill"
        orphan.mkdir()
        self.assertTrue(
            any("unknown skills" in error for error in self.validate(root))
        )

    def test_required_model_needs_a_preference(self) -> None:
        temporary, root = self.make_root()
        self.addCleanup(temporary.cleanup)
        path = root / ".agents/tasks/_template.md"
        path.write_text(
            path.read_text(encoding="utf-8").replace(
                "Require preferred model: `false`", "Require preferred model: `true`"
            ),
            encoding="utf-8",
        )
        self.assertTrue(any("needs at least one preference" in error for error in self.validate(root)))

    def test_secret_like_value_is_rejected(self) -> None:
        temporary, root = self.make_root()
        self.addCleanup(temporary.cleanup)
        path = root / ".agents/context/project.md"
        path.write_text(
            path.read_text(encoding="utf-8") + "\nAPI_KEY=sk-abcdefghijklmnopqrstuvwxyz123456\n",
            encoding="utf-8",
        )
        self.assertTrue(any("secret-like" in error for error in self.validate(root)))

    def test_strict_mode_reports_missing_official_validator(self) -> None:
        temporary, root = self.make_root()
        self.addCleanup(temporary.cleanup)
        with mock.patch.object(validator_module.shutil, "which", return_value=None):
            errors = self.validate(root, strict=True)
        self.assertTrue(any("skills-ref" in error and "not installed" in error for error in errors))

    def test_external_symlink_is_rejected_when_supported(self) -> None:
        temporary, root = self.make_root()
        self.addCleanup(temporary.cleanup)
        outside = root / "outside.txt"
        outside.write_text("outside", encoding="utf-8")
        link = root / ".agents/context/external-link.md"
        try:
            link.symlink_to(outside)
        except (OSError, NotImplementedError):
            self.skipTest("Symbolic links are unavailable in this environment")
        self.assertTrue(any("escapes .agents" in error for error in self.validate(root)))


if __name__ == "__main__":
    unittest.main()
