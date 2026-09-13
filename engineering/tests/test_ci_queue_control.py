#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
WORKFLOWS = ROOT / ".github" / "workflows"
POLICY = ROOT / "engineering" / "tooling" / "ci" / "queue-control-policy.json"
VALIDATOR = ROOT / "engineering" / "tooling" / "ci" / "validate_queue_control.py"

CANONICAL_GROUP = "${{ github.workflow }}-${{ github.ref }}-${{ github.ref == 'refs/heads/main' && github.run_id || 'dedupe' }}"
CANONICAL_CANCEL = "${{ github.ref != 'refs/heads/main' }}"

spec = importlib.util.spec_from_file_location("queue_control_validator", VALIDATOR)
assert spec is not None and spec.loader is not None
validator = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = validator
spec.loader.exec_module(validator)


def load_policy() -> dict[str, object]:
    return json.loads(POLICY.read_text(encoding="utf-8"))


def factory_workflow_paths() -> list[Path]:
    return sorted(WORKFLOWS.glob("factory-*.yml"))


def trigger_block(text: str, trigger: str) -> str:
    marker = f"  {trigger}:"
    start = text.find(marker)
    if start < 0:
        return ""
    lines = text[start:].splitlines()
    captured = [lines[0]]
    for line in lines[1:]:
        if line and not line.startswith("    "):
            break
        captured.append(line)
    return "\n".join(captured)


def scoped_workflow(*, push_paths: bool = True, pr_paths: tuple[str, ...] = ("src/**",), concurrency: bool = True, cancel: str = CANONICAL_CANCEL) -> str:
    push_path_lines = ""
    if push_paths:
        push_path_lines = "    paths:\n" + "".join(f"      - '{path}'\n" for path in pr_paths)
    pr_path_lines = "    paths:\n" + "".join(f"      - '{path}'\n" for path in pr_paths)
    concurrency_block = ""
    if concurrency:
        concurrency_block = (
            "\nconcurrency:\n"
            f"  group: {CANONICAL_GROUP}\n"
            f"  cancel-in-progress: {cancel}\n"
        )
    return (
        "name: Test\n\n"
        "on:\n"
        "  push:\n"
        "    branches:\n"
        "      - main\n"
        f"{push_path_lines}"
        "  pull_request:\n"
        f"{pr_path_lines}"
        f"{concurrency_block}\n"
        "permissions:\n  contents: read\n\n"
        "jobs:\n  test:\n    runs-on: ubuntu-latest\n    steps:\n      - run: true\n"
    )


def global_workflow(*, with_paths: bool = False) -> str:
    paths = "    paths:\n      - 'src/**'\n" if with_paths else ""
    return (
        "name: Global\n\n"
        "on:\n"
        "  push:\n"
        "    branches:\n"
        "      - main\n"
        f"{paths}"
        "  pull_request:\n"
        f"{paths}"
        "\nconcurrency:\n"
        f"  group: {CANONICAL_GROUP}\n"
        f"  cancel-in-progress: {CANONICAL_CANCEL}\n"
        "\npermissions:\n  contents: read\n\n"
        "jobs:\n  test:\n    runs-on: ubuntu-latest\n    steps:\n      - run: true\n"
    )


def mutating_workflow(*, cancel: bool = False) -> str:
    concurrency = "\nconcurrency:\n  cancel-in-progress: true\n" if cancel else ""
    return (
        "name: Mutating\n\n"
        "on:\n"
        "  push:\n"
        "    branches:\n"
        "      - feat/materialize\n"
        "    paths:\n"
        "      - 'migration/**'\n"
        f"{concurrency}\n"
        "permissions:\n  contents: write\n\n"
        "jobs:\n  test:\n    runs-on: ubuntu-latest\n    steps:\n      - run: true\n"
    )


def write_temp_repo(root: Path, workflows: dict[str, tuple[str, str]]) -> None:
    workflow_dir = root / ".github" / "workflows"
    policy_dir = root / "engineering" / "tooling" / "ci"
    workflow_dir.mkdir(parents=True)
    policy_dir.mkdir(parents=True)
    policy_workflows: dict[str, dict[str, object]] = {}
    for filename, (workflow_class, content) in workflows.items():
        relative = f".github/workflows/{filename}"
        (workflow_dir / filename).write_text(content, encoding="utf-8")
        policy_workflows[relative] = {"class": workflow_class}
    (policy_dir / "queue-control-policy.json").write_text(
        json.dumps(
            {
                "schema_version": 1,
                "classes": ["GLOBAL_READ_ONLY", "SCOPED_READ_ONLY", "MUTATING_EXEMPT"],
                "workflows": policy_workflows,
            },
            indent=2,
        ) + "\n",
        encoding="utf-8",
    )


