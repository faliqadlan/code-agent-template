from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from validate_template import validate_task_file


VALID_TASK = """---
name: dependency-audit
description: Audit dependencies for a selected repository target.
---

# Task: Dependency audit

## Objective

Audit `$TARGET` and report actionable dependency risks.

## Runtime inputs

- `TARGET` (required): Repository path or package manifest to inspect.

## Context

- Inspect the selected manifest and lock file.

## Constraints

- Preserve dependency versions unless the user separately requests changes.

## Execution requirements

1. Inspect `$TARGET` and collect repository evidence.

## Acceptance criteria

- [ ] Risks for `$TARGET` are supported by evidence.

## Verification

- Command or inspection: Run the repository's dependency check when available.
- Expected result: The check completes and findings identify their evidence.

## Output

Report findings, verification evidence, and residual risk.
"""


class ValidateTaskFileTests(unittest.TestCase):
    def write_task(self, directory: str, name: str, text: str = VALID_TASK) -> Path:
        path = Path(directory) / name
        path.write_text(text, encoding="utf-8")
        return path

    def test_valid_reusable_task_with_runtime_input(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            errors = validate_task_file(self.write_task(directory, "dependency-audit.md"))
        self.assertEqual([], errors)

    def test_missing_metadata_and_required_section(self) -> None:
        text = VALID_TASK.replace(
            "description: Audit dependencies for a selected repository target.\n", ""
        ).replace("## Verification", "## Checks")
        with tempfile.TemporaryDirectory() as directory:
            errors = validate_task_file(self.write_task(directory, "dependency-audit.md", text))
        self.assertTrue(any("description is required" in error for error in errors))
        self.assertTrue(any("missing required section 'Verification'" in error for error in errors))

    def test_invalid_filename_and_input_identifier(self) -> None:
        text = VALID_TASK.replace("`TARGET` (required)", "`target-name` (required)")
        with tempfile.TemporaryDirectory() as directory:
            errors = validate_task_file(self.write_task(directory, "Invalid_Name.md", text))
        self.assertTrue(any("filename must use lowercase kebab case" in error for error in errors))
        self.assertTrue(any("invalid runtime input name 'target-name'" in error for error in errors))

    def test_undeclared_and_unresolved_placeholders(self) -> None:
        text = VALID_TASK.replace(
            "1. Inspect `$TARGET` and collect repository evidence.",
            "1. Inspect `$TARGET` and `$SCOPE`; remove {{REPLACE_ME}} before use.",
        )
        with tempfile.TemporaryDirectory() as directory:
            errors = validate_task_file(self.write_task(directory, "dependency-audit.md", text))
        self.assertTrue(any("undeclared runtime input 'SCOPE'" in error for error in errors))
        self.assertTrue(any("unresolved placeholder syntax" in error for error in errors))

    def test_embedded_model_and_token_settings(self) -> None:
        text = VALID_TASK.replace(
            "description: Audit dependencies for a selected repository target.\n",
            "description: Audit dependencies for a selected repository target.\nmodel: example-model\n",
        ).replace("## Constraints\n", "## Constraints\n\nToken budget: 100000\n")
        with tempfile.TemporaryDirectory() as directory:
            errors = validate_task_file(self.write_task(directory, "dependency-audit.md", text))
        self.assertTrue(any("unsupported frontmatter field 'model'" in error for error in errors))
        self.assertTrue(any("runtime model or token setting" in error for error in errors))

    def test_legacy_prompt_path_is_rejected(self) -> None:
        text = VALID_TASK.replace(
            "- Inspect the selected manifest and lock file.",
            "- Load a compatibility prompt from `.ai/prompts/dependency-audit.md`.",
        )
        with tempfile.TemporaryDirectory() as directory:
            errors = validate_task_file(self.write_task(directory, "dependency-audit.md", text))
        self.assertTrue(any("legacy prompt path" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
