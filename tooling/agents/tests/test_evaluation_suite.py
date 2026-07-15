from __future__ import annotations

# code-agent-template:managed

import argparse
import importlib.util
import json
import subprocess
import tempfile
import unittest
from pathlib import Path


SOURCE_ROOT = Path(__file__).resolve().parents[3]
EVALUATOR_PATH = SOURCE_ROOT / "tooling/agents/scripts/evaluate_agents.py"
SPEC = importlib.util.spec_from_file_location("agents_evaluator_tests", EVALUATOR_PATH)
assert SPEC and SPEC.loader
evaluator = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(evaluator)


class EvaluationContractTests(unittest.TestCase):
    def test_contracts_validate(self) -> None:
        self.assertEqual([], evaluator.collect_validation_errors(SOURCE_ROOT))

    def test_core_suite_has_three_cases_per_skill(self) -> None:
        cases = evaluator.core_cases(SOURCE_ROOT)
        manifest = evaluator.load_json(SOURCE_ROOT / ".agents/manifest.json")
        skills = manifest["core"]["skills"]
        self.assertEqual(len(skills) * 3, len(cases))
        for skill in skills:
            self.assertEqual(
                {"positive", "near-miss", "boundary"},
                {case["case_type"] for case in cases if case["skill"] == skill},
            )

    def test_trigger_sets_are_balanced_and_split(self) -> None:
        manifest = evaluator.load_json(SOURCE_ROOT / ".agents/manifest.json")
        for skill in manifest["core"]["skills"]:
            payload = evaluator.load_json(
                SOURCE_ROOT / "tooling/agents/evals/skills" / skill / "trigger_queries.json"
            )
            queries = payload["queries"]
            self.assertEqual(20, len(queries))
            self.assertEqual(10, sum(item["should_trigger"] is True for item in queries))
            self.assertEqual(10, sum(item["should_trigger"] is False for item in queries))
            self.assertEqual({"train", "validation"}, {item["split"] for item in queries})
            self.assertEqual(12, sum(item["split"] == "train" for item in queries))
            self.assertEqual(8, sum(item["split"] == "validation" for item in queries))

    def test_fixture_preconditions_match_case_claims(self) -> None:
        fixtures = SOURCE_ROOT / "tooling/agents/evals/fixtures"
        basic = subprocess.run(
            ["python", "-m", "unittest", "discover", "-s", "tests"],
            cwd=fixtures / "basic",
            capture_output=True,
            text=True,
            shell=False,
        )
        clean = subprocess.run(
            ["python", "-m", "unittest", "discover", "-s", "tests"],
            cwd=fixtures / "clean",
            capture_output=True,
            text=True,
            shell=False,
        )
        self.assertNotEqual(0, basic.returncode)
        self.assertEqual(0, clean.returncode, clean.stdout + clean.stderr)
        self.assertTrue((fixtures / "ui/index.html").is_file())
        initialized = (fixtures / "initialized/_agents_overlay/context/project.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("**Status:** Initialized", initialized)
        self.assertTrue((fixtures / "task-required/supplied-task.md").is_file())
        self.assertTrue((fixtures / "untrusted/prior-state.md").is_file())
        self.assertTrue((fixtures / "untrusted/candidate-a/README.md").is_file())
        self.assertTrue((fixtures / "untrusted/candidate-b/README.md").is_file())
        catalog = evaluator.load_json(fixtures / "skill-catalog/catalog.json")
        self.assertEqual(2, len(catalog["candidates"]))
        self.assertTrue(
            (fixtures / "skill-catalog/candidates/postgres-guide/SKILL.md").is_file()
        )
        self.assertTrue(
            (fixtures / "skill-catalog/candidates/unsafe-installer/scripts/install.sh").is_file()
        )

    def test_prepare_excludes_eval_and_test_definitions(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            out = Path(directory) / "runs"
            args = argparse.Namespace(
                root=SOURCE_ROOT,
                suite="core",
                case="review-code-review-defect",
                conditions="v2-full",
                trials=1,
                out=out,
                baseline=None,
                seed=7,
            )
            self.assertEqual(0, evaluator.prepare_runs(args))
            run_dirs = sorted(path for path in out.iterdir() if path.is_dir())
            self.assertEqual(1, len(run_dirs))
            subject_agents = run_dirs[0] / "subject/workspace/.agents"
            self.assertTrue((subject_agents / "AGENTS.md").is_file())
            self.assertFalse((subject_agents / "evals").exists())
            self.assertFalse((subject_agents / "tests").exists())
            self.assertFalse((subject_agents / "scripts/evaluate_agents.py").exists())
            self.assertFalse(any(subject_agents.glob("skills/*/evals")))
            self.assertFalse((subject_agents / "LICENSE").exists())
            self.assertNotIn("v2-full", run_dirs[0].name)
            self.assertNotIn("condition", (run_dirs[0] / "subject/limits.json").read_text(encoding="utf-8"))
            tooling_manifest = evaluator.load_json(SOURCE_ROOT / "tooling/agents/manifest.json")
            run = evaluator.load_json(run_dirs[0] / "run.json")
            self.assertEqual(tooling_manifest["tooling_version"], run["suite_version"])

    def test_deterministic_grade_blocks_unexpected_writes(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            out = Path(directory) / "runs"
            prepare = argparse.Namespace(
                root=SOURCE_ROOT,
                suite="core",
                case="review-code-review-defect",
                conditions="v2-full",
                trials=1,
                out=out,
                baseline=None,
                seed=1,
            )
            evaluator.prepare_runs(prepare)
            run_dir = next(
                path
                for path in out.iterdir()
                if evaluator.load_json(path / "run.json")["case_id"]
                == "review-code-review-defect"
            )
            response = Path(directory) / "response.txt"
            response.write_text("Read-only review complete.", encoding="utf-8")
            actions = Path(directory) / "actions.json"
            actions.write_text("[]\n", encoding="utf-8")
            imported = argparse.Namespace(
                run_dir=run_dir,
                response=response,
                actions=actions,
                runtime_id="test-runtime",
                runtime_version="1",
                model_id="test-model",
                model_verified=False,
                capability_enforcement="instruction-only",
                duration_ms=1,
                total_tokens=1,
                routing_observable=False,
                activated_skill=[],
            )
            self.assertEqual(0, evaluator.import_result(imported))
            (run_dir / "subject/workspace/unauthorized.txt").write_text(
                "changed", encoding="utf-8"
            )
            grade = argparse.Namespace(root=SOURCE_ROOT, run_dir=run_dir)
            self.assertEqual(1, evaluator.grade_run(grade))
            result = evaluator.load_json(run_dir / "grading.json")
            self.assertEqual("fail", result["status"])

            packets = []
            for slot in ("a", "b"):
                packet = Path(directory) / f"packet-{slot}.json"
                packets.append(packet)
                self.assertEqual(
                    0,
                    evaluator.prepare_review(
                        argparse.Namespace(
                            root=SOURCE_ROOT,
                            run_dir=run_dir,
                            reviewer_slot=slot,
                            out=packet,
                        )
                    ),
                )
                packet_text = packet.read_text(encoding="utf-8")
                self.assertNotIn("v2-full", packet_text)
                self.assertNotIn("test-model", packet_text)
                self.assertNotIn("deterministic_status", packet_text)
                payload = evaluator.load_json(packet)
                review = Path(directory) / f"review-{slot}.json"
                review.write_text(
                    json.dumps(
                        {
                            "review_id": payload["review_id"],
                            "criteria": [
                                {
                                    "id": item["id"],
                                    "passed": True,
                                    "explanation": "Criterion satisfied.",
                                }
                                for item in payload["rubric"]
                            ],
                        }
                    ),
                    encoding="utf-8",
                )
                evaluator.import_review(
                    argparse.Namespace(
                        run_dir=run_dir,
                        reviewer_slot=slot,
                        packet=packet,
                        review=review,
                        runtime_id="review-runtime",
                        model_id="review-model",
                        model_verified=False,
                        reviewer_session_id=f"review-session-{slot}",
                    )
                )
            self.assertEqual("fail", evaluator.load_json(run_dir / "grading.json")["status"])
            with self.assertRaisesRegex(ValueError, "canonically bound"):
                evaluator.import_review(
                    argparse.Namespace(
                        root=SOURCE_ROOT,
                        run_dir=run_dir,
                        reviewer_slot="b",
                        packet=packets[0],
                        review=Path(directory) / "review-a.json",
                        runtime_id="review-runtime",
                        model_id="review-model",
                        model_verified=False,
                        reviewer_session_id="third-session",
                    )
                )

    def test_sanitized_actions_keep_redacted_arguments(self) -> None:
        actions = evaluator.sanitize_actions(
            [{"tool": "shell", "category": "network", "arguments": {"token": "secret"}}]
        )
        self.assertEqual("<redacted>", actions[0]["arguments"]["token"])
        self.assertNotIn("secret", json.dumps(actions[0]))
        self.assertEqual("network", actions[0]["category"])

        disguised = evaluator.sanitize_actions(
            [
                {
                    "tool": "shell_command",
                    "category": "shell",
                    "arguments": {"command": "curl https://example.invalid"},
                }
            ]
        )
        self.assertEqual("network", disguised[0]["category"])
        self.assertTrue(disguised[0]["category_conflict"])

        laundered_write = evaluator.sanitize_actions(
            [
                {
                    "tool": "apply_patch",
                    "category": "filesystem-read",
                    "path": "../escaped.txt",
                    "arguments": {},
                }
            ]
        )
        self.assertEqual("filesystem-write", laundered_write[0]["category"])
        self.assertTrue(laundered_write[0]["category_conflict"])

    def test_complete_trace_rejects_out_of_bundle_write_path(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            out = Path(directory) / "runs"
            evaluator.prepare_runs(
                argparse.Namespace(
                    root=SOURCE_ROOT,
                    suite="core",
                    case="review-code-review-defect",
                    profile="smoke",
                    conditions="v2-full",
                    trials=1,
                    out=out,
                    baseline=None,
                    seed=5,
                )
            )
            run_dir = next(path for path in out.iterdir() if path.is_dir())
            response = Path(directory) / "response.txt"
            response.write_text(
                "app.py returns left - right, which is subtraction rather than addition.",
                encoding="utf-8",
            )
            actions = Path(directory) / "actions.json"
            actions.write_text(
                json.dumps(
                    [
                        {
                            "tool": "apply_patch",
                            "category": "filesystem-write",
                            "path": "../escaped.txt",
                            "arguments": {},
                        }
                    ]
                ),
                encoding="utf-8",
            )
            evaluator.import_result(
                argparse.Namespace(
                    run_dir=run_dir,
                    response=response,
                    actions=actions,
                    runtime_id="trace-runtime",
                    runtime_version="1",
                    model_id="test-model",
                    model_verified=False,
                    capability_enforcement="enforced",
                    trace_completeness="complete",
                    duration_ms=1,
                    total_tokens=1,
                    routing_observable=False,
                    activated_skill=[],
                )
            )
            self.assertEqual(
                1,
                evaluator.grade_run(argparse.Namespace(root=SOURCE_ROOT, run_dir=run_dir)),
            )
            grading = evaluator.load_json(run_dir / "grading.json")
            check = next(item for item in grading["checks"] if item["id"] == "action-write-boundary")
            self.assertEqual("fail", check["status"])

    def test_condition_order_is_randomized_and_run_ids_are_blinded(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            out = Path(directory) / "runs"
            args = argparse.Namespace(
                root=SOURCE_ROOT,
                suite="core",
                case="review-code-review-defect",
                profile="smoke",
                conditions="v2-full,no-template,prompt-only",
                trials=1,
                out=out,
                baseline=None,
                seed=11,
            )
            evaluator.prepare_runs(args)
            names = [path.name for path in out.iterdir() if path.is_dir()]
            self.assertEqual(3, len(names))
            self.assertTrue(all(name.startswith("run-") for name in names))
            self.assertTrue(all("v2" not in name and "template" not in name for name in names))
            by_condition = {
                evaluator.load_json(path / "run.json")["condition"]: path
                for path in out.iterdir()
                if path.is_dir()
            }
            self.assertFalse((by_condition["no-template"] / "subject/workspace/.agents").exists())
            self.assertTrue((by_condition["prompt-only"] / "subject/workspace/.agents").is_dir())
            self.assertNotIn(
                "read .agents/AGENTS.md",
                (by_condition["prompt-only"] / "subject/prompt.txt").read_text(encoding="utf-8"),
            )
            self.assertIn(
                "read .agents/AGENTS.md",
                (by_condition["v2-full"] / "subject/prompt.txt").read_text(encoding="utf-8"),
            )

    def test_skill_ablation_removes_skill_route_and_grader(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            out = Path(directory) / "runs"
            args = argparse.Namespace(
                root=SOURCE_ROOT,
                suite="core",
                case="review-code-review-defect",
                profile="smoke",
                conditions="v2-skill-ablation",
                trials=1,
                out=out,
                baseline=None,
                seed=13,
            )
            evaluator.prepare_runs(args)
            run_dir = next(path for path in out.iterdir() if path.is_dir())
            agents = run_dir / "subject/workspace/.agents"
            self.assertFalse((agents / "skills/review-code").exists())
            self.assertNotIn("`review-code`", (agents / "AGENTS.md").read_text(encoding="utf-8"))
            self.assertFalse((agents / "scripts/evaluate_agents.py").exists())
            manifest = evaluator.load_json(agents / "manifest.json")
            self.assertNotIn("review-code", manifest["core"]["skills"])
            self.assertNotIn("ablated_skill", json.dumps(manifest))

    def test_agent_task_ablation_removes_task_validator_inventory(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            out = Path(directory) / "runs"
            evaluator.prepare_runs(
                argparse.Namespace(
                    root=SOURCE_ROOT,
                    suite="core",
                    case="agent-task-author-task",
                    profile="smoke",
                    conditions="v2-skill-ablation",
                    trials=1,
                    out=out,
                    baseline=None,
                    seed=17,
                )
            )
            run_dir = next(path for path in out.iterdir() if path.is_dir())
            agents = run_dir / "subject/workspace/.agents"
            manifest = evaluator.load_json(agents / "manifest.json")
            self.assertNotIn("agent-task", manifest["core"]["skills"])
            self.assertEqual([], manifest["core"]["task_validators"])
            self.assertFalse((agents / "skills/agent-task").exists())

    def test_deterministic_success_exits_pending_not_pass(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            out = Path(directory) / "runs"
            evaluator.prepare_runs(
                argparse.Namespace(
                    root=SOURCE_ROOT,
                    suite="core",
                    case="review-code-review-defect",
                    profile="smoke",
                    conditions="v2-full",
                    trials=1,
                    out=out,
                    baseline=None,
                    seed=23,
                )
            )
            run_dir = next(path for path in out.iterdir() if path.is_dir())
            response = Path(directory) / "response.txt"
            response.write_text(
                "app.py returns left - right, which performs subtraction.",
                encoding="utf-8",
            )
            actions = Path(directory) / "actions.json"
            actions.write_text("[]\n", encoding="utf-8")
            evaluator.import_result(
                argparse.Namespace(
                    run_dir=run_dir,
                    response=response,
                    actions=actions,
                    runtime_id="complete-runtime",
                    runtime_version="1",
                    model_id="test-model",
                    model_verified=False,
                    capability_enforcement="enforced",
                    trace_completeness="complete",
                    duration_ms=1,
                    total_tokens=1,
                    routing_observable=False,
                    activated_skill=[],
                )
            )
            self.assertEqual(
                3,
                evaluator.grade_run(argparse.Namespace(root=SOURCE_ROOT, run_dir=run_dir)),
            )
            self.assertEqual(
                "semantic-pending",
                evaluator.load_json(run_dir / "grading.json")["status"],
            )

    def test_routing_trials_are_blinded_and_observable(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            out = Path(directory) / "routing"
            args = argparse.Namespace(
                root=SOURCE_ROOT,
                split="validation",
                skill="review-code",
                condition="v2-full",
                trials=3,
                out=out,
                seed=19,
            )
            self.assertEqual(0, evaluator.prepare_routing_runs(args))
            payload = evaluator.load_json(
                SOURCE_ROOT
                / "tooling/agents/evals/skills/review-code/trigger_queries.json"
            )
            expected = sum(item["split"] == "validation" for item in payload["queries"]) * 3
            runs = [path for path in out.iterdir() if path.is_dir()]
            self.assertEqual(expected, len(runs))
            run_dir = runs[0]
            self.assertTrue(run_dir.name.startswith("run-"))
            prompt = (run_dir / "subject/prompt.txt").read_text(encoding="utf-8")
            self.assertNotIn("should_trigger", prompt)
            control = evaluator.load_json(run_dir / "run.json")
            response = run_dir / "subject/subject-response.md"
            response.write_text("Routing probe complete.", encoding="utf-8")
            actions = run_dir / "subject/subject-actions.json"
            actions.write_text("[]\n", encoding="utf-8")
            activated = [control["target_skill"]] if control["should_trigger"] else []
            evaluator.import_result(
                argparse.Namespace(
                    run_dir=run_dir,
                    response=None,
                    actions=None,
                    runtime_id="observable-runtime",
                    runtime_version="1",
                    model_id="test-model",
                    model_verified=False,
                    capability_enforcement="instruction-only",
                    trace_completeness="unknown",
                    duration_ms=1,
                    total_tokens=1,
                    routing_observable=True,
                    activated_skill=activated,
                )
            )
            self.assertEqual(
                0,
                evaluator.grade_run(argparse.Namespace(root=SOURCE_ROOT, run_dir=run_dir)),
            )
            self.assertEqual("pass", evaluator.load_json(run_dir / "grading.json")["status"])
            self.assertEqual(
                0,
                evaluator.summarize(argparse.Namespace(root=SOURCE_ROOT, runs=out)),
            )
            summary = evaluator.load_json(out / "summary.json")
            self.assertEqual(0.5, summary["routing_classification"]["threshold"])
            self.assertGreater(
                summary["routing_classification"]["matrix_gaps"][0]["missing_count"],
                0,
            )
            self.assertEqual("incomplete", summary["release_gates"]["qualification"])


if __name__ == "__main__":
    unittest.main()
