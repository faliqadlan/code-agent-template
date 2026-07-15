from __future__ import annotations

# code-agent-template:managed

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path


SOURCE_ROOT = Path(__file__).resolve().parents[3]
VALIDATOR_PATH = (
    SOURCE_ROOT / ".agents/skills/agent-task/scripts/validate_task.py"
)
SPEC = importlib.util.spec_from_file_location("runtime_task_validator_tests", VALIDATOR_PATH)
assert SPEC and SPEC.loader
task_validator = importlib.util.module_from_spec(SPEC)
PREVIOUS_DONT_WRITE_BYTECODE = sys.dont_write_bytecode
sys.dont_write_bytecode = True
try:
    SPEC.loader.exec_module(task_validator)
finally:
    sys.dont_write_bytecode = PREVIOUS_DONT_WRITE_BYTECODE


class TaskValidatorTests(unittest.TestCase):
    def valid_task_text(self) -> str:
        template = (SOURCE_ROOT / ".agents/tasks/_template.md").read_text(encoding="utf-8")
        replacements = {
            "name: task-name": "name: dependency-audit",
            "description: Describe the immutable cross-agent assignment and its observable outcome.": (
                "description: Produce an evidence-backed dependency audit."
            ),
            "# Task: Task name": "# Task: Dependency audit",
            "State the observable result for `$TARGET`.": (
                "Produce an evidence-backed dependency audit for `$TARGET`."
            ),
            "- Identify evidence the executing agent must inspect.": (
                "- Inspect dependency manifests and lockfiles."
            ),
            "- Approval gates: Describe actions requiring approval, or write `None.`": (
                "- Approval gates: None."
            ),
            "- [ ] Define an observable result for `$TARGET`.": (
                "- [ ] Report direct dependencies and unsupported versions for `$TARGET`."
            ),
            "- Method: Define the smallest relevant command or inspection.": (
                "- Method: Inspect manifests and run the repository dependency check."
            ),
            "- Expected result: State the successful outcome.": (
                "- Expected result: Every reported dependency is supported by repository evidence."
            ),
        }
        for old, new in replacements.items():
            template = template.replace(old, new)
        return template

    def make_task(self, root: Path, text: str | None = None) -> Path:
        task_root = root / ".agents/tasks"
        task_root.mkdir(parents=True)
        path = task_root / "dependency-audit-v1.md"
        path.write_text(text or self.valid_task_text(), encoding="utf-8")
        return path

    def test_template_contract_is_valid(self) -> None:
        path = SOURCE_ROOT / ".agents/tasks/_template.md"
        self.assertEqual(
            [],
            task_validator.validate_task(
                path,
                template=True,
                task_root=path.parent,
            ),
        )

    def test_published_task_and_cli_are_valid(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = self.make_task(Path(directory))
            self.assertEqual([], task_validator.validate_task(path, task_root=path.parent))
            self.assertEqual(0, task_validator.main([str(path)]))

    def test_duplicate_frontmatter_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            text = self.valid_task_text().replace(
                "name: dependency-audit",
                "name: dependency-audit\nname: duplicate",
            )
            path = self.make_task(Path(directory), text)
            self.assertTrue(
                any("duplicate frontmatter" in error for error in task_validator.validate_task(path))
            )

    def test_missing_required_capability_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            text = self.valid_task_text().replace(
                "- Required capabilities:\n  - `repository-read`\n  - `repository-write`\n  - `shell`",
                "- Required capabilities:",
            )
            path = self.make_task(Path(directory), text)
            self.assertTrue(
                any("at least one required capability" in error for error in task_validator.validate_task(path))
            )

    def test_required_model_without_preference_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            text = self.valid_task_text().replace(
                "Require preferred model: `false`",
                "Require preferred model: `true`",
            )
            path = self.make_task(Path(directory), text)
            self.assertTrue(
                any("needs at least one preference" in error for error in task_validator.validate_task(path))
            )

    def test_cli_rejects_task_outside_agents_tasks(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "dependency-audit-v1.md"
            path.write_text(self.valid_task_text(), encoding="utf-8")
            self.assertEqual(1, task_validator.main([str(path)]))


if __name__ == "__main__":
    unittest.main()
