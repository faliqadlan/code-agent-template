from __future__ import annotations

# code-agent-template:managed

import importlib.util
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest import mock


SOURCE_ROOT = Path(__file__).resolve().parents[2]
VALIDATOR_PATH = SOURCE_ROOT / ".agents/scripts/validate_template.py"
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
        return temporary, root

    def validate(self, root: Path, *, strict: bool = False) -> list[str]:
        return validator_module.Validator(root, strict_skills=strict).run()

    def test_shipped_template_passes(self) -> None:
        self.assertEqual([], self.validate(SOURCE_ROOT))

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

    def test_license_copies_must_match(self) -> None:
        temporary, root = self.make_root()
        self.addCleanup(temporary.cleanup)
        (root / ".agents/LICENSE").write_text("different\n", encoding="utf-8")
        self.assertTrue(any("must be identical" in error for error in self.validate(root)))

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