class QueueControlPolicyTest(unittest.TestCase):
    def test_policy_is_closed_over_factory_workflows(self) -> None:
        policy = load_policy()
        actual = {
            str(path.relative_to(ROOT)).replace("\\", "/")
            for path in factory_workflow_paths()
        }
        declared = set(policy["workflows"])
        self.assertEqual(declared, actual)
        self.assertEqual(len(actual), 41)

    def test_global_and_mutating_classifications_are_exact(self) -> None:
        policy = load_policy()["workflows"]
        self.assertEqual(policy[".github/workflows/factory-e1-s1-governance.yml"]["class"], "GLOBAL_READ_ONLY")
        self.assertEqual(policy[".github/workflows/factory-sonar-ci.yml"]["class"], "GLOBAL_READ_ONLY")
        self.assertEqual(policy[".github/workflows/factory-full-skill-materialize.yml"]["class"], "MUTATING_EXEMPT")

    def test_repository_satisfies_queue_control_policy(self) -> None:
        result = validator.validate_repository(ROOT)
        self.assertTrue(result.ok, result.errors_text)

    def test_i9_main_push_is_path_scoped(self) -> None:
        text = (WORKFLOWS / "factory-engineering-i9-machine-foundation.yml").read_text(encoding="utf-8")
        push = trigger_block(text, "push")
        self.assertIn("\n    paths:", push, "I9 main push must be path-scoped")

    def test_sonar_has_safe_read_only_concurrency(self) -> None:
        text = (WORKFLOWS / "factory-sonar-ci.yml").read_text(encoding="utf-8")
        self.assertIn("concurrency:", text)
        self.assertIn(f"group: {CANONICAL_GROUP}", text)
        self.assertIn(f"cancel-in-progress: {CANONICAL_CANCEL}", text)

    def test_mutating_materializer_has_no_cancel_in_progress(self) -> None:
        text = (WORKFLOWS / "factory-full-skill-materialize.yml").read_text(encoding="utf-8")
        self.assertNotIn("cancel-in-progress:", text)

    def test_docs_only_main_change_schedules_only_global_gates(self) -> None:
        scheduled = validator.workflows_for_changed_paths(ROOT, ("plans/example.md",))
        self.assertEqual(
            scheduled,
            (
                ".github/workflows/factory-e1-s1-governance.yml",
                ".github/workflows/factory-sonar-ci.yml",
            ),
        )


class QueueControlNegativeTest(unittest.TestCase):
    def test_rejects_unclassified_workflow(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            write_temp_repo(root, {"factory-a.yml": ("SCOPED_READ_ONLY", scoped_workflow())})
            (root / ".github/workflows/factory-extra.yml").write_text(scoped_workflow(), encoding="utf-8")
            result = validator.validate_repository(root)
            self.assertIn("unclassified workflow", result.errors_text)

    def test_rejects_policy_entry_for_missing_workflow(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            write_temp_repo(root, {"factory-a.yml": ("SCOPED_READ_ONLY", scoped_workflow())})
            policy_path = root / "engineering/tooling/ci/queue-control-policy.json"
            policy = json.loads(policy_path.read_text(encoding="utf-8"))
            policy["workflows"][".github/workflows/factory-missing.yml"] = {"class": "SCOPED_READ_ONLY"}
            policy_path.write_text(json.dumps(policy), encoding="utf-8")
            result = validator.validate_repository(root)
            self.assertIn("policy points to missing workflow", result.errors_text)

    def test_rejects_missing_push_paths(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            write_temp_repo(root, {"factory-a.yml": ("SCOPED_READ_ONLY", scoped_workflow(push_paths=False))})
            result = validator.validate_repository(root)
            self.assertIn("missing push.paths", result.errors_text)

    def test_rejects_mismatched_push_and_pr_paths(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            content = scoped_workflow().replace("    paths:\n      - 'src/**'\n  pull_request:", "    paths:\n      - 'other/**'\n  pull_request:", 1)
            write_temp_repo(root, {"factory-a.yml": ("SCOPED_READ_ONLY", content)})
            result = validator.validate_repository(root)
            self.assertIn("push.paths != pull_request.paths", result.errors_text)

    def test_rejects_missing_read_only_concurrency(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            write_temp_repo(root, {"factory-a.yml": ("SCOPED_READ_ONLY", scoped_workflow(concurrency=False))})
            result = validator.validate_repository(root)
            self.assertIn("missing canonical concurrency", result.errors_text)

    def test_rejects_concurrency_that_can_cancel_main(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            write_temp_repo(root, {"factory-a.yml": ("SCOPED_READ_ONLY", scoped_workflow(cancel="true"))})
            result = validator.validate_repository(root)
            self.assertIn("missing canonical concurrency", result.errors_text)

    def test_rejects_domain_paths_on_global_workflow(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            write_temp_repo(root, {"factory-global.yml": ("GLOBAL_READ_ONLY", global_workflow(with_paths=True))})
            result = validator.validate_repository(root)
            self.assertIn("global workflow must not use domain paths", result.errors_text)

    def test_rejects_cancel_in_progress_on_mutating_workflow(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            write_temp_repo(root, {"factory-mutating.yml": ("MUTATING_EXEMPT", mutating_workflow(cancel=True))})
            result = validator.validate_repository(root)
            self.assertIn("mutating workflow must not use cancel-in-progress", result.errors_text)

    def test_rejects_inline_paths_structure(self) -> None:
        content = scoped_workflow().replace("    paths:\n      - 'src/**'\n", "    paths: ['src/**']\n", 1)
        with self.assertRaises(validator.QueueControlError):
            validator.parse_workflow_contract(content, "factory-inline.yml")


if __name__ == "__main__":
    unittest.main()
